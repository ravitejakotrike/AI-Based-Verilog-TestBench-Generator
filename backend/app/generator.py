"""
AI Testbench generator.

Synthesizes a structured LLM prompt from parsed Verilog metadata and calls an
LLM provider (OpenAI, Gemini, or OpenRouter) to produce a complete Verilog
testbench. Falls back to an offline template generator if no provider is
configured or an API call fails.
"""

import os
import re

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


# ---------------------------------------------------------------------------
# Prompt synthesis
# ---------------------------------------------------------------------------

def _format_ports(ports) -> str:
    if not ports:
        return "  (none)"
    lines = []
    for p in ports:
        width = p.get("width", "1")
        if width and width != "1":
            lines.append(f"  {p['name']} : {width}")
        else:
            lines.append(f"  {p['name']} : 1-bit")
    return "\n".join(lines)


def _format_parameters(parameters) -> str:
    if not parameters:
        return "  (none)"
    lines = []
    for p in parameters:
        lines.append(f"  {p['name']} = {p['value']}")
    return "\n".join(lines)


def build_prompt(metadata: dict) -> str:
    """Build a detailed, structured prompt from parsed Verilog metadata."""
    module_name = metadata.get("module_name", "unknown_module")
    if not module_name or module_name == "unknown_module":
        module_name = "dut"

    inputs = metadata.get("inputs", [])
    outputs = metadata.get("outputs", [])
    parameters = metadata.get("parameters", [])
    clocks = metadata.get("clocks", [])
    resets = metadata.get("resets", [])

    clock_name = clocks[0] if clocks else "clk"
    reset_name = resets[0] if resets else "rst_n"
    active_low = "_n" in reset_name.lower() or "n" == reset_name.lower()[-1:]

    input_names = [p["name"] for p in inputs]
    output_names = [p["name"] for p in outputs]

    prompt = f"""You are an expert Verilog engineer. Generate a COMPLETE and SYNTACTICALLY CORRECT Verilog testbench for the module below.

MODULE NAME: {module_name}

INPUTS:
{_format_ports(inputs)}

OUTPUTS:
{_format_ports(outputs)}

PARAMETERS:
{_format_parameters(parameters)}

CLOCK SIGNAL(S): {', '.join(clocks) if clocks else 'clk (assumed)'}
RESET SIGNAL(S): {', '.join(resets) if resets else 'rst_n (assumed)'}

    The testbench MUST strictly follow these rules:
    1. Timescale directive: `timescale 1ns / 1ps
    2. Declarations:
       - Declare a `reg` ONLY for the inputs explicitly listed above.
       - Declare a `wire` ONLY for the outputs explicitly listed above.
       - STRICTLY FORBIDDEN: Do NOT invent, declare, or drive any extra signals, internal variables, or unnecessary wires that are not part of the DUT ports.
    3. If parameters exist, declare them with the SAME values as the module defaults.
    4. DUT instantiation: Use explicit port mapping for every port.
    5. Clock generation: always #5 {clock_name} = ~{clock_name};
    6. Initial block with:
       - Reset sequence: assert reset for 20ns, then deassert it (respect {'active-low' if active_low else 'active-high'} polarity).
       - Stimulus vectors that exercise the module's functionality.
       - $finish to end simulation.
    7. Monitor statements: $dumpfile("{module_name}_tb.vcd"); $dumpvars(0, {module_name}_tb);
    8. Verify syntax against standard Verilog-2001. Ensure no trailing commas in port maps and no missing semicolons.

    Output ONLY the complete Verilog testbench code wrapped in a single ```verilog code fence. Do not include any extra text, markdown, or explanations outside the code fence."""

    return prompt


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------

def _extract_verilog(text: str) -> str:
    """Extract testbench code from LLM output (strip markdown fences)."""
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            content = parts[1]
            lines = content.splitlines()
            if lines and lines[0].strip().lower() in ("verilog", "systemverilog"):
                lines = lines[1:]
            block = "\n".join(lines).strip()
            if block:
                return block
        blocks = [p.strip() for p in parts[1::2] if p.strip()]
        if blocks:
            return max(blocks, key=len)

    lines = text.splitlines()
    code_start = next(
        (i for i, line in enumerate(lines) if line.strip().startswith("`timescale")),
        0,
    )
    return "\n".join(lines[code_start:]).strip()


# ---------------------------------------------------------------------------
# Provider calls
# ---------------------------------------------------------------------------

def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an expert Verilog/SystemVerilog testbench generator.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def _call_gemini(prompt: str) -> str:
    import urllib.request
    import json

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ]
            }
        ]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


def _call_openrouter(prompt: str) -> str:
    import urllib.request
    import json

    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert Verilog/SystemVerilog testbench generator.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://verilog-tb-generator.local",
            "X-Title": "Verilog Testbench Generator",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Local offline fallback
# ---------------------------------------------------------------------------

