// src/pages/RecruiterJobsPage.jsx
// Recruiter job listings table with status management (Publish/Close/Edit/Delete).

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getRecruiterJobs,
  publishJob,
  closeJob,
  deleteJob,
} from '../api/recruiterApi'

export default function RecruiterJobsPage() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoadingId, setActionLoadingId] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  // Confirm delete modal state
  const [deleteConfirmJob, setDeleteConfirmJob] = useState(null)

  const fetchJobs = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getRecruiterJobs({
        page,
        page_size: 10,
        status: statusFilter,
        search: searchTerm,
      })
      if (res.success && res.data) {
        setJobs(res.data.items || [])
        setTotalPages(res.data.total_pages || 1)
        setTotalCount(res.data.total || 0)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load jobs.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [page, statusFilter, searchTerm])

  const handlePublish = async (jobId) => {
    setActionLoadingId(jobId)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      const res = await publishJob(jobId)
      if (res.success) {
        setSuccessMessage('Job published successfully! It is now OPEN to eligible students.')
        fetchJobs()
        setTimeout(() => setSuccessMessage(''), 4000)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to publish job.')
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleClose = async (jobId) => {
    setActionLoadingId(jobId)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      const res = await closeJob(jobId)
      if (res.success) {
        setSuccessMessage('Job closed successfully.')
        fetchJobs()
        setTimeout(() => setSuccessMessage(''), 4000)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to close job.')
    } finally {
      setActionLoadingId(null)
    }
  }

  const handleDelete = async () => {
    if (!deleteConfirmJob) return
    const jobId = deleteConfirmJob.id
    setActionLoadingId(jobId)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      const res = await deleteJob(jobId)
      if (res.success) {
        setSuccessMessage('Job posting deleted successfully.')
        setDeleteConfirmJob(null)
        fetchJobs()
        setTimeout(() => setSuccessMessage(''), 4000)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to delete job.')
    } finally {
      setActionLoadingId(null)
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPEN':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            ● OPEN
          </span>
        )
      case 'DRAFT':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            ○ DRAFT
          </span>
        )
      case 'CLOSED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
            ✕ CLOSED
          </span>
        )
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            ✓ COMPLETED
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">
            {status}
          </span>
        )
    }
  }

  const formatDate = (isoString) => {
    if (!isoString) return 'No deadline'
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header & New Job Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Job Postings & Drives
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Manage your campus hiring drives, publish draft openings, and view candidate applications.
          </p>
        </div>

        <Link
          to="/recruiter/jobs/create"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-sm transition self-start sm:self-auto"
        >
          <span>➕</span> Post New Job
        </Link>
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

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Status Filter Tabs */}
        <div className="flex bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
          {['ALL', 'OPEN', 'DRAFT', 'CLOSED'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st)
                setPage(1)
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${
                statusFilter === st
                  ? 'bg-white dark:bg-gray-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Search input */}
        <div className="w-full sm:w-64">
          <input
            type="text"
            placeholder="Search job title or location..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value)
              setPage(1)
            }}
            className="w-full px-3.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Jobs Table */}
      {loading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-16 bg-gray-200 dark:bg-gray-800 rounded-xl" />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16 px-4 rounded-2xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="text-4xl mb-3">📋</div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            No job postings found.
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            {searchTerm || statusFilter !== 'ALL'
              ? 'Try changing or clearing your search / status filter criteria.'
              : 'You have not created any job listings yet. Click below to create your first campus drive.'}
          </p>
          <div className="mt-4">
            <Link
              to="/recruiter/jobs/create"
              className="inline-block px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700"
            >
              + Create First Job
            </Link>
          </div>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800/60 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200 dark:border-gray-800">
              <tr>
                <th className="py-3.5 px-4">Role Title</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Package</th>
                <th className="py-3.5 px-4">Applicants</th>
                <th className="py-3.5 px-4">Deadline</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition">
                  <td className="py-4 px-4 font-semibold text-gray-900 dark:text-white">
                    <div>{job.title}</div>
                    <div className="text-xs font-normal text-gray-500 dark:text-gray-400 mt-0.5">
                      {job.location || 'Pan India'} • Min. {job.min_cgpa || '0.0'} CGPA
                    </div>
                  </td>
                  <td className="py-4 px-4">{getStatusBadge(job.status)}</td>
                  <td className="py-4 px-4 font-semibold text-gray-900 dark:text-white">
                    {job.package_lpa ? `${job.package_lpa} LPA` : 'Competitive'}
                  </td>
                  <td className="py-4 px-4">
                    {job.status === 'DRAFT' ? (
                      <span
                        title="Publish this job to start receiving applicants"
                        aria-label={`${job.total_applicants || 0} applied (publish this job to start receiving applicants)`}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 cursor-not-allowed"
                      >
                        {job.total_applicants || 0} applied
                      </span>
                    ) : (
                      <Link
                        to={`/recruiter/jobs/${job.id}/applicants`}
                        title="View applicants"
                        aria-label={`View ${job.total_applicants || 0} applicant${job.total_applicants === 1 ? '' : 's'} for ${job.title}`}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition underline-offset-2 hover:underline focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        {job.total_applicants || 0} applied
                      </Link>
                    )}
                  </td>
                  <td className="py-4 px-4 text-xs text-gray-500">
                    {formatDate(job.deadline)}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end flex-wrap gap-1.5 sm:gap-2">
                      {job.status === 'DRAFT' ? (
                        <button
                          type="button"
                          disabled
                          title="Publish this job to start receiving applicants"
                          aria-label={`View applicants for ${job.title} (disabled - publish this job to start receiving applicants)`}
                          className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 border border-gray-200 dark:border-gray-800 cursor-not-allowed opacity-60"
                        >
                          View Applicants
                        </button>
                      ) : (
                        <Link
                          to={`/recruiter/jobs/${job.id}/applicants`}
                          title={`View applicants for ${job.title}`}
                          aria-label={`View applicants for ${job.title}`}
                          className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900/80 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 transition shadow-2xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                          View Applicants
                        </Link>
                      )}

                      {job.status === 'DRAFT' && (
                        <button
                          onClick={() => handlePublish(job.id)}
                          disabled={actionLoadingId === job.id}
                          aria-label={`Publish ${job.title}`}
                          className="px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        >
                          {actionLoadingId === job.id ? 'Publishing...' : 'Publish'}
                        </button>
                      )}

                      {job.status === 'OPEN' && (
                        <button
                          onClick={() => handleClose(job.id)}
                          disabled={actionLoadingId === job.id}
                          aria-label={`Close ${job.title}`}
                          className="px-3 py-1 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white transition disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-rose-500"
                        >
                          {actionLoadingId === job.id ? 'Closing...' : 'Close'}
                        </button>
                      )}

                      <Link
                        to={`/recruiter/jobs/${job.id}`}
                        aria-label={`Edit ${job.title}`}
                        className="inline-block px-3 py-1 rounded-lg text-xs font-semibold border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        Edit
                      </Link>

                      <button
                        onClick={() => setDeleteConfirmJob(job)}
                        aria-label={`Delete ${job.title}`}
                        className="px-2 py-1 rounded-lg text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 transition focus:outline-none focus:ring-2 focus:ring-rose-500"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-800">
          <span className="text-xs text-gray-500">
            Page {page} of {totalPages} ({totalCount} total postings)
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

      {/* Delete Confirmation Modal */}
      {deleteConfirmJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-gray-200 dark:border-gray-800">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Delete Job Posting?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Are you sure you want to permanently delete{' '}
              <strong className="text-rose-600">{deleteConfirmJob.title}</strong>? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteConfirmJob(null)}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={actionLoadingId === deleteConfirmJob.id}
                className="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold rounded-lg"
              >
                {actionLoadingId === deleteConfirmJob.id ? 'Deleting...' : 'Delete Job'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
