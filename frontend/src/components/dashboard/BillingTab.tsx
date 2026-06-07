import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';
import { CreditCard, Check, Sparkles, ExternalLink } from 'lucide-react';
import { CheckoutButton } from '@/components/CheckoutButton';

export function BillingTab() {
  const { subscriptionPlan } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);

  // const handleCheckout = async (planName: string) => {
  //   setLoading('checkout');
  //   try {
  //     const response = await axiosClient.post<{ url: string }>(`/billing/checkout?plan=${planName}`);
  //     if (response.data && response.data.url) {
  //       window.location.href = response.data.url;
  //     } else {
  //       toast.error('Failed to initiate checkout. Please try again.');
  //     }
  //   } catch (error: any) {
  //     console.error('Checkout error:', error);
  //     const msg = error.response?.data?.detail || 'Billing checkout failed. Please verify Stripe configuration on the backend.';
  //     toast.error(msg);
  //   } finally {
  //     setLoading(null);
  //   }
  // };

  const handlePortal = async () => {
    setLoading('portal');
    try {
      const response = await axiosClient.post<{ url: string }>('/billing/portal');
      if (response.data && response.data.url) {
        window.location.href = response.data.url;
      } else {
        toast.error('Failed to open billing portal.');
      }
    } catch (error: any) {
      console.error('Portal error:', error);
      const msg = error.response?.data?.detail || 'Billing record not found. Please complete a checkout first.';
      toast.error(msg);
    } finally {
      setLoading(null);
    }
  };

  // Capitalize plan helper
  const planLabel = subscriptionPlan ? subscriptionPlan.toUpperCase() : 'FREE';

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="font-syne font-bold text-2xl text-qc-text">Billing & Subscriptions</h1>
        <p className="text-sm text-qc-muted mt-1">Manage your subscription plan, payment methods, and billing details.</p>
      </div>

      {/* Plan status card */}
      <div className="p-6 border border-qc-border rounded bg-qc-surface flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-qc-accent/5 rounded-full blur-2xl pointer-events-none" />
        
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono tracking-wide uppercase text-qc-muted">Current Plan</span>
            <span className="px-2 py-0.5 rounded border border-qc-accent/25 bg-qc-accent/10 text-qc-accent text-[10px] font-mono font-bold">
              {planLabel}
            </span>
          </div>
          <h2 className="font-syne font-bold text-xl text-qc-text">
            {subscriptionPlan === 'enterprise' ? 'QuantCAI Enterprise Plan' :
             subscriptionPlan === 'pro' ? 'QuantCAI Pro Subscription' :
             'QuantCAI Free Plan'}
          </h2>
          <p className="text-xs text-qc-muted leading-relaxed font-mono">
            {subscriptionPlan === 'enterprise' ? 'Unlimited quantum circuit simulations and cryptographic audits.' :
             subscriptionPlan === 'pro' ? '₹2,400 per month · Up to 500 API calls daily and 50 PQC scans monthly.' :
             'Free forever · 20 API calls daily, 3 PQC scans monthly, 1,024 simulator shots.'}
          </p>
        </div>

        {subscriptionPlan !== 'free' && subscriptionPlan ? (
          <button
            onClick={handlePortal}
            disabled={loading !== null}
            className="px-5 py-2.5 rounded border border-qc-border text-qc-text font-semibold text-xs hover:border-qc-accent/50 hover:bg-qc-border/20 transition-all flex items-center justify-center gap-1.5 self-start md:self-center disabled:opacity-50"
          >
            <CreditCard className="w-4 h-4 text-qc-muted" />
            {loading === 'portal' ? 'Opening Portal...' : 'Manage Subscription'}
            <ExternalLink className="w-3.5 h-3.5 text-qc-muted" />
          </button>
        ) : (
          <CheckoutButton
            amount={240000}
            currency="INR"
            planName="pro"
            className="px-5 py-2.5 text-xs self-start md:self-center"
          >
            <Sparkles className="w-4 h-4 fill-current" />
            Upgrade to Pro
          </CheckoutButton>
        )}
      </div>

      {/* Plan comparisons */}
      <div className="space-y-4">
        <h3 className="font-syne font-bold text-sm text-qc-text">Available Subscription Tiers</h3>
        <div className="grid md:grid-cols-3 gap-6">
          
          {/* Free Tier */}
          <div className="p-5 border border-qc-border rounded bg-qc-surface/30 flex flex-col justify-between">
            <div className="space-y-4">
              <div>
                <h4 className="font-syne font-bold text-sm text-qc-text">Free Plan</h4>
                <p className="font-syne font-extrabold text-2xl text-qc-text mt-1">₹0</p>
              </div>
              <ul className="space-y-2 text-[11px] text-qc-muted font-mono leading-relaxed">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Basic access to Learning Hub</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Standard single-qubit simulations</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>20 API calls / day</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Max 1,024 shots</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>3 PQC domain scans / mo</span>
                </li>
                <li className="flex items-center gap-2 text-qc-muted/50">
                  <Check className="w-3.5 h-3.5 text-qc-muted/30 flex-shrink-0" />
                  <span>Ideal noise simulator only</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Community support</span>
                </li>
              </ul>
            </div>
            {subscriptionPlan === 'free' || !subscriptionPlan ? (
              <div className="mt-8 text-center py-2 text-xs font-semibold text-qc-accent font-mono">
                Your Current Tier
              </div>
            ) : null}
          </div>

          {/* Pro Tier */}
          <div className={`p-5 border rounded flex flex-col justify-between ${
            subscriptionPlan === 'pro' ? 'border-qc-accent bg-qc-accent/[0.02]' : 'border-qc-border bg-qc-surface/30'
          }`}>
            <div className="space-y-4">
              <div>
                <h4 className="font-syne font-bold text-sm text-qc-text flex items-center justify-between">
                  Pro Plan
                  {subscriptionPlan === 'pro' && (
                    <span className="px-1.5 py-0.5 rounded bg-qc-accent text-qc-bg text-[8px] font-bold uppercase tracking-wider">Active</span>
                  )}
                </h4>
                <p className="font-syne font-extrabold text-2xl text-qc-text mt-1">₹2,400 <span className="text-xs font-light text-qc-muted">/ month</span></p>
              </div>
              <ul className="space-y-2 text-[11px] text-qc-muted font-mono leading-relaxed">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>500 API calls / day</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Max 65,536 shots + noise models</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>50 PQC domain scans / mo</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Thermal & Depolarizing noise</span>
                </li>
                <li className="flex items-center gap-2 font-semibold text-qc-text">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>AI Tutor access (QuantAI)</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Standard static PDF CBOM export</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Priority email support</span>
                </li>
              </ul>
            </div>
            {subscriptionPlan === 'free' || !subscriptionPlan ? (
              <CheckoutButton
                amount={240000}
                currency="INR"
                planName="pro"
                className="mt-8 w-full py-2"
              >
                Upgrade to Pro
              </CheckoutButton>
            ) : subscriptionPlan === 'pro' ? (
              <div className="mt-8 text-center py-2 text-xs font-semibold text-qc-accent font-mono">
                Your Active Subscription
              </div>
            ) : null}
          </div>

          {/* Enterprise Tier */}
          <div className={`p-5 border rounded flex flex-col justify-between ${
            subscriptionPlan === 'enterprise' ? 'border-qc-accent bg-qc-accent/[0.02]' : 'border-qc-border bg-qc-surface/30'
          }`}>
            <div className="space-y-4">
              <div>
                <h4 className="font-syne font-bold text-sm text-qc-text flex items-center justify-between">
                  Enterprise Compliance
                  {subscriptionPlan === 'enterprise' && (
                    <span className="px-1.5 py-0.5 rounded bg-qc-accent text-qc-bg text-[8px] font-bold uppercase tracking-wider">Active</span>
                  )}
                </h4>
                <p className="font-syne font-extrabold text-2xl text-qc-text mt-1">Contact Sales</p>
              </div>
              <ul className="space-y-2 text-[11px] text-qc-muted font-mono leading-relaxed">
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Sovereign PQC compliance suite</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>CycloneDX 1.6 automated CBOM generation</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Internal network & port scanning</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>LQM remediation & vulnerability mapping</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>SSO + multi-user organization console</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-qc-accent flex-shrink-0" />
                  <span>Dedicated SLA & consultative procurement</span>
                </li>
              </ul>
            </div>
            {subscriptionPlan === 'enterprise' ? (
              <div className="mt-8 text-center py-2 text-xs font-semibold text-qc-accent font-mono">
                Your Enterprise Workspace
              </div>
            ) : (
              <a
                href="mailto:sales@quantcai.in?subject=QuantCAI%20Enterprise%20Compliance%20Inquiry"
                className="mt-8 w-full py-2 text-center text-xs font-semibold rounded bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 hover:brightness-110 shadow-lg transition-all"
              >
                Contact Sales
              </a>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
