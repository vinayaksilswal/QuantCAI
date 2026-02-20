import { createContext } from 'react';
import { User as ApiUser } from '@/lib/api';

export type Role = 'root' | 'developer' | 'user' | null;

export interface FrontendUser {
    id: string;
    email: string;
    name?: string;
}

export type AuthContextType = {
    user: FrontendUser | null;
    session: ApiUser | null;
    role: Role;
    loading: boolean;
    signOut: () => Promise<void>;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name: string) => Promise<void>;
};

export const AuthContext = createContext<AuthContextType>({
    user: null,
    session: null,
    role: null,
    loading: true,
    signOut: async () => { },
    login: async () => { },
    register: async () => { },
});
