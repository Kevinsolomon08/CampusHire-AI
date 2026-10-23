// src/pages/StudentDashboard.jsx
// Modern Student Command Center: quick stats, profile health, recommended jobs, and quick actions.

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStudentProfile, getStudentJobs, getRecommendedJobs } from '../api/studentApi'
import { useAuthStore } from '../store/authStore'

// ─── Score ring colour helper ────────────────────────────────────────────────
function scoreColor(score) {
  if (score >= 70) return { ring: '#10b981', text: 'text-emerald-700 dark:text-emerald-300' }
  if (score >= 45) return { ring: '#6366f1', text: 'text-indigo-700 dark:text-indigo-300' }
  return { ring: '#f59e0b', text: 'text-amber-700 dark:text-amber-300' }
}

// ─── Mini SVG ring ───────────────────────────────────────────────────────────
function ScoreRing({ score }) {
  const r = 22
  const circ = 2 * Math.PI * r
  const pct = Math.min(100, Math.max(0, score))
  const offset = circ - (pct / 100) * circ
  const { ring } = scoreColor(score)

  return (
    <svg width="60" height="60" className="flex-shrink-0" style={{ transform: 'rotate(-90deg)' }}>
      <circle cx="30" cy="30" r={r} stroke="#e5e7eb" strokeWidth="5" fill="none" />
      <circle
        cx="30" cy="30" r={r}
        stroke={ring} strokeWidth="5" fill="none"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.8s ease' }}
      />
      <text
        x="30" y="34"
        textAnchor="middle"
        fontSize="11"
        fontWeight="700"
        fill="currentColor"
        style={{ transform: 'rotate(90deg)', transformOrigin: '30px 30px' }}
      >
        {Math.round(pct)}%
      </text>
    </svg>
  )
}

