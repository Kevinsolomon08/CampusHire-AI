// src/pages/RecruiterApplicantsPage.jsx
// Recruiter's applicants table for a specific job with filters, sorting, and status actions.

import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getJobDetail,
  getJobApplicants,
  updateApplicationStatus,
  scheduleInterview,
} from '../api/recruiterApi'

export default function RecruiterApplicantsPage() {
  const { id: jobId } = useParams()
  const navigate = useNavigate()

  const [job, setJob] = useState(null)
  const [applicants, setApplicants] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  // Filter & sort state
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [branch, setBranch] = useState('')
  const [minCgpa, setMinCgpa] = useState('')
  const [maxBacklogs, setMaxBacklogs] = useState('')
  const [batch, setBatch] = useState('')
  const [status, setStatus] = useState('')
  const [sortBy, setSortBy] = useState('applied_at')

  // Interview modal state
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false)
  const [selectedApp, setSelectedApp] = useState(null)
  const [interviewForm, setInterviewForm] = useState({
    scheduled_at: '',
    mode: 'ONLINE',
    round: 'TECHNICAL',
    interviewer: '',
    location_or_link: '',
    notes: '',
  })

  useEffect(() => {
    fetchJobDetail()
  }, [jobId])

  useEffect(() => {
    fetchApplicants()
  }, [page, branch, minCgpa, maxBacklogs, batch, status, sortBy])

  const fetchJobDetail = async () => {
    try {
      const res = await getJobDetail(parseInt(jobId))
      if (res.success && res.data) {
        setJob(res.data)
      }
    } catch (err) {
      setErrorMessage('Failed to load job details.')
    }
  }

  const fetchApplicants = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getJobApplicants({
        jobId: parseInt(jobId),
        page,
        page_size: 15,
        branch: branch || undefined,
        min_cgpa: minCgpa ? parseFloat(minCgpa) : undefined,
        max_backlogs: maxBacklogs ? parseInt(maxBacklogs) : undefined,
        batch: batch ? parseInt(batch) : undefined,
        status: status || undefined,
        sort_by: sortBy,
      })
      if (res.success && res.data) {
        setApplicants(res.data.items || [])
        setTotalPages(res.data.total_pages || 1)
        setTotalCount(res.data.total || 0)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load applicants.')
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (appId, newStatus) => {
    setActionLoading(appId)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      await updateApplicationStatus(appId, newStatus)
      setSuccessMessage(`Application status updated to ${newStatus}.`)
      fetchApplicants()
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to update status.')
    } finally {
      setActionLoading(null)
    }
  }

  const openScheduleModal = (app) => {
    setSelectedApp(app)
    setScheduleModalOpen(true)
    setInterviewForm({
      scheduled_at: '',
      mode: 'ONLINE',
      round: 'TECHNICAL',
      interviewer: '',
      location_or_link: '',
      notes: '',
    })
  }

  const handleScheduleSubmit = async () => {
    if (!interviewForm.scheduled_at) {
      setErrorMessage('Please select a date and time.')
      return
    }
    setActionLoading(selectedApp.application_id)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      await scheduleInterview(selectedApp.application_id, interviewForm)
      setSuccessMessage('Interview scheduled successfully.')
      setScheduleModalOpen(false)
      fetchApplicants()
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to schedule interview.')
    } finally {
      setActionLoading(null)
    }
  }

  const getStatusBadge = (status) => {
    const config = {
      APPLIED: { bg: 'bg-blue-100 dark:bg-blue-950/80', text: 'text-blue-800 dark:text-blue-300' },
      ELIGIBILITY_VERIFIED: { bg: 'bg-emerald-100 dark:bg-emerald-950/80', text: 'text-emerald-800 dark:text-emerald-300' },
      SHORTLISTED: { bg: 'bg-indigo-100 dark:bg-indigo-950/80', text: 'text-indigo-800 dark:text-indigo-300' },
      INTERVIEW_SCHEDULED: { bg: 'bg-purple-100 dark:bg-purple-950/80', text: 'text-purple-800 dark:text-purple-300' },
      INTERVIEW: { bg: 'bg-amber-100 dark:bg-amber-950/80', text: 'text-amber-800 dark:text-amber-300' },
      SELECTED: { bg: 'bg-emerald-100 dark:bg-emerald-950/80', text: 'text-emerald-800 dark:text-emerald-300' },
      REJECTED: { bg: 'bg-rose-100 dark:bg-rose-950/80', text: 'text-rose-800 dark:text-rose-300' },
    }
    const c = config[status] || config.APPLIED
    return (
      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold border ${c.bg} ${c.text}`}>
        {status.replace(/_/g, ' ')}
      </span>
    )
  }

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  if (!job && !loading) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Job not found.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Applicants for {job?.title || 'Job'}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {totalCount} total applicants
          </p>
        </div>
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

      {/* Filters & Sorting */}
      <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 space-y-4">
        <div>
          <p className="text-xs uppercase tracking-wider font-bold text-gray-600 dark:text-gray-400 mb-3">
            Filters
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            <input
              type="text"
              placeholder="Branch"
              value={branch}
              onChange={(e) => { setBranch(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
            />
            <input
              type="number"
              placeholder="Min CGPA"
              value={minCgpa}
              onChange={(e) => { setMinCgpa(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
              step="0.1"
              min="0"
              max="10"
            />
            <input
              type="number"
              placeholder="Max Backlogs"
              value={maxBacklogs}
              onChange={(e) => { setMaxBacklogs(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
              min="0"
            />
            <input
              type="number"
              placeholder="Batch"
              value={batch}
              onChange={(e) => { setBatch(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
            />
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs"
            >
              <option value="">All Statuses</option>
              <option value="APPLIED">Applied</option>
              <option value="ELIGIBILITY_VERIFIED">Verified</option>
              <option value="SHORTLISTED">Shortlisted</option>
              <option value="INTERVIEW_SCHEDULED">Scheduled</option>
              <option value="INTERVIEW">Interview</option>
              <option value="SELECTED">Selected</option>
              <option value="REJECTED">Rejected</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
              className="px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs"
            >
              <option value="applied_at">Applied Date</option>
              <option value="cgpa">CGPA (High to Low)</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Applicants Table */}
      {loading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-16 bg-gray-200 dark:bg-gray-800 rounded-xl" />
          ))}
        </div>
      ) : applicants.length === 0 ? (
        <div className="text-center py-12 rounded-2xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900">
          <p className="text-gray-500 text-sm">No applicants match your filters.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800/60 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200 dark:border-gray-800">
              <tr>
                <th className="py-3.5 px-4">Candidate</th>
                <th className="py-3.5 px-4">Branch</th>
                <th className="py-3.5 px-4">CGPA</th>
                <th className="py-3.5 px-4">Backlogs</th>
                <th className="py-3.5 px-4">AI Score</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {applicants.map((app) => (
                <tr key={app.application_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition">
                  <td className="py-4 px-4">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{app.student_name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{app.roll_number}</p>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-xs font-medium text-gray-700 dark:text-gray-300">
                    {app.branch}
                  </td>
                  <td className="py-4 px-4 font-semibold text-gray-900 dark:text-white">
                    {app.cgpa ? app.cgpa.toFixed(2) : '-'}
                  </td>
                  <td className="py-4 px-4 text-center font-semibold text-gray-900 dark:text-white">
                    {app.backlog_count}
                  </td>
                  <td className="py-4 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/60">
                      {app.ai_score ? `${app.ai_score.toFixed(1)}%` : 'Pending AI analysis'}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    {getStatusBadge(app.status)}
                  </td>
                  <td className="py-4 px-4 text-right space-x-1 whitespace-nowrap">
                    {app.status === 'ELIGIBILITY_VERIFIED' && (
                      <>
                        <button
                          onClick={() => handleStatusUpdate(app.application_id, 'SHORTLISTED')}
                          disabled={actionLoading === app.application_id}
                          className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition disabled:opacity-50"
                        >
                          {actionLoading === app.application_id ? 'Updating...' : 'Shortlist'}
                        </button>
                        <button
                          onClick={() => handleStatusUpdate(app.application_id, 'REJECTED')}
                          disabled={actionLoading === app.application_id}
                          className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white transition disabled:opacity-50"
                        >
                          {actionLoading === app.application_id ? '...' : 'Reject'}
                        </button>
                      </>
                    )}

                    {app.status === 'SHORTLISTED' && (
                      <button
                        onClick={() => openScheduleModal(app)}
                        className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white transition"
                      >
                        Schedule
                      </button>
                    )}

                    {(app.status === 'INTERVIEW' || app.status === 'INTERVIEW_SCHEDULED') && (
                      <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                        Interview scheduled
                      </span>
                    )}

                    {app.status === 'SELECTED' && (
                      <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                        ✓ Selected
                      </span>
                    )}

                    {app.status === 'REJECTED' && (
                      <span className="text-xs text-rose-600 dark:text-rose-400 font-semibold">
                        ✕ Rejected
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-800">
          <span className="text-xs text-gray-500">
            Page {page} of {totalPages}
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

      {/* Schedule Interview Modal */}
      {scheduleModalOpen && selectedApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-gray-200 dark:border-gray-800 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Schedule Interview
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              For <strong>{selectedApp.student_name}</strong>
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Date & Time *
                </label>
                <input
                  type="datetime-local"
                  value={interviewForm.scheduled_at}
                  onChange={(e) => setInterviewForm({ ...interviewForm, scheduled_at: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Mode
                </label>
                <select
                  value={interviewForm.mode}
                  onChange={(e) => setInterviewForm({ ...interviewForm, mode: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                >
                  <option value="ONLINE">Online</option>
                  <option value="OFFLINE">Offline</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Round
                </label>
                <select
                  value={interviewForm.round}
                  onChange={(e) => setInterviewForm({ ...interviewForm, round: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                >
                  <option value="TECHNICAL">Technical</option>
                  <option value="HR">HR</option>
                  <option value="MANAGERIAL">Managerial</option>
                  <option value="ASSESSMENT">Assessment</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Interviewer Name
                </label>
                <input
                  type="text"
                  value={interviewForm.interviewer}
                  onChange={(e) => setInterviewForm({ ...interviewForm, interviewer: e.target.value })}
                  placeholder="e.g., John Doe"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Location / Meeting Link
                </label>
                <input
                  type="text"
                  value={interviewForm.location_or_link}
                  onChange={(e) => setInterviewForm({ ...interviewForm, location_or_link: e.target.value })}
                  placeholder="e.g., https://meet.google.com/... or Conference Room 101"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Notes
                </label>
                <textarea
                  value={interviewForm.notes}
                  onChange={(e) => setInterviewForm({ ...interviewForm, notes: e.target.value })}
                  placeholder="Any additional instructions or notes..."
                  rows="3"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2 border-t border-gray-200 dark:border-gray-800">
              <button
                type="button"
                onClick={() => setScheduleModalOpen(false)}
                disabled={actionLoading === selectedApp.application_id}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleScheduleSubmit}
                disabled={actionLoading === selectedApp.application_id}
                className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold rounded-lg disabled:opacity-50"
              >
                {actionLoading === selectedApp.application_id ? 'Scheduling...' : 'Schedule Interview'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
