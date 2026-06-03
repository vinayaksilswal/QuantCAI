import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRazorpayCheckout } from '@/hooks/useRazorpayCheckout';

export function PaymentAutoTrigger() {
  const { user } = useAuth();
  const { startCheckout } = useRazorpayCheckout();

  useEffect(() => {
    if (user && localStorage.getItem('pending_checkout') === 'pro') {
      // Clear immediately to prevent multiple triggers
      localStorage.removeItem('pending_checkout');

      const triggerPayment = async () => {
        try {
          await startCheckout('pro', 2900, 'USD');
          window.location.reload();
        } catch (err) {
          console.error('Auto payment checkout failed:', err);
        }
      };

      // Small delay to allow the redirected page to render completely
      const timer = setTimeout(triggerPayment, 800);
      return () => clearTimeout(timer);
    }
  }, [user]);

  return null;
}
