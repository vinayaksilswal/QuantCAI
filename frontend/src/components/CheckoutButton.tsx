import React from 'react';

interface CheckoutButtonProps {
  planName: string;
  className?: string;
  children?: React.ReactNode;
}

export function CheckoutButton({
  planName,
  className = '',
  children
}: CheckoutButtonProps) {
  const handleCheckout = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    
    // Redirect to the WarriorPlus checkout/purchase page
    const wplusCheckoutUrl = import.meta.env.VITE_WARRIORPLUS_CHECKOUT_URL || 'https://warriorplus.com/as/o/466941';
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
