// src/pages/StudentProfilePage.jsx
// Comprehensive Student Profile management page with completion tracking and validation.

import React, { useEffect, useState } from 'react'
import { getStudentProfile, updateStudentProfile } from '../api/studentApi'

export default function StudentProfilePage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    roll_number: '',
    department: 'Computer Science',
    batch: 2025,
    cgpa: '',
    backlog_count: 0,
    phone: '',
    linkedin_url: '',
    skills: [],
    education: [{ degree: 'B.Tech / B.E.', institution: '', year: 2025, score: '' }],
    experience: [],
    projects: [],
    certifications: [],
  })

  const [skillInput, setSkillInput] = useState('')
  const [completionPct, setCompletionPct] = useState(0)

  // Fetch initial profile
  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getStudentProfile()
      if (res.success && res.data) {
        const d = res.data
        setFormData({
          name: d.name || '',
          email: d.email || '',
          roll_number: d.roll_number || '',
          department: d.department || 'Computer Science',
          batch: d.batch || 2025,
          cgpa: d.cgpa !== null && d.cgpa !== undefined ? d.cgpa : '',
          backlog_count: d.backlog_count !== null && d.backlog_count !== undefined ? d.backlog_count : 0,
          phone: d.phone || '',
          linkedin_url: d.linkedin_url || '',
          skills: Array.isArray(d.skills) ? d.skills : [],
          education: Array.isArray(d.education) && d.education.length > 0 ? d.education : [{ degree: 'B.Tech / B.E.', institution: '', year: 2025, score: '' }],
          experience: Array.isArray(d.experience) ? d.experience : [],
          projects: Array.isArray(d.projects) ? d.projects : [],
          certifications: Array.isArray(d.certifications) ? d.certifications : [],
        })
        setCompletionPct(d.profile_completion_pct || 0)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load profile.')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  // Skills tag manager
  const handleAddSkill = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      const trimmed = skillInput.trim().replace(/,$/, '')
      if (trimmed && !formData.skills.includes(trimmed)) {
        setFormData((prev) => ({ ...prev, skills: [...prev.skills, trimmed] }))
        setSkillInput('')
      }
    }
  }

  const handleRemoveSkill = (skillToRemove) => {
    setFormData((prev) => ({
      ...prev,
      skills: prev.skills.filter((s) => s !== skillToRemove),
    }))
  }

  // Array handlers (Education, Experience, Projects)
  const addEducation = () => {
    setFormData((prev) => ({
      ...prev,
      education: [...prev.education, { degree: '', institution: '', year: 2025, score: '' }],
    }))
  }

  const updateEducation = (index, field, value) => {
    setFormData((prev) => {
      const updated = [...prev.education]
      updated[index] = { ...updated[index], [field]: value }
      return { ...prev, education: updated }
    })
  }

  const removeEducation = (index) => {
    setFormData((prev) => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== index),
    }))
  }

  const addProject = () => {
    setFormData((prev) => ({
      ...prev,
      projects: [...prev.projects, { title: '', tech_stack: '', description: '', link: '' }],
    }))
  }

  const updateProject = (index, field, value) => {
    setFormData((prev) => {
      const updated = [...prev.projects]
      updated[index] = { ...updated[index], [field]: value }
      return { ...prev, projects: updated }
    })
  }

  const removeProject = (index) => {
    setFormData((prev) => ({
      ...prev,
      projects: prev.projects.filter((_, i) => i !== index),
    }))
  }

  // Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')

    // Client-side validations
    const parsedCgpa = formData.cgpa === '' ? null : parseFloat(formData.cgpa)
    if (parsedCgpa !== null && (isNaN(parsedCgpa) || parsedCgpa < 0 || parsedCgpa > 10)) {
      setErrorMessage('CGPA must be a valid number between 0.0 and 10.0.')
      return
    }

    const parsedBacklogs = parseInt(formData.backlog_count, 10)
    if (isNaN(parsedBacklogs) || parsedBacklogs < 0) {
      setErrorMessage('Backlog count must be 0 or higher.')
      return
    }

    const payload = {
      full_name: formData.name,
      roll_number: formData.roll_number,
      department: formData.department,
      batch: parseInt(formData.batch, 10),
      cgpa: parsedCgpa,
      backlog_count: parsedBacklogs,
      phone: formData.phone,
      linkedin_url: formData.linkedin_url,
      skills: formData.skills,
      education: formData.education,
      experience: formData.experience,
      projects: formData.projects,
      certifications: formData.certifications,
    }

    setSaving(true)
    try {
      const res = await updateStudentProfile(payload)
      if (res.success) {
        setSuccessMessage('Profile updated successfully!')
        if (res.data?.profile_completion_pct !== undefined) {
          setCompletionPct(res.data.profile_completion_pct)
        }
        setTimeout(() => setSuccessMessage(''), 4000)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-1/3" />
        <div className="h-24 bg-gray-200 dark:bg-gray-800 rounded-xl" />
        <div className="grid grid-cols-2 gap-4">
          <div className="h-12 bg-gray-200 dark:bg-gray-800 rounded" />
          <div className="h-12 bg-gray-200 dark:bg-gray-800 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header & Completion Card */}
      <div className="border-b border-gray-200 dark:border-gray-800 pb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          My Student Profile
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Keep your academic and professional profile updated to qualify for top job opportunities.
        </p>

        {/* Profile Completion Bar */}
        <div className="mt-6 bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/50 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">
              Profile Completion Status
            </span>
            <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
              {completionPct}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 h-2.5 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                completionPct >= 80
                  ? 'bg-emerald-500'
                  : completionPct >= 50
                  ? 'bg-indigo-600'
                  : 'bg-amber-500'
              }`}
              style={{ width: `${completionPct}%` }}
            />
          </div>
          <p className="text-xs text-indigo-700/80 dark:text-indigo-300/80 mt-2">
            {completionPct === 100
              ? '🎉 Excellent! Your profile is 100% complete and ready for recruiters.'
              : 'Tip: Add CGPA, department, skills, and upload your resume to reach 100%.'}
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

      {/* Profile Form */}
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Basic Information */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>👤</span> Personal Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Full Name
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Email (Read-only)
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                disabled
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900/60 text-gray-500 text-sm cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Roll / Student ID Number
              </label>
              <input
                type="text"
                name="roll_number"
                value={formData.roll_number}
                onChange={handleChange}
                required
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+91 9876543210"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                LinkedIn Profile URL
              </label>
              <input
                type="url"
                name="linkedin_url"
                value={formData.linkedin_url}
                onChange={handleChange}
                placeholder="https://linkedin.com/in/yourname"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Academic Eligibility Fields */}
        <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>🎓</span> Academic & Placement Criteria
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Department / Branch
              </label>
              <select
                name="department"
                value={formData.department}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              >
                <option value="Computer Science">Computer Science (CSE)</option>
                <option value="Information Technology">Information Technology (IT)</option>
                <option value="Electronics & Communication">Electronics & Communication (ECE)</option>
                <option value="Electrical & Electronics">Electrical & Electronics (EEE)</option>
                <option value="Mechanical Engineering">Mechanical Engineering (MECH)</option>
                <option value="Civil Engineering">Civil Engineering (CIVIL)</option>
                <option value="Data Science & AI">Data Science & AI</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Graduating Batch (Year)
              </label>
              <select
                name="batch"
                value={formData.batch}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              >
                <option value={2024}>2024</option>
                <option value={2025}>2025</option>
                <option value={2026}>2026</option>
                <option value={2027}>2027</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                CGPA (0.00 - 10.00)
              </label>
              <input
                type="number"
                name="cgpa"
                step="0.01"
                min="0"
                max="10"
                value={formData.cgpa}
                onChange={handleChange}
                placeholder="e.g. 8.75"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Active Backlogs Count
              </label>
              <input
                type="number"
                name="backlog_count"
                min="0"
                value={formData.backlog_count}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Technical Skills */}
        <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>⚡</span> Technical Skills
          </h2>
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
              Add Skills (Type and press Enter)
            </label>
            <input
              type="text"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={handleAddSkill}
              placeholder="e.g. React, Python, Docker, SQL..."
              className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex flex-wrap gap-2 mt-3">
              {formData.skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(skill)}
                    className="hover:text-rose-600 font-bold ml-1"
                  >
                    ×
                  </button>
                </span>
              ))}
              {formData.skills.length === 0 && (
                <span className="text-xs text-gray-400">No skills added yet.</span>
              )}
            </div>
          </div>
        </div>

        {/* Section 4: Projects */}
        <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <span>🚀</span> Key Projects
            </h2>
            <button
              type="button"
              onClick={addProject}
              className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              + Add Project
            </button>
          </div>
          {formData.projects.map((proj, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/60 dark:bg-gray-800/40 space-y-3"
            >
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-gray-500 uppercase">Project #{idx + 1}</span>
                <button
                  type="button"
                  onClick={() => removeProject(idx)}
                  className="text-xs text-rose-500 hover:underline"
                >
                  Remove
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Project Title"
                  value={proj.title || ''}
                  onChange={(e) => updateProject(idx, 'title', e.target.value)}
                  className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                />
                <input
                  type="text"
                  placeholder="Tech Stack (e.g. React, FastAPI)"
                  value={proj.tech_stack || ''}
                  onChange={(e) => updateProject(idx, 'tech_stack', e.target.value)}
                  className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
                />
              </div>
              <textarea
                rows={2}
                placeholder="Brief description of what you built and achieved..."
                value={proj.description || ''}
                onChange={(e) => updateProject(idx, 'description', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              />
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="pt-6 border-t border-gray-200 dark:border-gray-800 flex justify-end gap-4">
          <button
            type="button"
            onClick={fetchProfile}
            className="px-5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
          >
            Reset
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <>
                <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                Saving Profile...
              </>
            ) : (
              'Save Profile Changes'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
