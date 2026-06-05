import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ShieldAlert } from 'lucide-react';

const AuthCallback = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { loginWithGoogle } = useAuth() as any;

  useEffect(() => {
    // If the user is already authenticated (either from a previous session or from the first mount's completed callback),
    // redirect them to their target path immediately.
    if (user) {
      const redirectPath = localStorage.getItem('oauth_redirect_path') || '/profile';
      localStorage.removeItem('oauth_redirect_path');
      navigate(redirectPath, { replace: true });
      return;
    }

    const handleCallback = async () => {
      const storedState = localStorage.getItem('oauth_state');
      if (!storedState) {
        // Exit early if the first mount's execution already cleared the stored state.
        return;
      }

      try {
        // Parse fragment parameters
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        
        const idToken = params.get('id_token');
        const state = params.get('state');
        const errorParam = params.get('error');
        
        if (errorParam) {
          throw new Error(`Google login failed: ${errorParam}`);
        }
        
        if (!idToken) {
          throw new Error('No identity token received from Google.');
        }
        
        if (!state || state !== storedState) {
          throw new Error('OAuth state mismatch. Request may have been compromised.');
        }
        
        // Clear OAuth state from storage so no other run/mount can trigger it
        localStorage.setItem('oauth_state', ''); // set empty to prevent other check while removing
        localStorage.removeItem('oauth_state');
        localStorage.removeItem('oauth_nonce');
        
        // Execute Google login. This updates the global 'user' context state upon completion.
        await loginWithGoogle(idToken);
      } catch (err: any) {
        console.error('OAuth callback error:', err);
        setError(err?.message || 'Authentication failed. Please try again.');
      }
    };
    
    handleCallback();
  }, [navigate, loginWithGoogle, user]);

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-[#0a0f1d] text-white">
      <div className="w-full max-w-[440px] px-6 text-center">
        {error ? (
          <div className="border border-red-500/20 bg-red-500/10 rounded-2xl p-8 shadow-lg">
            <div className="flex justify-center mb-4 text-red-400">
              <ShieldAlert className="h-12 w-12" />
            </div>
            <h1 className="font-syne font-bold text-xl mb-2">Authentication Failed</h1>
            <p className="text-sm text-slate-400 font-mono mb-6">{error}</p>
            <button
              onClick={() => navigate('/login')}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-xs transition-all"
            >
              Back to Login
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mb-4" />
            <h2 className="font-syne font-bold text-lg text-white">Completing authentication...</h2>
            <p className="text-xs text-slate-400 mt-1">Please wait while we establish your secure session.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthCallback;
