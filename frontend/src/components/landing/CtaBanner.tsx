import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const CtaBanner = () => (
  <section className="py-20 sm:py-28 px-4 sm:px-6 relative z-10">
    <div className="max-w-3xl mx-auto text-center">
      {/* Decorative glow behind the CTA */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-[100px] pointer-events-none" />

      <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 drop-shadow-lg relative">
        The quantum advantage starts now.
      </h2>
      <p className="text-blue-200 text-sm sm:text-base max-w-xl mx-auto mb-8 leading-relaxed drop-shadow-sm relative">
        Whether you're building quantum algorithms or hardening your infrastructure
        against quantum threats — QuantCAI gives you the tools to move first.
      </p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 relative">
        <Link
          to="/get-started"
          className="w-full sm:w-auto px-7 py-3.5 rounded-lg bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-semibold text-sm hover:from-teal-400 hover:to-cyan-400 transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-teal-500/30"
        >
          Get Started Free
          <ArrowRight className="h-4 w-4" />
        </Link>
        <Link
          to="/learn"
          className="w-full sm:w-auto px-7 py-3.5 rounded-lg border border-white/10 text-white font-medium text-sm hover:border-blue-400/30 hover:bg-white/10 backdrop-blur-sm transition-all duration-300 flex items-center justify-center gap-2"
        >
          Read the Docs
        </Link>
      </div>
    </div>
  </section>
);
