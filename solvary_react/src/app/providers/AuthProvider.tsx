import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react';
import type { User } from '@/shared/types/api';
import {
  apiLogout,
  fetchCurrentUser,
  googleLogin as apiGoogleLogin,
  login as apiLogin,
  register as apiRegister,
} from '@/shared/lib/api';

interface AuthContext {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (credential: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContext | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, check if we have a stored token and fetch the user
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setIsLoading(false);
      return;
    }

    fetchCurrentUser()
      .then(setUser)
      .catch(() => {
        // Token expired or invalid
        localStorage.removeItem('auth_token');
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await apiLogin(email, password);
      localStorage.setItem('auth_token', response.access_token);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithGoogle = useCallback(async (credential: string) => {
    setIsLoading(true);
    try {
      const response = await apiGoogleLogin(credential);
      localStorage.setItem('auth_token', response.access_token);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      setIsLoading(true);
      try {
        const response = await apiRegister(name, email, password);
        localStorage.setItem('auth_token', response.access_token);
        setUser(response.user);
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('auth_token');
    // Revoke the refresh token server-side (fire and forget)
    apiLogout().catch(() => {});
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isAdmin: user?.role === 'admin',
      isLoading,
      login,
      loginWithGoogle,
      register,
      logout,
    }),
    [user, isLoading, login, loginWithGoogle, register, logout],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
