// src/pages/RecruiterApplicantsPage.jsx
// Recruiter's applicants table for a specific job with AI scoring, ranking, filters, and detailed match analysis.

import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  getJobDetail,
  getJobApplicants,
  recalculateJobScores,
  exportJobApplicantsCsv,
  getApplicationMatchAnalysis,
  updateApplicationStatus,
  scheduleInterview,
} from '../api/recruiterApi'

export default function RecruiterApplicantsPage() {
  const { id: jobId } = useParams()
  const navigate = useNavigate()

  const [job, setJob] = useState(null)
  const [applicants, setApplicants] = useState([])
  const [loading, setLoading] = useState(true)
  const [recalculating, setRecalculating] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportOpen, setExportOpen] = useState(false)
  const [exportTopK, setExportTopK] = useState('5')
  const [actionLoading, setActionLoading] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  // Filter & sort state (Default sort: 'rank')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [branch, setBranch] = useState('')
  const [minCgpa, setMinCgpa] = useState('')
  const [maxBacklogs, setMaxBacklogs] = useState('')
  const [batch, setBatch] = useState('')
  const [status, setStatus] = useState('')
  const [minAiScore, setMinAiScore] = useState('')
  const [sortBy, setSortBy] = useState('rank')

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

  // AI Match Analysis modal state
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisData, setAnalysisData] = useState(null)
  const [analysisError, setAnalysisError] = useState('')

  const fetchJobDetail = async () => {
    try {
      const res = await getJobDetail(parseInt(jobId))
      if (res.success && res.data) {
        setJob(res.data)
      }
    } catch {
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
        min_ai_score: minAiScore ? parseFloat(minAiScore) : undefined,
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

  useEffect(() => {
    fetchJobDetail()
  }, [jobId])

  useEffect(() => {
    fetchApplicants()
  }, [page, branch, minCgpa, maxBacklogs, batch, status, minAiScore, sortBy])

  const handleRecalculateScores = async () => {
    setRecalculating(true)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      const res = await recalculateJobScores(parseInt(jobId))
      if (res.success) {
        setSuccessMessage('AI match scores and applicant ranks recalculated successfully.')
        await fetchApplicants()
        setTimeout(() => setSuccessMessage(''), 4000)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to recalculate scores.')
    } finally {
      setRecalculating(false)
    }
  }

  const handleExportCsv = async (kVal = null) => {
    setExporting(true)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      const targetK = kVal !== null ? kVal : exportTopK
      await exportJobApplicantsCsv({
        jobId: parseInt(jobId),
        topK: targetK || undefined,
      })
      const label = targetK ? `Top ${targetK}` : 'All'
      setSuccessMessage(`Successfully exported ${label} candidates CSV.`)
      setTimeout(() => setSuccessMessage(''), 4000)
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to export candidates CSV. Make sure scored applicants exist.')
    } finally {
      setExporting(false)
    }
  }

  const handleOpenAnalysis = async (app) => {
    setSelectedApp(app)
    setAnalysisModalOpen(true)
    setAnalysisLoading(true)
    setAnalysisError('')
    setAnalysisData(null)
    try {
      const res = await getApplicationMatchAnalysis(app.application_id)
      if (res.success && res.data) {
        setAnalysisData(res.data)
      } else {
        setAnalysisError('Could not load AI analysis for this applicant.')
      }
    } catch (err) {
      setAnalysisError(err.response?.data?.message || 'Failed to retrieve AI analysis.')
    } finally {
      setAnalysisLoading(false)
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

  const getRankBadge = (rank) => {
    if (!rank) {
      return (
        <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
          —
        </span>
      )
    }
    if (rank === 1) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold bg-amber-100 text-amber-900 dark:bg-amber-900/60 dark:text-amber-200 border border-amber-300 dark:border-amber-700">
          🥇 #1
        </span>
      )
    }
    if (rank === 2) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600">
          🥈 #2
        </span>
      )
    }
    if (rank === 3) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold bg-orange-100 text-orange-900 dark:bg-orange-950/60 dark:text-orange-200 border border-orange-300 dark:border-orange-800">
          🥉 #3
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700 font-mono">
        #{rank}
      </span>
    )
  }

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800'
    if (score >= 60) return 'text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800'
    if (score >= 40) return 'text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800'
    return 'text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800'
  }

  if (!job && !loading) {
    return (
      <div className="text-center py-16 space-y-4">
        <p className="text-gray-500">Job not found.</p>
        <div>
          <Link
            to="/recruiter/jobs"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            ← Back to Jobs
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Navigation Back to Jobs */}
      <div>
        <Link
          to="/recruiter/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 transition focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded"
        >
          ← Back to Jobs
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Applicants for {job?.title || (loading ? 'Job...' : `Job #${jobId}`)}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {job?.title ? (
              <span className="font-semibold text-gray-700 dark:text-gray-300">{job.title} • </span>
            ) : null}
            {totalCount} total applicant{totalCount !== 1 ? 's' : ''} • AI candidate ranking active
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Export Top Candidates Button */}
          <button
            onClick={() => setExportOpen((prev) => !prev)}
            className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border transition ${
              exportOpen
                ? 'bg-indigo-50 border-indigo-300 text-indigo-700 dark:bg-indigo-950/60 dark:border-indigo-700 dark:text-indigo-300'
                : 'bg-white hover:bg-gray-50 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-700 shadow-sm'
            }`}
            title="Export top ranked candidates to CSV"
          >
            <span>📥</span>
            Export Top Candidates
            <span className="text-[10px] opacity-75">{exportOpen ? '▲' : '▼'}</span>
          </button>

          {/* Recalculate AI Scores Button */}
          <button
            onClick={handleRecalculateScores}
            disabled={recalculating || loading}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition disabled:opacity-50"
            title="Recalculate AI embeddings, scores, and rankings"
          >
            {recalculating ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                Scoring Applicants...
              </>
            ) : (
              <>
                <span>⚡</span>
                Recalculate AI Scores
              </>
            )}
          </button>
        </div>
      </div>

      {/* Inline Export Controls */}
      {exportOpen && (
        <div className="p-4 rounded-xl border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/50 dark:bg-indigo-950/30 space-y-3 animate-fadeIn">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold text-indigo-950 dark:text-indigo-200 flex items-center gap-1.5">
                <span>📄</span> Export Top Ranked Candidates to CSV
              </p>
              <p className="text-[11px] text-indigo-800/80 dark:text-indigo-300/80">
                Exports ranked applicants ordered best-to-worst with full skill breakdown and contact details.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setExportOpen(false)}
                className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1"
                title="Close export control"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Quick Export:</span>
            {[5, 10, 25].map((k) => (
              <button
                key={k}
                onClick={() => {
                  setExportTopK(String(k))
                  handleExportCsv(String(k))
                }}
                disabled={exporting}
                className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-white dark:bg-gray-800 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 shadow-2xs transition disabled:opacity-50"
              >
                Top {k}
              </button>
            ))}
            <button
              onClick={() => {
                setExportTopK('')
                handleExportCsv('')
              }}
              disabled={exporting}
              className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-white dark:bg-gray-800 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 shadow-2xs transition disabled:opacity-50"
            >
              Export All
            </button>

            <div className="h-4 w-px bg-indigo-200 dark:bg-indigo-800 mx-1 hidden sm:block" />

            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-600 dark:text-gray-400">Custom Top K:</span>
              <input
                type="number"
                min="1"
                placeholder="e.g. 15"
                value={exportTopK}
                onChange={(e) => setExportTopK(e.target.value)}
                className="w-20 px-2 py-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs text-center"
              />
              <button
                onClick={() => handleExportCsv(exportTopK)}
                disabled={exporting}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition disabled:opacity-50"
              >
                {exporting ? (
                  <>
                    <svg className="animate-spin h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                    </svg>
                    Exporting...
                  </>
                ) : (
                  <>
                    <span>⬇️</span> Download CSV
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Persistent AI Principle Note */}
      <div className="flex items-start gap-3 p-3.5 rounded-xl border border-indigo-100 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/30 text-indigo-900 dark:text-indigo-200 text-xs">
        <span className="text-base leading-none">💡</span>
        <div>
          <p className="font-semibold mb-0.5">AI-Assisted Screening Note</p>
          <p className="text-indigo-800/90 dark:text-indigo-300">
            AI scores are a screening aid to help prioritize review — they don't represent a hiring decision. Final selection is always your call.
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
      <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 space-y-4 shadow-sm">
        <div>
          <div className="flex justify-between items-center mb-3">
            <p className="text-xs uppercase tracking-wider font-bold text-gray-600 dark:text-gray-400">
              Filters & Ordering
            </p>
            {(branch || minCgpa || maxBacklogs || batch || status || minAiScore || sortBy !== 'rank') && (
              <button
                onClick={() => {
                  setBranch('')
                  setMinCgpa('')
                  setMaxBacklogs('')
                  setBatch('')
                  setStatus('')
                  setMinAiScore('')
                  setSortBy('rank')
                  setPage(1)
                }}
                className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
              >
                Reset Filters
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2">
            <input
              type="text"
              placeholder="Branch"
              value={branch}
              onChange={(e) => { setBranch(e.target.value); setPage(1) }}
              className="px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
            />
            <input
              type="number"
              placeholder="Min CGPA"
              value={minCgpa}
              onChange={(e) => { setMinCgpa(e.target.value); setPage(1) }}
              className="px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
              step="0.1"
              min="0"
              max="10"
            />
            <input
              type="number"
              placeholder="Max Backlogs"
              value={maxBacklogs}
              onChange={(e) => { setMaxBacklogs(e.target.value); setPage(1) }}
              className="px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
              min="0"
            />
            <input
              type="number"
              placeholder="Batch"
              value={batch}
              onChange={(e) => { setBatch(e.target.value); setPage(1) }}
              className="px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
            />
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1) }}
              className="px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs"
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
            <input
              type="number"
              placeholder="Min AI Score %"
              value={minAiScore}
              onChange={(e) => { setMinAiScore(e.target.value); setPage(1) }}
              className="px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs placeholder-gray-400"
              min="0"
              max="100"
              step="1"
            />
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
              className="px-2.5 py-1.5 rounded-lg border border-indigo-300 dark:border-indigo-700 bg-indigo-50/50 dark:bg-indigo-950/40 text-xs font-semibold text-indigo-900 dark:text-indigo-200"
            >
              <option value="rank">⭐ Rank (Best Match)</option>
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
          {[1, 2, 3, 4].map((n) => (
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
                <th className="py-3.5 px-4 w-16 text-center">Rank</th>
                <th className="py-3.5 px-4">Candidate</th>
                <th className="py-3.5 px-4">Branch & Academics</th>
                <th className="py-3.5 px-4">AI Score</th>
                <th className="py-3.5 px-4">Skill Match</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {applicants.map((app) => (
                <tr key={app.application_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition">
                  <td className="py-4 px-4 text-center">
                    {getRankBadge(app.rank)}
                  </td>
                  <td className="py-4 px-4">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{app.student_name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{app.roll_number} • {app.student_email}</p>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <p className="text-xs font-medium text-gray-900 dark:text-gray-200">{app.branch}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      CGPA: <span className="font-semibold text-gray-700 dark:text-gray-300">{app.cgpa ? app.cgpa.toFixed(2) : '-'}</span>
                      {app.backlog_count > 0 ? (
                        <span className="ml-2 text-rose-600 dark:text-rose-400 font-semibold font-mono">
                          ({app.backlog_count} backlog{app.backlog_count > 1 ? 's' : ''})
                        </span>
                      ) : (
                        <span className="ml-2 text-emerald-600 dark:text-emerald-400 font-medium">
                          (0 backlogs)
                        </span>
                      )}
                    </p>
                  </td>
                  <td className="py-4 px-4">
                    {app.ai_score !== null && app.ai_score !== undefined ? (
                      <div className="space-y-1">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${getScoreColorClass(app.ai_score)}`}>
                          {app.ai_score.toFixed(1)}% Match
                        </span>
                      </div>
                    ) : (
                      <span
                        className="inline-flex items-center text-xs font-medium text-gray-500 dark:text-gray-400 italic"
                        title="Resume text extraction or embedding could not be generated"
                      >
                        AI analysis unavailable for this candidate — please review their resume manually
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-4">
                    {app.skill_score !== null && app.skill_score !== undefined ? (
                      <span className="text-xs font-semibold text-gray-900 dark:text-gray-200">
                        {app.skill_score.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="py-4 px-4">
                    {getStatusBadge(app.status)}
                  </td>
                  <td className="py-4 px-4 text-right space-x-1.5 whitespace-nowrap">
                    {/* View AI Analysis Button */}
                    <button
                      onClick={() => handleOpenAnalysis(app)}
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-300 dark:border-gray-700 transition"
                      title="View full AI match breakdown and skills comparison"
                    >
                      🔍 View AI Analysis
                    </button>

                    {app.status === 'ELIGIBILITY_VERIFIED' && (
                      <>
                        <button
                          onClick={() => handleStatusUpdate(app.application_id, 'SHORTLISTED')}
                          disabled={actionLoading === app.application_id}
                          className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition disabled:opacity-50"
                        >
                          {actionLoading === app.application_id ? '...' : 'Shortlist'}
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

      {/* AI Match Analysis Modal */}
      {analysisModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl border border-gray-200 dark:border-gray-800 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-gray-100 dark:border-gray-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                    {analysisData?.candidate_name || selectedApp?.student_name || 'Candidate Match Analysis'}
                  </h3>
                  {analysisData?.rank && getRankBadge(analysisData.rank)}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Applied for <strong>{analysisData?.job_title || job?.title}</strong> • {analysisData?.branch}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAnalysisModalOpen(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
              >
                ✕
              </button>
            </div>

            {/* Persistent AI Principle Note */}
            <div className="p-3 rounded-xl border border-indigo-100 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/30 text-indigo-900 dark:text-indigo-200 text-xs flex items-start gap-2">
              <span className="text-sm leading-none">ℹ️</span>
              <p>
                {analysisData?.disclaimer || "AI scores are a screening aid to help prioritize review — they don't represent a hiring decision. Final selection is always your call."}
              </p>
            </div>

            {analysisLoading ? (
              <div className="py-12 text-center space-y-3">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent"></div>
                <p className="text-sm text-gray-500">Analyzing resume and profile match...</p>
              </div>
            ) : analysisError ? (
              <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 text-sm font-medium">
                {analysisError}
              </div>
            ) : analysisData ? (
              <div className="space-y-5">
                {/* Fallback Banner if scoring unavailable */}
                {!analysisData.scoring_available && (
                  <div className="p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 text-sm">
                    ⚠️ AI analysis unavailable for this candidate — please review their resume manually.
                  </div>
                )}

                {/* Overall Score Highlight */}
                <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-transparent border border-indigo-100 dark:border-indigo-900/50 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div>
                    <span className="text-xs uppercase tracking-wider font-bold text-indigo-600 dark:text-indigo-400">
                      Overall Composite Match
                    </span>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-4xl font-extrabold text-gray-900 dark:text-white">
                        {analysisData.overall_score !== null ? `${analysisData.overall_score.toFixed(1)}%` : 'N/A'}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">weighted score</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1">
                      Eligibility Status
                    </span>
                    {analysisData.eligibility?.eligible ? (
                      <span className="inline-flex px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                        ✓ Meets All Criteria
                      </span>
                    ) : (
                      <span className="inline-flex px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-300 dark:border-rose-800">
                        ✕ Ineligible
                      </span>
                    )}
                  </div>
                </div>

                {/* Component Breakdown Grid */}
                <div>
                  <h4 className="text-xs uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-3">
                    Component Score Breakdown
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {/* Semantic Similarity */}
                    <div className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/40">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Semantic Match</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {analysisData.semantic_similarity !== null ? `${analysisData.semantic_similarity.toFixed(1)}%` : '—'}
                      </p>
                      <p className="text-[10px] text-gray-400 mt-0.5">50% weight (AI vectors)</p>
                    </div>

                    {/* Skill Match */}
                    <div className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/40">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Skill Match</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {analysisData.skill_match_percentage !== null ? `${analysisData.skill_match_percentage.toFixed(1)}%` : '—'}
                      </p>
                      <p className="text-[10px] text-gray-400 mt-0.5">25% weight (Required × 2)</p>
                    </div>

                    {/* Experience Relevance */}
                    <div className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/40">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Experience</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {analysisData.experience_relevance !== null ? `${analysisData.experience_relevance.toFixed(1)}%` : '—'}
                      </p>
                      <p className="text-[10px] text-gray-400 mt-0.5">15% weight</p>
                    </div>

                    {/* Education Relevance */}
                    <div className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/40">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Education</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {analysisData.education_relevance !== null ? `${analysisData.education_relevance.toFixed(1)}%` : '—'}
                      </p>
                      <p className="text-[10px] text-gray-400 mt-0.5">10% weight</p>
                    </div>
                  </div>
                </div>

                {/* Skills Analysis */}
                <div className="space-y-3">
                  <h4 className="text-xs uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400">
                    Skill Keyword Analysis
                  </h4>

                  {/* Matching Skills */}
                  <div>
                    <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 block mb-1.5">
                      ✓ Matching Skills ({analysisData.matching_skills?.length || 0})
                    </span>
                    {analysisData.matching_skills && analysisData.matching_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {analysisData.matching_skills.map((skill, i) => (
                          <span
                            key={i}
                            className="inline-flex px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60"
                          >
                            ✓ {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">No matching skills detected.</p>
                    )}
                  </div>

                  {/* Missing Required Skills */}
                  <div>
                    <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 block mb-1.5">
                      ✕ Missing Required Skills ({analysisData.missing_required_skills?.length || 0})
                    </span>
                    {analysisData.missing_required_skills && analysisData.missing_required_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {analysisData.missing_required_skills.map((skill, i) => (
                          <span
                            key={i}
                            className="inline-flex px-2.5 py-1 rounded-lg text-xs font-medium bg-rose-50 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60"
                          >
                            ✕ {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                        ✓ All mandatory required skills are present in the candidate resume!
                      </p>
                    )}
                  </div>

                  {/* Matching Preferred Skills */}
                  {analysisData.matching_preferred_skills && analysisData.matching_preferred_skills.length > 0 && (
                    <div>
                      <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 block mb-1.5">
                        ⭐ Preferred Skills Matched ({analysisData.matching_preferred_skills.length})
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {analysisData.matching_preferred_skills.map((skill, i) => (
                          <span
                            key={i}
                            className="inline-flex px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-800 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60"
                          >
                            ★ {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Eligibility Failure Reasons (if any) */}
                {analysisData.eligibility?.reasons && analysisData.eligibility.reasons.length > 0 && (
                  <div className="p-3.5 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/60 dark:bg-rose-950/30">
                    <p className="text-xs font-bold text-rose-900 dark:text-rose-200 mb-1">
                      Eligibility Check Remarks:
                    </p>
                    <ul className="list-disc list-inside space-y-0.5 text-xs text-rose-800 dark:text-rose-300">
                      {analysisData.eligibility.reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : null}

            {/* Modal Footer */}
            <div className="flex justify-end pt-3 border-t border-gray-100 dark:border-gray-800">
              <button
                type="button"
                onClick={() => setAnalysisModalOpen(false)}
                className="px-5 py-2 text-sm font-semibold bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl transition"
              >
                Close Analysis
              </button>
            </div>
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
