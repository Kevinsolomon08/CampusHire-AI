// src/pages/StudentApplicationsPage.jsx
// Student applications list with status badges and navigation to detail pages.

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStudentApplications } from '../api/studentApi'

export default function StudentApplicationsPage() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    fetchApplications()
  }, [])

  const fetchApplications = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getStudentApplications()
      if (res.success && res.data) {
        setApplications(res.data)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load applications.')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const badgeConfig = {
      APPLIED: {
        bg: 'bg-blue-100 dark:bg-blue-950/80',
        text: 'text-blue-800 dark:text-blue-300',
        border: 'border-blue-200 dark:border-blue-800',
        icon: '📝',
      },
      ELIGIBILITY_VERIFIED: {
        bg: 'bg-emerald-100 dark:bg-emerald-950/80',
        text: 'text-emerald-800 dark:text-emerald-300',
        border: 'border-emerald-200 dark:border-emerald-800',
        icon: '✓',
      },
      SHORTLISTED: {
        bg: 'bg-indigo-100 dark:bg-indigo-950/80',
        text: 'text-indigo-800 dark:text-indigo-300',
        border: 'border-indigo-200 dark:border-indigo-800',
        icon: '⭐',
      },
      INTERVIEW_SCHEDULED: {
        bg: 'bg-purple-100 dark:bg-purple-950/80',
        text: 'text-purple-800 dark:text-purple-300',
        border: 'border-purple-200 dark:border-purple-800',
        icon: '📅',
      },
      INTERVIEW: {
        bg: 'bg-amber-100 dark:bg-amber-950/80',
        text: 'text-amber-800 dark:text-amber-300',
        border: 'border-amber-200 dark:border-amber-800',
        icon: '🎤',
      },
      SELECTED: {
        bg: 'bg-emerald-100 dark:bg-emerald-950/80',
        text: 'text-emerald-800 dark:text-emerald-300',
        border: 'border-emerald-200 dark:border-emerald-800',
        icon: '🎉',
      },
      REJECTED: {
        bg: 'bg-rose-100 dark:bg-rose-950/80',
        text: 'text-rose-800 dark:text-rose-300',
        border: 'border-rose-200 dark:border-rose-800',
        icon: '✕',
      },
    }

    const config = badgeConfig[status] || badgeConfig.APPLIED
    return (
      <span
        className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold border ${config.bg} ${config.text} ${config.border}`}
      >
        <span>{config.icon}</span>
        {status.replace(/_/g, ' ')}
      </span>
    )
  }

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-4 max-w-4xl">
        {[1, 2, 3].map((n) => (
          <div key={n} className="h-20 bg-gray-200 dark:bg-gray-800 rounded-xl" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 pb-5">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          My Applications
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Track the status of all your job applications and upcoming interviews.
        </p>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          ⚠️ {errorMessage}
        </div>
      )}

      {/* Applications List */}
      {applications.length === 0 ? (
        <div className="text-center py-16 px-4 rounded-2xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="text-4xl mb-3">📋</div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            No applications yet.
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            Start applying to job postings to see them listed here.
          </p>
          <div className="mt-4">
            <Link
              to="/student/jobs"
              className="inline-block px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700"
            >
              Browse Jobs
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <Link
              key={app.id}
              to={`/student/applications/${app.id}`}
              className="block p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-700 transition"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900 dark:text-white">{app.job.title}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {app.job.company_name} • {app.job.location || 'Remote'} • {app.job.package_lpa ? `${app.job.package_lpa} LPA` : 'Competitive'}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  {getStatusBadge(app.status)}
                  <span className="text-xs text-gray-400">
                    Applied {formatDate(app.applied_at)}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
