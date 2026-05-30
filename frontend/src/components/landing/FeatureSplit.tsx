import { useState } from 'react';

/* ── Inline SVG Icons ─────────────────────────────────────────────── */
const ShieldIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
  </svg>
);

const CodeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
  </svg>
);

/* ── Code snippets ────────────────────────────────────────────────── */
const curlSnippet = `curl -X POST https://api.quantcai.in/v1/simulate \\
  -H "X-API-Key: qcai_your_key" \\
  -d '{
    "circuit_qasm": "OPENQASM 2.0; qreg q[2]; h q[0]; cx q[0],q[1]; measure q -> c;",
    "shots": 1024
  }'`;

const responseSnippet = `{
  "job_id": "sim_8f3k2x",
  "status": "completed",
  "counts": {
    "00": 512,
    "11": 512
  },
  "execution_time_ms": 847
}`;

export const FeatureSplit = () => {
  const [scanDomain, setScanDomain] = useState('');
  const [showResult, setShowResult] = useState(false);

  const handleScan = (e: React.FormEvent) => {
    e.preventDefault();
    if (scanDomain.trim()) setShowResult(true);
  };

  return (
    <section id="features" className="py-20 sm:py-28 px-4 sm:px-6 relative z-10">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <p className="text-teal-400 text-xs font-mono uppercase tracking-widest mb-3 drop-shadow-sm">
            Two APIs. One Platform.
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white drop-shadow-lg">
            Built for developers. Trusted by security teams.
          </h2>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* ── LEFT: Quantum Simulation API ── */}
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 sm:p-8 group hover:border-teal-400/30 transition-all duration-300 shadow-2xl shadow-blue-500/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg border border-teal-400/30 flex items-center justify-center text-teal-400 bg-teal-400/10">
                <CodeIcon />
              </div>
              <div>
                <h3 className="font-bold text-lg text-white drop-shadow-md">Quantum Simulation API</h3>
                <p className="text-blue-200 text-xs">For developers</p>
              </div>
            </div>

            <p className="text-blue-200 text-sm mb-6 leading-relaxed drop-shadow-sm">
              POST your OpenQASM circuit. Get results back in &lt; 3 seconds.
              Statevector, counts, and noise-model simulation — all via REST.
            </p>

            {/* Code block - Request */}
            <div className="rounded-xl border border-white/10 bg-black/30 backdrop-blur-sm overflow-hidden mb-3">
              <div className="flex items-center gap-2 px-3 py-1.5 border-b border-white/10 bg-black/20">
                <span className="w-2 h-2 rounded-full bg-red-400/60" />
                <span className="w-2 h-2 rounded-full bg-yellow-400/60" />
                <span className="w-2 h-2 rounded-full bg-green-400/60" />
                <span className="ml-2 text-[10px] text-blue-300/70 font-mono">request.sh</span>
              </div>
              <pre className="p-4 text-xs sm:text-[13px] leading-relaxed text-blue-100 font-mono overflow-x-auto">
                <code>{curlSnippet}</code>
              </pre>
            </div>

            {/* Code block - Response */}
            <div className="rounded-xl border border-white/10 bg-black/30 backdrop-blur-sm overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-1.5 border-b border-white/10 bg-black/20">
                <span className="text-[10px] text-teal-400 font-mono">← 200 OK</span>
              </div>
              <pre className="p-4 text-xs sm:text-[13px] leading-relaxed text-teal-300/80 font-mono overflow-x-auto">
                <code>{responseSnippet}</code>
              </pre>
            </div>
          </div>

          {/* ── RIGHT: PQC Scanner ── */}
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 sm:p-8 group hover:border-teal-400/30 transition-all duration-300 shadow-2xl shadow-purple-500/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg border border-teal-400/30 flex items-center justify-center text-teal-400 bg-teal-400/10">
                <ShieldIcon />
              </div>
              <div>
                <h3 className="font-bold text-lg text-white drop-shadow-md">PQC Vulnerability Scanner</h3>
                <p className="text-blue-200 text-xs">For security teams</p>
              </div>
            </div>

            <p className="text-blue-200 text-sm mb-6 leading-relaxed drop-shadow-sm">
              Is your TLS stack quantum-safe? We'll tell you in 30 seconds.
              Full certificate-chain audit with NIST PQC compliance scoring.
            </p>

            {/* Scanner input */}
            <form onSubmit={handleScan} className="mb-6">
              <div className="flex gap-2">
                <input
                  id="scanner-input"
                  type="text"
                  placeholder="Enter a domain to scan"
                  value={scanDomain}
                  onChange={e => setScanDomain(e.target.value)}
                  className="flex-1 px-3 py-2.5 rounded-lg border border-white/10 bg-black/30 backdrop-blur-sm text-white text-sm font-mono placeholder:text-blue-300/40 focus:outline-none focus:border-teal-400/50 focus:ring-1 focus:ring-teal-400/20 transition-all"
                />
                <button
                  id="scanner-btn"
                  type="submit"
                  className="px-5 py-2.5 rounded-lg bg-teal-500 text-white text-sm font-semibold hover:bg-teal-400 transition-all whitespace-nowrap shadow-lg shadow-teal-500/25"
                >
                  Scan Now
                </button>
              </div>
            </form>

            {/* Demo result */}
            <div className={`rounded-xl border overflow-hidden transition-all duration-500 backdrop-blur-sm ${showResult ? 'border-red-400/40 opacity-100' : 'border-white/10 opacity-60'}`}>
              <div className="px-4 py-2.5 border-b border-white/10 bg-black/20 flex items-center justify-between">
                <span className="text-sm font-mono text-white">{showResult && scanDomain ? scanDomain : 'example.com'}</span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-400 tracking-wider">CRITICAL</span>
              </div>
              <div className="p-4 bg-black/20 space-y-3">
                <div className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-white font-mono">RSA-2048 certificate detected</p>
                    <p className="text-xs text-blue-300/70 mt-0.5">Vulnerable to Shor's algorithm · Estimated break: 2030–2035</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-white font-mono">ECDHE key exchange — not quantum-safe</p>
                    <p className="text-xs text-blue-300/70 mt-0.5">Migrate to ML-KEM (FIPS 203) for hybrid key exchange</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-white font-mono">SHA-256 hashing — acceptable</p>
                    <p className="text-xs text-blue-300/70 mt-0.5">Grover's provides only quadratic speedup · Low risk</p>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
                  <span className="text-xs text-blue-300/70 font-mono">Risk Score</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-1.5 rounded-full bg-white/10 overflow-hidden">
                      <div className="w-[85%] h-full rounded-full bg-red-400" />
                    </div>
                    <span className="text-sm font-mono font-bold text-red-400">8.5/10</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
