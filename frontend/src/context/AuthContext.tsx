import { useEffect, useMemo, useState, ReactNode } from 'react';
import { api, User as ApiUser } from '@/lib/api';
import { AuthContext, Role, FrontendUser } from './AuthContextInstance';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [session, setSession] = useState<ApiUser | null>(null);
  const [user, setUser] = useState<FrontendUser | null>(null);
  const [role, setRole] = useState<Role>(null);
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
            localStorage.setItem('auth_user', JSON.stringify(currentUser));
            setLoading(false);
            return;
          }
        }
      } catch (error) {
        console.log('Refresh token failed or expired');
      }

      // 2. Fallback to localStorage if offline or refresh failed (for UI state)
      const storedUser = localStorage.getItem('auth_user');
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
        } catch (error) {
          console.error('Error parsing stored user:', error);
          localStorage.removeItem('auth_user');
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
        localStorage.setItem('auth_user', JSON.stringify(userData));
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
        localStorage.setItem('auth_user', JSON.stringify(userData));
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
      api.setToken(null);
      localStorage.removeItem('auth_user');
    }
  };

  const value = useMemo(
    () => ({ user, session, role, loading, signOut, login, register }),
    [user, session, role, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// useAuth is now in @/hooks/useAuth.ts

