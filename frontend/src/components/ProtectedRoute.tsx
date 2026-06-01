import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ReactElement } from 'react';

export function ProtectedRoute({ children, roles }: { children: ReactElement; roles?: Array<'root' | 'admin' | 'developer' | 'user' | 'learner' | 'enterprise_user'> }) {
  const { user, role, loading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access
  if (roles && roles.length > 0) {
    if (!role) {
      // User exists but no role - show error message
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
          <div className="text-center text-white">
            <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
            <p className="text-gray-300">Your account does not have the required role.</p>
            <p className="text-sm text-gray-400 mt-2">Required roles: {roles.join(', ')}</p>
            <p className="text-sm text-gray-400">Your role: None</p>
          </div>
        </div>
      );
    }

    // Normalize role to lowercase for comparison
    const normalizedRole = role.toLowerCase() as any;
    const normalizedRoles = roles.map(r => r.toLowerCase() as any);

    if (!normalizedRoles.includes(normalizedRole)) {
      // User doesn't have required role - show error message instead of silent redirect
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
          <div className="text-center text-white">
            <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
            <p className="text-gray-300">You don't have permission to access this page.</p>
            <p className="text-sm text-gray-400 mt-2">Required roles: {roles.join(', ')}</p>
            <p className="text-sm text-gray-400">Your role: {role}</p>
            <button
              onClick={() => window.location.href = '/'}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
            >
              Go to Home
            </button>
          </div>
        </div>
      );
    }
  }

  return children;
}

