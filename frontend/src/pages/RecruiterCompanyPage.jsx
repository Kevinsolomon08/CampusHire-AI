// src/pages/RecruiterCompanyPage.jsx
// Recruiter company profile creation and management page.

import React, { useEffect, useState } from 'react'
import { getRecruiterProfile, updateCompany, createCompany } from '../api/recruiterApi'

export default function RecruiterCompanyPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [companyId, setCompanyId] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const [formData, setFormData] = useState({
    name: '',
    website: '',
    industry: 'Technology & Software',
    description: '',
    logo_url: '',
    contact_email: '',
    contact_phone: '',
    address: '',
  })

  useEffect(() => {
    fetchCompanyProfile()
  }, [])

  const fetchCompanyProfile = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getRecruiterProfile()
      if (res.success && res.data?.company) {
        const c = res.data.company
        setCompanyId(c.id)
        setFormData({
          name: c.name || '',
          website: c.website || '',
          industry: c.industry || 'Technology & Software',
          description: c.description || '',
          logo_url: c.logo_url || '',
          contact_email: c.contact_email || '',
          contact_phone: c.contact_phone || '',
          address: c.address || '',
        })
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load company profile.')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')

    if (!formData.name.trim()) {
      setErrorMessage('Company Name is required.')
      return
    }

    setSaving(true)
    try {
      let res
      if (companyId) {
        res = await updateCompany(companyId, formData)
      } else {
        res = await createCompany(formData)
        if (res.data?.id) setCompanyId(res.data.id)
      }

      if (res.success) {
        setSuccessMessage('Company profile saved successfully!')
        setTimeout(() => setSuccessMessage(''), 4000)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to save company profile.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-6 max-w-3xl">
        <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-1/3" />
        <div className="h-64 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 pb-5">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Company Profile
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Manage your organization details and public branding presented to student candidates during campus drives.
        </p>
      </div>

      {/* Alerts */}
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

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Company Legal / Brand Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="e.g. Acme Technologies Inc."
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Official Website
              </label>
              <input
                type="url"
                name="website"
                value={formData.website}
                onChange={handleChange}
                placeholder="https://company.com"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Industry Sector
              </label>
              <select
                name="industry"
                value={formData.industry}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              >
                <option value="Technology & Software">Technology & Software</option>
                <option value="Financial Services & Banking">Financial Services & Banking</option>
                <option value="E-Commerce & Retail">E-Commerce & Retail</option>
                <option value="Consulting & Analytics">Consulting & Analytics</option>
                <option value="Healthcare & BioTech">Healthcare & BioTech</option>
                <option value="Manufacturing & Automotive">Manufacturing & Automotive</option>
                <option value="Telecommunications">Telecommunications</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Recruitment Contact Email
              </label>
              <input
                type="email"
                name="contact_email"
                value={formData.contact_email}
                onChange={handleChange}
                placeholder="campus-hiring@company.com"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Contact Phone
              </label>
              <input
                type="tel"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleChange}
                placeholder="+91 80 1234 5678"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Logo URL (Square Image)
              </label>
              <input
                type="url"
                name="logo_url"
                value={formData.logo_url}
                onChange={handleChange}
                placeholder="https://company.com/logo.png"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                About the Company
              </label>
              <textarea
                name="description"
                rows={4}
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe your organization culture, engineering mission, and what students will work on..."
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Headquarters / Office Address
              </label>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="e.g. Outer Ring Road, Bellandur, Bengaluru, Karnataka 560103"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <>
                <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                Saving Company...
              </>
            ) : (
              'Save Company Profile'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
