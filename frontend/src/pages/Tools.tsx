import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Link } from 'react-router-dom';
import { Zap, ArrowRight, Wrench } from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';

const Tools = () => {
    usePageTracking('tools');

    const tools = [
        {
            id: 'quantum-states',
            title: 'Interactive Quantum States',
            description: 'Explore quantum superposition and entanglement through real-time visualization. Apply quantum gates and observe how they transform qubit states.',
            icon: Zap,
            path: '/quantum-states',
            color: 'text-blue-400',
            bgColor: 'bg-blue-400/10',
            borderColor: 'border-blue-400/20'
        },
        {
            id: 'circuit-builder',
            title: 'Multi-Qubit Circuit Builder',
            description: 'Design and simulate complex quantum circuits with multiple qubits. Drag and drop gates, run experiments, and save your work.',
            icon: Zap, // Using Zap for now, or could vary
            path: '/circuit-builder',
            color: 'text-purple-400',
            bgColor: 'bg-purple-400/10',
            borderColor: 'border-purple-400/20'
        }
    ];

    return (
        <div className="min-h-screen relative overflow-hidden">
            <Navbar />

            <div className="pt-32 pb-20 px-6 relative z-10">
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <div className="text-center mb-16">
                        <div className="flex items-center justify-center mb-6">
                            <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 backdrop-blur-xl animate-float">
                                <Wrench className="h-12 w-12 text-blue-300" />
                            </div>
                        </div>
                        <h1 className="text-5xl font-bold text-white mb-6 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                            Quantum Tools
                        </h1>
                        <p className="text-xl text-blue-200 max-w-2xl mx-auto leading-relaxed">
                            Interactive simulations and utilities to help you experiment with quantum mechanical concepts directly in your browser.
                        </p>
                    </div>

                    {/* Tools Grid */}
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {tools.map((tool) => {
                            const Icon = tool.icon;
                            return (
                                <Link key={tool.id} to={tool.path} className="group">
                                    <Card className={`h-full bg-slate-900/40 backdrop-blur-xl border ${tool.borderColor} transition-all duration-300 hover:scale-[1.02] hover:bg-slate-800/60 hover:shadow-2xl hover:shadow-blue-500/20`}>
                                        <CardHeader>
                                            <div className={`w-12 h-12 rounded-lg ${tool.bgColor} flex items-center justify-center mb-4 transition-colors group-hover:bg-opacity-20`}>
                                                <Icon className={`h-6 w-6 ${tool.color}`} />
                                            </div>
                                            <CardTitle className="text-white text-xl group-hover:text-blue-300 transition-colors">
                                                {tool.title}
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <CardDescription className="text-gray-400 text-base mb-6 line-clamp-3">
                                                {tool.description}
                                            </CardDescription>
                                            <div className={`flex items-center ${tool.color} text-sm font-medium opacity-80 group-hover:opacity-100 transition-opacity`}>
                                                Launch Tool <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                                            </div>
                                        </CardContent>
                                    </Card>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </div>

            <Footer />
        </div>
    );
};

export default Tools;
