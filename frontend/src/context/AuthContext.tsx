import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react';
import { api, User as ApiUser } from '@/lib/api';

type Role = 'root' | 'developer' | 'user' | null;

// Convert backend User to frontend User type
interface FrontendUser {
  id: string;
  email: string;
  name?: string;
}

type AuthContextType = {
  user: FrontendUser | null;
  session: ApiUser | null;
  role: Role;
  loading: boolean;
  signOut: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({ 
  user: null, 
  session: null, 
  role: null, 
  loading: true, 
  signOut: async () => {},
  login: async () => {},
  register: async () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [session, setSession] = useState<ApiUser | null>(null);
  const [user, setUser] = useState<FrontendUser | null>(null);
  const [role, setRole] = useState<Role>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      // Check localStorage for existing session
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
      
      // Try to get current user from API
      try {
        const currentUser = await api.getMe();
        if (currentUser) {
          setSession(currentUser);
          setUser({
            id: currentUser.id?.toString() ?? '',
            email: currentUser.email,
            name: currentUser.name,
          });
          setRole((currentUser.role as Role) ?? 'user');
        }
      } catch (error) {
        // API might not be fully implemented yet
        console.log('getMe endpoint not available yet');
      }
      
      setLoading(false);
    };
    init();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const userData = await api.login(email, password);
      setSession(userData);
      setUser({
        id: userData.id?.toString() ?? '',
        email: userData.email,
        name: userData.name,
      });
      setRole((userData.role as Role) ?? 'user');
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      const userData = await api.register(email, password, name);
      setSession(userData);
      setUser({
        id: userData.id?.toString() ?? '',
        email: userData.email,
        name: userData.name,
      });
      setRole((userData.role as Role) ?? 'user');
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
    }
  };

  const value = useMemo(
    () => ({ user, session, role, loading, signOut, login, register }),
    [user, session, role, loading]
  );
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);

