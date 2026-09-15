// src/pages/StudentDashboard.jsx
// Modern Student Command Center with quick actions, profile health, and job drive summaries.

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStudentProfile, getStudentJobs } from '../api/studentApi'
import { useAuthStore } from '../store/authStore'

export default function StudentDashboard() {
  const { user } = useAuthStore()
  const [profile, setProfile] = useState(null)
  const [jobsSummary, setJobsSummary] = useState({ total: 0, eligible: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true)
      try {
        const [profileRes, jobsRes] = await Promise.allSettled([
          getStudentProfile(),
          getStudentJobs({ page: 1, page_size: 20 }),
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
      } catch (err) {
        console.error('Dashboard load error:', err)
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
            Match your department & CGPA
          </div>
        </div>
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
