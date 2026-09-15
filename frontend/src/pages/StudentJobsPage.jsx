// src/pages/StudentJobsPage.jsx
// Student Jobs listing page with dynamic eligibility badges and search/filter.

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStudentJobs } from '../api/studentApi'

export default function StudentJobsPage() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    fetchJobs()
  }, [page, searchTerm])

  const fetchJobs = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getStudentJobs({ page, page_size: 6, search: searchTerm })
      if (res.success && res.data) {
        setJobs(res.data.items || [])
        setTotalPages(res.data.total_pages || 1)
        setTotalCount(res.data.total || 0)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load job listings.')
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    setPage(1)
    fetchJobs()
  }

  const formatDate = (isoString) => {
    if (!isoString) return 'Rolling deadline'
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Campus Placement Drives
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Browse verified job openings and check your real-time eligibility based on your academic profile.
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <input
            type="text"
            placeholder="Search by role or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-3.5 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 w-64"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition"
          >
            Search
          </button>
        </form>
      </div>

      {/* Error state */}
      {errorMessage && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          ⚠️ {errorMessage}
        </div>
      )}

      {/* Loading Skeleton */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div
              key={n}
              className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 animate-pulse space-y-3"
            >
              <div className="flex justify-between items-start">
                <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
                <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded w-20" />
              </div>
              <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/3" />
              <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-3/4" />
            </div>
          ))}
        </div>
      ) : jobs.length === 0 ? (
        /* Empty State */
        <div className="text-center py-16 px-4 rounded-2xl border border-dashed border-gray-300 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="text-4xl mb-3">💼</div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            No jobs available.
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-md mx-auto">
            {searchTerm
              ? `No job openings match "${searchTerm}". Try resetting your search terms.`
              : 'There are currently no open campus hiring drives. Please check back soon!'}
          </p>
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="mt-4 px-4 py-2 text-xs font-semibold bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 transition"
            >
              Clear Search
            </button>
          )}
        </div>
      ) : (
        /* Job Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {jobs.map((job) => {
            const isEligible = job.eligibility?.eligible
            return (
              <div
                key={job.id}
                className="flex flex-col justify-between p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:shadow-md transition duration-200 group"
              >
                <div className="space-y-3">
                  {/* Top row: Company & Eligibility Badge */}
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                        {job.company?.name || 'Company'}
                      </span>
                      <h2 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition">
                        {job.title}
                      </h2>
                    </div>

                    {/* Eligibility Badge */}
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold shrink-0 ${
                        isEligible
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                          : 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
                      }`}
                    >
                      {isEligible ? '✓ ELIGIBLE' : '✕ NOT ELIGIBLE'}
                    </span>
                  </div>

                  {/* Compensation & Location */}
                  <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-gray-600 dark:text-gray-300 pt-1">
                    {job.package_lpa && (
                      <span className="flex items-center gap-1 font-semibold text-gray-900 dark:text-white">
                        <span>💰</span> {job.package_lpa} LPA
                      </span>
                    )}
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <span>📍</span> {job.location}
                      </span>
                    )}
                    <span className="flex items-center gap-1 text-gray-500">
                      <span>⏳</span> Deadline: {formatDate(job.deadline)}
                    </span>
                  </div>

                  {/* Skills preview */}
                  {job.required_skills && Array.isArray(job.required_skills) && job.required_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {job.required_skills.slice(0, 4).map((sk) => (
                        <span
                          key={sk}
                          className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300"
                        >
                          {sk}
                        </span>
                      ))}
                      {job.required_skills.length > 4 && (
                        <span className="text-[11px] text-gray-400 self-center">
                          +{job.required_skills.length - 4} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Ineligibility Reason Preview if not eligible */}
                  {!isEligible && job.eligibility?.reasons?.length > 0 && (
                    <div className="text-xs text-rose-600 dark:text-rose-400 bg-rose-50/70 dark:bg-rose-950/30 p-2.5 rounded-lg border border-rose-100 dark:border-rose-900/40">
                      <strong>Requirement mismatch:</strong> {job.eligibility.reasons[0]}
                    </div>
                  )}
                </div>

                {/* Footer Action Link */}
                <div className="pt-4 mt-4 border-t border-gray-100 dark:border-gray-800/80 flex items-center justify-between">
                  <span className="text-xs text-gray-400">
                    {isEligible ? 'You meet all criteria' : 'Review criteria details'}
                  </span>
                  <Link
                    to={`/student/jobs/${job.id}`}
                    className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition"
                  >
                    View Details & Eligibility →
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-800">
          <span className="text-xs text-gray-500">
            Showing page {page} of {totalPages} ({totalCount} total openings)
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
