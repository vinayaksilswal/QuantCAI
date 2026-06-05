import { useAuth } from '@/hooks/useAuth';
import { useRazorpayCheckout } from '@/hooks/useRazorpayCheckout';
import { useNavigate } from 'react-router-dom';

/* ── Inline SVG Icons ─────────────────────────────────────────────── */
const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
  </svg>
);

/* ── Types ─────────────────────────────────────────────────────────── */
interface PlanProps {
  name: string;
  price: string;
  period?: string;
  badge?: string;
  features: string[];
  cta: string;
  ctaHref?: string;
  onClick?: () => void;
  highlighted?: boolean;
  loading?: boolean;
}

const PlanCard = ({ name, price, period, badge, features, cta, ctaHref, onClick, highlighted, loading }: PlanProps) => (
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
  const { user } = useAuth();
  const { startCheckout, loading } = useRazorpayCheckout();
  const navigate = useNavigate();

  const handleProClick = async () => {
    if (user) {
      try {
        await startCheckout('pro', 240000, 'INR');
        window.location.reload();
      } catch (err) {
        console.error('Checkout failed:', err);
      }
    } else {
      localStorage.setItem('pending_checkout', 'pro');
      navigate('/signup?plan=pro');
    }
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
            name="Free"
            price="$0"
            features={[
              '20 API calls / day',
              'Max 1,024 shots per circuit',
              '3 PQC scans / month',
              'Community support',
            ]}
            cta="Start Free"
            ctaHref="/signup"
          />
          <PlanCard
            name="Pro"
            price="$29"
            period="month"
            badge="Most Popular"
            highlighted
            features={[
              '500 API calls / day',
              '65,536 shots + noise models',
              '50 PQC scans / month',
              'Full AI Tutor access',
              'CBOM PDF export',
              'Priority email support',
            ]}
            cta="Start Pro Trial"
            onClick={handleProClick}
            loading={loading}
          />
          <PlanCard
            name="Enterprise"
            price="$299"
            period="month"
            features={[
              'Unlimited API calls',
              'Unlimited shots + custom noise',
              'Unlimited PQC scans',
              'SSO + multi-user orgs',
              'SLA + priority support',
              'Annual contracts available',
            ]}
            cta="Contact Sales"
            ctaHref="mailto:sales@quantcai.in"
          />
        </div>
      </div>
    </section>
  );
};