def _local_generate(metadata: dict) -> str:
    """
    Offline template-based testbench generator.

    Produces a complete, syntactically valid Verilog testbench purely from the
    parsed metadata. Used as a reliable fallback when no AI credits are
    available or a provider call fails.
    """
    module_name = metadata.get("module_name", "dut")
    if not module_name or module_name == "unknown_module":
        module_name = "dut"

    inputs = metadata.get("inputs", [])
    outputs = metadata.get("outputs", [])
    parameters = metadata.get("parameters", [])
    clocks = metadata.get("clocks", [])
    resets = metadata.get("resets", [])

    clock_name = clocks[0] if clocks else "clk"
    reset_name = resets[0] if resets else "rst_n"
    reset_is_active_low = "_n" in reset_name.lower()

    def sig(name):
        return re.sub(r"\W", "_", name)

    decl_lines = []
    input_regs = []
    for p in inputs:
        name = sig(p["name"])
        input_regs.append(name)
        width = p.get("width", "1")
        if width and width != "1":
            width_str = width if width.startswith("[") else f"[{width}]"
            decl_lines.append(f"    reg {width_str} {name};")
        else:
            decl_lines.append(f"    reg {name};")

    for p in outputs:
        name = sig(p["name"])
        width = p.get("width", "1")
        if width and width != "1":
            width_str = width if width.startswith("[") else f"[{width}]"
            decl_lines.append(f"    wire {width_str} {name};")
        else:
            decl_lines.append(f"    wire {name};")

    clk_sig = sig(clock_name)
    rst_sig = sig(reset_name)
    decl_lines.append(f"    reg {clk_sig} = 0;")
    decl_lines.append(f"    reg {rst_sig} = {'1' if reset_is_active_low else '0'};")

    io_names = set([sig(p["name"]) for p in inputs] + [sig(p["name"]) for p in outputs])
    param_lines = []
    for p in parameters:
        name = p.get("name", "").strip()
        value = p.get("value", "").strip()
        if name and value and sig(name) not in io_names:
            param_lines.append(f"    parameter {name} = {value};")

    port_conns = []
    for p in inputs:
        port_conns.append(f"        .{p['name']}({sig(p['name'])})")
    for p in outputs:
        port_conns.append(f"        .{p['name']}({sig(p['name'])})")
    inst_conns = ",\n".join(port_conns)
    dut_inst = (
        f"\n    {module_name} dut (\n{inst_conns}\n    );"
        if port_conns
        else f"\n    {module_name} dut ();"
    )

    stimulus = []
    if input_regs:
        n = len(input_regs)
        for i in range(n):
            stimulus.append(f"        {input_regs[i]} = 0;")
        stimulus.append("        #10;")
        for i in range(n):
            stimulus.append(f"        {input_regs[i]} = 1;")
        stimulus.append("        #10;")
        stimulus.append(f"        {input_regs[0]} = 0;")
        stimulus.append("        #10;")
        stimulus.append(f"        {input_regs[0]} = 1;")
        stimulus.append("        #10;")
    else:
        stimulus.append("        #20;")

    if reset_is_active_low:
        reset_seq = (
            f"        {rst_sig} = 0;      // assert reset (active low)\n"
            f"        #20;\n"
            f"        {rst_sig} = 1;      // deassert reset"
        )
    else:
        reset_seq = (
            f"        {rst_sig} = 1;      // assert reset (active high)\n"
            f"        #20;\n"
            f"        {rst_sig} = 0;      // deassert reset"
        )

    stim_text = "\n".join(stimulus)

    tb = f"""`timescale 1ns / 1ps

module {module_name}_tb;

    // Register declarations for inputs
{chr(10).join(decl_lines)}

    // Parameters
{chr(10).join(param_lines) if param_lines else '    // (no parameters)'}
{dut_inst}

    // Clock generation
    always #5 {clk_sig} = ~{clk_sig};

    // Initial block: reset, stimulus, and monitoring
    initial begin
        // Dump waveform
        $dumpfile("{module_name}_tb.vcd");
        $dumpvars(0, {module_name}_tb);

        // Apply reset
{reset_seq};

        // Stimulus vectors
{stim_text}

        // Finish simulation
        $finish;
    end

    // Monitor signal changes
    initial begin
        $monitor("t=%0t ", $time);
    end

endmodule
"""

    tb = tb.replace("\n\n\n", "\n\n")
    return tb.strip()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_testbench(metadata: dict) -> dict:
    """Generate a testbench from metadata. Returns {'testbench': str}."""
    use_ai = os.getenv("USE_AI", "true").lower() in ("1", "true", "yes", "on")

    if use_ai:
        try:
            prompt = build_prompt(metadata)
            if AI_PROVIDER == "gemini":
                if not GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY is not configured.")
                raw = _call_gemini(prompt)
            elif AI_PROVIDER == "openrouter":
                if not OPENROUTER_API_KEY:
                    raise ValueError("OPENROUTER_API_KEY is not configured.")
                raw = _call_openrouter(prompt)
            else:
                if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-YOUR"):
                    raise ValueError("OPENAI_API_KEY is not configured.")
                raw = _call_openai(prompt)

            testbench = _extract_verilog(raw)
            if testbench:
                return {"testbench": testbench, "source": "ai"}
        except Exception:
            # Fall back to the local template generator on any provider error
            pass

    # Local offline fallback (no API credits required)
    testbench = _local_generate(metadata)
    return {"testbench": testbench, "source": "local"}
