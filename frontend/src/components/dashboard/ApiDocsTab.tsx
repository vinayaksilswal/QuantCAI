import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Copy, Check, Terminal, Code2, ShieldAlert } from 'lucide-react';
import { toast } from 'sonner';

interface CodeSnippet {
  python: string;
  javascript: string;
  curl: string;
}

export function ApiDocsTab() {
  const [activeLang, setActiveLang] = useState<'python' | 'javascript' | 'curl'>('python');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    toast.success('Copied code snippet to clipboard.');
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getBaseUrl = () => {
    return window.location.origin;
  };

  const endpoints = [
    {
      title: "1. Authentication",
      description: "All requests must authenticate using the `X-API-Key` header with your active developer credentials. Ensure you keep your keys secure.",
      method: "HEADER",
      path: "X-API-Key: qc_live_••••••••",
      snippets: {
        python: `# Pass API key inside headers\nheaders = {\n    "X-API-Key": "your_qc_live_key_here",\n    "Content-Type": "application/json"\n}`,
        javascript: `// Pass API key inside headers\nconst headers = {\n  "X-API-Key": "your_qc_live_key_here",\n  "Content-Type": "application/json"\n};`,
        curl: `curl -H "X-API-Key: your_qc_live_key_here" \\\n     -H "Content-Type: application/json" \\\n     ${getBaseUrl()}/api/v1/...`
      }
    },
    {
      title: "2. Simulate Quantum Circuit",
      description: "Submits a JSON gate instruction payload to run on the AerSimulator. Returns execution probabilities and simulation overhead.",
      method: "POST",
      path: "/api/v1/circuit/simulate",
      snippets: {
        python: `import requests\n\nurl = "${getBaseUrl()}/api/v1/circuit/simulate"\nheaders = {\n    "X-API-Key": "your_qc_live_key_here",\n    "Content-Type": "application/json"\n}\n\npayload = {\n    "num_qubits": 3,\n    "shots": 1024,\n    "use_noise": False,\n    "gates": [\n        {"name": "h", "qubits": [0]},\n        {"name": "cx", "qubits": [0, 1]},\n        {"name": "measure", "qubits": [0, 1]}\n    ]\n}\n\nresponse = requests.post(url, json=payload, headers=headers)\nprint(response.json())`,
        javascript: `const url = "${getBaseUrl()}/api/v1/circuit/simulate";\nconst payload = {\n  num_qubits: 3,\n  shots: 1024,\n  use_noise: false,\n  gates: [\n    { name: "h", qubits: [0] },\n    { name: "cx", qubits: [0, 1] },\n    { name: "measure", qubits: [0, 1] }\n  ]\n};\n\nconst response = await fetch(url, {\n  method: "POST",\n  headers: {\n    "X-API-Key": "your_qc_live_key_here",\n    "Content-Type": "application/json"\n  },\n  body: JSON.stringify(payload)\n});\nconst data = await response.json();\nconsole.log(data);`,
        curl: `curl -X POST ${getBaseUrl()}/api/v1/circuit/simulate \\\n     -H "X-API-Key: your_qc_live_key_here" \\\n     -H "Content-Type: application/json" \\\n     -d '{\n       "num_qubits": 3,\n       "shots": 1024,\n       "use_noise": false,\n       "gates": [\n         {"name": "h", "qubits": [0]},\n         {"name": "cx", "qubits": [0, 1]},\n         {"name": "measure", "qubits": [0, 1]}\n       ]\n     }'`
      }
    },
    {
      title: "3. Export to OpenQASM 3.0",
      description: "Translates standard JSON quantum instructions directly into raw OpenQASM 3.0 specification strings.",
      method: "POST",
      path: "/api/v1/circuit/export",
      snippets: {
        python: `import requests\n\nurl = "${getBaseUrl()}/api/v1/circuit/export"\nheaders = {\n    "X-API-Key": "your_qc_live_key_here",\n    "Content-Type": "application/json"\n}\n\npayload = {\n    "num_qubits": 2,\n    "gates": [\n        {"name": "h", "qubits": [0]},\n        {"name": "cx", "qubits": [0, 1]}\n    ]\n}\n\nresponse = requests.post(url, json=payload, headers=headers)\nprint(response.json()["qasm"])`,
        javascript: `const url = "${getBaseUrl()}/api/v1/circuit/export";\nconst payload = {\n  num_qubits: 2,\n  gates: [\n    { name: "h", qubits: [0] },\n    { name: "cx", qubits: [0, 1] }\n  ]\n};\n\nconst response = await fetch(url, {\n  method: "POST",\n  headers: {\n    "X-API-Key": "your_qc_live_key_here",\n    "Content-Type": "application/json"\n  },\n  body: JSON.stringify(payload)\n});\nconst data = await response.json();\nconsole.log(data.qasm);`,
        curl: `curl -X POST ${getBaseUrl()}/api/v1/circuit/export \\\n     -H "X-API-Key: your_qc_live_key_here" \\\n     -H "Content-Type: application/json" \\\n     -d '{\n       "num_qubits": 2,\n       "gates": [\n         {"name": "h", "qubits": [0]},\n         {"name": "cx", "qubits": [0, 1]}\n       ]\n     }'`
      }
    },
    {
      title: "4. Run PQC TLS Scan",
      description: "Performs full handshake audits on targets to extract active public key curves, algorithms, and HNDL vulnerabilities.",
      method: "POST",
      path: "/api/v1/pqc/scan",
      snippets: {
        python: `import requests\n\nurl = "${getBaseUrl()}/api/v1/pqc/scan"\nheaders = {\n    "X-API-Key": "your_qc_live_key_here",\n    "Content-Type": "application/json"\n}\n\npayload = {\n    "domain": "google.com",\n    "port": 443\n}\n\nresponse = requests.post(url, json=payload, headers=headers)\nprint(response.json())`,
        javascript: `const url = "${getBaseUrl()}/api/v1/pqc/scan";\nconst payload = {\n  domain: "google.com",\n  port: 443\n};\n\nconst response = await fetch(url, {\n  method: "POST",\n  headers: {\n    "X-API-Key": "your_qc_live_key_here",\n    "Content-Type": "application/json"\n  },\n  body: JSON.stringify(payload)\n});\nconst data = await response.json();\nconsole.log(data);`,
        curl: `curl -X POST ${getBaseUrl()}/api/v1/pqc/scan \\\n     -H "X-API-Key: your_qc_live_key_here" \\\n     -H "Content-Type: application/json" \\\n     -d '{\n       "domain": "google.com",\n       "port": 443\n     }'`
      }
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in font-sans">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-syne bg-gradient-to-r from-blue-400 via-indigo-200 to-purple-400 bg-clip-text text-transparent">
            API Documentation
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Standard integration guidelines for running metered quantum simulation workflows and cryptographic scans.
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-blue-500/20 bg-blue-500/5 text-blue-300 text-xs font-mono font-semibold">
          <Code2 className="w-3.5 h-3.5" /> API VERSION: V1.0
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center gap-3 pb-3">
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400 border border-blue-500/20">
              <Terminal className="w-4 h-4" />
            </div>
            <CardTitle className="text-sm font-semibold text-white">Rate Limits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-300 leading-relaxed font-mono">
            <p>All endpoints enforce request thresholds mapped to your subscription plan. Standard rate limit headers are included in all API responses:</p>
            <ul className="list-disc pl-4 space-y-1 mt-1 text-[10px]">
              <li><strong className="text-white">X-RateLimit-Limit:</strong> Total daily query quota.</li>
              <li><strong className="text-white">X-RateLimit-Remaining:</strong> Remaining calls in current reset cycle.</li>
              <li><strong className="text-white">X-RateLimit-Reset:</strong> Seconds remaining until daily reset.</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center gap-3 pb-3">
            <div className="p-2 bg-red-500/10 rounded-lg text-red-400 border border-red-500/20">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <CardTitle className="text-sm font-semibold text-white">Security & Billing Safety</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-300 leading-relaxed font-mono">
            <p>Wallet top-ups must have a positive credit balance to authenticate requests. If balance drops to $0 or lower:</p>
            <ul className="list-disc pl-4 space-y-1 mt-1 text-[10px]">
              <li>API keys are temporarily blocked automatically.</li>
              <li>Requests reject with <code className="text-red-400 bg-red-950/20 px-1 rounded">402 Payment Required</code>.</li>
              <li>Top up simulated credits via your dashboard to unblock.</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Code language tabs selector */}
      <div className="flex border-b border-slate-850">
        {(['python', 'javascript', 'curl'] as const).map((lang) => (
          <button
            key={lang}
            onClick={() => setActiveLang(lang)}
            className={`px-6 py-3 text-xs font-mono font-bold uppercase tracking-wider border-b-2 transition-all ${
              activeLang === lang
                ? 'border-blue-500 text-blue-400 bg-slate-900/20'
                : 'border-transparent text-slate-500 hover:text-slate-350'
            }`}
          >
            {lang === 'python' ? 'Python' : lang === 'javascript' ? 'JavaScript' : 'cURL'}
          </button>
        ))}
      </div>

      {/* Endpoints details */}
      <div className="space-y-8">
        {endpoints.map((ep, idx) => (
          <div key={idx} className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start border-b border-slate-800/40 pb-8">
            {/* Documentation (Left: 5 columns) */}
            <div className="lg:col-span-5 space-y-3">
              <h3 className="text-lg font-bold text-white font-syne">{ep.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed font-inter">
                {ep.description}
              </p>
              <div className="flex items-center gap-2 mt-2 font-mono text-[11px]">
                <Badge className={`${
                  ep.method === 'POST' ? 'bg-blue-600/15 text-blue-400 border-blue-500/20' : 
                  ep.method === 'HEADER' ? 'bg-amber-600/15 text-amber-400 border-amber-500/20' : 
                  'bg-slate-700/20 text-slate-400'
                } border`}>
                  {ep.method}
                </Badge>
                <span className="text-slate-300 font-semibold select-all">{ep.path}</span>
              </div>
            </div>

            {/* Code Block (Right: 7 columns) */}
            <div className="lg:col-span-7 bg-slate-950/60 rounded-2xl border border-slate-850 overflow-hidden relative group shadow-2xl">
              <button
                onClick={() => handleCopy(ep.snippets[activeLang], idx)}
                className="absolute top-3 right-3 p-2 rounded-lg border border-slate-800 bg-slate-900 hover:border-slate-700 transition-all text-slate-400 hover:text-white"
                title="Copy snippet"
              >
                {copiedIndex === idx ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
              <div className="p-4 overflow-x-auto text-[11px] font-mono text-slate-300 whitespace-pre leading-relaxed select-all">
                {ep.snippets[activeLang]}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
