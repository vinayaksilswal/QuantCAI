import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';

export function PaymentAutoTrigger() {
  const { user } = useAuth();

  useEffect(() => {
    if (user && localStorage.getItem('pending_checkout') === 'pro') {
      // Clear immediately to prevent multiple triggers
      localStorage.removeItem('pending_checkout');
      
      const wplusCheckoutUrl = import.meta.env.VITE_WARRIORPLUS_CHECKOUT_URL || 'https://warriorplus.com/o2/buy/b0pzyf/jgbrsv/qd1f63';
      window.location.href = wplusCheckoutUrl;
    }
  }, [user]);

  return null;
}
