import { Activity, Layers, Cpu, Zap } from 'lucide-react';
import { PlacedGate, CircuitTelemetry } from '@/types/circuit';
import { useMemo } from 'react';

interface TelemetryBarProps {
    placedGates: PlacedGate[];
    numWires: number;
    shots: number;
}

export const TelemetryBar = ({ placedGates, numWires, shots }: TelemetryBarProps) => {
    const telemetry: CircuitTelemetry = useMemo(() => {
        const depth = placedGates.length > 0
            ? Math.max(0, ...placedGates.map(g => g.step)) + 1
            : 0;

        const totalGates = placedGates.length;

        // Active qubits = unique wires + targetWires used
        const activeQubitSet = new Set<number>();
        placedGates.forEach(g => {
            activeQubitSet.add(g.wire);
            if (g.targetWire !== undefined) activeQubitSet.add(g.targetWire);
            if (g.thirdWire !== undefined) activeQubitSet.add(g.thirdWire);
        });
        const activeQubits = activeQubitSet.size;

        // QPU cost heuristic: depth × qubits × $0.00015 per shot
        const costPerShot = depth * numWires * 0.00015;
        const totalCost = costPerShot * shots;
        const estimatedQPUCost = totalCost < 0.01
            ? `$${totalCost.toFixed(4)}`
            : `$${totalCost.toFixed(2)}`;

        return { circuitDepth: depth, totalGates, estimatedQPUCost, activeQubits };
    }, [placedGates, numWires, shots]);

    return (
        <div className="flex items-center gap-1 px-4 py-2 bg-slate-900/90 backdrop-blur-sm border-t border-slate-800/80 rounded-b-xl">
            <TelemetryChip
                icon={Layers}
                label="Circuit Depth"
                value={String(telemetry.circuitDepth)}
                color="cyan"
            />
            <Divider />
            <TelemetryChip
                icon={Activity}
                label="Total Gates"
                value={String(telemetry.totalGates)}
                color="blue"
            />
            <Divider />
            <TelemetryChip
                icon={Cpu}
                label="Active Qubits"
                value={`${telemetry.activeQubits}/${numWires}`}
                color="purple"
            />
            <Divider />
            <TelemetryChip
                icon={Zap}
                label="Est. QPU Cost"
                value={telemetry.estimatedQPUCost}
                color="amber"
            />
        </div>
    );
};

const Divider = () => (
    <div className="w-px h-6 bg-slate-700/60 mx-2" />
);

interface TelemetryChipProps {
    icon: any;
    label: string;
    value: string;
    color: 'cyan' | 'blue' | 'purple' | 'amber';
}

const COLOR_MAP = {
    cyan: {
        icon: 'text-cyan-400',
        value: 'text-cyan-300',
        glow: 'shadow-cyan-500/10',
    },
    blue: {
        icon: 'text-blue-400',
        value: 'text-blue-300',
        glow: 'shadow-blue-500/10',
    },
    purple: {
        icon: 'text-purple-400',
        value: 'text-purple-300',
        glow: 'shadow-purple-500/10',
    },
    amber: {
        icon: 'text-amber-400',
        value: 'text-amber-300',
        glow: 'shadow-amber-500/10',
    },
};

const TelemetryChip = ({ icon: Icon, label, value, color }: TelemetryChipProps) => {
    const colors = COLOR_MAP[color];

    return (
        <div className="flex items-center gap-2 px-2 py-1">
            <Icon className={`w-3.5 h-3.5 ${colors.icon}`} />
            <div className="flex items-baseline gap-1.5">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">
                    {label}
                </span>
                <span className={`text-sm font-bold font-mono ${colors.value} tabular-nums`}>
                    {value}
                </span>
            </div>
        </div>
    );
};
