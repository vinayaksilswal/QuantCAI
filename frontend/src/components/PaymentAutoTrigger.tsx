import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useRazorpayCheckout } from '@/hooks/useRazorpayCheckout';
import { api } from '@/lib/api';

export function PaymentAutoTrigger() {
  const { user } = useAuth();
  const { startCheckout } = useRazorpayCheckout();
  const navigate = useNavigate();

  useEffect(() => {
    if (user && localStorage.getItem('pending_checkout') === 'pro') {
      // Clear immediately to prevent multiple triggers
      localStorage.removeItem('pending_checkout');

      const triggerPayment = async () => {
        try {
          const result = await startCheckout('pro', 240000, 'INR');
          if (result) {
            // Refresh token to get updated JWT with new subscription plan
            try {
              const tokenData = await api.refresh();
              if (tokenData.access_token) {
                api.setToken(tokenData.access_token);
              }
            } catch {
              // Token refresh failed, but subscription is active server-side.
              // User will get the updated plan on next login.
            }
            navigate('/profile');
          }
        } catch (err) {
          console.error('Auto payment checkout failed:', err);
          // Don't redirect on failure — user can try again from the pricing section
        }
      };

      // Small delay to allow the redirected page to render completely
      const timer = setTimeout(triggerPayment, 1000);
      return () => clearTimeout(timer);
    }
  }, [user]);

  return null;
}
