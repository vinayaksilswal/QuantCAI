import { Link } from 'react-router-dom';
import { CheckoutButton } from '@/components/CheckoutButton';


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
  highlighted?: boolean;
  planKey?: string; // "pro" or "enterprise" for PayPal checkout
}

const PlanCard = ({ name, price, originalPrice, discountPercentage, period, badge, features, cta, ctaHref, highlighted, planKey }: PlanProps) => {
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
      {planKey ? (
        <div className="mt-auto w-full">
          <div className="bg-white rounded-xl p-4 text-center mt-auto shadow-md border border-gray-200">
            <div className="flex justify-center items-center gap-2 mb-2">
              <span className="text-gray-400 line-through text-xs font-semibold">Regular Price: $99</span> 
              <span className="text-red-600 font-bold text-sm">Today: $27</span>
            </div>
            <a href="https://warriorplus.com/o2/buy/rrynld/0" target="_blank" rel="noopener noreferrer" className="bg-[#ffdd00] hover:bg-[#ffcc00] text-black font-black flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg shadow-sm mb-1 transition-colors border border-yellow-400">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              ADD TO CART
            </a>
            <div className="text-[10px] text-gray-500 italic mb-2">powered by WarriorPlus.com</div>
            <div className="flex justify-center items-center gap-1 opacity-60 grayscale">
              <svg className="h-4" viewBox="0 0 38 24" xmlns="http://www.w3.org/2000/svg"><path d="M35 0H3C1.3 0 0 1.3 0 3v18c0 1.7 1.4 3 3 3h32c1.7 0 3-1.3 3-3V3c0-1.7-1.4-3-3-3z" fill="#000" opacity=".07"/><path d="M35 1c1.1 0 2 .9 2 2v18c0 1.1-.9 2-2 2H3c-1.1 0-2-.9-2-2V3c0-1.1.9-2 2-2h32" fill="#FFF"/><path d="M28.3 10.1c.2-.4.4-1.2-.4-1.5-.7-.3-1.5-.3-2.3-.3-2.5 0-4.3 1.3-4.3 3.2 0 1.4 1.3 2.2 2.3 2.7 1 .5 1.4.8 1.4 1.3 0 .7-.8 1.1-1.6 1.1-1.1 0-1.7-.2-2.3-.4l-.3-.1-.3 1.5c.6.3 1.5.5 2.5.5 2.7 0 4.4-1.3 4.4-3.3 0-1.1-.6-2-2.3-2.8-1-.5-1.5-.8-1.5-1.3 0-.4.5-1 1.5-1 .8.1 1.4.3 1.8.5l.2.1.2-1.5zM21.5 8.1l-1.9 10.4h-3l-2.1-7.2c-.1-.5-.5-.8-.9-.9l-2.8-.6v-.1h4.6c.5 0 .9.3 1 .9l1.2 5.8h.1l1.9-6.7h2.9zm13.1 0l-1.6 10.4h-2.9l-.7-5c-.1-.4-.1-.8-.3-1.1l-.9-4.3h3.1l.5 3.7c.1.6.2 1.3.2 1.3h.1s.2-.6.4-1.2l1.6-3.8h2.6v.1l-2 4.6zM11.3 8.1H8.5L7.2 18.5h2.8l1.3-10.4z" fill="#142688"/></svg>
              <svg className="h-4" viewBox="0 0 38 24" xmlns="http://www.w3.org/2000/svg"><path d="M35 0H3C1.3 0 0 1.3 0 3v18c0 1.7 1.4 3 3 3h32c1.7 0 3-1.3 3-3V3c0-1.7-1.4-3-3-3z" fill="#000" opacity=".07"/><path d="M35 1c1.1 0 2 .9 2 2v18c0 1.1-.9 2-2 2H3c-1.1 0-2-.9-2-2V3c0-1.1.9-2 2-2h32" fill="#FFF"/><path d="M22.7 12c0 2.4-.9 4.6-2.5 6.3l.1-.1c2 2 5.2 2 7.2 0 1.7-1.7 2.5-3.9 2.5-6.2 0-2.3-.9-4.5-2.5-6.2-2-2-5.2-2-7.2 0 1.6 1.7 2.4 3.9 2.4 6.2z" fill="#FF5F00"/><path d="M14.6 5.8C12.6 3.8 9.4 3.8 7.4 5.8c-1.7 1.7-2.5 3.9-2.5 6.2 0 2.3.9 4.5 2.5 6.2 2 2 5.2 2 7.2 0 1.6-1.7 2.5-3.9 2.5-6.2 0-2.3-.9-4.6-2.5-6.2z" fill="#EB001B"/><path d="M22.7 12c0-2.3-.8-4.5-2.5-6.2-1.7 1.7-2.5 3.9-2.5 6.2 0 2.4.9 4.6 2.5 6.3 1.6-1.7 2.5-3.9 2.5-6.3z" fill="#F79E1B"/></svg>
            </div>
          </div>
        </div>
      ) : ctaHref?.startsWith('/') ? (
        <div className="mt-auto w-full">
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
        </div>
      ) : (
        <div className="mt-auto w-full">
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
        </div>
      )}
    </div>
  );
};

export const PricingSection = () => {
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
              '500 Developer API requests per day (Wallet overage available)',
              'Static Cryptographic Bill of Materials (CBOM) Export & Priority Support',
            ]}
            cta="Upgrade to Pro"
            planKey="pro"
          />
          <PlanCard
            name="Enterprise & Research"
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
            cta="Request Demo"
            ctaHref="/enterprise"
          />
        </div>
      </div>
    </section>
  );
};
