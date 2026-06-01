import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { QuantumSimulatorTab } from '@/components/dashboard/QuantumSimulatorTab';
import { usePageTracking } from '@/hooks/usePageTracking';
import { Link } from 'react-router-dom';
import { ArrowLeft, Cpu } from 'lucide-react';

export default function QuantumSimulator() {
  usePageTracking('quantum-simulator');

  return (
    <div className="min-h-screen relative overflow-hidden bg-[#0a0f1d] text-white">
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
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
