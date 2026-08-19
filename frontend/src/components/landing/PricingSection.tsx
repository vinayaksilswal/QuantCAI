import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useEffect, useState } from 'react';
import { Check, Minus, ShieldCheck } from 'lucide-react';

/**
 * Pricing.
 *
 * Checkout still runs through WarriorPlus — same URL, same custom={user.id}
 * parameter, same auto-checkout-after-login flow. What changed is the framing:
 * the plan no longer sits inside a white panel showing "Regular: $99 /
 * Today: $27" above a WarriorPlus-branded image button. A struck-through
 * anchor price and a countdown-style discount are the visual grammar of
 * affiliate marketing, and a CISO evaluating a cryptography vendor reads it as
 * a reason to leave. The price is simply the price.
 *
 * Limits below mirror backend/core/config.py TIER_LIMITS exactly. They were
 * stale — Pro advertised 15 qubits after the ceiling moved to 24.
 */

const WARRIORPLUS_CHECKOUT = 'https://warriorplus.com/o2/buy/b0pzyf/jgbrsv/qd1f63';

interface PlanProps {
  name: string;
  price: string;
  period?: string;
  billingNote?: string;
  summary: string;
  badge?: string;
  features: string[];
  cta: string;
  ctaHref?: string;
  highlighted?: boolean;
  planKey?: 'pro';
}

const PlanCard = ({
  name, price, period, billingNote, summary, badge, features, cta, ctaHref, highlighted, planKey,
}: PlanProps) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleProCheckout = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!user) {
      // Send them to sign in, then bounce straight back into checkout.
      navigate('/login', {
        state: { from: { pathname: window.location.pathname, search: '?autoCheckout=warriorplus' } },
      });
    } else {
      window.location.href = `${WARRIORPLUS_CHECKOUT}?custom=${user.id}`;
    }
  };

  const ctaClasses = highlighted
    ? 'bg-qc-accent text-qc-accent-fg hover:bg-qc-accent-hover'
    : 'border border-qc-border-strong text-qc-text hover:bg-qc-surface-hover';

  return (
    <div
      className={`relative flex flex-col rounded-xl p-6 sm:p-7 h-full ${
        highlighted
          ? 'border-2 border-qc-accent bg-qc-surface shadow-qc-lg'
          : 'border border-qc-border bg-qc-surface'
      }`}
    >
      {badge && (
        <span className="absolute -top-3 left-6 px-3 py-1 rounded-full bg-qc-accent text-qc-accent-fg text-[11px] font-bold tracking-wide uppercase">
          {badge}
        </span>
      )}

      <h3 className="font-semibold text-lg text-qc-text">{name}</h3>
      <p className="text-sm text-qc-muted mt-1 min-h-[2.5rem]">{summary}</p>

      <div className="flex items-baseline gap-1.5 mt-5">
        <span className="font-bold text-4xl text-qc-text tracking-tight">{price}</span>
        {period && <span className="text-qc-muted text-sm">{period}</span>}
      </div>
      <p className="text-xs text-qc-subtle mt-1.5 min-h-[1rem]">{billingNote ?? ''}</p>

      <div className="qc-rule my-6" />

      <ul className="space-y-3 flex-1">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2.5">
            <Check className="w-4 h-4 text-qc-accent shrink-0 mt-0.5" aria-hidden="true" />
            <span className="text-sm text-qc-muted leading-relaxed">{f}</span>
          </li>
        ))}
      </ul>

      <div className="mt-7">
        {planKey === 'pro' ? (
          <a
            href={WARRIORPLUS_CHECKOUT}
            onClick={handleProCheckout}
            className={`qc-tap flex items-center justify-center w-full rounded-lg py-3 text-sm font-semibold transition-colors ${ctaClasses}`}
          >
            {cta}
          </a>
        ) : ctaHref?.startsWith('/') ? (
          <Link
            to={ctaHref}
            className={`qc-tap flex items-center justify-center w-full rounded-lg py-3 text-sm font-semibold transition-colors ${ctaClasses}`}
          >
            {cta}
          </Link>
        ) : (
          <a
            href={ctaHref}
            className={`qc-tap flex items-center justify-center w-full rounded-lg py-3 text-sm font-semibold transition-colors ${ctaClasses}`}
          >
            {cta}
          </a>
        )}
      </div>
    </div>
  );
};

/* Mirrors backend/core/config.py TIER_LIMITS. Keep the two in step. */
const comparison = [
  { name: 'Max qubits (statevector)', free: '3', pro: '24', ent: '26' },
  { name: 'Simulation methods', free: 'Statevector', pro: 'MPS, stabilizer, density matrix', ent: 'All' },
  { name: 'Max shots', free: '1,024', pro: '65,536', ent: '65,536' },
  { name: 'Noise models', free: null, pro: 'Depolarizing, thermal', ent: 'Depolarizing, thermal' },
  { name: 'Daily simulation runs', free: '10', pro: '500', ent: 'Unlimited' },
  { name: 'PQC domain scans', free: '3 / mo', pro: '50 / mo', ent: 'Unlimited' },
  { name: 'CycloneDX CBOM export', free: null, pro: 'CycloneDX 1.6', ent: 'CycloneDX 1.6' },
  { name: 'Developer API', free: '10 req / day', pro: '500 req / day', ent: '100,000 req / day' },
  { name: 'Scheduled monitoring', free: null, pro: null, ent: 'Included' },
  { name: 'Support', free: 'Community', pro: 'Priority email', ent: 'Dedicated SLA' },
];

const Cell = ({ value }: { value: string | null }) =>
  value === null ? (
    <Minus className="w-4 h-4 text-qc-subtle mx-auto" aria-label="Not included" />
  ) : (
    <span>{value}</span>
  );

