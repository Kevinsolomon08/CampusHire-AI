// src/pages/StudentInterviewsPage.jsx
// Student's upcoming and past interviews schedule.

import React, { useEffect, useState } from 'react'
import { getStudentInterviews } from '../api/studentApi'

export default function StudentInterviewsPage() {
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    fetchInterviews()
  }, [page])

  const fetchInterviews = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getStudentInterviews({ page, page_size: 10 })
      if (res.success && res.data) {
        setInterviews(res.data.items || [])
        setTotalPages(res.data.total_pages || 1)
        setTotalCount(res.data.total || 0)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load interviews.')
    } finally {
      setLoading(false)
    }
  }

  const getRoundBadge = (round) => {
    const config = {
      TECHNICAL: { bg: 'bg-blue-100 dark:bg-blue-950/80', text: 'text-blue-800 dark:text-blue-300', icon: '💻' },
      HR: { bg: 'bg-purple-100 dark:bg-purple-950/80', text: 'text-purple-800 dark:text-purple-300', icon: '👤' },
      MANAGERIAL: { bg: 'bg-indigo-100 dark:bg-indigo-950/80', text: 'text-indigo-800 dark:text-indigo-300', icon: '👨‍💼' },
      ASSESSMENT: { bg: 'bg-amber-100 dark:bg-amber-950/80', text: 'text-amber-800 dark:text-amber-300', icon: '📝' },
      OTHER: { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-800 dark:text-gray-300', icon: '•' },
    }
    const c = config[round] || config.OTHER
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
        <span>{c.icon}</span>
        {round}
      </span>
    )
  }

  const getResultBadge = (result) => {
    const config = {
      PENDING: { bg: 'bg-amber-100 dark:bg-amber-950/80', text: 'text-amber-800 dark:text-amber-300', icon: '⏳' },
      PASSED: { bg: 'bg-emerald-100 dark:bg-emerald-950/80', text: 'text-emerald-800 dark:text-emerald-300', icon: '✓' },
      FAILED: { bg: 'bg-rose-100 dark:bg-rose-950/80', text: 'text-rose-800 dark:text-rose-300', icon: '✕' },
      NO_SHOW: { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-800 dark:text-gray-300', icon: '🚫' },
    }
    const c = config[result] || config.PENDING
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
        <span>{c.icon}</span>
        {result}
      </span>
    )
  }

  const formatDateTime = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
    })
  }

  const isUpcoming = (scheduledAt) => {
    return new Date(scheduledAt) > new Date()
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-4 max-w-4xl">
        {[1, 2, 3].map((n) => (
          <div key={n} className="h-24 bg-gray-200 dark:bg-gray-800 rounded-xl" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 pb-5">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          My Interviews
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Upcoming and past interview schedules.
        </p>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          ⚠️ {errorMessage}
        </div>
      )}

      {/* Interviews List */}
      {interviews.length === 0 ? (
        <div className="text-center py-16 px-4 rounded-2xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="text-4xl mb-3">📅</div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            No interviews scheduled yet.
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            Once you are shortlisted and a recruiter schedules an interview, it will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {interviews.map((interview) => {
            const upcoming = isUpcoming(interview.scheduled_at)
            return (
              <div
                key={interview.id}
                className={`p-5 rounded-xl border ${
                  upcoming
                    ? 'border-indigo-200 dark:border-indigo-800 bg-indigo-50/50 dark:bg-indigo-950/20'
                    : 'border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-bold text-gray-900 dark:text-white">
                        {interview.job_title}
                      </h3>
                      {upcoming && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-600 text-white">
                          Upcoming
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {interview.company_name}
                    </p>
                  </div>
                  <div className="text-right">
                    {getRoundBadge(interview.round)}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 p-3 rounded-lg bg-white/50 dark:bg-gray-800/40 text-xs">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400 font-medium">Date & Time</span>
                    <p className="text-sm font-bold text-gray-900 dark:text-white mt-1">
                      {formatDateTime(interview.scheduled_at)}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400 font-medium">Mode</span>
                    <p className="text-sm font-bold text-gray-900 dark:text-white mt-1">
                      {interview.mode}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400 font-medium">Interviewer</span>
                    <p className="text-sm font-bold text-gray-900 dark:text-white mt-1">
                      {interview.interviewer || 'TBD'}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400 font-medium">Status</span>
                    <div className="mt-1">
                      {getResultBadge(interview.result)}
                    </div>
                  </div>
                </div>

                {interview.location_or_link && (
                  <div className="mb-3 p-2 rounded bg-gray-100 dark:bg-gray-800/60 text-xs">
                    <span className="text-gray-600 dark:text-gray-400 font-medium">Location / Link:</span>
                    {interview.mode === 'ONLINE' ? (
                      <a
                        href={interview.location_or_link}
                        target="_blank"
                        rel="noreferrer"
                        className="block text-indigo-600 dark:text-indigo-400 hover:underline font-mono text-xs mt-1 break-all"
                      >
                        {interview.location_or_link}
                      </a>
                    ) : (
                      <p className="text-gray-900 dark:text-gray-300 font-mono text-xs mt-1">
                        {interview.location_or_link}
                      </p>
                    )}
                  </div>
                )}

                {interview.notes && (
                  <div className="p-2 rounded bg-gray-100 dark:bg-gray-800/60 text-xs">
                    <span className="text-gray-600 dark:text-gray-400 font-medium">Notes:</span>
                    <p className="text-gray-900 dark:text-gray-300 mt-1">{interview.notes}</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-800">
          <span className="text-xs text-gray-500">
            Page {page} of {totalPages} ({totalCount} total interviews)
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 text-xs font-semibold disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 text-xs font-semibold disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