// ─── Recommended job card ─────────────────────────────────────────────────────
function RecommendedJobCard({ job }) {
  const { text: scoreText } = scoreColor(job.semantic_score)
  const isEligible = job.eligibility?.eligible

  return (
    <Link
      to={`/student/jobs/${job.id}`}
      className="group flex gap-4 p-4 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-indigo-400 dark:hover:border-indigo-600 hover:shadow-md transition-all duration-200"
    >
      {/* Score ring */}
      <div className="flex flex-col items-center gap-1">
        <ScoreRing score={job.semantic_score} />
        <span className={`text-[10px] font-semibold ${scoreText}`}>Match</span>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition text-sm leading-snug line-clamp-2">
            {job.title}
          </h3>
          {/* Eligibility pill — visually separate from the match score */}
          <span
            title={
              isEligible
                ? 'You meet all hard criteria for this job'
                : (job.eligibility?.reasons?.join(' | ') || 'Not eligible')
            }
            className={`flex-shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full border ${
              isEligible
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
                : 'bg-red-50 text-red-600 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800'
            }`}
          >
            {isEligible ? '✓ Eligible' : '✕ Not Eligible'}
          </span>
        </div>

        <div className="text-xs text-gray-500 dark:text-gray-400 flex flex-wrap gap-x-3 gap-y-0.5">
          {job.company?.name && <span>🏢 {job.company.name}</span>}
          {job.location && <span>📍 {job.location}</span>}
          {job.package_lpa && <span>💰 {job.package_lpa} LPA</span>}
          {job.min_cgpa && <span>🎓 {job.min_cgpa}+ CGPA</span>}
        </div>

        {/* Not-eligible reasons */}
        {!isEligible && job.eligibility?.reasons?.length > 0 && (
          <p className="text-[10px] text-red-500 dark:text-red-400 leading-tight line-clamp-2">
            ⚠️ {job.eligibility.reasons.join(' • ')}
          </p>
        )}

        {/* Required skills chips */}
        {Array.isArray(job.required_skills) && job.required_skills.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {job.required_skills.slice(0, 5).map((skill) => (
              <span
                key={skill}
                className="text-[10px] bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-1.5 py-0.5 rounded-full"
              >
                {skill}
              </span>
            ))}
            {job.required_skills.length > 5 && (
              <span className="text-[10px] text-gray-400 dark:text-gray-500 self-center">
                +{job.required_skills.length - 5} more
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function StudentDashboard() {
  const { user } = useAuthStore()
  const [profile, setProfile] = useState(null)
  const [jobsSummary, setJobsSummary] = useState({ total: 0, eligible: 0 })
  const [recommendations, setRecommendations] = useState(null)   // null = loading
  const [recoMessage, setRecoMessage] = useState(null)
  const [hasResume, setHasResume] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true)
      try {
        const [profileRes, jobsRes, recoRes] = await Promise.allSettled([
          getStudentProfile(),
          getStudentJobs({ page: 1, page_size: 20 }),
          getRecommendedJobs(),
        ])

        if (profileRes.status === 'fulfilled' && profileRes.value.success) {
          setProfile(profileRes.value.data)
        }

        if (jobsRes.status === 'fulfilled' && jobsRes.value.success) {
          const items = jobsRes.value.data.items || []
          const eligibleCount = items.filter((j) => j.eligibility?.eligible).length
          setJobsSummary({
            total: jobsRes.value.data.total || items.length,
            eligible: eligibleCount,
          })
        }

        if (recoRes.status === 'fulfilled' && recoRes.value.success) {
          const d = recoRes.value.data
          setRecommendations(d.items || [])
          setRecoMessage(d.message || null)
          setHasResume(d.has_resume ?? true)
        } else {
          setRecommendations([])
        }
      } catch (err) {
        console.error('Dashboard load error:', err)
        setRecommendations([])
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  const completionPct = profile?.profile_completion_pct ?? 0

  return (
    <div className="space-y-8">
      {/* Header Greeting */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white">
          Welcome back, {profile?.name || user?.name || 'Student'}! 👋
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Here is your real-time campus recruitment readiness and active job opportunities.
        </p>
      </div>

      {/* Quick Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Card 1: Profile Health */}
        <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-xs uppercase font-bold text-gray-400">
            <span>Profile Health</span>
            <span className="text-indigo-600 font-bold">{completionPct}%</span>
          </div>
          <div className="w-full bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                completionPct >= 80
                  ? 'bg-emerald-500'
                  : completionPct >= 50
                  ? 'bg-indigo-600'
                  : 'bg-amber-500'
              }`}
              style={{ width: `${completionPct}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {profile?.primary_resume ? '✓ Resume attached' : '⚠️ No resume uploaded'}
          </div>
        </div>

        {/* Card 2: Academic Summary */}
        <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-1">
          <span className="text-xs uppercase font-bold text-gray-400">Academic Standing</span>
          <div className="text-xl font-extrabold text-gray-900 dark:text-white">
            {profile?.cgpa ? `${profile.cgpa} CGPA` : 'CGPA Not Set'}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {profile?.department || 'Computer Science'} • Class of {profile?.batch || '2025'}
          </div>
        </div>

        {/* Card 3: Eligible Openings */}
        <div className="p-5 rounded-2xl border border-emerald-100 dark:border-emerald-950 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-sm space-y-1">
          <span className="text-xs uppercase font-bold text-emerald-800 dark:text-emerald-400">
            Eligible Drives
          </span>
          <div className="text-xl font-extrabold text-emerald-900 dark:text-emerald-200">
            {jobsSummary.eligible} of {jobsSummary.total} Drives
          </div>
          <div className="text-xs text-emerald-700 dark:text-emerald-300">
            Match your department &amp; CGPA
          </div>
        </div>
      </div>

      {/* ── AI Recommended Jobs ──────────────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span>✨</span> AI Job Recommendations
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Ranked by relevance to your resume. Eligibility shown separately — a high match
              score does <em>not</em> mean you meet all hard criteria.
            </p>
          </div>
          <Link
            to="/student/jobs"
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex-shrink-0"
          >
            View all →
          </Link>
        </div>

        {/* Loading skeleton */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-24 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse"
              />
            ))}
          </div>
        )}

        {/* No resume / upload prompt */}
        {!loading && !hasResume && (
          <div className="flex flex-col items-center justify-center gap-3 p-8 rounded-2xl border-2 border-dashed border-indigo-200 dark:border-indigo-800 bg-indigo-50/30 dark:bg-indigo-950/20 text-center">
            <div className="text-4xl">📄</div>
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              Upload your resume to see personalised job recommendations
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 max-w-xs">
              Our AI will match your skills and experience against open job postings and surface
              the most relevant opportunities for you.
            </p>
            <Link
              to="/student/resume"
              className="mt-1 px-4 py-2 text-xs font-bold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition"
            >
              Upload Resume →
            </Link>
          </div>
        )}

        {/* Empty with resume (embedding issue or no open jobs) */}
        {!loading && hasResume && recommendations !== null && recommendations.length === 0 && (
          <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-center text-sm text-gray-500 dark:text-gray-400">
            {recoMessage || 'No recommendations available right now. Check back soon.'}
          </div>
        )}

        {/* Recommendation cards */}
        {!loading && recommendations && recommendations.length > 0 && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {recommendations.map((job) => (
                <RecommendedJobCard key={job.id} job={job} />
              ))}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-gray-400 dark:text-gray-500">
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" />
                ≥70% — Strong match
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 rounded-full bg-indigo-500" />
                45–69% — Moderate match
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 rounded-full bg-amber-400" />
                &lt;45% — Weak match
              </span>
              <span className="ml-auto italic">
                Eligibility (✓/✕) is independent of the match score
              </span>
            </div>
          </>
        )}
      </div>

      {/* Quick Action Navigation Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/student/jobs"
            className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-indigo-400 hover:shadow-md transition group space-y-2"
          >
            <div className="text-2xl">💼</div>
            <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 transition">
              Browse Job Drives
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              View open opportunities and check your real-time eligibility assessment.
            </p>
          </Link>

          <Link
            to="/student/profile"
            className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-indigo-400 hover:shadow-md transition group space-y-2"
          >
            <div className="text-2xl">👤</div>
            <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 transition">
              Edit My Profile
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Update CGPA, active backlogs, skills, education, and portfolio projects.
            </p>
          </Link>

          <Link
            to="/student/resume"
            className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-indigo-400 hover:shadow-md transition group space-y-2"
          >
            <div className="text-2xl">📄</div>
            <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 transition">
              Resume Manager
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Upload or update your official PDF resume for recruiters.
            </p>
          </Link>
        </div>
      </div>
    </div>
  )
}
