import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface CircuitResultsProps {
    results: any;
}

export const CircuitResults = ({ results }: CircuitResultsProps) => {
    if (!results) return null;

    const probabilities = results.probabilities;
    const data = Object.keys(probabilities).sort().map(key => ({
        state: `|${key}⟩`,
        probability: probabilities[key] * 100, // Convert to percentage
        raw: probabilities[key]
    }));

    const metrics = results.metrics;

    return (
        <Card className="bg-slate-900/50 border-slate-800 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <CardHeader>
                <CardTitle className="text-xl text-blue-100">Simulation Results</CardTitle>
            </CardHeader>
            <CardContent>
                <Tabs defaultValue="chart">
                    <TabsList className="bg-slate-800 mb-4">
                        <TabsTrigger value="chart">Probabilities</TabsTrigger>
                        <TabsTrigger value="statevector" disabled={!results.statevector}>Statevector</TabsTrigger>
                        <TabsTrigger value="metrics">Metrics</TabsTrigger>
                    </TabsList>

                    <TabsContent value="chart" className="h-[300px]">
                        {data.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                                <BarChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="state" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                                        cursor={{ fill: '#334155', opacity: 0.2 }}
                                    />
                                    <Bar dataKey="probability" radius={[4, 4, 0, 0]}>
                                        {data.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.raw > 0.01 ? '#60a5fa' : '#334155'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-slate-500">
                                No data available for this simulation
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="statevector">
                        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                            {results.statevector && results.statevector.map((state: any, idx: number) => (
                                <div key={idx} className="flex justify-between items-center p-2 rounded bg-slate-800/50 text-sm">
                                    <span className="font-mono text-blue-300">|{state.basis}⟩</span>
                                    <div className="text-right">
                                        <div className="text-slate-200">
                                            {state.amplitude.real.toFixed(3)} {state.amplitude.imag >= 0 ? '+' : ''}{state.amplitude.imag.toFixed(3)}i
                                        </div>
                                        <div className="text-xs text-slate-500">
                                            Phase: {(state.phase * 180 / Math.PI).toFixed(1)}°
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </TabsContent>

                    <TabsContent value="metrics">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-lg bg-slate-800/50">
                                <div className="text-sm text-slate-400">Circuit Depth</div>
                                <div className="text-2xl font-bold text-white">{metrics?.depth || 0}</div>
                            </div>
                            <div className="p-4 rounded-lg bg-slate-800/50">
                                <div className="text-sm text-slate-400">Qubits Used</div>
                                <div className="text-2xl font-bold text-white">{metrics?.qubit_count || 0}</div>
                            </div>
                            <div className="col-span-2 p-4 rounded-lg bg-slate-800/50">
                                <div className="text-sm text-slate-400 mb-2">Gate Count</div>
                                <div className="flex flex-wrap gap-2">
                                    {metrics?.gate_count && Object.entries(metrics.gate_count).map(([gate, count]) => (
                                        <span key={gate} className="px-2 py-1 rounded bg-slate-700 text-xs font-mono text-blue-200">
                                            {gate}: {count as number}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </TabsContent>
                </Tabs>
            </CardContent>
        </Card>
    );
};
