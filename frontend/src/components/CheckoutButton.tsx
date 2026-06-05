import React from 'react';
import { useRazorpayCheckout } from '@/hooks/useRazorpayCheckout';

interface CheckoutButtonProps {
  amount: number; // in paise/cents
  currency?: string; // defaults to 'INR'
  planName: string;
  onSuccess?: (payload: any) => void;
  onError?: (error: any) => void;
  className?: string;
  children?: React.ReactNode;
}

export function CheckoutButton({
  amount,
  currency = 'INR',
  planName,
  onSuccess,
  onError,
  className = '',
  children
}: CheckoutButtonProps) {
  const { startCheckout, loading } = useRazorpayCheckout();

  const handleCheckout = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    try {
      const payload = await startCheckout(planName, amount, currency);
      if (onSuccess && payload) {
        onSuccess(payload);
      } else if (payload) {
        // Notify the app that subscription changed without a full page reload
        window.dispatchEvent(new CustomEvent('subscription-updated', { detail: { plan: planName } }));
      }
    } catch (err) {
      if (onError) {
        onError(err);
      }
    }
  };

  return (
    <button
      onClick={handleCheckout}
      disabled={loading}
      className={`px-5 py-2.5 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-qc-accent/10 ${className}`}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-qc-bg" />
          Processing...
        </span>
      ) : (
        children || `Upgrade now`
      )}
    </button>
  );
}

export default CheckoutButton;
