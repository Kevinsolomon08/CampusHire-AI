// src/pages/StudentJobDetailPage.jsx
// Detailed Job View for Students showing full requirements and exact eligibility reasons.

import React, { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { getStudentJobDetail, applyForJob } from '../api/studentApi'

export default function StudentJobDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [applyModalOpen, setApplyModalOpen] = useState(false)
  const [hasApplied, setHasApplied] = useState(false)
  const [applyLoading, setApplyLoading] = useState(false)

  useEffect(() => {
    fetchDetail()
  }, [id])

  const fetchDetail = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getStudentJobDetail(id)
      if (res.success && res.data) {
        setJob(res.data)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Job posting not found.')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (isoString) => {
    if (!isoString) return 'Rolling Applications'
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const handleApplySubmit = async () => {
    setApplyLoading(true)
    setErrorMessage('')
    try {
      await applyForJob(parseInt(id))
      setHasApplied(true)
      setApplyModalOpen(false)
      // Navigate to applications list after successful apply
      setTimeout(() => navigate('/student/applications'), 1500)
    } catch (err) {
      const msg = err.response?.data?.message || 'Failed to submit application.'
      setErrorMessage(msg)
    } finally {
      setApplyLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-6 max-w-4xl">
        <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-24" />
        <div className="h-32 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
        <div className="h-28 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
        <div className="h-48 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
      </div>
    )
  }

  if (errorMessage || !job) {
    return (
      <div className="text-center py-16 px-4 max-w-xl mx-auto space-y-4">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {errorMessage || 'Job Not Found'}
        </h2>
        <p className="text-sm text-gray-500">
          The job posting you are looking for might have expired or been removed.
        </p>
        <Link
          to="/student/jobs"
          className="inline-block px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700"
        >
          ← Back to All Jobs
        </Link>
      </div>
    )
  }

  const isEligible = job.eligibility?.eligible
  const reasons = job.eligibility?.reasons || []

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Top Navigation */}
      <div>
        <Link
          to="/student/jobs"
          className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400 transition"
        >
          ← Back to Campus Drives
        </Link>
      </div>

      {/* Main Job Overview Card */}
      <div className="p-6 sm:p-8 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                {job.company?.name || 'Recruiting Partner'}
              </span>
              {job.company?.website && (
                <a
                  href={job.company.website}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-gray-400 hover:underline"
                >
                  ↗ Visit Website
                </a>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white mt-1">
              {job.title}
            </h1>
          </div>

          {/* Eligibility Badge */}
          <span
            className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold shrink-0 ${
              isEligible
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
            }`}
          >
            {isEligible ? '✓ YOU ARE ELIGIBLE' : '✕ NOT ELIGIBLE'}
          </span>
        </div>

        {/* Key Attributes Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-700/60 text-xs">
          <div>
            <span className="text-gray-400 uppercase font-bold text-[10px]">Package</span>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {job.package_lpa ? `${job.package_lpa} LPA` : 'Competitive'}
            </div>
          </div>
          <div>
            <span className="text-gray-400 uppercase font-bold text-[10px]">Location</span>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {job.location || 'Pan India'}
            </div>
          </div>
          <div>
            <span className="text-gray-400 uppercase font-bold text-[10px]">Deadline</span>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {formatDate(job.deadline)}
            </div>
          </div>
          <div>
            <span className="text-gray-400 uppercase font-bold text-[10px]">Min. CGPA</span>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {job.min_cgpa ? `${job.min_cgpa} / 10.0` : 'None'}
            </div>
          </div>
        </div>

        {/* ELIGIBILITY ASSESSMENT BOX */}
        <div
          className={`p-5 rounded-xl border ${
            isEligible
              ? 'border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/60 dark:bg-emerald-950/30'
              : 'border-rose-200 bg-rose-50/70 dark:border-rose-900/60 dark:bg-rose-950/30'
          }`}
        >
          <div className="flex items-start gap-3">
            <span className="text-xl">{isEligible ? '✅' : '⚠️'}</span>
            <div className="space-y-2 flex-1">
              <h2
                className={`text-sm font-bold ${
                  isEligible
                    ? 'text-emerald-900 dark:text-emerald-200'
                    : 'text-rose-900 dark:text-rose-200'
                }`}
              >
                {isEligible
                  ? 'Eligibility Check Passed — You are eligible for this position!'
                  : 'Eligibility Check Failed — You do not meet the minimum requirements'}
              </h2>

              {isEligible ? (
                <p className="text-xs text-emerald-800 dark:text-emerald-300">
                  Your current CGPA, department, backlog count, and graduating batch satisfy all the criteria set by {job.company?.name || 'the recruiter'}.
                </p>
              ) : (
                <div className="space-y-1.5 pt-1">
                  <p className="text-xs font-semibold text-rose-800 dark:text-rose-300">
                    The following criteria were not satisfied:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-xs text-rose-700 dark:text-rose-400">
                    {reasons.map((r, i) => (
                      <li key={i} className="font-medium">
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Job Description */}
        {job.description && (
          <div className="space-y-2 pt-2">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">
              Role Description
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line leading-relaxed">
              {job.description}
            </p>
          </div>
        )}

        {/* Requirements */}
        {job.requirements && Array.isArray(job.requirements) && job.requirements.length > 0 && (
          <div className="space-y-2 pt-2">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">
              Role Requirements
            </h2>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-300">
              {job.requirements.map((req, i) => (
                <li key={i}>{req}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Required Skills */}
        {job.required_skills && Array.isArray(job.required_skills) && job.required_skills.length > 0 && (
          <div className="space-y-2 pt-2">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">
              Required Skills
            </h2>
            <div className="flex flex-wrap gap-2">
              {job.required_skills.map((skill) => (
                <span
                  key={skill}
                  className="px-3 py-1 rounded-lg text-xs font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Application CTA Bar */}
        <div className="pt-6 border-t border-gray-200 dark:border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            {!isEligible ? (
              <span className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                🔒 Application locked: You do not meet the minimum criteria for this position.
              </span>
            ) : hasApplied ? (
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                ✓ Application submitted for {job.title}!
              </span>
            ) : (
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                ✨ Ready to apply with your primary resume!
              </span>
            )}
          </div>

          <button
            type="button"
            disabled={!isEligible}
            onClick={() => setApplyModalOpen(true)}
            className={`px-8 py-3 rounded-xl text-sm font-bold transition shadow-sm ${
              isEligible
                ? 'bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer active:scale-98'
                : 'bg-gray-200 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed'
            }`}
          >
            {hasApplied ? 'Applied ✓' : 'Apply Now'}
          </button>
        </div>
      </div>

      {/* Application Stub Confirmation Modal */}
      {applyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-gray-200 dark:border-gray-800">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Confirm Job Application
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              You are applying for <strong className="text-indigo-600">{job.title}</strong> at{' '}
              <strong>{job.company?.name}</strong> using your current profile and primary uploaded resume.
            </p>
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl text-xs text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              ✓ Verified: You meet all academic eligibility requirements!
            </div>
            {errorMessage && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 rounded-xl text-xs text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
                ⚠️ {errorMessage}
              </div>
            )}
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setApplyModalOpen(false)}
                disabled={applyLoading}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleApplySubmit}
                disabled={applyLoading}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg disabled:opacity-50"
              >
                {applyLoading ? 'Submitting...' : 'Confirm & Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