export const PricingSection = () => {
  const location = useLocation();
  const { user } = useAuth();
  const [isAnnual, setIsAnnual] = useState(false);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.get('autoCheckout') === 'warriorplus') {
      searchParams.delete('autoCheckout');
      const newSearch = searchParams.toString();
      window.history.replaceState({}, '', window.location.pathname + (newSearch ? '?' + newSearch : ''));
      const customParam = user ? `?custom=${user.id}` : '';
      window.location.href = `${WARRIORPLUS_CHECKOUT}${customParam}`;
    }
  }, [location.search, user]);

  return (
    <section id="pricing" className="qc-section border-t border-qc-border bg-qc-bg-raised">
      <div className="qc-container">
        <div className="max-w-2xl">
          <span className="qc-eyebrow">Pricing</span>
          <h2 className="text-fluid-h2 font-bold text-qc-text mt-3">
            Start free. Pay when it becomes evidence.
          </h2>
          <p className="text-fluid-lead text-qc-muted mt-4 qc-measure">
            No card required to scan. Upgrade when you need the machine-readable
            inventory and the higher simulation ceiling.
          </p>
        </div>

        {/* Billing toggle */}
        <div className="flex items-center gap-3 mt-8">
          <span className={`text-sm ${!isAnnual ? 'text-qc-text font-medium' : 'text-qc-muted'}`}>
            Monthly
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={isAnnual}
            aria-label="Toggle annual billing"
            onClick={() => setIsAnnual(!isAnnual)}
            className={`relative w-14 h-8 rounded-full transition-colors ${
              isAnnual ? 'bg-qc-accent' : 'bg-qc-surface-hover border border-qc-border-strong'
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-qc-text transition-transform ${
                isAnnual ? 'translate-x-6' : ''
              }`}
            />
          </button>
          <span className={`text-sm flex items-center gap-2 ${isAnnual ? 'text-qc-text font-medium' : 'text-qc-muted'}`}>
            Annual
            <span className="qc-pill qc-pill-ok">Save 33%</span>
          </span>
        </div>

        <div className="grid md:grid-cols-3 gap-5 sm:gap-6 mt-8 items-stretch">
          <PlanCard
            name="Free"
            price="$0"
            period="/ forever"
            summary="Check a handful of domains and learn the platform."
            features={[
              '3 PQC domain scans per month',
              'Circuit builder up to 3 qubits',
              'Ideal simulator, 1,024 shots',
              '10 simulation runs per day',
              '10 developer API requests per day',
              'Learning hub and community support',
            ]}
            cta="Create free account"
            ctaHref="/signup"
          />
          <PlanCard
            name="Pro"
            price={isAnnual ? '$18' : '$27'}
            period="/ month"
            billingNote={isAnnual ? 'Billed $216 annually' : 'Billed monthly, cancel anytime'}
            summary="For teams producing migration evidence."
            badge="Most popular"
            highlighted
            planKey="pro"
            features={[
              '50 PQC domain scans per month',
              'CycloneDX 1.6 CBOM export',
              'Circuit builder up to 24 qubits',
              'Matrix-product-state and stabilizer methods',
              'Depolarizing and thermal noise models',
              '500 simulation runs and 500 API requests per day',
              'Workspace-aware AI assistant',
              'Priority email support',
            ]}
            cta="Upgrade to Pro"
          />
          <PlanCard
            name="Enterprise"
            price="Custom"
            summary="For regulated environments and internal networks."
            features={[
              'Unlimited scans and scheduled monitoring',
              'Internal network and IP range scanning',
              'Public readiness badge for your site',
              'SSO and team management',
              '100,000 API requests per day',
              'Dedicated SLA and onboarding',
            ]}
            cta="Talk to us"
            ctaHref="/enterprise"
          />
        </div>

        {/* Refund terms — a factual statement of policy, not a sales badge. */}
        <div className="qc-card p-5 sm:p-6 mt-8 flex items-start gap-4">
          <ShieldCheck className="w-5 h-5 text-qc-accent shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-semibold text-qc-text">30-day refund policy</h3>
            <p className="text-sm text-qc-muted mt-1 leading-relaxed">
              If Pro does not do what you need, request a full refund within 30 days of
              purchase. See the{' '}
              <Link to="/refund-policy" className="text-qc-accent hover:underline">
                refund policy
              </Link>{' '}
              for details.
            </p>
          </div>
        </div>

        {/* Comparison. Scrolls inside itself on small screens instead of
            forcing the page sideways; hiding it on mobile removed the one
            place a buyer can compare plans on the device most of them browse
            from. */}
        <div className="mt-14">
          <h3 className="text-xl font-semibold text-qc-text mb-5">Compare plans</h3>
          <div className="qc-card overflow-x-auto">
            <table className="w-full min-w-[38rem] text-left border-collapse">
              <thead>
                <tr className="border-b border-qc-border">
                  <th scope="col" className="p-4 text-sm font-semibold text-qc-muted">Feature</th>
                  <th scope="col" className="p-4 text-sm font-semibold text-qc-muted text-center">Free</th>
                  <th scope="col" className="p-4 text-sm font-bold text-qc-accent text-center">Pro</th>
                  <th scope="col" className="p-4 text-sm font-semibold text-qc-muted text-center">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row) => (
                  <tr key={row.name} className="border-b border-qc-border last:border-0">
                    <th scope="row" className="p-4 text-sm font-normal text-qc-text">{row.name}</th>
                    <td className="p-4 text-sm text-qc-muted text-center"><Cell value={row.free} /></td>
                    <td className="p-4 text-sm text-qc-text text-center font-medium"><Cell value={row.pro} /></td>
                    <td className="p-4 text-sm text-qc-muted text-center"><Cell value={row.ent} /></td>
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
