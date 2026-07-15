import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useEffect, useState } from 'react';
import { CheckCircle2, ShieldCheck } from 'lucide-react';

/* ── Inline SVG Icons ─────────────────────────────────────────────── */
const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
  </svg>
);

const MinusIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-slate-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 12h-15" />
  </svg>
);

/* ── Types ─────────────────────────────────────────────────────────── */
interface PlanProps {
  name: string;
  price: string | React.ReactNode;
  originalPrice?: string;
  discountPercentage?: string;
  period?: string;
  badge?: string;
  features: string[];
  cta: string;
  ctaHref?: string;
  highlighted?: boolean;
  planKey?: string; // "pro" or "enterprise" for checkout
}

const PlanCard = ({ name, price, originalPrice, discountPercentage, period, badge, features, cta, ctaHref, highlighted, planKey }: PlanProps) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleProCheckout = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (!user) {
      navigate('/login', { state: { from: { pathname: window.location.pathname, search: '?autoCheckout=warriorplus' } } });
    } else {
      window.location.href = `https://warriorplus.com/o2/buy/b0pzyf/jgbrsv/qd1f63?custom=${user.id}`;
    }
  };

  return (
    <div className={`relative rounded-2xl border p-6 sm:p-8 flex flex-col transition-all duration-300 backdrop-blur-xl h-full
      ${highlighted
        ? 'border-teal-400/40 bg-white/10 shadow-2xl shadow-teal-500/20 hover:border-teal-400/60'
        : 'border-white/10 bg-white/5 shadow-2xl shadow-blue-500/10 hover:border-blue-400/30'
      }`}
    >
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-0.5 rounded-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white text-[10px] font-bold tracking-wider uppercase shadow-lg shadow-teal-500/30">
          {badge}
        </div>
      )}
      <div className="mb-6">
        <h3 className="font-bold text-lg text-white mb-1 drop-shadow-md">{name}</h3>
        {originalPrice && (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-slate-400 line-through text-sm">{originalPrice}</span>
            {discountPercentage && (
              <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400 text-[10px] font-bold tracking-wider uppercase">
                {discountPercentage}
              </span>
            )}
          </div>
        )}
        <div className="flex items-baseline gap-1">
          <span className="font-extrabold text-3xl text-white drop-shadow-md">{price}</span>
          {period && <span className="text-blue-300/70 text-sm">{period}</span>}
        </div>
      </div>
      <ul className="space-y-3 mb-8 flex-1">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-blue-200">
            <CheckIcon />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      {planKey === 'pro' ? (
        <div className="mt-auto w-full">
          <div className="bg-white rounded-xl p-4 text-center mt-auto shadow-md border border-gray-200">
             <div className="flex justify-center items-center gap-2 mb-2">
               <span className="text-gray-400 line-through text-xs font-semibold">Regular: $99</span> 
               <span className="text-red-600 font-bold text-sm">Today: {price}</span>
             </div>
             <div className="flex justify-center items-center py-2 w-full">
               <a href="https://warriorplus.com/o2/buy/b0pzyf/jgbrsv/qd1f63" onClick={handleProCheckout}>
                 <img src="https://warriorplus.com/o2/btn/fn300011000/b0pzyf/jgbrsv/467202" alt="WarriorPlus Buy Button" className="hover:scale-105 transition-transform" />
               </a>
             </div>
          </div>
        </div>
      ) : ctaHref?.startsWith('/') ? (
        <div className="mt-auto w-full">
          <Link
            to={ctaHref}
            className={`block text-center py-3 rounded-xl text-sm font-semibold transition-all duration-300
              ${highlighted
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white hover:from-teal-400 hover:to-cyan-400 shadow-lg shadow-teal-500/30 hover:shadow-xl'
                : 'border border-white/10 text-white hover:border-blue-400/30 hover:bg-white/10 backdrop-blur-sm'
              }`}
          >
            {cta}
          </Link>
        </div>
      ) : (
        <div className="mt-auto w-full">
          <a
            href={ctaHref}
            className={`block text-center py-3 rounded-xl text-sm font-semibold transition-all duration-300
              ${highlighted
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white hover:from-teal-400 hover:to-cyan-400 shadow-lg shadow-teal-500/30 hover:shadow-xl'
                : 'border border-white/10 text-white hover:border-blue-400/30 hover:bg-white/10 backdrop-blur-sm'
              }`}
          >
            {cta}
          </a>
        </div>
      )}
    </div>
  );
};

