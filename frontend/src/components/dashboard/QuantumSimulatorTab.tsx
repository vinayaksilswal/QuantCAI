import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useAI } from '@/hooks/useAI';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';
import { useSubscription } from '@/context/SubscriptionContext';
import { 
  Play, 
  RotateCcw, 
  AlertCircle, 
  BarChart4, 
  Cpu, 
  Terminal, 
  FileCode, 
  Settings, 
  ShieldAlert, 
  Clock, 
  Sparkles,
  Layers
} from 'lucide-react';

interface SimulationResult {
  status: string;
  execution_time_ms: number;
  probabilities: Record<string, number>;
  num_qubits: number;
  circuit_depth: number;
  warnings?: string[];
  metadata?: {
    backend: string;
    noise_model: string;
    shots: number;
  };
  qpu_telemetry?: {
    provider: string;
    qpu_name: string;
    queue_time_seconds: number;
    calibration_date: string;
    readout_error_rate: number;
    cnot_gate_fidelity: number;
  };
}


const DEFAULT_QASM_3 = `OPENQASM 3.0;
include "stdgates.inc";
qubit[5] q;
bit[5] c;
h q[0];
cx q[0], q[1];
cx q[1], q[2];
c = measure q;`;

export function QuantumSimulatorTab() {
  const { subscriptionPlan } = useAuth();
  const { updateClientContext } = useAI();
  
  // IDE State
  const [qasm, setQasm] = useState(DEFAULT_QASM_3);
  const [shots, setShots] = useState(1024);
  const [backend, setBackend] = useState('Local AerSimulator');
  const [noiseModel, setNoiseModel] = useState('Ideal');
  
  // Results & Console States
  const [activeTab, setActiveTab] = useState<'visualizations' | 'console'>('visualizations');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [rawResponse, setRawResponse] = useState<any>(null);

  // Sync editor parameters to AI Context
  useEffect(() => {
    updateClientContext('qasm-ide', {
      qasm_string: qasm,
      line_count: qasm.split('\n').length,
      console_error: errorMsg
    });
  }, [qasm, errorMsg, updateClientContext]);

  // Sync scroll refs for line numbers
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const { tier } = useSubscription();
  const isFree = tier === 'FREE';
  const maxShots = isFree ? 1024 : 65536;

  // Handle scroll syncing between editor and gutter
  const handleEditorScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Synchronize scrolling on mount and edit
  useEffect(() => {
    handleEditorScroll();
  }, [qasm]);

  const handleShotsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) return;
    setShots(val);
  };

  const handleReset = () => {
    setQasm(DEFAULT_QASM_3);
    setShots(1024);
    setBackend('Local AerSimulator');
    setNoiseModel('Ideal');
    setResult(null);
    setErrorMsg(null);
    setLogs([]);
    setRawResponse(null);
    setActiveTab('visualizations');
    toast.info('Editor parameters reset to default Bell state.');
  };

  const addLog = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = {
      info: '⚙️ [SYSTEM]',
      success: '⚡ [SUCCESS]',
      warning: '⚠️ [WARNING]',
      error: '❌ [ERROR]',
    }[type];
    setLogs((prev) => [...prev, `[${timestamp}] ${prefix} ${message}`]);
  };

  const executeSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setResult(null);
    setRawResponse(null);
    setLogs([]);
    
    // Parse QASM qubits count
    let parsedQubits = 5;
    const qubitMatch = qasm.match(/qubit\s*\[\s*(\d+)\s*\]/i);
    if (qubitMatch) {
      parsedQubits = parseInt(qubitMatch[1], 10);
    } else {
      const qregMatch = qasm.match(/qreg\s+\w+\s*\[\s*(\d+)\s*\]/i);
      if (qregMatch) {
        parsedQubits = parseInt(qregMatch[1], 10);
      }
    }

    if (isFree) {
      if (parsedQubits > 5) {
        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'qubits' } }));
        toast.error("Free tier is limited to 5 qubits. Upgrade to Pro!");
        return;
      }
      if (shots > 1024) {
        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'shots' } }));
        toast.error("Free tier is limited to a maximum of 1,024 shots.");
        return;
      }
      if (noiseModel !== 'Ideal') {
        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'noise' } }));
        toast.error("Noise models require a Pro subscription.");
        return;
      }
    } else if (tier === 'PRO') {
      if (parsedQubits > 30) {
        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'qubits' } }));
        toast.error("Pro tier is limited to 30 qubits. Upgrade to Enterprise!");
        return;
      }
      if (shots > 65536) {
        toast.error("Pro tier is limited to 65,536 shots.");
        return;
      }
    }

    // Client-side validation
    if (shots < 1 || shots > maxShots) {
      toast.error(`Shots must be between 1 and ${maxShots} for your tier.`);
      return;
    }

    setLoading(true);
    addLog('Initiating OpenQASM 3.0 compiler engine...', 'info');
    addLog('Validating qubit declarations and constraints...', 'info');
    addLog(`Configuring backend: ${backend} | Noise: ${noiseModel}...`, 'info');

    // Automatically switch to console tab to view live compiler outputs
    setActiveTab('console');

    try {
      addLog(`Sending compilation task to server...`, 'info');
      const response = await axiosClient.post<SimulationResult>('/api/v1/simulator/execute', {
        qasm_string: qasm,
        shots: shots,
        backend_choice: backend,
        noise_model: noiseModel,
      });

      const data = response.data;
      setRawResponse(data);
      setResult(data);
      
      addLog(`QASM compilation complete. Target qubits: ${data.num_qubits}, Depth: ${data.circuit_depth}`, 'success');
      addLog(`AerSimulator execution finished in ${data.execution_time_ms.toFixed(1)} ms.`, 'success');

      if (data.warnings && data.warnings.length > 0) {
        data.warnings.forEach(warn => {
          addLog(warn, 'warning');
        });
      }

      setLoading(false);
      // Switch back to visualizations to show results
      setActiveTab('visualizations');
      toast.success('Quantum circuit simulated successfully!');
    } catch (err: any) {
      console.error('Simulation execution failed:', err);
      const errorData = err.response?.data?.detail || {};
      const msg = typeof errorData === 'string' ? errorData : errorData.message || err.message || 'FastAPI simulation engine failed.';
      const errorCode = typeof errorData === 'object' ? errorData.error || "" : "";
      const status = err.response?.status;
      
      if (status === 402 || status === 429 || errorCode.includes("LIMIT") || errorCode.includes("RESTRICTED") || errorCode.includes("EXCEEDED")) {
        let reason = 'qubits';
        if (errorCode.includes("DEPTH")) reason = 'depth';
        else if (errorCode.includes("SHOTS")) reason = 'shots';
        else if (errorCode.includes("NOISE")) reason = 'noise';
        else if (errorCode.includes("AI")) reason = 'chats';
        else if (errorCode.includes("PQC")) reason = 'pqc';
        
        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason } }));
      }
      
      const cleanMsg = typeof msg === 'string' ? msg : JSON.stringify(msg);
      setErrorMsg(cleanMsg);
      addLog(`Compilation/Runtime failure. Check stack trace.`, 'error');
      addLog(cleanMsg, 'error');
      
      setLoading(false);
      toast.error('Compilation or execution failed.');
    }
  };

  // Generate line numbers
  const lines = qasm.split('\n');
  const lineCount = Math.max(lines.length, 1);
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1);

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="font-syne font-bold text-2xl text-qc-text tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-qc-accent animate-pulse" />
            QuantCAI Pro Quantum Simulator
          </h2>
          <p className="text-sm text-qc-muted mt-1 font-mono">
            Enterprise multi-qubit compiler and execution engine supporting raw OpenQASM 3.0 grammar.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-qc-accent/10 border border-qc-accent/30 text-qc-accent font-mono capitalize">
            {subscriptionPlan || 'Free'} Tier
          </span>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Editor & Configuration (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="border border-slate-800 rounded-xl bg-slate-950/40 backdrop-blur-xl shadow-2xl overflow-hidden">
            {/* Editor Header Tab Bar */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#0a0f1d]/80 border-b border-slate-800/80">
              <div className="flex items-center gap-2 text-slate-300 font-mono text-xs">
                <FileCode className="w-4 h-4 text-qc-accent" />
                <span>main.qasm</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                <span className="text-[10px] text-slate-500 font-mono">PARSER ONLINE</span>
              </div>
            </div>

            {/* Code Editor Workspace */}
            <div className="flex bg-[#030712] font-mono text-xs overflow-hidden h-[320px]">
              {/* Gutter Line Numbers */}
              <div 
                ref={lineNumbersRef}
                className="select-none text-slate-600 bg-black/40 py-3 text-right pr-3 pl-4 border-r border-slate-900 leading-relaxed min-w-[3.5rem] overflow-y-hidden"
              >
                {lineNumbers.map((n) => (
                  <div key={n} className="h-5 pr-0.5">{n}</div>
                ))}
              </div>

              {/* Text Area Input */}
              <textarea
                ref={textareaRef}
                value={qasm}
                onChange={(e) => setQasm(e.target.value)}
                onScroll={handleEditorScroll}
                className="flex-1 bg-transparent text-slate-100 py-3 px-4 resize-none focus:outline-none overflow-y-auto leading-relaxed h-full font-mono placeholder-slate-600 focus:ring-0 whitespace-pre"
                spellCheck={false}
                placeholder="// Enter OpenQASM 3.0 here"
              />
            </div>
          </div>

          {/* Configuration Parameters Panel */}
          <form onSubmit={executeSimulation} className="p-5 border border-slate-800 rounded-xl bg-slate-900/20 backdrop-blur-lg space-y-5">
            <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3 text-slate-300">
              <Settings className="w-4 h-4 text-slate-400" />
              <h3 className="font-syne font-bold text-sm">Execution Configuration</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Shots Allocation */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold tracking-wide uppercase text-qc-muted block">
                  Simulation Shots
                </label>
                <input
                  type="number"
                  value={shots}
                  onChange={handleShotsChange}
                  min={1}
                  max={maxShots}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-[#070b13] text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50 focus:ring-1 focus:ring-qc-accent/20 transition-all"
                  required
                />
                <span className="text-[10px] text-slate-500 font-mono block">
                  Max Limit: {maxShots.toLocaleString()}
                </span>
              </div>

              {/* Backend Choice Selector */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold tracking-wide uppercase text-qc-muted block">
                  Execution Backend
                </label>
                <select
                  value={backend}
                  onChange={(e) => setBackend(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-[#070b13] text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50 focus:ring-1 focus:ring-qc-accent/20 transition-all appearance-none"
                >
                  <option value="Local AerSimulator">Local AerSimulator</option>
                  <option value="AWS Braket">AWS Braket</option>
                  <option value="IBM Quantum">IBM Quantum</option>
                </select>
                {backend !== 'Local AerSimulator' && (
                  <span className="text-[10px] text-amber-400 font-mono block mt-1.5 leading-snug">
                    ⚠️ Surcharge: 1,000 base + 10 credits/shot will be deducted from your wallet.
                  </span>
                )}
              </div>


              {/* Noise Model Selector */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold tracking-wide uppercase text-qc-muted flex items-center justify-between">
                  <span>Noise Model</span>
                  {isFree && (
                    <span className="text-[9px] bg-amber-500/10 text-amber-500 border border-amber-500/20 px-1 py-0.2 rounded font-mono font-normal">
                      PRO ONLY
                    </span>
                  )}
                </label>
                
                <div className="relative group">
                  <select
                    value={noiseModel}
                    onChange={(e) => setNoiseModel(e.target.value)}
                    disabled={isFree}
                    className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-[#070b13] text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50 focus:ring-1 focus:ring-qc-accent/20 disabled:opacity-40 disabled:cursor-not-allowed appearance-none transition-all"
                  >
                    <option value="Ideal">Ideal Simulator</option>
                    <option value="Depolarizing">Depolarizing Channel</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Execute & Reset buttons */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-2.5 rounded-lg bg-qc-accent text-slate-950 font-bold font-syne text-xs hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-lg shadow-qc-accent/10 hover:shadow-qc-accent/25"
              >
                {loading ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-t-transparent border-slate-950 rounded-full animate-spin" />
                    Executing Compiler...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current text-slate-950" />
                    Execute Multi-Qubit QASM
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleReset}
                disabled={loading}
                className="px-4 py-2.5 rounded-lg border border-slate-800 text-qc-muted hover:text-qc-text hover:bg-slate-800/30 transition-all active:scale-[0.98] cursor-pointer"
                title="Reset Workspace"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Execution Console & Visualizations (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="border border-slate-800 rounded-xl bg-slate-950/30 backdrop-blur-xl shadow-2xl overflow-hidden min-h-[465px] flex flex-col justify-between">
            <div>
              {/* Result Headers/Tabs */}
              <div className="flex border-b border-slate-800 bg-[#0a0f1d]/50 p-1">
                <button
                  onClick={() => setActiveTab('visualizations')}
                  className={`flex-1 py-2 px-3 rounded-lg font-mono text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                    activeTab === 'visualizations'
                      ? 'bg-slate-800/80 text-qc-accent border border-slate-700/50 shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <BarChart4 className="w-3.5 h-3.5" />
                  Visualizations
                </button>
                <button
                  onClick={() => setActiveTab('console')}
                  className={`flex-1 py-2 px-3 rounded-lg font-mono text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                    activeTab === 'console'
                      ? 'bg-slate-800/80 text-qc-accent border border-slate-700/50 shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Terminal className="w-3.5 h-3.5" />
                  Execution Console
                </button>
              </div>

              {/* Tab Content container */}
              <div className="p-5">
                {/* 1. Visualizations Tab */}
                {activeTab === 'visualizations' && (
                  <div className="space-y-4">
                    {/* Error display inside Visualizations */}
                    {errorMsg && (
                      <div className="p-4 border border-rose-900/30 bg-rose-950/10 rounded-xl flex items-start gap-3 text-rose-200 font-mono text-xs">
                        <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold text-rose-400">Simulation Error</p>
                          <p className="mt-1 text-rose-300/80 leading-relaxed whitespace-pre-wrap">{errorMsg}</p>
                        </div>
                      </div>
                    )}

                    {/* Results probability bars */}
                    {result && !errorMsg && (
                      <div className="space-y-4 animate-fade-in">
                        <div className="flex items-center justify-between">
                          <h4 className="font-syne font-bold text-xs text-slate-300 tracking-wider uppercase">
                            State Probabilities
                          </h4>
                          <span className="text-[10px] text-slate-500 font-mono">
                            Total Outcomes: {Object.keys(result.probabilities).length}
                          </span>
                        </div>
                        <div className="space-y-3.5">
                          {Object.entries(result.probabilities)
                            .sort((a, b) => b[1] - a[1]) // Sort descending
                            .map(([state, probability]) => {
                              const percentage = probability * 100;
                              return (
                                <div key={state} className="space-y-1.5 font-mono text-xs">
                                  <div className="flex justify-between items-baseline">
                                    <span className="font-semibold text-qc-accent text-sm">|{state}⟩</span>
                                    <span className="text-slate-400">
                                      {Math.round(probability * result.metadata!.shots)} shots ({percentage.toFixed(1)}%)
                                    </span>
                                  </div>
                                  <div className="w-full h-4 rounded-full bg-slate-950 border border-slate-900 overflow-hidden relative">
                                    <div 
                                      className="h-full bg-gradient-to-r from-qc-accent/30 to-qc-accent rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(0,212,170,0.2)]"
                                      style={{ width: `${percentage}%` }}
                                    />
                                  </div>
                                </div>
                              );
                            })}
                        </div>

                        {/* QPU Telemetry Panel */}
                        {result.qpu_telemetry && (
                          <div className="mt-6 p-4 border border-purple-900/30 bg-purple-950/5 rounded-xl space-y-3 font-mono text-xs">
                            <div className="flex items-center gap-2 border-b border-purple-900/20 pb-2">
                              <Cpu className="w-4 h-4 text-purple-400" />
                              <h4 className="font-syne font-bold text-xs text-purple-300 uppercase tracking-wider">
                                QPU Hardware Telemetry
                              </h4>
                            </div>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[10px] text-slate-400">
                              <div>QPU Target: <span className="text-slate-200 font-bold">{result.qpu_telemetry.qpu_name}</span></div>
                              <div>Queue Delay: <span className="text-slate-200 font-bold">{result.qpu_telemetry.queue_time_seconds}s</span></div>
                              <div>Readout Error: <span className="text-slate-200 font-bold">{(result.qpu_telemetry.readout_error_rate * 100).toFixed(1)}%</span></div>
                              <div>CNOT Fidelity: <span className="text-slate-200 font-bold">{(result.qpu_telemetry.cnot_gate_fidelity * 100).toFixed(1)}%</span></div>
                            </div>
                            <div className="text-[9px] text-slate-500 pt-1">
                              Calibration Timestamp: {new Date(result.qpu_telemetry.calibration_date).toLocaleString()}
                            </div>
                          </div>
                        )}
                      </div>
                    )}


                    {/* Loading State for visualization */}
                    {loading && (
                      <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                        <div className="w-12 h-12 border-2 border-t-transparent border-qc-accent rounded-full animate-spin shadow-[0_0_15px_rgba(0,212,170,0.1)]" />
                        <div className="font-mono text-xs">
                          <p className="text-slate-200 font-bold uppercase tracking-widest animate-pulse">Running compiler...</p>
                          <p className="text-slate-500 text-[10px] mt-1">Transpilation and simulation in progress</p>
                        </div>
                      </div>
                    )}

                    {/* Standard Placeholder */}
                    {!loading && !result && !errorMsg && (
                      <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
                        <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-2xl">
                          <Cpu className="w-10 h-10 text-slate-500 animate-pulse" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-300">No active compiler simulation</p>
                          <p className="text-xs text-slate-500 mt-1 max-w-[260px] leading-relaxed">
                            Press "Execute Multi-Qubit QASM" to compile and view quantum state amplitudes.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 2. Execution Console Tab */}
                {activeTab === 'console' && (
                  <div className="space-y-4 font-mono text-xs">
                    {/* Live Compiler Steps */}
                    <div className="p-3.5 bg-black/60 border border-slate-900 rounded-xl overflow-hidden h-[180px] flex flex-col justify-between">
                      <div className="overflow-y-auto space-y-1 h-full pr-1 text-slate-300 leading-normal scrollbar-thin">
                        {logs.length === 0 ? (
                          <div className="text-slate-600 italic">Console idle. Awaiting compilation...</div>
                        ) : (
                          logs.map((logLine, idx) => (
                            <div 
                              key={idx} 
                              className={
                                logLine.includes('[ERROR]') ? 'text-rose-500 font-bold' :
                                logLine.includes('[SUCCESS]') ? 'text-emerald-400 font-bold' :
                                logLine.includes('[WARNING]') ? 'text-amber-500' : 'text-slate-300'
                              }
                            >
                              {logLine}
                            </div>
                          ))
                        )}
                        {loading && (
                          <div className="text-qc-accent animate-pulse flex items-center gap-1.5 mt-1 font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-qc-accent animate-ping" />
                            [SYSTEM] COMPILING TARGET SOURCE CIRCUITS...
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Raw JSON Log Response */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-slate-500 text-[10px]">
                        <span>TELEMETRY RAW RESPONSE</span>
                        {rawResponse && <span>STATUS: 200 OK</span>}
                      </div>
                      
                      {rawResponse ? (
                        <pre className="p-3.5 bg-black/40 border border-slate-900 rounded-xl overflow-x-auto text-[10px] text-slate-400 max-h-[140px] leading-relaxed">
                          {JSON.stringify(rawResponse, null, 2)}
                        </pre>
                      ) : (
                        <div className="p-6 bg-black/20 border border-slate-900/50 rounded-xl text-center text-slate-600 text-[10px]">
                          No telemetry response logs loaded.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Results Metadata footer */}
            {result && !errorMsg && (
              <div className="p-4 bg-[#0a0f1d]/30 border-t border-slate-800/80 grid grid-cols-2 gap-4 text-[10px] text-slate-400 font-mono leading-normal">
                <div className="space-y-1">
                  <p className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-qc-accent" />
                    Qubits: <span className="text-slate-200 font-bold">{result.num_qubits}</span>
                  </p>
                  <p className="flex items-center gap-1.5">
                    <Settings className="w-3.5 h-3.5 text-qc-accent" />
                    Depth: <span className="text-slate-200 font-bold">{result.circuit_depth}</span>
                  </p>
                </div>
                <div className="space-y-1 text-right">
                  <p className="flex items-center justify-end gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-qc-accent" />
                    Execution: <span className="text-slate-200 font-bold">{result.execution_time_ms.toFixed(1)} ms</span>
                  </p>
                  <p className="flex items-center justify-end gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-qc-accent" />
                    Noise: <span className="text-slate-200 font-bold">{result.metadata?.noise_model || noiseModel}</span>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
