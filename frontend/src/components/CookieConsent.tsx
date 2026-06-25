import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Shield } from 'lucide-react';
import { Link } from 'react-router-dom';

export const CookieConsent = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if the user has already consented
    const consent = localStorage.getItem('quantcai-cookie-consent');
    if (!consent) {
      setIsVisible(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('quantcai-cookie-consent', 'accepted');
    setIsVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem('quantcai-cookie-consent', 'declined');
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6 sm:pb-4 pointer-events-none">
      <div className="max-w-5xl mx-auto bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 shadow-2xl rounded-2xl p-6 pointer-events-auto flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none -mr-32 -mt-32"></div>
        
        <div className="flex items-start gap-4 flex-1">
          <div className="hidden sm:flex items-center justify-center w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/20 shrink-0">
            <Shield className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg mb-1">Your Privacy Matters</h3>
            <p className="text-slate-300 text-sm leading-relaxed">
              We use cookies and tracking technologies to enhance your experience, analyze site usage, and assist in our marketing efforts in compliance with CCPA and GDPR. 
              Read our <Link to="/privacy" className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2">Privacy Policy</Link> for details on how we process your data.
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto shrink-0 justify-end">
          <Button 
            variant="outline" 
            onClick={handleDecline}
            className="flex-1 md:flex-none border-slate-600 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            Decline All
          </Button>
          <Button 
            onClick={handleAccept}
            className="flex-1 md:flex-none bg-cyan-600 hover:bg-cyan-500 text-white font-medium shadow-[0_0_15px_rgba(34,211,238,0.2)]"
          >
            Accept Cookies
          </Button>
        </div>
      </div>
    </div>
  );
};
