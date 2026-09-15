// src/pages/RecruiterDashboard.jsx
// Recruiter Command Center with real database counts, active drives, and quick actions.

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRecruiterProfile, getRecruiterJobs } from '../api/recruiterApi'
import { useAuthStore } from '../store/authStore'

export default function RecruiterDashboard() {
  const { user } = useAuthStore()
  const [profile, setProfile] = useState(null)
  const [recentJobs, setRecentJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true)
      try {
        const [profRes, jobsRes] = await Promise.allSettled([
          getRecruiterProfile(),
          getRecruiterJobs({ page: 1, page_size: 5 }),
        ])

        if (profRes.status === 'fulfilled' && profRes.value.success) {
          setProfile(profRes.value.data)
        }

        if (jobsRes.status === 'fulfilled' && jobsRes.value.success) {
          setRecentJobs(jobsRes.value.data.items || [])
        }
      } catch (err) {
        console.error('Recruiter dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    loadDashboard()
  }, [])

  const totalJobs = profile?.total_jobs ?? 0
  const activeJobs = profile?.active_jobs ?? 0
  const companyName = profile?.company?.name || 'Your Company'

  return (
    <div className="space-y-8">
      {/* Header Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white">
            Welcome back, {profile?.name || user?.name || 'Recruiter'}! 💼
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Recruitment Command Center for <strong className="text-indigo-600 dark:text-indigo-400">{companyName}</strong>.
          </p>
        </div>

        <Link
          to="/recruiter/jobs/create"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-sm transition self-start sm:self-auto"
        >
          <span>➕</span> Post New Drive
        </Link>
      </div>

      {/* Top Metric Cards (Queried directly from DB) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Card 1: Total Jobs */}
        <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-1">
          <span className="text-xs uppercase font-bold text-gray-400">Total Drives</span>
          <div className="text-2xl font-extrabold text-gray-900 dark:text-white">
            {loading ? '...' : totalJobs}
          </div>
          <div className="text-xs text-gray-500">Created by your team</div>
        </div>

        {/* Card 2: Active OPEN Jobs */}
        <div className="p-5 rounded-2xl border border-emerald-100 dark:border-emerald-950 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-sm space-y-1">
          <span className="text-xs uppercase font-bold text-emerald-800 dark:text-emerald-400">Active Drives</span>
          <div className="text-2xl font-extrabold text-emerald-900 dark:text-emerald-200">
            {loading ? '...' : activeJobs}
          </div>
          <div className="text-xs text-emerald-700 dark:text-emerald-300">Open to applications</div>
        </div>

        {/* Card 3: Total Applicants (Placeholder wired for Prompt 5) */}
        <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-1">
          <span className="text-xs uppercase font-bold text-gray-400">Total Applicants</span>
          <div className="text-2xl font-extrabold text-gray-900 dark:text-white">
            0
          </div>
          <div className="text-xs text-gray-400">Ready for incoming candidates</div>
        </div>

        {/* Card 4: Shortlisted Candidates (Placeholder wired for Prompt 6) */}
        <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-1">
          <span className="text-xs uppercase font-bold text-gray-400">Shortlisted</span>
          <div className="text-2xl font-extrabold text-gray-900 dark:text-white">
            0
          </div>
          <div className="text-xs text-gray-400">AI Scoring & Interviews</div>
        </div>
      </div>

      {/* Quick Action Navigation Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">
          Recruitment Tools
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/recruiter/jobs"
            className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-indigo-400 hover:shadow-md transition group space-y-2"
          >
            <div className="text-2xl">📋</div>
            <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 transition">
              Manage Job Postings
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Publish drafts, modify eligibility filters, close hiring rounds, and track applicants.
            </p>
          </Link>

          <Link
            to="/recruiter/jobs/create"
            className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-indigo-400 hover:shadow-md transition group space-y-2"
          >
            <div className="text-2xl">➕</div>
            <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 transition">
              Post New Campus Drive
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Define CGPA cutoff, permitted branches, batch, backlogs, and package compensation.
            </p>
          </Link>

          <Link
            to="/recruiter/company"
            className="p-5 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-indigo-400 hover:shadow-md transition group space-y-2"
          >
            <div className="text-2xl">🏢</div>
            <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 transition">
              Company Branding
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Update organization info, website, logo, and recruitment contact points.
            </p>
          </Link>
        </div>
      </div>

      {/* Recent Job Openings Table Preview */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Recent Campus Drives
          </h2>
          <Link
            to="/recruiter/jobs"
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            View All ({totalJobs}) →
          </Link>
        </div>

        {recentJobs.length === 0 ? (
          <div className="p-6 text-center text-sm text-gray-500 border border-gray-200 dark:border-gray-800 rounded-2xl bg-white dark:bg-gray-900">
            No drives created yet. Click "Post New Drive" above to publish your first opening!
          </div>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800/60 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200 dark:border-gray-800">
                <tr>
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Package</th>
                  <th className="py-3 px-4">Applicants</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {recentJobs.map((j) => (
                  <tr key={j.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/40">
                    <td className="py-3.5 px-4 font-semibold text-gray-900 dark:text-white">
                      {j.title}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                          j.status === 'OPEN'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300'
                            : j.status === 'DRAFT'
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300'
                            : 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300'
                        }`}
                      >
                        {j.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-gray-700 dark:text-gray-300">
                      {j.package_lpa ? `${j.package_lpa} LPA` : 'Competitive'}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-gray-500">
                      {j.total_applicants} candidates
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/recruiter/jobs/${j.id}`}
                        className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
                      >
                        Edit →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
