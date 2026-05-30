// QuantCAI Login / Signup View
import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

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
    if (role === 'root') navigate('/admin', { replace: true });
    else if (role === 'developer' || role === 'user') navigate('/dashboard', { replace: true });
    else navigate('/', { replace: true });
  }, [user, role, navigate]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (mode === 'signin') {
        await login(email, password);
        // Navigation will happen via useEffect when user state updates
      } else {
        if (!name.trim()) {
          setError('Username is required for registration');
          setLoading(false);
          return;
        }
        await register(email, password, name);
        // Navigation will happen via useEffect when user state updates
      }
    } catch (err: any) {
      console.error('Login error:', err);
      // Ensure we display a string
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
    <div className="min-h-screen relative flex flex-col justify-center items-center bg-qc-bg">
      
      {/* Background styling elements (Grid + Glow) */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-30" 
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px'
        }} 
      />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-qc-accent/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Auth Container */}
      <div className="relative z-10 w-full max-w-[400px] px-6">
        
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <a href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded border border-qc-accent/50 flex items-center justify-center text-qc-accent font-mono text-sm font-bold group-hover:bg-qc-accent/10 transition-colors">
              Q
            </div>
            <span className="font-syne font-bold text-qc-text text-lg tracking-tight">QuantCAI</span>
          </a>
        </div>

        <div className="border border-qc-border rounded-lg bg-qc-surface/60 backdrop-blur-xl p-8 shadow-2xl">
          <div className="mb-6">
            <h1 className="font-syne font-bold text-2xl text-qc-text">
              {mode === 'signin' ? 'Welcome Back' : 'Initialize Account'}
            </h1>
            <p className="text-xs text-qc-muted font-mono mt-1">
              {mode === 'signin' ? 'Authenticate to access the quantum engine.' : 'Register for API access and simulation tools.'}
            </p>
          </div>

          {error && (
            <div className="mb-5 p-3 rounded border border-qc-danger/30 bg-qc-danger/10 text-[11px] text-qc-danger font-mono animate-pulse">
              [ERROR] {error}
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div className="space-y-1.5">
                <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-qc-muted">Workspace Name</label>
                <input
                  type="text"
                  placeholder="e.g. Alice's Org"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg/50 text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50 transition-colors"
                  required
                  disabled={loading}
                />
              </div>
            )}
            
            <div className="space-y-1.5">
              <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-qc-muted">Email Identity</label>
              <input 
                type="email" 
                placeholder="developer@quantcai.in" 
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg/50 text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50 transition-colors" 
                required 
                disabled={loading}
              />
            </div>
            
            <div className="space-y-1.5">
              <label className="text-[10px] font-mono font-bold tracking-wide uppercase text-qc-muted">Security Key</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                className="w-full px-3 py-2 rounded border border-qc-border bg-qc-bg/50 text-qc-text font-mono text-xs focus:outline-none focus:border-qc-accent/50 transition-colors" 
                required 
                disabled={loading}
              />
            </div>

            <button 
              disabled={loading} 
              type="submit" 
              className="w-full mt-2 py-2.5 rounded bg-qc-accent text-qc-bg font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50"
            >
              {loading 
                ? (mode === 'signin' ? 'Authenticating...' : 'Provisioning...') 
                : (mode === 'signin' ? 'Execute Login' : 'Provision Workspace')
              }
            </button>
          </form>

          <div className="my-6 flex items-center justify-center gap-4">
            <div className="h-px bg-qc-border flex-1" />
            <span className="text-[10px] font-mono text-qc-muted uppercase">SSO / Federation</span>
            <div className="h-px bg-qc-border flex-1" />
          </div>

          <button 
            disabled={loading} 
            onClick={signInWithGoogle} 
            className="w-full py-2.5 rounded border border-qc-border text-qc-text font-semibold text-xs hover:bg-qc-border/40 transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <div className="mt-6 text-center text-[11px] font-mono text-qc-muted">
            {mode === 'signin' ? (
              <>
                Unregistered identity?{' '}
                <button onClick={() => setMode('signup')} className="text-qc-accent hover:brightness-110">Sign up</button>
              </>
            ) : (
              <>
                Registered identity?{' '}
                <button onClick={() => setMode('signin')} className="text-qc-accent hover:brightness-110">Sign in</button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;


