// src/components/Navbar.jsx
// Shared responsive Navbar with user identity, role badge, and logout.

import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Navbar({ portalTitle }) {
  const { user, role, logout } = useAuthStore()
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    // Fetch unread notification count
    const fetchUnreadCount = async () => {
      try {
        // Dynamically import the appropriate API based on role
        if (role === 'STUDENT') {
          const { getUnreadNotificationCount } = await import(
            '../api/studentApi'
          )
          const response = await getUnreadNotificationCount()
          if (response.data) {
            setUnreadCount(response.data.unread_count || 0)
          }
        } else if (role === 'RECRUITER') {
          const { getUnreadNotificationCount } = await import(
            '../api/recruiterApi'
          )
          const response = await getUnreadNotificationCount()
          if (response.data) {
            setUnreadCount(response.data.unread_count || 0)
          }
        }
      } catch (err) {
        console.error('Failed to fetch unread count:', err)
      }
    }

    if (user && (role === 'STUDENT' || role === 'RECRUITER')) {
      fetchUnreadCount()
      // Poll for updates every 30 seconds
      const interval = setInterval(fetchUnreadCount, 30000)
      return () => clearInterval(interval)
    }
  }, [user, role])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const roleColors = {
    STUDENT: 'bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-300',
    RECRUITER: 'bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-900/40 dark:text-indigo-300',
    PLACEMENT_OFFICER: 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/40 dark:text-amber-300',
  }

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Brand & Portal Title */}
          <div className="flex items-center space-x-3">
            <Link to="/" className="flex items-center space-x-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-bold shadow-md shadow-indigo-500/20">
                CH
              </span>
              <span className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">
                Campus<span className="text-indigo-600 dark:text-indigo-400">Hire</span>
              </span>
            </Link>

            {portalTitle && (
              <>
                <span className="text-gray-300 dark:text-gray-700">|</span>
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 hidden sm:inline">
                  {portalTitle}
                </span>
              </>
            )}
          </div>

          {/* User Profile & Actions */}
          <div className="flex items-center space-x-4">
            {/* Notifications Bell */}
            {user && (role === 'STUDENT' || role === 'RECRUITER') && (
              <button
                onClick={() =>
                  navigate(
                    role === 'STUDENT'
                      ? '/student/notifications'
                      : '/recruiter/notifications'
                  )
                }
                className="relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
                title="Notifications"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                {unreadCount > 0 && (
                  <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>
            )}

            {user && (
              <div className="flex items-center space-x-3 text-right">
                <div className="hidden sm:block">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {user.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {user.email}
                  </div>
                </div>

                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                    roleColors[role] || 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {role?.replace('_', ' ')}
                </span>
              </div>
            )}

            <button
              onClick={handleLogout}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-700 rounded-lg text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none transition shadow-sm"
              title="Sign out of CampusHire"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
