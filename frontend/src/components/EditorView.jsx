import { useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import {
    Upload,
    Wand2,
    Copy,
    Check,
    Download,
    Loader2,
    FileCode2,
    Info,
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DEFAULT_CODE = `// Paste your Verilog module here
module adder (
    input [3:0] a,
    input [3:0] b,
    output [4:0] sum
);
    assign sum = a + b;
endmodule
`;

export default function EditorView({ token }) {
    const [code, setCode] = useState(DEFAULT_CODE);
    const [testbench, setTestbench] = useState('');
    const [metadata, setMetadata] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [copied, setCopied] = useState(false);
    const fileInputRef = useRef(null);

    const handleGenerate = async () => {
        if (!code.trim()) {
            setError('Please enter a Verilog module first.');
            return;
        }
        setError('');
        setLoading(true);
        setTestbench('');
        setMetadata(null);
        try {
            const res = await fetch(`${API_URL}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ code }),
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || 'Generation failed');
            }
            setTestbench(data.testbench);
            setMetadata(data.metadata);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            setCode(event.target.result);
            setError('');
        };
        reader.readAsText(file);
        // Reset input so the same file can be re-uploaded
        e.target.value = '';
    };

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(testbench);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            setError('Failed to copy to clipboard.');
        }
    };

    const handleDownload = () => {
        const moduleName = metadata?.module_name || 'module';
        const blob = new Blob([testbench], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${moduleName}_tb.v`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <main className="flex flex-1 flex-col lg:flex-row overflow-hidden">
            {/* Left pane: Verilog module editor */}
            <section className="flex flex-col flex-1 min-h-[250px] lg:min-h-0 border-b lg:border-b-0 lg:border-r border-gray-800">
                <div className="flex items-center justify-between px-4 py-2.5 bg-gray-900 border-b border-gray-800 shrink-0">
                    <div className="flex items-center gap-2">
                        <FileCode2 className="w-4 h-4 text-emerald-400" />
                        <h2 className="text-sm font-semibold text-gray-200">
                            Verilog Module
                        </h2>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="flex items-center gap-1.5 text-xs font-medium text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 px-2.5 py-1.5 rounded-md transition"
                        >
                            <Upload className="w-3.5 h-3.5" />
                            Upload .v
                        </button>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".v,.sv,.vhd"
                            onChange={handleFileUpload}
                            className="hidden"
                        />
                    </div>
                </div>

                <Editor
                    height="100%"
                    defaultLanguage="verilog"
                    language="verilog"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    theme="vs-dark"
                    options={{
                        fontSize: 14,
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        wordWrap: 'on',
                        automaticLayout: true,
                        tabSize: 4,
                        padding: { top: 12, bottom: 12 },
                    }}
                />
            </section>

            {/* Right pane: Generated testbench */}
            <section className="flex flex-col flex-1 min-h-[250px] lg:min-h-0">
                <div className="flex items-center justify-between px-4 py-2.5 bg-gray-900 border-b border-gray-800 shrink-0">
                    <div className="flex items-center gap-2">
                        <Wand2 className="w-4 h-4 text-teal-400" />
                        <h2 className="text-sm font-semibold text-gray-200">
                            Generated Testbench
                        </h2>
                        {testbench && (
                            <span className="text-xs text-gray-500">
                                {metadata?.module_name || 'module'}_tb.v
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        {testbench && (
                            <>
                                <button
                                    onClick={handleCopy}
                                    className="flex items-center gap-1.5 text-xs font-medium text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 px-2.5 py-1.5 rounded-md transition"
                                >
                                    {copied ? (
                                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                                    ) : (
                                        <Copy className="w-3.5 h-3.5" />
                                    )}
                                    {copied ? 'Copied' : 'Copy'}
                                </button>
                                <button
                                    onClick={handleDownload}
                                    className="flex items-center gap-1.5 text-xs font-medium text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 px-2.5 py-1.5 rounded-md transition"
                                >
                                    <Download className="w-3.5 h-3.5" />
                                    Download
                                </button>
                            </>
                        )}
                    </div>
                </div>

                <div className="flex-1 relative">
                    {loading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950/80 z-10">
                            <Loader2 className="w-10 h-10 text-emerald-500 animate-spin mb-4" />
                            <p className="text-gray-300 text-sm font-medium">
                                Generating testbench...
                            </p>
                            <p className="text-gray-500 text-xs mt-1">
                                AI is analyzing your design and writing the testbench
                            </p>
                        </div>
                    ) : testbench ? (
                        <Editor
                            height="100%"
                            defaultLanguage="verilog"
                            language="verilog"
                            value={testbench}
                            theme="vs-dark"
                            options={{
                                fontSize: 14,
                                minimap: { enabled: false },
                                scrollBeyondLastLine: false,
                                wordWrap: 'on',
                                automaticLayout: true,
                                readOnly: true,
                                domReadOnly: true,
                                tabSize: 4,
                                padding: { top: 12, bottom: 12 },
                            }}
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-center px-6">
                            {error ? (
                                <div className="max-w-md">
                                    <div className="bg-red-900/30 border border-red-800 text-red-300 text-sm rounded-lg px-4 py-3 mb-4 text-left">
                                        {error}
                                    </div>
                                    <button
                                        onClick={handleGenerate}
                                        className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2.5 rounded-lg transition"
                                    >
                                        <Wand2 className="w-4 h-4" />
                                        Try Again
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <div className="w-14 h-14 rounded-2xl bg-gray-800 flex items-center justify-center mb-4">
                                        <Wand2 className="w-7 h-7 text-gray-500" />
                                    </div>
                                    <p className="text-gray-400 text-sm max-w-sm">
                                        Enter your Verilog module in the left pane, then click
                                        <span className="text-emerald-400 font-medium"> Generate Testbench </span>
                                        below to create an AI-powered testbench.
                                    </p>
                                </>
                            )}
                        </div>
                    )}
                </div>

                <div className="px-4 py-3 bg-gray-900 border-t border-gray-800 shrink-0">
                    <button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Wand2 className="w-5 h-5" />
                        )}
                        {loading ? 'Generating...' : 'Generate Testbench'}
                    </button>
                </div>
            </section>
        </main>
    );
}
