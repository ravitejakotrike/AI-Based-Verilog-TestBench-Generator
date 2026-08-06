"""
Verilog module parser.

Uses PyVerilog to extract structured metadata (module name, inputs, outputs,
parameters, clock/reset signals). Falls back to a regex-based parser when
PyVerilog cannot handle non-compliant or partial syntax.

Expected output shape:
{
  "module_name": str,
  "inputs": [ {"name": str, "width": str} ],
  "outputs": [ {"name": str, "width": str} ],
  "parameters": [ {"name": str, "value": str} ],
  "clocks": [str],
  "resets": [str],
  "raw": str
}
"""

import re

try:
    from pyverilog.vparser.parser import parse as pyv_parse
    PYVERILOG_AVAILABLE = True
except Exception:  # pragma: no cover - pyverilog may not be installed
    PYVERILOG_AVAILABLE = False


# ---------------------------------------------------------------------------
# Regex helpers (fallback parser)
# ---------------------------------------------------------------------------

_PARAM_RE = re.compile(
    r"(?:parameter\s+)?"
    r"(?:(?:\[[^;\]]*\])\s+)?"          # optional parameter width
    r"([A-Za-z_][A-Za-z0-9_]*)"          # parameter name
    r"\s*=\s*"
    r"([0-9]+'[hHbBoOdD][0-9a-fA-F_xXzZ]+|[0-9]+|\w+)",  # value
    re.IGNORECASE,
)

# Matches a single port declaration: direction [type] [signed] [width] name
# Handles ANSI-style inline declarations and standalone declarations.
_PORT_DECL_RE = re.compile(
    r"\b(?:input|output|inout)\b"
    r"(?:\s+(?:reg|wire|logic|signed|unsigned))?"
    r"(?:\s+(?:reg|wire|logic|signed|unsigned))?"
    r"(?:\s*\[([^\]]*)\])?"              # optional width e.g. [7:0]
    r"\s+([A-Za-z_][A-Za-z0-9_]*)"       # port name
    r"(?=\s*[,);])",                     # must be followed by , ) or ;
    re.IGNORECASE,
)

_CLOCK_RE = re.compile(r"\b(clk|clock)\b", re.IGNORECASE)
_RESET_RE = re.compile(r"\b(rst|reset|rst_n|resetn)\b", re.IGNORECASE)


def _parse_width(width: str | None) -> str:
    """Normalize a width expression for display."""
    if not width:
        return "1"
    return width.strip()


def _regex_parse(source: str) -> dict:
    """Fallback parser using regular expressions."""
    # Module name
    module_match = re.search(
        r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)", source
    )
    module_name = module_match.group(1) if module_match else "unknown_module"

    # Parameters
    parameters = []
    for m in _PARAM_RE.finditer(source):
        parameters.append({"name": m.group(1), "value": m.group(2)})

    # Ports
    inputs = []
    outputs = []
    for m in _PORT_DECL_RE.finditer(source):
        direction = m.group(0).split()[0].lower()
        width = _parse_width(m.group(1))
        names = [n.strip() for n in m.group(2).split(",") if n.strip()]
        for name in names:
            entry = {"name": name, "width": width}
            if direction == "input":
                inputs.append(entry)
            elif direction == "output":
                outputs.append(entry)

    # Clocks / resets
    clock_hits = set()
    reset_hits = set()
    for port in inputs + outputs:
        if _CLOCK_RE.search(port["name"]):
            clock_hits.add(port["name"])
        if _RESET_RE.search(port["name"]):
            reset_hits.add(port["name"])

    return {
        "module_name": module_name,
        "inputs": inputs,
        "outputs": outputs,
        "parameters": parameters,
        "clocks": sorted(clock_hits),
        "resets": sorted(reset_hits),
        "raw": source,
    }


def _pyverilog_parse(source: str) -> dict:
    """Parse using PyVerilog and map AST to our metadata shape."""
    ast, _ = pyv_parse(source, preprocess_include=None, preprocess_define=None)

    module = None
    for definition in ast.description.definitions:
        if hasattr(definition, "module"):
            module = definition.module
        elif hasattr(definition, "name") and definition.name:  # pragma: no cover
            module = definition

    if module is None:
        raise ValueError("No module definition found in Verilog source.")

    module_name = getattr(module, "name", "unknown_module")

    # IO ports from module.portlist
    inputs = []
    outputs = []
    portlist = getattr(module, "portlist", None)
    if portlist and portlist.ports:
        for item in portlist.ports:
            if hasattr(item, "first") and item.first is not None:
                # Either a connection or a declaration alias
                target = item.first
                if hasattr(target, "name"):
                    port_reg = target.name
                    width_expr = getattr(target, "width", None)
                    width = _ast_width(width_expr)
                    direction = getattr(target, "type", None)
                    if direction == "input":
                        inputs.append({"name": port_reg, "width": width})
                    elif direction == "output":
                        outputs.append({"name": port_reg, "width": width})

    # Parameters via module.paramlist
    parameters = []
    paramlist = getattr(module, "paramlist", None)
    if paramlist and paramlist.params:
        for param in paramlist.params:
            name = getattr(param, "name", None)
            value_m = getattr(param, "value", None)
            value = _ast_value(value_m)
            if name:
                parameters.append({"name": name, "value": value})

    # Fallback merging: some codebases declare ports in body, not portlist.
    # Merge any missing IO found by regex to be safe.
    regex_meta = _regex_parse(source)
    existing_inputs = {p["name"] for p in inputs}
    existing_outputs = {p["name"] for p in outputs}
    for p in regex_meta["inputs"]:
        if p["name"] not in existing_inputs:
            inputs.append(p)
    for p in regex_meta["outputs"]:
        if p["name"] not in existing_outputs:
            outputs.append(p)
    if not parameters:
        parameters = regex_meta["parameters"]

    clocks = [p["name"] for p in inputs + outputs if _CLOCK_RE.search(p["name"])]
    resets = [p["name"] for p in inputs + outputs if _RESET_RE.search(p["name"])]

    return {
        "module_name": module_name,
        "inputs": inputs,
        "outputs": outputs,
        "parameters": parameters,
        "clocks": sorted(clocks),
        "resets": sorted(resets),
        "raw": source,
    }


def _ast_width(width_expr) -> str:
    """Extract a readable width string from a PyVerilog width node."""
    if width_expr is None:
        return "1"
    # width is a Width node with .msb/.lsb
    msb = getattr(getattr(width_expr, "msb", None), "value", None)
    lsb = getattr(getattr(width_expr, "lsb", None), "value", None)
    if msb is not None and lsb is not None:
        return f"[{msb}:{lsb}]"
    return "1"


def _ast_value(node) -> str:
    """Convert a PyVerilog value node to a string."""
    if node is None:
        return ""
    if hasattr(node, "value"):
        return str(node.value)
    return str(node)


def parse_verilog(source: str) -> dict:
    """
    Public entry point. Tries PyVerilog first, falls back to regex.
    Returns a flattened metadata dict.
    """
    if PYVERILOG_AVAILABLE:
        try:
            return _pyverilog_parse(source)
        except Exception:
            # Fall through to regex parser on any PyVerilog failure
            pass
    return _regex_parse(source)
