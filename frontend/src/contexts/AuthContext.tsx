// import React, { createContext, useContext, useState, useEffect } from 'react';
// import type { ReactNode } from 'react';
// // import { apiClient } from '../services/api';

// // User types
// export type UserRole = "admin" | "user";

// export interface User {
//   id: string;
//   username: string;
//   role: UserRole;
//   name: string;
// }

// export interface AuthContextType {
//   user: User | null;
//   login: (username: string, password: string) => Promise<User>;
//   logout: () => void;
//   isAuthenticated: boolean;
//   hasRole: (role: UserRole) => boolean;
//   hasPermission: (permission: string) => boolean;
// }

// // Permission definitions
// export const PERMISSIONS = {
//   // Process permissions
//   PROCESS_TEXT: "process:text",
//   PROCESS_HTML: "process:html",
  
//   // View permissions
//   VIEW_HISTORY: "view:history",
//   VIEW_STATISTICS: "view:statistics",
//   VIEW_TRAINING_RESULTS: "view:training_results",
  
//   // Admin permissions
//   ACCESS_SETTINGS: "access:settings",
//   MANAGE_USERS: "manage:users",
//   VIEW_SYSTEM_INFO: "view:system_info",
// } as const;

// // Role permissions mapping
// const ROLE_PERMISSIONS = {
//   admin: [
//     PERMISSIONS.PROCESS_TEXT,
//     PERMISSIONS.PROCESS_HTML,
//     PERMISSIONS.VIEW_HISTORY,
//     PERMISSIONS.VIEW_STATISTICS,
//     PERMISSIONS.VIEW_TRAINING_RESULTS,
//     PERMISSIONS.ACCESS_SETTINGS,
//     PERMISSIONS.MANAGE_USERS,
//     PERMISSIONS.VIEW_SYSTEM_INFO,
//   ],
//   user: [
//     PERMISSIONS.PROCESS_TEXT,
//     PERMISSIONS.PROCESS_HTML,
//     PERMISSIONS.VIEW_HISTORY,
//   ],
// } as const;

// // Create context
// const AuthContext = createContext<AuthContextType | undefined>(undefined);

// // Auth provider component
// export function AuthProvider({ children }: { children: ReactNode }) {
//   const [user, setUser] = useState<User | null>(null);
//   const [isAuthenticated, setIsAuthenticated] = useState(false);

//   // Load user from localStorage on mount
//   useEffect(() => {
//     const storedUser = localStorage.getItem('auth_user');
//     if (storedUser) {
//       try {
//         const parsedUser = JSON.parse(storedUser);
//         setUser(parsedUser);
//         setIsAuthenticated(true);
//       } catch (error) {
//         console.error('Failed to parse stored user:', error);
//         localStorage.removeItem('auth_user');
//       }
//     }
//   }, []);

//   // Login function
//   const login = async (username: string, password: string) => {
//     try {
//       const response = await apiClient.login(username, password);
      
//       if (response.success && response.data?.user) {
//         setUser(response.data.user);
//         setIsAuthenticated(true);
//         return response.data.user;
//       } else {
//         throw new Error(response.data?.message || 'Login failed');
//       }
//     } catch (error) {
//       throw error;
//     }
//   };

//   // Logout function
//   const logout = () => {
//     apiClient.logout();
//     setUser(null);
//     setIsAuthenticated(false);
//   };

//   // Check if user has specific role
//   const hasRole = (role: UserRole): boolean => {
//     return user?.role === role;
//   };

//   // Check if user has specific permission
//   const hasPermission = (permission: string): boolean => {
//     if (!user) return false;
    
//     const userPermissions = ROLE_PERMISSIONS[user.role] || [];
//     return userPermissions.includes(permission as any);
//   };

//   const value: AuthContextType = {
//     user,
//     login,
//     logout,
//     isAuthenticated,
//     hasRole,
//     hasPermission,
//   };

//   return (
//     <AuthContext.Provider value={value}>
//       {children}
//     </AuthContext.Provider>
//   );
// }

// // Hook to use auth context
// export function useAuth(): AuthContextType {
//   const context = useContext(AuthContext);
//   if (context === undefined) {
//     throw new Error('useAuth must be used within an AuthProvider');
//   }
//   return context;
// }

// // Higher-order component for route protection
// export function withAuth<P extends object>(
//   Component: React.ComponentType<P>,
//   requiredRole?: UserRole,
//   requiredPermission?: string
// ) {
//   return function AuthenticatedComponent(props: P) {
//     const { isAuthenticated, hasRole, hasPermission } = useAuth();

//     if (!isAuthenticated) {
//       return (
//         <div className="min-h-screen bg-gray-100 flex items-center justify-center">
//           <div className="text-center">
//             <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h2>
//             <p className="text-gray-600">Please sign in to access this page.</p>
//           </div>
//         </div>
//       );
//     }

//     if (requiredRole && !hasRole(requiredRole)) {
//       return (
//         <div className="min-h-screen bg-gray-100 flex items-center justify-center">
//           <div className="text-center">
//             <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
//             <p className="text-gray-600">You don't have permission to access this page.</p>
//           </div>
//         </div>
//       );
//     }

//     if (requiredPermission && !hasPermission(requiredPermission)) {
//       return (
//         <div className="min-h-screen bg-gray-100 flex items-center justify-center">
//           <div className="text-center">
//             <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
//             <p className="text-gray-600">You don't have the required permissions.</p>
//           </div>
//         </div>
//       );
//     }

//     return <Component {...props} />;
//   };
// }

// // Permission-based component wrapper
// export function PermissionGate({
//   children,
//   permission,
//   role,
//   fallback = null,
// }: {
//   children: ReactNode;
//   permission?: string;
//   role?: UserRole;
//   fallback?: ReactNode;
// }) {
//   const { hasRole, hasPermission } = useAuth();

//   if (role && !hasRole(role)) {
//     return <>{fallback}</>;
//   }

//   if (permission && !hasPermission(permission)) {
//     return <>{fallback}</>;
//   }

//   return <>{children}</>;
// }
import React, { createContext, useContext, useState, useEffect } from 'react';
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
  isAuthenticated: boolean;
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
  ],
} as const;

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // API base URL
  const API_BASE = 'http://localhost:8002/api';

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('auth_user');
    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Failed to parse stored user:', error);
        localStorage.removeItem('auth_user');
      }
    }
  }, []);

  // Login function
  const login = async (username: string, password: string) => {
    try {
      // Replace apiClient.login with direct fetch
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();
      
      if (data.success && data.user) {
        // Save user to state and localStorage
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('auth_user', JSON.stringify(data.user));
        
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
    // Clear user state and localStorage
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_token');
  };

  // Check if user has specific role
  const hasRole = (role: UserRole): boolean => {
    return user?.role === role;
  };

  // Check if user has specific permission
  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    const userPermissions = ROLE_PERMISSIONS[user.role] || [];
    return userPermissions.includes(permission as any);
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isAuthenticated,
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

// Higher-order component for route protection
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  requiredRole?: UserRole,
  requiredPermission?: string
) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, hasRole, hasPermission } = useAuth();

    if (!isAuthenticated) {
      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h2>
            <p className="text-gray-600">Please sign in to access this page.</p>
          </div>
        </div>
      );
    }

    if (requiredRole && !hasRole(requiredRole)) {
      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">You don't have permission to access this page.</p>
          </div>
        </div>
      );
    }

    if (requiredPermission && !hasPermission(requiredPermission)) {
      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">You don't have the required permissions.</p>
          </div>
        </div>
      );
    }

    return <Component {...props} />;
  };
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