import React, { useState, useEffect } from 'react';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';

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
  const [loading, setLoading] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  // Safely load the Razorpay script dynamically
  useEffect(() => {
    const loadScript = async () => {
      // If already loaded, do nothing
      if ((window as any).Razorpay) {
        setScriptLoaded(true);
        return;
      }

      // Check if script is already injected in DOM
      const existingScript = document.querySelector(
        'script[src="https://checkout.razorpay.com/v1/checkout.js"]'
      );
      if (existingScript) {
        existingScript.addEventListener('load', () => setScriptLoaded(true));
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      script.onload = () => {
        setScriptLoaded(true);
      };
      script.onerror = () => {
        console.error('Failed to load Razorpay SDK');
        toast.error('Failed to load Razorpay SDK. Please check your internet connection.');
      };
      document.body.appendChild(script);
    };

    loadScript();
  }, []);

  const handleCheckout = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();

    if (!scriptLoaded || !(window as any).Razorpay) {
      toast.error('Payment gateway is still loading. Please try again in a moment.');
      return;
    }

    setLoading(true);

    try {
      // 1. Create order on FastAPI backend
      // Specify amount in paise/cents as requested
      const orderResponse = await axiosClient.post('/api/create-order', {
        amount: amount,
        currency: currency,
      });

      const orderData = orderResponse.data;
      if (!orderData || !orderData.order_id) {
        throw new Error('Failed to create order on the backend.');
      }

      const razorpayKey = import.meta.env.VITE_RAZORPAY_KEY_ID;
      if (!razorpayKey) {
        throw new Error('Razorpay public key (VITE_RAZORPAY_KEY_ID) is not configured.');
      }

      // 2. Open Razorpay Checkout Modal
      const options = {
        key: razorpayKey,
        amount: orderData.amount, // amount in paise/cents (returned from backend order)
        currency: orderData.currency || 'INR',
        name: 'QuantCAI',
        description: `Upgrade to ${planName.toUpperCase()} Plan`,
        order_id: orderData.order_id,
        // Optional pre-fill info - can be customized or retrieved from auth context if needed
        prefill: {
          name: '',
          email: '',
          contact: '',
        },
        theme: {
          color: '#00d4aa', // QuantCAI teal accent color
        },
        handler: async function (response: {
          razorpay_payment_id: string;
          razorpay_order_id: string;
          razorpay_signature: string;
        }) {
          // 3. On successful payment, send payload to backend verify endpoint
          setLoading(true);
          try {
            const verifyResponse = await axiosClient.post('/api/verify-payment', {
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature,
            });

            if (verifyResponse.data && verifyResponse.data.status === 'success') {
              toast.success('Subscription upgraded successfully!');
              
              // Trigger auth state refresh or page reload
              if (onSuccess) {
                onSuccess(verifyResponse.data);
              } else {
                window.location.reload();
              }
            } else {
              throw new Error('Payment verification failed.');
            }
          } catch (verifyErr: any) {
            console.error('Payment verification error:', verifyErr);
            const errMsg = verifyErr.response?.data?.detail || 'Verification failed. Please contact support.';
            toast.error(errMsg);
            if (onError) onError(verifyErr);
          } finally {
            setLoading(false);
          }
        },
        modal: {
          ondismiss: function () {
            setLoading(false);
            toast.info('Payment cancelled.');
          },
        },
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.on('payment.failed', function (resp: any) {
        console.error('Payment failed:', resp.error);
        toast.error(`Payment failed: ${resp.error.description}`);
        if (onError) onError(resp.error);
        setLoading(false);
      });

      rzp.open();
    } catch (err: any) {
      console.error('Checkout error:', err);
      const errMsg = err.response?.data?.detail || err.message || 'Something went wrong during checkout.';
      toast.error(errMsg);
      if (onError) onError(err);
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleCheckout}
      disabled={loading || !scriptLoaded}
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
