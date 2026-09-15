import React, { useEffect, useState } from 'react'
import { getDashboard, getStatistics } from '../api/adminApi'

export default function PlacementDashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [dashRes, statsRes] = await Promise.all([
        getDashboard(),
        getStatistics(),
      ])
      if (dashRes.data) setDashboard(dashRes.data)
      if (statsRes.data) setStatistics(statsRes.data)
    } catch (err) {
      setError('Failed to load dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-gray-600">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-6xl mx-auto p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Campus recruitment overview</p>
        </div>

        {/* Top Cards */}
        {dashboard && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Students Card */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm font-medium">
                    Total Students
                  </p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {dashboard.total_students}
                  </p>
                </div>
                <div className="bg-blue-100 p-3 rounded-lg">
                  <svg
                    className="w-6 h-6 text-blue-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 12H9m6 0a6 6 0 11-12 0 6 6 0 0112 0z"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* Companies Card */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm font-medium">
                    Companies
                  </p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {dashboard.total_companies}
                  </p>
                </div>
                <div className="bg-green-100 p-3 rounded-lg">
                  <svg
                    className="w-6 h-6 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* Applications Card */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm font-medium">
                    Applications
                  </p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {dashboard.total_applications}
                  </p>
                </div>
                <div className="bg-purple-100 p-3 rounded-lg">
                  <svg
                    className="w-6 h-6 text-purple-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* Selected Card */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-emerald-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm font-medium">Selected</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {dashboard.applications_selected}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {dashboard.placement_percentage}% placement rate
                  </p>
                </div>
                <div className="bg-emerald-100 p-3 rounded-lg">
                  <svg
                    className="w-6 h-6 text-emerald-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Charts Section */}
        {statistics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Application Funnel */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Application Funnel
              </h2>
              <div className="space-y-4">
                {statistics.application_funnel?.map((stage, idx) => {
                  const maxCount = Math.max(
                    ...statistics.application_funnel.map((s) => s.count)
                  )
                  const percentage = (stage.count / maxCount) * 100
                  return (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700">
                          {stage.stage}
                        </span>
                        <span className="text-sm font-semibold text-gray-900">
                          {stage.count}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Recruitment Drive Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Job Status Distribution
              </h2>
              <div className="space-y-3">
                {statistics.recruitment_drive_status?.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="text-sm font-medium text-gray-700">
                      {item.status}
                    </span>
                    <span className="text-sm font-semibold text-gray-900 bg-white px-3 py-1 rounded">
                      {item.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Applications by Company */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Applications by Company
              </h2>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {statistics.applications_by_company?.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 rounded"
                  >
                    <span className="text-sm text-gray-700 truncate">
                      {item.company}
                    </span>
                    <span className="text-sm font-semibold text-indigo-600 ml-2">
                      {item.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Selections by Company */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Selections by Company
              </h2>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {statistics.selections_by_company?.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 rounded"
                  >
                    <span className="text-sm text-gray-700 truncate">
                      {item.company}
                    </span>
                    <span className="text-sm font-semibold text-emerald-600 ml-2">
                      {item.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Applications by Department */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Applications by Department
              </h2>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {statistics.applications_by_department?.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 rounded"
                  >
                    <span className="text-sm text-gray-700">{item.department}</span>
                    <span className="text-sm font-semibold text-blue-600 ml-2">
                      {item.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Selection Rate by Department */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Selection Rate by Department
              </h2>
              <div className="space-y-3">
                {statistics.selection_rate_by_department?.map((item, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">
                        {item.department}
                      </span>
                      <span className="text-sm font-semibold text-gray-900">
                        {item.rate}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-emerald-500 h-2 rounded-full transition-all"
                        style={{ width: `${item.rate}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Refresh Button */}
        <div className="flex justify-end">
          <button
            onClick={fetchData}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  )
}
