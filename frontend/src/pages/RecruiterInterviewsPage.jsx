// src/pages/RecruiterInterviewsPage.jsx
// Recruiter's interview list with ability to update interview results.

import React, { useEffect, useState } from 'react'
import { getRecruiterInterviews, updateInterview } from '../api/recruiterApi'

export default function RecruiterInterviewsPage() {
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  // Result update modal state
  const [resultModalOpen, setResultModalOpen] = useState(false)
  const [selectedInterview, setSelectedInterview] = useState(null)
  const [resultForm, setResultForm] = useState({
    result: 'PENDING',
    notes: '',
  })

  useEffect(() => {
    fetchInterviews()
  }, [page])

  const fetchInterviews = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getRecruiterInterviews({ page, page_size: 15 })
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

  const openResultModal = (interview) => {
    setSelectedInterview(interview)
    setResultForm({
      result: interview.result || 'PENDING',
      notes: interview.notes || '',
    })
    setResultModalOpen(true)
  }

  const handleResultSubmit = async () => {
    setActionLoading(selectedInterview.id)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      await updateInterview(selectedInterview.id, {
        result: resultForm.result,
        notes: resultForm.notes,
      })
      setSuccessMessage('Interview result updated successfully.')
      setResultModalOpen(false)
      fetchInterviews()
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to update interview.')
    } finally {
      setActionLoading(null)
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
          Scheduled Interviews
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Manage and update interview schedules and results for all candidates.
        </p>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
          ✓ {successMessage}
        </div>
      )}
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
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Interviews scheduled by your company will appear here.
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
                        {interview.student_name}
                      </h3>
                      {upcoming && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-600 text-white">
                          Upcoming
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {interview.job_title} • {interview.company_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getRoundBadge(interview.round)}
                    {getResultBadge(interview.result)}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4 p-3 rounded-lg bg-white/50 dark:bg-gray-800/40 text-xs">
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
                    <span className="text-gray-500 dark:text-gray-400 font-medium">Result</span>
                    <p className="text-sm font-bold text-gray-900 dark:text-white mt-1">
                      {interview.result}
                    </p>
                  </div>
                  <div className="text-right">
                    <button
                      onClick={() => openResultModal(interview)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition"
                    >
                      Update Result
                    </button>
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

      {/* Result Update Modal */}
      {resultModalOpen && selectedInterview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-gray-200 dark:border-gray-800">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Update Interview Result
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              For <strong>{selectedInterview.student_name}</strong> - {selectedInterview.job_title}
            </p>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {formatDateTime(selectedInterview.scheduled_at)}
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Interview Result *
                </label>
                <select
                  value={resultForm.result}
                  onChange={(e) => setResultForm({ ...resultForm, result: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm font-medium"
                >
                  <option value="PENDING">Pending</option>
                  <option value="PASSED">Passed</option>
                  <option value="FAILED">Failed</option>
                  <option value="NO_SHOW">No Show</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Additional Notes
                </label>
                <textarea
                  value={resultForm.notes}
                  onChange={(e) => setResultForm({ ...resultForm, notes: e.target.value })}
                  placeholder="e.g., Strong technical skills, good communication, needs to improve on problem-solving..."
                  rows="4"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                />
              </div>

              {resultForm.result === 'PASSED' && (
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300">
                  ✓ This candidate will be marked as <strong>SELECTED</strong> upon submission.
                </div>
              )}

              {resultForm.result === 'FAILED' && (
                <div className="p-3 bg-rose-50 dark:bg-rose-950/40 rounded-lg border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-300">
                  ✕ This candidate will be marked as <strong>REJECTED</strong> upon submission.
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 pt-2 border-t border-gray-200 dark:border-gray-800">
              <button
                type="button"
                onClick={() => setResultModalOpen(false)}
                disabled={actionLoading === selectedInterview.id}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleResultSubmit}
                disabled={actionLoading === selectedInterview.id}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg disabled:opacity-50"
              >
                {actionLoading === selectedInterview.id ? 'Updating...' : 'Save Result'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
