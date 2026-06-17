import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';

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
  amount,
  currency
}: CheckoutButtonProps) {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleCheckout = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    console.log(`Checkout initiated for ${planName}`, amount, currency);
    
    if (!user) {
      localStorage.setItem('pending_checkout', 'pro');
      navigate('/login');
      return;
    }
    
    // Redirect to the WarriorPlus checkout/purchase page
    const wplusCheckoutUrl = import.meta.env.VITE_WARRIORPLUS_CHECKOUT_URL || 'https://warriorplus.com/o2/buy/b0pzyf/jgbrsv/qd1f63';
    window.location.href = wplusCheckoutUrl;
  };

  return (
    <button
      onClick={handleCheckout}
      className={`px-5 py-2.5 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-1.5 shadow-lg shadow-qc-accent/10 ${className}`}
    >
      {children || `Upgrade now`}
    </button>
  );
}

export default CheckoutButton;
