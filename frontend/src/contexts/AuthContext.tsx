import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

// User types
export type UserRole = "admin" | "user";

export interface User {
  id: string;
  username: string;
  role: UserRole;
  name: string;
}

export interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
  authFetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasRole: (role: UserRole) => boolean;
  hasPermission: (permission: string) => boolean;
}

// Permission definitions
export const PERMISSIONS = {
  // Process permissions
  PROCESS_TEXT: "process:text",
  PROCESS_HTML: "process:html",

  // View permissions
  VIEW_HISTORY: "view:history",
  VIEW_STATISTICS: "view:statistics",
  VIEW_TRAINING_RESULTS: "view:training_results",

  // Admin permissions
  ACCESS_SETTINGS: "access:settings",
  MANAGE_USERS: "manage:users",
  VIEW_SYSTEM_INFO: "view:system_info",
} as const;

// Role permissions mapping
const ROLE_PERMISSIONS = {
  admin: [
    PERMISSIONS.PROCESS_TEXT,
    PERMISSIONS.PROCESS_HTML,
    PERMISSIONS.VIEW_HISTORY,
    PERMISSIONS.VIEW_STATISTICS,
    PERMISSIONS.VIEW_TRAINING_RESULTS,
    PERMISSIONS.ACCESS_SETTINGS,
    PERMISSIONS.MANAGE_USERS,
    PERMISSIONS.VIEW_SYSTEM_INFO,
  ],
  user: [
    PERMISSIONS.PROCESS_TEXT,
    PERMISSIONS.PROCESS_HTML,
    PERMISSIONS.VIEW_HISTORY,
    PERMISSIONS.ACCESS_SETTINGS,
  ],
} as const;

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';

  const verifySession = (onFinally?: () => void) => {
    fetch(`${API_BASE}/auth/verify`, {
      method: 'GET',
      credentials: 'include',
    })
      .then(res => res.json())
      .then(data => {
        if (data.success && data.user) {
          setUser(data.user);
          setIsAuthenticated(true);
        } else {
          setUser(null);
          setIsAuthenticated(false);
        }
      })
      .catch(() => {/* server unreachable — keep current state */})
      .finally(() => onFinally?.());
  };

  // Verify session on mount
  useEffect(() => {
    verifySession(() => setIsLoading(false));
  }, []);

  // Poll every 5 minutes to catch expired sessions
  useEffect(() => {
    const interval = setInterval(() => verifySession(), 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Login function
  const login = async (username: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.success && data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        return data.user;
      } else {
        throw new Error(data.message || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  // Logout function
  const logout = () => {
    // Invalidate session cookie on server (fire-and-forget)
    fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    }).catch(() => {/* ignore errors on logout */ });

    setUser(null);
    setIsAuthenticated(false);
  };

  // Fetch wrapper that logs out on 401
  const authFetch = async (input: RequestInfo, init?: RequestInit): Promise<Response> => {
    const res = await fetch(input, { credentials: 'include', ...init });
    if (res.status === 401) {
      setUser(null);
      setIsAuthenticated(false);
    }
    return res;
  };

  // Check if user has specific role
  const hasRole = (role: UserRole): boolean => {
    return user?.role === role;
  };

  // Check if user has specific permission
  const hasPermission = (permission: string): boolean => {
    if (!user) {
      return permission === PERMISSIONS.PROCESS_TEXT || permission === PERMISSIONS.PROCESS_HTML || permission === PERMISSIONS.VIEW_HISTORY;
    }
    const userPermissions = ROLE_PERMISSIONS[user.role] || [];
    return userPermissions.includes(permission as any);
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    authFetch,
    isAuthenticated,
    isLoading,
    hasRole,
    hasPermission,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}


// Permission-based component wrapper
export function PermissionGate({
  children,
  permission,
  role,
  fallback = null,
}: {
  children: ReactNode;
  permission?: string;
  role?: UserRole;
  fallback?: ReactNode;
}) {
  const { hasRole, hasPermission } = useAuth();

  if (role && !hasRole(role)) {
    return <>{fallback}</>;
  }

  if (permission && !hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}