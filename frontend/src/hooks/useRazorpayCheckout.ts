import { useState } from 'react';
import { axiosClient } from '@/lib/axiosClient';
import { toast } from 'sonner';

export function useRazorpayCheckout() {
  const [loading, setLoading] = useState(false);

  const loadRazorpayScript = (): Promise<boolean> => {
    return new Promise((resolve) => {
      if ((window as any).Razorpay) {
        resolve(true);
        return;
      }

      const existingScript = document.querySelector(
        'script[src="https://checkout.razorpay.com/v1/checkout.js"]'
      );
      if (existingScript) {
        existingScript.addEventListener('load', () => resolve(true));
        existingScript.addEventListener('error', () => resolve(false));
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const startCheckout = async (planName: string, amount: number, currency: string = 'INR') => {
    setLoading(true);
    try {
      // 1. Load the Razorpay SDK
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded || !(window as any).Razorpay) {
        toast.error('Failed to load payment gateway. Please check your internet connection and try again.');
        setLoading(false);
        return;
      }

      const razorpayKey = import.meta.env.VITE_RAZORPAY_KEY_ID;
      if (!razorpayKey) {
        toast.error('Payment gateway is not configured. Please contact support.');
        setLoading(false);
        return;
      }

      // 2. Create order on the backend (real Razorpay order, no mocks)
      const orderResponse = await axiosClient.post('/api/create-order', {
        amount,
        currency,
      });

      const orderData = orderResponse.data;
      if (!orderData || !orderData.order_id) {
        throw new Error('Failed to create payment order. Please try again.');
      }

      // 3. Open Razorpay Checkout Modal
      return new Promise((resolve, reject) => {
        const options = {
          key: orderData.razorpay_key || razorpayKey,
          amount: orderData.amount,
          currency: orderData.currency || 'INR',
          name: 'QuantCAI',
          description: `Upgrade to ${planName.toUpperCase()} Plan`,
          order_id: orderData.order_id,
          prefill: {
            name: '',
            email: '',
            contact: '',
          },
          theme: {
            color: '#00d4aa',
          },
          handler: async function (response: any) {
            // Payment succeeded — verify on backend
            setLoading(true);
            try {
              const verifyResponse = await axiosClient.post('/api/verify-payment', {
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_signature: response.razorpay_signature,
              });

              if (verifyResponse.data && verifyResponse.data.status === 'success') {
                localStorage.setItem('subscription_plan', planName.toLowerCase());
                // Notify the app that subscription changed
                window.dispatchEvent(new CustomEvent('subscription-updated', { detail: { plan: planName } }));
                toast.success('Payment successful! Your plan has been upgraded.');
                resolve(verifyResponse.data);
              } else {
                throw new Error('Payment verification failed. Please contact support.');
              }
            } catch (verifyErr: any) {
              console.error('Payment verification error:', verifyErr);
              const errMsg = verifyErr.response?.data?.detail || 'Payment verification failed. Please contact support.';
              toast.error(errMsg);
              reject(verifyErr);
            } finally {
              setLoading(false);
            }
          },
          modal: {
            ondismiss: function () {
              setLoading(false);
              toast.info('Payment cancelled.');
              reject(new Error('Payment cancelled'));
            },
          },
        };

        const rzp = new (window as any).Razorpay(options);
        rzp.on('payment.failed', function (resp: any) {
          console.error('Payment failed:', resp.error);
          toast.error(`Payment failed: ${resp.error.description}`);
          reject(resp.error);
          setLoading(false);
        });

        rzp.open();
      });
    } catch (err: any) {
      console.error('Checkout error:', err);
      const errMsg = err.response?.data?.detail || err.message || 'Something went wrong during checkout.';
      toast.error(errMsg);
      setLoading(false);
      throw err;
    }
  };

  return { startCheckout, loading };
}
