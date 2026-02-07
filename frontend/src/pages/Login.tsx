import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { role, user, login, register } = useAuth();

  useEffect(() => {
    if (!user) return;
    if (role === 'root') navigate('/admin', { replace: true });
    else if (role === 'developer') navigate('/developer', { replace: true });
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
          setError('Name is required for registration');
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
    <div className="min-h-screen relative">
      <Navbar />
      <div className="pt-32 pb-20 px-6 max-w-md mx-auto w-full">
        <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
          <CardContent className="p-6">
            <h1 className="text-3xl font-bold text-white mb-2">{mode === 'signin' ? 'Log In' : 'Create Account'}</h1>
            {error && <div className="mb-4 text-sm text-red-300">{error}</div>}
            <form onSubmit={onSubmit} className="space-y-4">
              {mode === 'signup' && (
                <Input
                  type="text"
                  placeholder="Name"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="bg-slate-800/50 border-slate-600 text-white"
                  required
                />
              )}
              <Input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" required />
              <Input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className="bg-slate-800/50 border-slate-600 text-white" required />
              <Button disabled={loading} type="submit" className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">{loading ? (mode === 'signin' ? 'Signing in…' : 'Creating…') : (mode === 'signin' ? 'Sign In' : 'Sign Up')}</Button>
            </form>
            <div className="my-4 h-px bg-slate-700" />
            <Button disabled={loading} onClick={signInWithGoogle} className="w-full bg-white text-black hover:bg-slate-200">
              Continue with Google
            </Button>
            <div className="mt-4 text-sm text-gray-300">
              {mode === 'signin' ? (
                <>
                  Don't have an account?{' '}
                  <button onClick={() => setMode('signup')} className="text-blue-300 hover:text-blue-200">Sign up</button>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <button onClick={() => setMode('signin')} className="text-blue-300 hover:text-blue-200">Sign in</button>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
      <Footer />
    </div>
  );
};

export default Login;


