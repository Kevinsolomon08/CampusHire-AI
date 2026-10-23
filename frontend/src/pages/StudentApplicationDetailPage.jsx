// src/pages/StudentApplicationDetailPage.jsx
// Detailed application view with vertical status timeline/stepper.

import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getApplicationDetail } from '../api/studentApi'

export default function StudentApplicationDetailPage() {
  const { id } = useParams()
  const [application, setApplication] = useState(null)
  const [loading, setLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    fetchApplicationDetail()
  }, [id])

  const fetchApplicationDetail = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getApplicationDetail(parseInt(id))
      if (res.success && res.data) {
        setApplication(res.data)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Application not found.')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      APPLIED: 'bg-blue-500',
      ELIGIBILITY_VERIFIED: 'bg-emerald-500',
      SHORTLISTED: 'bg-indigo-500',
      INTERVIEW_SCHEDULED: 'bg-purple-500',
      INTERVIEW: 'bg-amber-500',
      SELECTED: 'bg-green-500',
      REJECTED: 'bg-rose-500',
    }
    return colors[status] || 'bg-gray-500'
  }

  const getStatusIcon = (status) => {
    const icons = {
      APPLIED: '📝',
      ELIGIBILITY_VERIFIED: '✓',
      SHORTLISTED: '⭐',
      INTERVIEW_SCHEDULED: '📅',
      INTERVIEW: '🎤',
      SELECTED: '🎉',
      REJECTED: '✕',
    }
    return icons[status] || '•'
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

  if (loading) {
    return (
      <div className="animate-pulse space-y-6 max-w-3xl">
        <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-24" />
        <div className="h-40 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
        <div className="h-96 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
      </div>
    )
  }

  if (errorMessage || !application) {
    return (
      <div className="text-center py-16 px-4 max-w-xl mx-auto space-y-4">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {errorMessage || 'Application Not Found'}
        </h2>
        <Link
          to="/student/applications"
          className="inline-block px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700"
        >
          ← Back to Applications
        </Link>
      </div>
    )
  }

  const currentStatus = application.status
  const statusHistory = application.status_history || []

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Back Link */}
      <div>
        <Link
          to="/student/applications"
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400 transition"
        >
          ← Back to Applications
        </Link>
      </div>

      {/* Job Info Card */}
      <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
        <div>
          <p className="text-xs uppercase tracking-wider text-indigo-600 dark:text-indigo-400 font-bold">
            {application.job.company_name}
          </p>
          <h1 className="text-2xl font-extrabold text-gray-900 dark:text-white mt-1">
            {application.job.title}
          </h1>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/60 text-xs">
          <div>
            <span className="text-gray-400 font-bold">Package</span>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {application.job.package_lpa ? `${application.job.package_lpa} LPA` : 'Competitive'}
            </div>
          </div>
          <div>
            <span className="text-gray-400 font-bold">Location</span>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {application.job.location || 'Remote'}
            </div>
          </div>
          <div>
            <span className="text-gray-400 font-bold">Applied On</span>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {new Date(application.applied_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </div>
          </div>
          <div>
            <span className="text-gray-400 font-bold">Current Status</span>
            <div className="text-sm font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
              {currentStatus.replace(/_/g, ' ')}
            </div>
          </div>
        </div>
      </div>

      {/* Status Timeline / Stepper */}
      <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-6">
          Application Timeline
        </h2>

        <div className="space-y-6">
          {statusHistory.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">No status history available.</p>
          ) : (
            statusHistory.map((entry, index) => {
              const isLast = index === statusHistory.length - 1
              return (
                <div key={entry.id} className="relative flex gap-4">
                  {/* Timeline line and dot */}
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-lg ${getStatusColor(entry.new_status)} shadow-md`}
                    >
                      {getStatusIcon(entry.new_status)}
                    </div>
                    {!isLast && (
                      <div className="w-1 h-12 bg-gray-200 dark:bg-gray-700 mt-2 mb-2" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="pt-1 pb-4 flex-1">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1">
                      <h3 className="font-bold text-gray-900 dark:text-white">
                        {entry.new_status.replace(/_/g, ' ')}
                      </h3>
                      <span className="text-xs text-gray-400">
                        {formatDateTime(entry.changed_at)}
                      </span>
                    </div>

                    {entry.old_status && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                        From: <span className="font-medium">{entry.old_status.replace(/_/g, ' ')}</span>
                      </p>
                    )}

                    {entry.changed_by_name && (
                      <p className="text-xs text-gray-600 dark:text-gray-300 mb-2">
                        By: <span className="font-medium">{entry.changed_by_name}</span>
                        {entry.changed_by_role && ` (${entry.changed_by_role})`}
                      </p>
                    )}

                    {entry.remarks && (
                      <p className="text-xs bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded px-3 py-2 text-gray-700 dark:text-gray-300">
                        {entry.remarks}
                      </p>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* AI Scoring Placeholders */}
      {/* AI Resume & Match Evaluation */}
      <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>⚡</span> AI Resume & Match Evaluation
          </h2>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            Active
          </span>
        </div>

        {/* AI Disclaimer */}
        <div className="p-3 rounded-xl border border-indigo-100 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/30 text-indigo-900 dark:text-indigo-200 text-xs">
          💡 AI scores are a screening aid to help prioritize review — they don't represent a hiring decision. Final selection is always the recruiter's call.
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50">
            <p className="text-xs uppercase tracking-wider text-indigo-600 dark:text-indigo-400 font-bold">
              Overall Composite Score
            </p>
            <p className="text-2xl font-extrabold text-indigo-900 dark:text-indigo-200 mt-1">
              {application.ai_score !== null && application.ai_score !== undefined
                ? `${application.ai_score.toFixed(1)}%`
                : 'Pending analysis'}
            </p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Weighted match score</p>
          </div>

          <div className="p-4 rounded-xl bg-purple-50/50 dark:bg-purple-950/30 border border-purple-100 dark:border-purple-900/50">
            <p className="text-xs uppercase tracking-wider text-purple-600 dark:text-purple-400 font-bold">
              Applicant Rank
            </p>
            <p className="text-2xl font-extrabold text-purple-900 dark:text-purple-200 mt-1">
              {application.rank ? `#${application.rank}` : '—'}
            </p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Among all applicants</p>
          </div>

          <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/50">
            <p className="text-xs uppercase tracking-wider text-emerald-600 dark:text-emerald-400 font-bold">
              Skill Match
            </p>
            <p className="text-2xl font-extrabold text-emerald-900 dark:text-emerald-200 mt-1">
              {application.skill_score !== null && application.skill_score !== undefined
                ? `${application.skill_score.toFixed(1)}%`
                : '—'}
            </p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Required & preferred skills</p>
          </div>

          <div className="p-4 rounded-xl bg-amber-50/50 dark:bg-amber-950/30 border border-amber-100 dark:border-amber-900/50">
            <p className="text-xs uppercase tracking-wider text-amber-600 dark:text-amber-400 font-bold">
              Semantic Fit
            </p>
            <p className="text-2xl font-extrabold text-amber-900 dark:text-amber-200 mt-1">
              {application.semantic_score !== null && application.semantic_score !== undefined
                ? `${application.semantic_score.toFixed(1)}%`
                : '—'}
            </p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Resume & job description</p>
          </div>
        </div>
      </div>
    </div>
  )
}
