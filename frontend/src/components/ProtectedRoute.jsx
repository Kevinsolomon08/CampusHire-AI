// src/components/ProtectedRoute.jsx
// Route guard that checks authentication and role permissions without crashing.

import React from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user, role } = useAuthStore()
  const location = useLocation()

  // 1. Not authenticated -> Redirect to Login
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // 2. Check Role permissions
  if (allowedRoles && allowedRoles.length > 0) {
    const rolesArray = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles]
    const userRole = role || user.role

    if (!rolesArray.includes(userRole)) {
      // Determine the user's correct home route
      let userHomeRoute = '/login'
      if (userRole === 'STUDENT') userHomeRoute = '/student/dashboard'
      else if (userRole === 'RECRUITER') userHomeRoute = '/recruiter/dashboard'
      else if (userRole === 'PLACEMENT_OFFICER') userHomeRoute = '/placement/dashboard'

      return (
        <div className="flex min-h-[80vh] items-center justify-center p-6">
          <div className="max-w-md w-full rounded-2xl bg-white p-8 shadow-xl border border-red-100 text-center dark:bg-gray-800 dark:border-red-900/30">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400">
              <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Access Restricted
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              You are not authorized to perform this action or view this section.
            </p>
            <div className="rounded-lg bg-gray-50 dark:bg-gray-700/50 p-3 mb-6 text-xs text-left text-gray-700 dark:text-gray-300 space-y-1">
              <div>
                <span className="font-semibold text-gray-500 dark:text-gray-400">Your Role:</span>{' '}
                <span className="inline-block font-mono bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200 px-1.5 py-0.5 rounded">
                  {userRole}
                </span>
              </div>
              <div>
                <span className="font-semibold text-gray-500 dark:text-gray-400">Allowed Roles:</span>{' '}
                <span className="font-mono text-gray-800 dark:text-gray-200">
                  {rolesArray.join(', ')}
                </span>
              </div>
            </div>
            <Link
              to={userHomeRoute}
              className="inline-flex items-center justify-center w-full px-4 py-2.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition"
            >
              Go to Your Dashboard
            </Link>
          </div>
        </div>
      )
    }
  }

  return children
}
