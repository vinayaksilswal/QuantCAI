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
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded || !(window as any).Razorpay) {
        toast.error('Failed to load Razorpay SDK. Please check your internet connection.');
        setLoading(false);
        return;
      }

      // 1. Create order on FastAPI backend
      const orderResponse = await axiosClient.post('/api/create-order', {
        amount,
        currency,
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
      return new Promise((resolve, reject) => {
        const options = {
          key: razorpayKey,
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
            setLoading(true);
            try {
              const verifyResponse = await axiosClient.post('/api/verify-payment', {
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_signature: response.razorpay_signature,
              });

              if (verifyResponse.data && verifyResponse.data.status === 'success') {
                toast.success('Subscription upgraded successfully!');
                resolve(verifyResponse.data);
              } else {
                throw new Error('Payment verification failed.');
              }
            } catch (verifyErr: any) {
              console.error('Payment verification error:', verifyErr);
              const errMsg = verifyErr.response?.data?.detail || 'Verification failed. Please contact support.';
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
