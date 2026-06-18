import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { fetchApi } from '@/lib/api';
import { Loader2 } from 'lucide-react';

interface CheckoutButtonProps {
  planName: string;
  amount?: number;
  currency?: string;
  className?: string;
  children?: React.ReactNode;
}

export function CheckoutButton({
  planName,
  className = '',
  children,
}: CheckoutButtonProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleCheckout = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();

    if (!user) {
      localStorage.setItem('pending_checkout', planName.toLowerCase());
      navigate('/login');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetchApi<{ url: string; subscription_id: string; plan: string }>('/api/billing/subscribe', {
        method: 'POST',
        body: JSON.stringify({ plan: planName.toLowerCase() }),
      });

      if (response.url) {
        window.location.href = response.url;
      }
    } catch (err: any) {
      console.error('Checkout failed:', err);
      window.dispatchEvent(
        new CustomEvent('show-rate-limit', {
          detail: { message: err.message || 'Checkout is temporarily unavailable. Please try again later.' },
        })
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleCheckout}
      disabled={isLoading}
      className={`px-5 py-2.5 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 shadow-lg shadow-qc-accent/10 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          Redirecting to PayPal...
        </>
      ) : (
        children || `Upgrade now`
      )}
    </button>
  );
}

export default CheckoutButton;
