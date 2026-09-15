// src/layouts/RecruiterLayout.jsx
// Shell layout for Recruiter portal with Navbar, Sidebar navigation, and content container.

import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'

export default function RecruiterLayout({ children }) {
  const location = useLocation()

  const navItems = [
    { label: '📊 Dashboard', path: '/recruiter/dashboard' },
    { label: '💼 Job Postings', path: '/recruiter/jobs' },
    { label: '➕ Post New Job', path: '/recruiter/jobs/create' },
    { label: '🏢 Company Profile', path: '/recruiter/company' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
      <Navbar portalTitle="Recruiter Portal" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Sidebar */}
          <aside className="md:col-span-1">
            <div className="bg-white dark:bg-gray-900 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-800 space-y-1">
              <div className="px-3 py-2 text-xs font-bold uppercase tracking-wider text-gray-400">
                Recruiter Menu
              </div>
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`block px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 font-semibold'
                        : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800'
                    }`}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="md:col-span-3">
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 sm:p-8 shadow-sm border border-gray-200 dark:border-gray-800">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
