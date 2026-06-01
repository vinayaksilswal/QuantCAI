// QuantCAI Login / Signup View
import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Mail, Lock, User, ShieldAlert, ArrowRight } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const [mode, setMode] = useState<'signin' | 'signup'>(location.pathname === '/signup' ? 'signup' : 'signin');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { role, user, login, register } = useAuth();

  useEffect(() => {
    if (location.pathname === '/signup') {
      setMode('signup');
    } else if (location.pathname === '/login') {
      setMode('signin');
    }
  }, [location.pathname]);

  useEffect(() => {
    if (!user) return;
    const from = (location.state as any)?.from;
    const fromPath = from?.pathname || '/';
    // Redirect /dashboard to /profile since they are merged
    const targetPath = fromPath === '/dashboard' ? '/profile' : fromPath;
    navigate(targetPath + (from?.search || ''), { replace: true });
  }, [user, navigate, location.state]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (mode === 'signin') {
        await login(email, password);
      } else {
        if (!name.trim()) {
          setError('Workspace/User name is required for registration.');
          setLoading(false);
          return;
        }
        await register(email, password, name);
      }
    } catch (err: any) {
      console.error('Authentication error:', err);
      const errorMessage = err?.message || (typeof err === 'string' ? err : 'Authentication failed. Please try again.');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const signInWithGoogle = async () => {
    setLoading(true);
    setError(null);
    setError('Google OAuth is not yet implemented in the backend.');
    setLoading(false);
  };

  return (
    <div className="min-h-screen relative flex flex-col justify-center items-center bg-[#0a0f1d]">
      
      {/* Decorative animated/glowing background blobs */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-20" 
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px'
        }} 
      />
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-[440px] px-6 py-12 animate-fade-in">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8 text-center">
          <a href="/" className="flex items-center gap-3 group mb-2">
            <div className="w-10 h-10 rounded-xl border border-blue-500/30 flex items-center justify-center text-blue-400 font-syne text-lg font-bold bg-blue-900/10 group-hover:bg-blue-500/20 group-hover:border-blue-500/50 transition-all duration-300 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
              Q
            </div>
            <span className="font-syne font-bold text-white text-2xl tracking-tight drop-shadow-[0_0_10px_rgba(255,255,255,0.15)]">QuantCAI</span>
          </a>
          <p className="text-xs text-slate-400 font-inter">Quantum Simulation & Post-Quantum Audit Engine</p>
        </div>

        {/* Card */}
        <div className="border border-slate-800/80 rounded-2xl bg-slate-900/40 backdrop-blur-2xl p-8 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
          <div className="mb-8">
            <h1 className="font-syne font-bold text-2xl text-white tracking-tight">
              {mode === 'signin' ? 'Welcome Back' : 'Get Started'}
            </h1>
            <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
              {mode === 'signin' ? 'Authenticate your credentials to access the quantum console.' : 'Provision your workspace environment for advanced quantum processing.'}
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-xs text-red-300 font-mono flex items-start gap-2.5 animate-shake">
              <ShieldAlert className="h-4.5 w-4.5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-red-400 uppercase mr-1">Error:</span>
                {error}
              </div>
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-5">
            {mode === 'signup' && (
              <div className="space-y-2">
                <label className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400">Workspace / User Name</label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="e.g. Alice's Lab"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-800 bg-slate-950/50 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all font-mono"
                    required
                    disabled={loading}
                  />
                  <User className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                </div>
              </div>
            )}
            
            <div className="space-y-2">
              <label className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400">Email Address</label>
              <div className="relative">
                <input 
                  type="email" 
                  placeholder="developer@quantcai.in" 
                  value={email} 
                  onChange={e => setEmail(e.target.value)} 
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-800 bg-slate-950/50 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all font-mono" 
                  required 
                  disabled={loading}
                />
                <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400">Security Key (Password)</label>
              <div className="relative">
                <input 
                  type="password" 
                  placeholder="••••••••" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)} 
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-800 bg-slate-950/50 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all font-mono" 
                  required 
                  disabled={loading}
                />
                <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
              </div>
            </div>

            <button 
              disabled={loading} 
              type="submit" 
              className="w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-xs hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-1.5 shadow-lg shadow-blue-500/10"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-t-transparent border-white rounded-full animate-spin mr-1" />
                  {mode === 'signin' ? 'Authenticating...' : 'Provisioning...'}
                </>
              ) : (
                <>
                  {mode === 'signin' ? 'Execute Login' : 'Provision Workspace'}
                  <ArrowRight className="h-4.5 w-4.5" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-8 flex items-center justify-center gap-4">
            <div className="h-px bg-slate-800/80 flex-1" />
            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">SSO / Federation</span>
            <div className="h-px bg-slate-800/80 flex-1" />
          </div>

          <button 
            disabled={loading} 
            onClick={signInWithGoogle} 
            className="w-full py-3 rounded-xl border border-slate-800 bg-slate-950/30 text-slate-300 font-bold text-xs hover:bg-slate-900/60 hover:text-white transition-all flex items-center justify-center gap-2.5 active:scale-[0.99]"
          >
            <svg className="w-4 h-4 text-slate-400" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          {/* Toggle link */}
          <div className="mt-8 text-center text-xs text-slate-400">
            {mode === 'signin' ? (
              <>
                New to QuantCAI?{' '}
                <button onClick={() => setMode('signup')} className="text-blue-400 font-semibold hover:text-blue-300 hover:underline transition-all">Create an account</button>
              </>
            ) : (
              <>
                Already registered?{' '}
                <button onClick={() => setMode('signin')} className="text-blue-400 font-semibold hover:text-blue-300 hover:underline transition-all">Sign in here</button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