export const PricingSection = () => {
  const location = useLocation();
  const { user } = useAuth();
  const [isAnnual, setIsAnnual] = useState(false);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get('autoCheckout') === 'warriorplus') {
      searchParams.delete('autoCheckout');
      const newSearch = searchParams.toString();
      const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '');
      window.history.replaceState({}, '', newUrl);

      const customParam = user ? `?custom=${user.id}` : '';
      window.location.href = `https://warriorplus.com/o2/buy/b0pzyf/jgbrsv/qd1f63${customParam}`;
    }
  }, [location.search, user]);

  return (
    <section id="pricing" className="py-20 sm:py-28 px-4 sm:px-6 relative z-10">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <p className="text-teal-400 text-xs font-mono uppercase tracking-widest mb-3 drop-shadow-sm">Pricing</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 drop-shadow-lg">
            Start free. Scale when you're ready.
          </h2>
          <p className="text-blue-200 text-sm max-w-lg mx-auto mb-8 drop-shadow-sm">
            No credit card required for Free tier. All plans include API access to both
            quantum simulation and PQC scanning.
          </p>

          {/* Annual Toggle */}
          <div className="flex items-center justify-center gap-3">
            <span className={`text-sm font-medium ${!isAnnual ? 'text-white drop-shadow-sm' : 'text-slate-400'}`}>Monthly</span>
            <button 
              onClick={() => setIsAnnual(!isAnnual)}
              className="relative w-14 h-7 rounded-full bg-slate-800 border border-slate-700 transition-colors duration-300 focus:outline-none"
            >
              <div className={`absolute top-1 left-1 w-5 h-5 rounded-full bg-teal-400 shadow-md transform transition-transform duration-300 ${isAnnual ? 'translate-x-7' : ''}`} />
            </button>
            <span className={`text-sm font-medium flex items-center gap-2 ${isAnnual ? 'text-white drop-shadow-sm' : 'text-slate-400'}`}>
              Annually
              <span className="px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-400 text-[10px] font-bold tracking-wider uppercase border border-teal-500/30">
                Save 20%
              </span>
            </span>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-16">
          <PlanCard
            name="Free Tier"
            price="$0"
            period="/ forever"
            features={[
              'Basic Learning Hub & Interactive States',
              'Quantum Circuit Builder (Up to 3 Qubits)',
              'Ideal Quantum Simulator (1,024 Shots)',
              '10 daily circuit simulation runs',
              '3 PQC Domain Scans per month',
              '10 Developer API requests per day',
              'Community forum support',
            ]}
            cta="Start Free"
            ctaHref="/signup"
          />
          <PlanCard
            name="Pro Tier"
            price={isAnnual ? "$216" : "$27"}
            originalPrice={isAnnual ? "$1188" : "$99"}
            discountPercentage="72% OFF"
            period={isAnnual ? "/ year" : "/ month"}
            badge="Most Popular"
            highlighted
            features={[
              'Full Circuit Builder (Up to 15 Qubits)',
              'Advanced Simulator (65,536 Shots)',
              'Thermal & Depolarizing Noise Models',
              '500 daily circuit simulation runs',
              '50 PQC Domain Scans per month',
              'Unlimited AI Tutor access (QuantAI)',
              '500 API requests / day',
              'CBOM Export & Priority Support',
            ]}
            cta="Upgrade to Pro"
            planKey="pro"
          />
          <PlanCard
            name="Enterprise"
            price="Custom"
            period=""
            features={[
              'Sovereign PQC compliance suite',
              'CycloneDX 1.6 CBOM generation',
              'Internal network & port scanning',
              'Cryptographic Vulnerability Mapping',
              'Unlimited simulation runs & API',
              'Single Sign-On (SSO) & Teams',
              'Dedicated SLA & Custom engineering',
            ]}
            cta="Request Demo"
            ctaHref="/enterprise"
          />
        </div>

        {/* Guarantee Badge */}
        <div className="flex justify-center mb-16">
          <div className="inline-flex items-center gap-4 bg-slate-900/60 border border-slate-700/50 backdrop-blur-sm rounded-2xl p-4 sm:p-6 shadow-xl max-w-2xl text-left">
            <div className="w-12 h-12 rounded-full bg-teal-500/10 flex items-center justify-center shrink-0 border border-teal-500/20">
              <ShieldCheck className="h-6 w-6 text-teal-400" />
            </div>
            <div>
              <h4 className="text-white font-bold text-sm sm:text-base">30-Day Money-Back Guarantee</h4>
              <p className="text-slate-400 text-xs sm:text-sm mt-1">
                Try QuantCAI Pro completely risk-free. If you're not satisfied with the PQC scanner or simulators, we'll refund 100% of your payment. No questions asked.
              </p>
            </div>
          </div>
        </div>

        {/* Feature Comparison Table */}
        <div className="max-w-4xl mx-auto hidden sm:block">
          <h3 className="text-2xl font-bold text-center text-white mb-8">Compare Plan Features</h3>
          <div className="bg-slate-900/40 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-xl">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/5 border-b border-white/10">
                  <th className="p-4 text-slate-300 font-semibold w-1/3">Feature</th>
                  <th className="p-4 text-center text-slate-300 font-semibold">Free</th>
                  <th className="p-4 text-center text-teal-400 font-bold bg-teal-500/5">Pro</th>
                  <th className="p-4 text-center text-slate-300 font-semibold">Enterprise</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {[
                  { name: 'Max Qubits', free: '3', pro: '15', ent: 'Unlimited' },
                  { name: 'Max Simulator Shots', free: '1,024', pro: '65,536', ent: 'Unlimited' },
                  { name: 'Noise Models', free: <MinusIcon />, pro: <CheckIcon />, ent: <CheckIcon /> },
                  { name: 'PQC Domain Scans', free: '3 / mo', pro: '50 / mo', ent: 'Unlimited' },
                  { name: 'CBOM Export', free: <MinusIcon />, pro: <CheckIcon />, ent: 'CycloneDX 1.6' },
                  { name: 'QuantAI Tutor', free: 'Basic', pro: 'Unlimited', ent: 'Unlimited' },
                  { name: 'Support', free: 'Community', pro: 'Priority Email', ent: 'Dedicated SLA' },
                ].map((row, i) => (
                  <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                    <td className="p-4 text-sm text-slate-300">{row.name}</td>
                    <td className="p-4 text-sm text-center text-slate-400"><div className="flex justify-center">{row.free}</div></td>
                    <td className="p-4 text-sm text-center text-teal-300 bg-teal-500/5 font-medium"><div className="flex justify-center">{row.pro}</div></td>
                    <td className="p-4 text-sm text-center text-slate-300"><div className="flex justify-center">{row.ent}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </section>
  );
};
