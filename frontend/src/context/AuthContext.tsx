import { useEffect, useMemo, useState, ReactNode } from 'react';
import { api, User as ApiUser } from '@/lib/api';
import { AuthContext, Role, FrontendUser } from './AuthContextInstance';

// JWT decode helper function
function decodeJwt(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [session, setSession] = useState<ApiUser | null>(null);
  const [user, setUser] = useState<FrontendUser | null>(null);
  const [role, setRole] = useState<Role>(null);
  const [subscriptionPlan, setSubscriptionPlan] = useState<'free' | 'pro' | 'enterprise' | null>('free');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      // 1. Try to initialize from refresh token (auto-login)
      try {
        const tokenData = await api.refresh();
        if (tokenData.access_token) {
          api.setToken(tokenData.access_token);
          const currentUser = await api.getMe();
          if (currentUser) {
            setSession(currentUser);
            setUser({
              id: currentUser.id?.toString() ?? '',
              email: currentUser.email,
              name: currentUser.name,
            });
            setRole((currentUser.role as Role) ?? 'user');
            
            const decoded = decodeJwt(tokenData.access_token);
            const plan = decoded?.subscription_plan || 'free';
            setSubscriptionPlan(plan);
            
            localStorage.setItem('auth_user', JSON.stringify(currentUser));
            localStorage.setItem('subscription_plan', plan);
            setLoading(false);
            return;
          }
        }
      } catch (error) {
        console.log('Refresh token failed or expired. Clearing session.');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('subscription_plan');
      }

      // 2. Fallback to localStorage if offline or refresh failed (for UI state)
      const storedUser = localStorage.getItem('auth_user');
      const storedPlan = localStorage.getItem('subscription_plan') as any;
      if (storedUser) {
        try {
          const userData: ApiUser = JSON.parse(storedUser);
          setSession(userData);
          setUser({
            id: userData.id?.toString() ?? '',
            email: userData.email,
            name: userData.name,
          });
          setRole((userData.role as Role) ?? 'user');
          setSubscriptionPlan(storedPlan || 'free');
        } catch (error) {
          console.error('Error parsing stored user:', error);
          localStorage.removeItem('auth_user');
          localStorage.removeItem('subscription_plan');
        }
      }

      setLoading(false);
    };
    init();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const tokenData = await api.login(email, password);
      if (tokenData.access_token) {
        api.setToken(tokenData.access_token);
        const userData = await api.getMe();
        setSession(userData);
        setUser({
          id: userData.id?.toString() ?? '',
          email: userData.email,
          name: userData.name,
        });
        setRole((userData.role as Role) ?? 'user');
        
        const decoded = decodeJwt(tokenData.access_token);
        const plan = decoded?.subscription_plan || 'free';
        setSubscriptionPlan(plan);
        
        localStorage.setItem('auth_user', JSON.stringify(userData));
        localStorage.setItem('subscription_plan', plan);
      }
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      const tokenData = await api.register(email, password, name);
      if (tokenData.access_token) {
        api.setToken(tokenData.access_token);
        const userData = await api.getMe();
        setSession(userData);
        setUser({
          id: userData.id?.toString() ?? '',
          email: userData.email,
          name: userData.name,
        });
        setRole((userData.role as Role) ?? 'user');
        
        const decoded = decodeJwt(tokenData.access_token);
        const plan = decoded?.subscription_plan || 'free';
        setSubscriptionPlan(plan);
        
        localStorage.setItem('auth_user', JSON.stringify(userData));
        localStorage.setItem('subscription_plan', plan);
      }
    } catch (error) {
      throw error;
    }
  };

  const signOut = async () => {
    try {
      await api.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setSession(null);
      setRole(null);
      setSubscriptionPlan('free');
      api.setToken(null);
      localStorage.removeItem('auth_user');
      localStorage.removeItem('subscription_plan');
    }
  };

  const value = useMemo(
    () => ({ user, session, role, loading, subscriptionPlan, signOut, login, register }),
    [user, session, role, loading, subscriptionPlan]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// useAuth is now in @/hooks/useAuth.ts

