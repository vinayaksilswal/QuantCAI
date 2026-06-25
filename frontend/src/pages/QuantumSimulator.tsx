import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { QuantumSimulatorTab } from '@/components/dashboard/QuantumSimulatorTab';
import { usePageTracking } from '@/hooks/usePageTracking';
import { Link } from 'react-router-dom';
import { ArrowLeft, Cpu } from 'lucide-react';

export default function QuantumSimulator() {
  usePageTracking('quantum-simulator');

  return (
    <div className="min-h-screen relative overflow-hidden bg-transparent text-white">
      {/* Decorative background gradients matching design specs */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      <div className="absolute top-1/4 left-1/3 w-[500px] h-[300px] bg-cyan-500/[0.02] rounded-full blur-[100px] pointer-events-none" />

      <Navbar />

      <div className="pt-32 pb-20 px-6 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Breadcrumb / Back to Tools */}
          <div className="mb-8">
            <Link to="/tools" className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors font-mono">
              <ArrowLeft className="h-4 w-4" /> Back to Tools
            </Link>
          </div>

          {/* Page Wrapper */}
          <div className="p-8 border border-slate-800 rounded-2xl bg-slate-900/40 backdrop-blur-xl shadow-2xl">
            {/* Header Icon */}
            <div className="flex items-center gap-4 mb-8 border-b border-slate-800 pb-6">
              <div className="p-3.5 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 shadow-lg shadow-cyan-500/10">
                <Cpu className="h-7 w-7 text-cyan-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white tracking-tight font-syne">Quantum Simulator Tool</h1>
                <p className="text-sm text-slate-400 mt-1 font-mono">Execute OpenQASM circuits on remote backend processors.</p>
              </div>
            </div>

            <QuantumSimulatorTab />

            {/* Researcher SEO Section */}
            <div className="mt-16 pt-8 border-t border-slate-800">
              <div className="max-w-4xl">
                <h2 className="text-2xl font-bold text-white mb-4">Professional Quantum Circuit Simulator for Advanced Research</h2>
                <p className="text-slate-400 mb-8 leading-relaxed">
                  For quantum researchers and algorithm developers, the gap between theoretical circuit design and actual hardware execution is often fraught with friction. Setting up local development environments, managing API tokens for disparate Quantum Processing Units (QPUs), and manually translating visual circuits into OpenQASM syntax wastes valuable research hours. You need a unified environment where you can prototype entanglement protocols, debug complex statevectors step-by-step, and seamlessly deploy to real hardware without leaving your browser.
                </p>

                <div className="grid md:grid-cols-3 gap-6">
                  <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
                    <h3 className="text-lg font-semibold text-white mb-2">1. Visual Circuit Design with Instant OpenQASM 3.0 Export</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      Stop writing boilerplate code. Our interactive drag-and-drop circuit builder allows you to rapidly prototype complex quantum algorithms. As you place gates, the platform dynamically generates clean, syntax-perfect OpenQASM 3.0 code in real-time. Export your complete .qasm payload with a single click.
                    </p>
                  </div>
                  <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
                    <h3 className="text-lg font-semibold text-white mb-2">2. Execute on Real Hardware</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      When you are ready to validate your algorithms against real-world quantum noise, bypass the queue. QuantCAI allows you to seamlessly switch your execution backend from our local simulator directly to trapped-ion and superconducting processors.
                    </p>
                  </div>
                  <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
                    <h3 className="text-lg font-semibold text-white mb-2">3. Debugging and Quantum Error Mitigation</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      Hardware noise is the enemy of NISQ-era research. Our integrated debugger lets you step backward and forward through your circuit depth. Unlock advanced algorithmic error mitigation toggles including ZNE and PEC.
                    </p>
                  </div>
                </div>

                <div className="mt-8 bg-gradient-to-r from-blue-900/30 to-cyan-900/30 border border-cyan-500/30 p-6 rounded-xl flex flex-col md:flex-row items-center justify-between gap-6">
                  <p className="text-slate-300 text-sm">
                    Don't let local compute limits bottleneck your algorithmic research. Scale your experiments, unlock direct API access to real hardware, and utilize advanced error mitigation pipelines.
                  </p>
                  <Link to="/signup?plan=pro" className="shrink-0 bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg font-semibold transition-colors">
                    Upgrade to Pro
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
