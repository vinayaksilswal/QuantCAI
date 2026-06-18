import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { fetchApi } from '@/lib/api';

export function PaymentAutoTrigger() {
  const { user } = useAuth();

  useEffect(() => {
    const pendingPlan = localStorage.getItem('pending_checkout');
    if (user && pendingPlan) {
      // Clear immediately to prevent multiple triggers
      localStorage.removeItem('pending_checkout');

      // Create PayPal subscription and redirect
      fetchApi<{ url: string }>('/api/billing/subscribe', {
        method: 'POST',
        body: JSON.stringify({ plan: pendingPlan }),
      })
        .then((response) => {
          if (response.url) {
            window.location.href = response.url;
          }
        })
        .catch((err) => {
          console.error('Auto-checkout failed:', err);
        });
    }
  }, [user]);

  return null;
}
