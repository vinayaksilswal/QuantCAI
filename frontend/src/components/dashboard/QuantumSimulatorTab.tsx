import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';
import { Play, RotateCcw, AlertCircle, Info, BarChart4, Cpu } from 'lucide-react';

interface SimulationResult {
  counts: Record<string, number>;
  statevector?: any;
  execution_time_ms: number;
  shots: number;
  circuit_depth: number;
  num_qubits: number;
}

interface JobResponse {
  job_id: string;
  status: 'queued' | 'running' | 'complete' | 'failed';
  result?: SimulationResult;
  error?: string;
}

const DEFAULT_QASM = `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;`;

export function QuantumSimulatorTab() {
  const { subscriptionPlan } = useAuth();
  const [qasm, setQasm] = useState(DEFAULT_QASM);
  const [shots, setShots] = useState(1024);
  const [noiseModel, setNoiseModel] = useState<'ideal' | 'depolarizing' | 'thermal'>('ideal');
  
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isFree = subscriptionPlan === 'free' || !subscriptionPlan;
  const maxShots = isFree ? 1024 : 65536;

  const handleShotsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) return;
    setShots(val);
  };

  const handleReset = () => {
    setQasm(DEFAULT_QASM);
    setShots(1024);
    setNoiseModel('ideal');
    setResult(null);
    setJobId(null);
    setJobStatus(null);
    setErrorMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setResult(null);
    
    // Client-side shot validation
    if (shots < 1 || shots > maxShots) {
      toast.error(`Shots must be between 1 and ${maxShots} for your tier.`);
      return;
    }

    setLoading(true);
    setJobStatus('submitting');

    try {
      // POST to simulator
      const response = await axiosClient.post<{ job_id: string; status: string }>('/api/v1/simulate', {
        circuit_qasm: qasm,
        shots: shots,
        noise_model: noiseModel,
      });

      const newJobId = response.data.job_id;
      setJobId(newJobId);
      setJobStatus('queued');
      
      // Start polling
      pollJobStatus(newJobId);
    } catch (err: any) {
      console.error('Error submitting simulation:', err);
      const msg = err.response?.data?.detail || 'Failed to submit simulation circuit.';
      setErrorMsg(msg);
      setJobStatus(null);
      setLoading(false);
    }
  };

  const pollJobStatus = (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axiosClient.get<JobResponse>(`/api/v1/simulate/${id}`);
        const status = response.data.status;
        setJobStatus(status);

        if (status === 'complete' && response.data.result) {
          setResult(response.data.result);
          setLoading(false);
          clearInterval(interval);
          toast.success('Quantum simulation completed successfully!');
        } else if (status === 'failed') {
          setErrorMsg(response.data.error || 'Simulating task failed on Celery worker.');
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err: any) {
        console.error('Error polling simulation status:', err);
        setErrorMsg('Error connecting to polling server.');
        setLoading(false);
        clearInterval(interval);
      }
    }, 2000);
  };

  // Render CSS bar chart counts
  const renderCounts = () => {
    if (!result) return null;
    const { counts, shots: totalShots } = result;

    return (
      <div className="space-y-4">
        <h4 className="font-syne font-bold text-sm text-qc-text">Measurement Outcomes (Counts)</h4>
        <div className="space-y-3.5">
          {Object.entries(counts).map(([state, count]) => {
            const percentage = (count / totalShots) * 100;
            return (
              <div key={state} className="space-y-1.5 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="font-semibold text-qc-text">|{state}⟩</span>
                  <span className="text-qc-muted">{count} shots ({percentage.toFixed(1)}%)</span>
                </div>
                <div className="w-full h-5 rounded bg-qc-border overflow-hidden relative">
                  <div 
                    className="h-full bg-gradient-to-r from-qc-accent/50 to-qc-accent rounded transition-all duration-700"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="font-syne font-bold text-2xl text-qc-text">Quantum Simulator</h1>
        <p className="text-sm text-qc-muted mt-1">Write OpenQASM 2.0 circuits, configure parameters, and execute them on a remote simulator.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 items-start">
        {/* Left Column: Form */}
        <form onSubmit={handleSubmit} className="space-y-5 p-5 border border-qc-border rounded bg-qc-surface/30">
          {/* OpenQASM Input */}
          <div className="space-y-2">
            <label className="text-xs font-mono font-bold tracking-wide uppercase text-qc-muted">OpenQASM 2.0 Code</label>
            <textarea
              value={qasm}
              onChange={(e) => setQasm(e.target.value)}
              className="w-full h-[240px] p-3 rounded border border-qc-border bg-qc-bg text-qc-text font-mono text-xs leading-relaxed focus:outline-none focus:border-qc-accent/50 resize-y"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Shots Input */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-bold tracking-wide uppercase text-qc-muted">Shots</label>
              <input
                type="number"
                value={shots}
                onChange={handleShotsChange}
                min={1}
                max={maxShots}
                className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50"
                required
              />
              <span className="text-[10px] text-qc-muted font-mono block">Max: {maxShots} ({subscriptionPlan === 'free' || !subscriptionPlan ? 'Free' : 'Pro'})</span>
            </div>

            {/* Noise Model Selector */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-bold tracking-wide uppercase text-qc-muted flex items-center gap-1">
                Noise Model
              </label>
              
              <div className="relative group">
                <select
                  value={noiseModel}
                  onChange={(e) => setNoiseModel(e.target.value as any)}
                  disabled={isFree}
                  className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50 disabled:opacity-50 disabled:cursor-not-allowed appearance-none"
                >
                  <option value="ideal">Ideal Simulator</option>
                  <option value="depolarizing">Depolarizing Channel</option>
                  <option value="thermal">Thermal Relaxation</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-qc-muted">
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
                
                {/* Custom hover tooltip */}
                {isFree && (
                  <div className="absolute hidden group-hover:flex items-center gap-1.5 bg-black text-[10px] text-qc-muted px-2.5 py-1.5 rounded border border-qc-border -top-10 left-0 w-max z-10 shadow-lg">
                    <Info className="w-3.5 h-3.5 text-qc-accent" />
                    <span>Noise models require Pro</span>
                  </div>
                )}
              </div>
              <span className="text-[10px] text-qc-muted font-mono block">Select channel decay</span>
            </div>
          </div>

          {/* CTA Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2.5 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Execute Simulation
            </button>
            <button
              type="button"
              onClick={handleReset}
              disabled={loading}
              className="px-4 py-2.5 rounded border border-qc-border text-qc-muted hover:text-qc-text hover:bg-qc-border/40 transition-colors active:scale-[0.98]"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </form>

        {/* Right Column: Results */}
        <div className="p-5 border border-qc-border rounded bg-qc-surface/30 min-h-[420px] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 border-b border-qc-border/50 pb-3 text-qc-muted">
              <BarChart4 className="w-4 h-4" />
              <h3 className="font-syne font-bold text-sm text-qc-text">Simulation Results</h3>
            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="mt-4 p-4 border border-qc-danger/25 bg-qc-danger/5 rounded flex items-start gap-2.5 text-qc-text font-mono text-xs">
                <AlertCircle className="w-4.5 h-4.5 text-qc-danger flex-shrink-0" />
                <div>
                  <p className="font-bold text-qc-danger">Execution Failure</p>
                  <p className="mt-1 text-qc-muted leading-relaxed">{errorMsg}</p>
                </div>
              </div>
            )}

            {/* Polling / Queued Status */}
            {loading && !result && (
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <div className="w-10 h-10 border-2 border-t-transparent border-qc-accent rounded-full animate-spin" />
                <div className="text-center font-mono text-xs">
                  <p className="text-qc-text font-bold uppercase tracking-wider">Job Status: {jobStatus}</p>
                  {jobId && <p className="text-qc-muted text-[10px] mt-1">Job ID: {jobId}</p>}
                  <p className="text-qc-muted text-[10px] mt-1">Polling results every 2 seconds...</p>
                </div>
              </div>
            )}

            {/* Completed Result bar chart */}
            {result && renderCounts()}

            {/* Default Placeholder */}
            {!loading && !result && !errorMsg && (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <Cpu className="w-12 h-12 text-qc-border mb-4" />
                <p className="text-sm font-semibold text-qc-muted">No Simulation Active</p>
                <p className="text-xs text-qc-muted/60 mt-1 max-w-[280px]">Submit an OpenQASM circuit from the editor to execute it and display output.</p>
              </div>
            )}
          </div>

          {/* Result Metadata footer */}
          {result && (
            <div className="border-t border-qc-border/50 pt-4 mt-6 grid grid-cols-2 gap-4 text-[10px] text-qc-muted font-mono leading-relaxed">
              <div>
                <p>Qubits detected: <span className="text-qc-text font-semibold">{result.num_qubits}</span></p>
                <p>Circuit depth: <span className="text-qc-text font-semibold">{result.circuit_depth}</span></p>
              </div>
              <div className="text-right">
                <p>Execution time: <span className="text-qc-text font-semibold">{result.execution_time_ms.toFixed(1)} ms</span></p>
                <p>Noise model: <span className="text-qc-text font-semibold">{noiseModel === 'ideal' ? 'Ideal' : noiseModel}</span></p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
