import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Clock, Zap, Copy, Check, Sparkles } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

interface CircuitResultsProps {
    results: any;
    qasmCode?: string;
    activeTab?: string;
    onTabChange?: (tab: string) => void;
    onQASMChange?: (newQasm: string) => void;
    onOptimize?: () => void;
}

export const CircuitResults = ({ results, qasmCode, activeTab = 'chart', onTabChange, onQASMChange, onOptimize }: CircuitResultsProps) => {
    const [copied, setCopied] = useState(false);
    const [localQasm, setLocalQasm] = useState<string | undefined>(qasmCode);
    const [isFocused, setIsFocused] = useState(false);
    const lastExternalQasm = useRef(qasmCode);

    useEffect(() => {
        if (qasmCode !== lastExternalQasm.current) {
            lastExternalQasm.current = qasmCode;
            if (!isFocused) {
                setLocalQasm(qasmCode);
            }
        }
    }, [qasmCode, isFocused]);

    const handleCopyQASM = () => {
        if (qasmCode) {
            navigator.clipboard.writeText(qasmCode);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Normalize probabilities from counts if necessary
    const probabilities = results?.probabilities || (results?.counts && results?.shots ? 
        Object.fromEntries(Object.entries(results.counts).map(([k, v]) => [k, (v as number) / results.shots])) 
        : null);

    // Build chart data from results
    const data = probabilities
        ? Object.keys(probabilities).sort().map(key => ({
            state: `|${key}⟩`,
            probability: probabilities[key] * 100,
            raw: probabilities[key]
        }))
        : [];

    const metrics = results?.metrics || (results?.circuit_depth ? {
        depth: results.circuit_depth,
        qubit_count: results.num_qubits,
        gate_count: results.gate_count || {}
    } : null);

    return (
        <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-sm flex flex-col h-full">
            <CardHeader className="py-3 px-4 border-b border-slate-800/50">
                <CardTitle className="text-sm font-semibold text-slate-200 flex items-center justify-between">
                    <span>Simulation Results</span>
                    {results?.execution_time_ms && (
                        <span className="flex items-center gap-1 text-[10px] font-mono text-slate-500 font-normal">
                            <Clock className="w-3 h-3" />
                            {results.execution_time_ms.toFixed(1)}ms
                        </span>
                    )}
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-hidden">
                <Tabs value={activeTab} onValueChange={onTabChange} className="flex flex-col h-full">
                    <TabsList className="bg-slate-800/60 rounded-none border-b border-slate-800/50 h-9 px-2 shrink-0">
                        <TabsTrigger value="chart" className="text-xs data-[state=active]:bg-slate-700/60 data-[state=active]:text-cyan-300 rounded-md px-3">
                            Probabilities
                        </TabsTrigger>
                        <TabsTrigger value="statevector" disabled={!results?.statevector} className="text-xs data-[state=active]:bg-slate-700/60 data-[state=active]:text-cyan-300 rounded-md px-3">
                            Statevector
                        </TabsTrigger>
                        <TabsTrigger value="qasm" className="text-xs data-[state=active]:bg-slate-700/60 data-[state=active]:text-cyan-300 rounded-md px-3">
                            Live QASM
                        </TabsTrigger>
                        <TabsTrigger value="metrics" className="text-xs data-[state=active]:bg-slate-700/60 data-[state=active]:text-cyan-300 rounded-md px-3">
                            Metrics
                        </TabsTrigger>
                    </TabsList>

                    {/* Probabilities Chart */}
                    <TabsContent value="chart" className="flex-1 p-3 m-0 overflow-hidden">
                        {data.length > 0 ? (
                            <div className="h-full min-h-[200px]">
                                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                                    <BarChart data={data} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis
                                            dataKey="state"
                                            stroke="#475569"
                                            tick={{ fontSize: 10, fill: '#94a3b8' }}
                                            angle={-45}
                                            textAnchor="end"
                                            height={50}
                                        />
                                        <YAxis
                                            stroke="#475569"
                                            tick={{ fontSize: 10, fill: '#94a3b8' }}
                                            label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: '#0f172a',
                                                borderColor: '#1e293b',
                                                color: '#f1f5f9',
                                                borderRadius: '8px',
                                                fontSize: '12px',
                                            }}
                                            cursor={{ fill: '#1e293b', opacity: 0.3 }}
                                            formatter={(value: any) => [`${Number(value).toFixed(2)}%`, 'Probability']}
                                        />
                                        <Bar dataKey="probability" radius={[4, 4, 0, 0]}>
                                            {data.map((entry, index) => (
                                                <Cell
                                                    key={`cell-${index}`}
                                                    fill={entry.raw > 0.01 ? '#22d3ee' : '#1e293b'}
                                                    style={{
                                                        filter: entry.raw > 0.01 ? 'drop-shadow(0 0 6px rgba(34, 211, 238, 0.4))' : 'none'
                                                    }}
                                                />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full text-slate-600">
                                <div className="text-center">
                                    <Zap className="w-8 h-8 mx-auto mb-2 opacity-30" />
                                    <p className="text-xs">Run a circuit to see probability distribution</p>
                                </div>
                            </div>
                        )}
                    </TabsContent>

                    {/* Statevector */}
                    <TabsContent value="statevector" className="flex-1 p-3 m-0 overflow-auto">
                        <div className="space-y-1.5">
                            {results?.statevector && results.statevector.map((sv: any, idx: number) => {
                                const real = sv.real || 0;
                                const imag = sv.imag || 0;
                                const prob = (real * real + imag * imag) * 100;
                                if (prob < 0.1) return null; // Hide near-zero amplitudes
                                const phase = Math.atan2(imag, real) * 180 / Math.PI;
                                const basis = idx.toString(2).padStart(Math.log2(results.statevector.length) || 1, '0');
                                
                                return (
                                    <div key={idx} className="flex justify-between items-center p-2 rounded-md bg-slate-800/40 border border-slate-800/50 text-xs">
                                        <span className="font-mono text-cyan-300 font-bold">|{basis}⟩</span>
                                        <div className="text-right">
                                            <div className="text-slate-200 font-mono">
                                                {real.toFixed(4)} {imag >= 0 ? '+' : ''}{imag.toFixed(4)}i
                                            </div>
                                            <div className="text-[10px] text-slate-600">
                                                θ = {phase.toFixed(1)}° • P = {prob.toFixed(1)}%
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                            {(!results?.statevector || results.statevector.length === 0) && (
                                <div className="text-center text-xs text-slate-600 py-8">
                                    Statevector only available for ideal (noiseless) simulations
                                </div>
                            )}
                        </div>
                    </TabsContent>

                    {/* Live QASM */}
                    <TabsContent value="qasm" className="flex-1 p-3 m-0 overflow-hidden flex flex-col">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">OpenQASM 3.0</span>
                            <button
                                onClick={handleCopyQASM}
                                className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-cyan-400 transition-colors px-2 py-1 rounded bg-slate-800/50 hover:bg-slate-700/50"
                            >
                                {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                                {copied ? 'Copied!' : 'Copy'}
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto rounded-lg bg-[#0a0f1a] border border-slate-800/50 p-3">
                            <textarea
                                value={localQasm || ''}
                                onFocus={() => setIsFocused(true)}
                                onBlur={() => setIsFocused(false)}
                                onChange={(e) => {
                                    setLocalQasm(e.target.value);
                                    onQASMChange?.(e.target.value);
                                }}
                                className="w-full h-full bg-transparent text-xs font-mono text-slate-300 whitespace-pre leading-relaxed focus:outline-none resize-none"
                                spellCheck={false}
                                placeholder="// Add gates to see live QASM output"
                            />
                        </div>
                    </TabsContent>

                    {/* Metrics */}
                    <TabsContent value="metrics" className="flex-1 p-3 m-0 overflow-auto">
                        {metrics ? (
                            <div className="space-y-3">
                                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/40 border border-slate-800/50">
                                    <div>
                                        <div className="text-[10px] text-slate-500 uppercase tracking-wider">Est. QPU Cost</div>
                                        <div className="text-xl font-bold text-emerald-400 font-mono mt-1">${(metrics.depth * 0.15).toFixed(2)}</div>
                                    </div>
                                    <Button onClick={onOptimize} size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white">
                                        <Sparkles className="w-4 h-4 mr-1.5" />
                                        Optimize
                                    </Button>
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                    <MetricCard label="Circuit Depth" value={metrics.depth} />
                                    <MetricCard label="Qubits Used" value={metrics.qubit_count} />
                                </div>
                                <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800/50">
                                    <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Gate Count</div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {Object.entries(metrics.gate_count).map(([gate, count]) => (
                                            <span key={gate} className="px-2 py-1 rounded-md bg-slate-700/60 text-[10px] font-mono text-cyan-300 border border-slate-700/50">
                                                {gate}: {count as number}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                {results?.type && (
                                    <div className="flex items-center gap-2 text-[10px] text-slate-500">
                                        <div className={`w-2 h-2 rounded-full ${results.type === 'ideal' ? 'bg-green-400' : 'bg-amber-400'}`} />
                                        {results.type === 'ideal' ? 'Ideal Simulation' : 'Noisy Simulation'}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center text-xs text-slate-600 py-8">
                                Run a circuit to see metrics
                            </div>
                        )}
                    </TabsContent>
                </Tabs>
            </CardContent>
        </Card>
    );
};

const MetricCard = ({ label, value }: { label: string; value: number | string }) => (
    <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800/50">
        <div className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</div>
        <div className="text-xl font-bold text-white font-mono mt-1">{value}</div>
    </div>
);
