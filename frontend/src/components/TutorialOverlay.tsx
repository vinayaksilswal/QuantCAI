import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { PlacedGate } from "@/types/circuit";
import { tutorialScenarios, TutorialScenario } from "@/data/tutorial_data";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, XCircle, ArrowRight, HelpCircle } from 'lucide-react';
import { toast } from "sonner";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";


interface TutorialOverlayProps {
    placedGates: PlacedGate[];
    setPlacedGates: (gates: PlacedGate[]) => void;
}

export const TutorialOverlay = ({ placedGates, setPlacedGates }: TutorialOverlayProps) => {
    const [activeScenario, setActiveScenario] = useState<TutorialScenario | null>(null);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const [isOpen, setIsOpen] = useState(false); // Dialog open state

    const startScenario = (id: string) => {
        const scenario = tutorialScenarios.find(s => s.id === id);
        if (scenario) {
            setActiveScenario(scenario);
            setCurrentStepIndex(0);
            setIsComplete(false);
            setPlacedGates([]); // Clear board
            setIsOpen(false);
            toast.info(`Started tutorial: ${scenario.title}`);
        }
    };

    const currentStep = activeScenario?.steps[currentStepIndex];

    // Check progress
    useEffect(() => {
        if (!activeScenario || !currentStep) return;

        // Check if the required gate is placed correctly
        // We look for a gate that matches targetGate, targetWire, and maybe loosely targetStep (order matters more than absolute step)
        // For strict tutorial: match exact step index relative to others?
        // Let's match exact wire and roughly the step (or just presence if it's the latest gate).

        const matchingGate = placedGates.find(g =>
            g.name === currentStep.targetGate &&
            g.wire === currentStep.targetWire &&
            g.step === currentStep.targetStep
        );

        if (matchingGate) {
            // Step complete!
            toast.success("Step Complete!");
            if (currentStepIndex < activeScenario.steps.length - 1) {
                setCurrentStepIndex(prev => prev + 1);
            } else {
                setIsComplete(true);
                toast.success("Tutorial Completed! Great job.");
            }
        }
    }, [placedGates, currentStepIndex, activeScenario]);

    const exitTutorial = () => {
        setActiveScenario(null);
        setIsComplete(false);
    };

    if (!activeScenario) {
        return (
            <div className="fixed bottom-6 right-6 z-50">
                <Dialog open={isOpen} onOpenChange={setIsOpen}>
                    <DialogTrigger asChild>
                        <Button className="rounded-full h-12 w-12 bg-blue-600 hover:bg-blue-700 shadow-xl border-2 border-blue-400">
                            <HelpCircle className="w-6 h-6" />
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-900 border-slate-700">
                        <DialogHeader>
                            <DialogTitle className="text-blue-100">Interactive Tutorials</DialogTitle>
                            <DialogDescription>
                                Select a tutorial to learn quantum circuit building step-by-step.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            {tutorialScenarios.map(scenario => (
                                <Button
                                    key={scenario.id}
                                    variant="secondary"
                                    className="justify-start h-auto py-3 px-4 bg-slate-800 hover:bg-slate-700"
                                    onClick={() => startScenario(scenario.id)}
                                >
                                    <div className="text-left">
                                        <div className="font-bold text-blue-200">{scenario.title}</div>
                                        <div className="text-xs text-slate-400 text-nowrap">Click to start</div>
                                    </div>
                                    <ArrowRight className="ml-auto w-4 h-4 opacity-50" />
                                </Button>
                            ))}
                        </div>
                    </DialogContent>
                </Dialog>
            </div>
        );
    }

    if (isComplete) {
        return (
            <div className="absolute top-24 left-1/2 -translate-x-1/2 z-50 animate-in zoom-in duration-300">
                <Card className="bg-green-900/90 border-green-500 w-[400px]">
                    <CardContent className="p-6 text-center">
                        <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-white mb-2">Tutorial Complete!</h2>
                        <p className="text-green-100 mb-6">You have successfully built the circuit.</p>
                        <Button onClick={exitTutorial} className="w-full bg-white text-green-900 hover:bg-green-100">
                            Back to Builder
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="absolute top-24 left-1/2 -translate-x-1/2 z-40 w-full max-w-lg px-4 pointer-events-none">
            {/* Guide Card - pointer-events-auto allows clicking buttons inside */}
            <Card className="bg-blue-950/90 border-blue-500 backdrop-blur pointer-events-auto shadow-2xl">
                <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-mono text-blue-300 uppercase tracking-widest">
                            Step {currentStepIndex + 1} / {activeScenario.steps.length}
                        </span>
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0 hover:bg-blue-800 rounded-full" onClick={exitTutorial}>
                            <XCircle className="w-4 h-4 text-blue-300" />
                        </Button>
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{currentStep?.title}</h3>
                    <p className="text-blue-100 mb-4 text-sm leading-relaxed">
                        {currentStep?.description}
                    </p>
                    {currentStep?.hint && (
                        <div className="bg-blue-900/50 p-3 rounded border border-blue-800 text-xs text-blue-200 flex gap-2">
                            <HelpCircle className="w-4 h-4 shrink-0" />
                            {currentStep.hint}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};
