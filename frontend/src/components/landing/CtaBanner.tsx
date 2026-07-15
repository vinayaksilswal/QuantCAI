import { ArrowRight, Shield, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export const CtaBanner = () => (
  <section className="py-20 sm:py-28 px-4 sm:px-6 relative z-10 overflow-hidden">
    <div className="max-w-3xl mx-auto text-center relative">
      {/* Decorative animated glow behind the CTA */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full pointer-events-none animate-pulse" 
        style={{
          background: 'radial-gradient(ellipse at center, rgba(20, 184, 166, 0.12) 0%, rgba(99, 102, 241, 0.08) 40%, transparent 70%)',
        }}
      />

      <div className="relative">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-medium mb-6 backdrop-blur-sm">
          <Sparkles className="h-3.5 w-3.5" />
          Join 500+ teams already migrating to quantum-safe
        </div>

        <h2 className="text-3xl sm:text-5xl font-bold text-white mb-5 drop-shadow-lg leading-tight">
          The quantum advantage{' '}
          <span className="bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">
            starts now.
          </span>
        </h2>
        <p className="text-blue-200/90 text-sm sm:text-base max-w-xl mx-auto mb-10 leading-relaxed drop-shadow-sm">
          Whether you're building quantum algorithms or hardening your infrastructure
          against quantum threats — QuantCAI gives you the tools to move first.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/get-started"
            className="group w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-semibold text-sm hover:from-teal-400 hover:to-cyan-400 transition-all duration-300 flex items-center justify-center gap-2 shadow-xl shadow-teal-500/25 hover:shadow-2xl hover:shadow-teal-500/40 hover:scale-[1.03]"
          >
            <Shield className="h-4 w-4" />
            Get Started Free
            <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            to="/learn"
            className="w-full sm:w-auto px-8 py-4 rounded-xl border border-white/10 text-white font-medium text-sm hover:border-blue-400/30 hover:bg-white/10 backdrop-blur-sm transition-all duration-300 flex items-center justify-center gap-2"
          >
            Read the Docs
          </Link>
        </div>
      </div>
    </div>
  </section>
);
