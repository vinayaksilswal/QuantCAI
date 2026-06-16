import { Link } from 'react-router-dom';

/* ── Inline SVG Icons ─────────────────────────────────────────────── */
const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
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
  onClick?: () => void;
  highlighted?: boolean;
  loading?: boolean;
}

const PlanCard = ({ name, price, originalPrice, discountPercentage, period, badge, features, cta, ctaHref, onClick, highlighted, loading }: PlanProps) => (
  <div className={`relative rounded-2xl border p-6 sm:p-8 flex flex-col transition-all duration-300 backdrop-blur-xl
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
        {period && <span className="text-blue-300/70 text-sm">/{period}</span>}
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
    {onClick ? (
      <button
        onClick={onClick}
        disabled={loading}
        className={`block w-full text-center py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 disabled:opacity-50
          ${highlighted
            ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white hover:from-teal-400 hover:to-cyan-400 shadow-lg shadow-teal-500/30'
            : 'border border-white/10 text-white hover:border-blue-400/30 hover:bg-white/10 backdrop-blur-sm'
          }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />
            Processing...
          </span>
        ) : cta}
      </button>
    ) : ctaHref?.startsWith('/') ? (
      <Link
        to={ctaHref}
        className={`block text-center py-2.5 rounded-lg text-sm font-semibold transition-all duration-300
          ${highlighted
            ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white hover:from-teal-400 hover:to-cyan-400 shadow-lg shadow-teal-500/30'
            : 'border border-white/10 text-white hover:border-blue-400/30 hover:bg-white/10 backdrop-blur-sm'
          }`}
      >
        {cta}
      </Link>
    ) : (
      <a
        href={ctaHref}
        className={`block text-center py-2.5 rounded-lg text-sm font-semibold transition-all duration-300
          ${highlighted
            ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white hover:from-teal-400 hover:to-cyan-400 shadow-lg shadow-teal-500/30'
            : 'border border-white/10 text-white hover:border-blue-400/30 hover:bg-white/10 backdrop-blur-sm'
          }`}
      >
        {cta}
      </a>
    )}
  </div>
);

export const PricingSection = () => {
  const handleProClick = () => {
    const wplusCheckoutUrl = import.meta.env.VITE_WARRIORPLUS_CHECKOUT_URL || 'https://warriorplus.com/as/o/466941';
    window.location.href = wplusCheckoutUrl;
  };

  return (
    <section id="pricing" className="py-20 sm:py-28 px-4 sm:px-6 relative z-10">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-14">
          <p className="text-teal-400 text-xs font-mono uppercase tracking-widest mb-3 drop-shadow-sm">Pricing</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3 drop-shadow-lg">
            Start free. Scale when you're ready.
          </h2>
          <p className="text-blue-200 text-sm max-w-lg mx-auto drop-shadow-sm">
            No credit card required for Free tier. All plans include API access to both
            quantum simulation and PQC scanning.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <PlanCard
            name="Free Tier"
            price="$0"
            features={[
              'Basic Learning Hub & Interactive Quantum States',
              'Quantum Circuit Builder (Up to 3 Qubits)',
              'Ideal Quantum Simulator (Maximum 1,024 Shots)',
              '10 daily circuit simulation runs',
              '3 Post-Quantum Cryptography Domain Scans per month',
              '10 Developer API requests per day',
              'Community forum support',
            ]}
            cta="Start Free"
            ctaHref="/signup"
          />
          <PlanCard
            name="Pro Tier"
            price="$27"
            originalPrice="$99"
            discountPercentage="72% OFF"
            period="month"
            badge="Most Popular"
            highlighted
            features={[
              'Full Interactive States & Quantum Circuit Builder (Up to 15 Qubits)',
              'Advanced Quantum Simulator (Maximum 65,536 Shots)',
              'Thermal & Depolarizing Quantum Noise Models',
              '500 daily circuit simulation runs',
              '50 Post-Quantum Cryptography Domain Scans per month',
              'Unlimited Artificial Intelligence Tutor access (QuantAI)',
              '500 Developer API requests per day',
              'Static Cryptographic Bill of Materials (CBOM) Export & Priority Support',
            ]}
            cta="Upgrade to Pro"
            onClick={handleProClick}
            loading={false}
          />
          <PlanCard
            name="Enterprise Compliance"
            price="Custom"
            features={[
              'Sovereign Post-Quantum Cryptography compliance suite',
              'CycloneDX 1.6 automated Cryptographic Bill of Materials generation',
              'Internal network & port scanning',
              'Cryptographic Vulnerability Mapping & Remediation',
              'Unlimited daily circuit simulation runs',
              'Single Sign-On (SSO) & multi-user organization console',
              'Dedicated Service Level Agreement (SLA) & consultative procurement',
            ]}
            cta="Contact Sales"
            ctaHref="/enterprise"
          />
        </div>
      </div>
    </section>
  );
};
