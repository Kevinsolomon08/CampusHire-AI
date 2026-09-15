// src/pages/PlacementReportsPage.jsx
// Placement Officer Reports generation page with filters, KPI cards, breakdown tables, and CSV export.

import React, { useEffect, useState } from 'react'
import { getReports, downloadReportCsv, getCompanies } from '../api/adminApi'

export default function PlacementReportsPage() {
  const [report, setReport] = useState(null)
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('company') // 'company' | 'department' | 'batch'

  // Filters
  const [batch, setBatch] = useState('')
  const [department, setDepartment] = useState('')
  const [companyId, setCompanyId] = useState('')
  const [jobId, setJobId] = useState('')

  useEffect(() => {
    fetchCompaniesList()
  }, [])

  useEffect(() => {
    fetchReportData()
  }, [batch, department, companyId, jobId])

  const fetchCompaniesList = async () => {
    try {
      const res = await getCompanies({ page: 1, page_size: 100 })
      if (res.data?.items) {
        setCompanies(res.data.items)
      }
    } catch (err) {
      console.error('Failed to load companies dropdown', err)
    }
  }

  const fetchReportData = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await getReports({
        batch: batch ? parseInt(batch) : null,
        department: department || undefined,
        company_id: companyId ? parseInt(companyId) : null,
        job_id: jobId ? parseInt(jobId) : null,
      })
      if (res.data) {
        setReport(res.data)
      }
    } catch (err) {
      setError('Failed to generate placement report. Please check your connection and try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadCsv = async () => {
    try {
      setExporting(true)
      const blobData = await downloadReportCsv({
        batch: batch ? parseInt(batch) : null,
        department: department || undefined,
        company_id: companyId ? parseInt(companyId) : null,
        job_id: jobId ? parseInt(jobId) : null,
      })

      const url = window.URL.createObjectURL(new Blob([blobData], { type: 'text/csv' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `CampusHire_Placement_Report_${new Date().toISOString().slice(0, 10)}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      alert('Failed to download CSV report. Please try again.')
      console.error(err)
    } finally {
      setExporting(false)
    }
  }

  const handleResetFilters = () => {
    setBatch('')
    setDepartment('')
    setCompanyId('')
    setJobId('')
  }

  const summary = report?.summary || {
    total_applications: 0,
    total_shortlisted: 0,
    total_interviewed: 0,
    total_selected: 0,
    total_rejected: 0,
    selection_rate: 0,
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
              Placement Reports & Analytics
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Generate customizable recruitment reports, filter by department and batch, and export CSVs.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchReportData}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              <svg
                className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
            <button
              onClick={handleDownloadCsv}
              disabled={exporting || loading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {exporting ? 'Exporting...' : 'Download CSV Report'}
            </button>
          </div>
        </div>

        {/* Filters Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
              Report Filters
            </h2>
            {(batch || department || companyId || jobId) && (
              <button
                onClick={handleResetFilters}
                className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
              >
                Clear all filters
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Batch Year */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Batch Year
              </label>
              <select
                value={batch}
                onChange={(e) => setBatch(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Batches</option>
                <option value="2024">2024</option>
                <option value="2025">2025</option>
                <option value="2026">2026</option>
              </select>
            </div>

            {/* Department */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Department
              </label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Departments</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Electronics">Electronics</option>
                <option value="Mechanical">Mechanical</option>
                <option value="Civil">Civil</option>
              </select>
            </div>

            {/* Company */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Company
              </label>
              <select
                value={companyId}
                onChange={(e) => setCompanyId(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Companies</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Job ID Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Job ID Filter
              </label>
              <input
                type="number"
                placeholder="e.g. 1"
                value={jobId}
                onChange={(e) => setJobId(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-rose-800 dark:text-rose-300">{error}</p>
            </div>
            <button
              onClick={fetchReportData}
              className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading Spinner */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
            <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
              Generating report metrics...
            </p>
          </div>
        ) : (
          <>
            {/* KPI Summary Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Total Applications</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {summary.total_applications}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
                <p className="text-xs font-medium text-indigo-600 dark:text-indigo-400">Shortlisted</p>
                <p className="text-2xl font-bold text-indigo-700 dark:text-indigo-300 mt-1">
                  {summary.total_shortlisted}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
                <p className="text-xs font-medium text-purple-600 dark:text-purple-400">Interviewed</p>
                <p className="text-2xl font-bold text-purple-700 dark:text-purple-300 mt-1">
                  {summary.total_interviewed}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
                <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Selected</p>
                <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">
                  {summary.total_selected}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
                <p className="text-xs font-medium text-rose-600 dark:text-rose-400">Rejected</p>
                <p className="text-2xl font-bold text-rose-700 dark:text-rose-300 mt-1">
                  {summary.total_rejected}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm bg-gradient-to-br from-indigo-50/50 to-white dark:from-gray-800 dark:to-gray-850">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Placement Rate</p>
                <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
                  {summary.selection_rate}%
                </p>
              </div>
            </div>

            {/* Breakdown Tables Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              {/* Tabs */}
              <div className="flex border-b border-gray-200 dark:border-gray-700 px-4 bg-gray-50/60 dark:bg-gray-800/60">
                <button
                  onClick={() => setActiveTab('company')}
                  className={`py-3 px-4 text-sm font-semibold border-b-2 transition ${
                    activeTab === 'company'
                      ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  Company-wise Breakdown ({report?.company_breakdown?.length || 0})
                </button>
                <button
                  onClick={() => setActiveTab('department')}
                  className={`py-3 px-4 text-sm font-semibold border-b-2 transition ${
                    activeTab === 'department'
                      ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  Department-wise Breakdown ({report?.department_breakdown?.length || 0})
                </button>
                <button
                  onClick={() => setActiveTab('batch')}
                  className={`py-3 px-4 text-sm font-semibold border-b-2 transition ${
                    activeTab === 'batch'
                      ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  Batch-wise Breakdown ({report?.batch_breakdown?.length || 0})
                </button>
              </div>

              {/* Table Content */}
              <div className="p-4 sm:p-6">
                {activeTab === 'company' && (
                  report?.company_breakdown?.length === 0 ? (
                    <div className="py-12 text-center text-sm text-gray-500 dark:text-gray-400">
                      No company records match the current filters.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 dark:bg-gray-900/40 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200 dark:border-gray-700">
                          <tr>
                            <th className="py-3 px-4">Company Name</th>
                            <th className="py-3 px-4 text-center">Applications</th>
                            <th className="py-3 px-4 text-center text-emerald-600">Selected</th>
                            <th className="py-3 px-4 text-center text-rose-600">Rejected</th>
                            <th className="py-3 px-4 text-right">Selection Rate</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                          {report?.company_breakdown?.map((item) => (
                            <tr key={item.company_id} className="hover:bg-gray-50/60 dark:hover:bg-gray-750 transition">
                              <td className="py-3.5 px-4 font-semibold text-gray-900 dark:text-white">
                                {item.company_name}
                              </td>
                              <td className="py-3.5 px-4 text-center font-medium text-gray-700 dark:text-gray-300">
                                {item.applications}
                              </td>
                              <td className="py-3.5 px-4 text-center font-semibold text-emerald-600 dark:text-emerald-400">
                                {item.selected}
                              </td>
                              <td className="py-3.5 px-4 text-center font-semibold text-rose-600 dark:text-rose-400">
                                {item.rejected}
                              </td>
                              <td className="py-3.5 px-4 text-right">
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300">
                                  {item.selection_rate}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
                )}

                {activeTab === 'department' && (
                  report?.department_breakdown?.length === 0 ? (
                    <div className="py-12 text-center text-sm text-gray-500 dark:text-gray-400">
                      No department records match the current filters.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 dark:bg-gray-900/40 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200 dark:border-gray-700">
                          <tr>
                            <th className="py-3 px-4">Department / Branch</th>
                            <th className="py-3 px-4 text-center">Applications</th>
                            <th className="py-3 px-4 text-center text-emerald-600">Selected</th>
                            <th className="py-3 px-4 text-center text-rose-600">Rejected</th>
                            <th className="py-3 px-4 text-right">Selection Rate</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                          {report?.department_breakdown?.map((item, idx) => (
                            <tr key={idx} className="hover:bg-gray-50/60 dark:hover:bg-gray-750 transition">
                              <td className="py-3.5 px-4 font-semibold text-gray-900 dark:text-white">
                                {item.department}
                              </td>
                              <td className="py-3.5 px-4 text-center font-medium text-gray-700 dark:text-gray-300">
                                {item.applications}
                              </td>
                              <td className="py-3.5 px-4 text-center font-semibold text-emerald-600 dark:text-emerald-400">
                                {item.selected}
                              </td>
                              <td className="py-3.5 px-4 text-center font-semibold text-rose-600 dark:text-rose-400">
                                {item.rejected}
                              </td>
                              <td className="py-3.5 px-4 text-right">
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300">
                                  {item.selection_rate}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
                )}

                {activeTab === 'batch' && (
                  report?.batch_breakdown?.length === 0 ? (
                    <div className="py-12 text-center text-sm text-gray-500 dark:text-gray-400">
                      No batch records match the current filters.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 dark:bg-gray-900/40 text-xs uppercase font-semibold text-gray-500 border-b border-gray-200 dark:border-gray-700">
                          <tr>
                            <th className="py-3 px-4">Graduating Batch Year</th>
                            <th className="py-3 px-4 text-center">Applications</th>
                            <th className="py-3 px-4 text-center text-emerald-600">Selected</th>
                            <th className="py-3 px-4 text-center text-rose-600">Rejected</th>
                            <th className="py-3 px-4 text-right">Selection Rate</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                          {report?.batch_breakdown?.map((item, idx) => (
                            <tr key={idx} className="hover:bg-gray-50/60 dark:hover:bg-gray-750 transition">
                              <td className="py-3.5 px-4 font-semibold text-gray-900 dark:text-white">
                                Batch of {item.batch}
                              </td>
                              <td className="py-3.5 px-4 text-center font-medium text-gray-700 dark:text-gray-300">
                                {item.applications}
                              </td>
                              <td className="py-3.5 px-4 text-center font-semibold text-emerald-600 dark:text-emerald-400">
                                {item.selected}
                              </td>
                              <td className="py-3.5 px-4 text-center font-semibold text-rose-600 dark:text-rose-400">
                                {item.rejected}
                              </td>
                              <td className="py-3.5 px-4 text-right">
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300">
                                  {item.selection_rate}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
