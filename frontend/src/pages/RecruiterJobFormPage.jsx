// src/pages/RecruiterJobFormPage.jsx
// Comprehensive Job Creation & Editing form matching all specifications and criteria.

import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { createJob, getJobDetail, updateJob, publishJob } from '../api/recruiterApi'

const BRANCH_OPTIONS = [
  'Computer Science',
  'Information Technology',
  'Electronics & Communication',
  'Electrical & Electronics',
  'Mechanical Engineering',
  'Civil Engineering',
  'Data Science & AI',
]

export default function RecruiterJobFormPage() {
  const { id } = useParams()
  const isEditing = Boolean(id)
  const navigate = useNavigate()

  const [loading, setLoading] = useState(isEditing)
  const [saving, setSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  // Form State
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    employment_type: 'FULL_TIME',
    location: '',
    package_lpa: '',
    deadline: '',
    minimum_cgpa: '',
    maximum_backlogs: 0,
    eligible_batch: 2025,
    experience_requirement: 'Fresher (0 years)',
    allowed_branches: ['Computer Science', 'Information Technology'],
    required_skills: [],
    preferred_skills: [],
    requirements: [''],
    status: 'DRAFT',
  })

  const [reqSkillInput, setReqSkillInput] = useState('')
  const [prefSkillInput, setPrefSkillInput] = useState('')

  useEffect(() => {
    if (isEditing) {
      fetchJobDetails()
    }
  }, [id])

  const fetchJobDetails = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getJobDetail(id)
      if (res.success && res.data) {
        const j = res.data
        let deadlineFormatted = ''
        if (j.deadline) {
          const d = new Date(j.deadline)
          deadlineFormatted = d.toISOString().slice(0, 16)
        }

        setFormData({
          title: j.title || '',
          description: j.description || '',
          employment_type: j.employment_type || 'FULL_TIME',
          location: j.location || '',
          package_lpa: j.package_lpa !== null && j.package_lpa !== undefined ? j.package_lpa : '',
          deadline: deadlineFormatted,
          minimum_cgpa: j.min_cgpa !== null && j.min_cgpa !== undefined ? j.min_cgpa : '',
          maximum_backlogs: j.maximum_backlogs !== null && j.maximum_backlogs !== undefined ? j.maximum_backlogs : 0,
          eligible_batch: j.eligible_batch || 2025,
          experience_requirement: j.experience_requirement || 'Fresher (0 years)',
          allowed_branches: Array.isArray(j.allowed_branches) ? j.allowed_branches : ['Computer Science'],
          required_skills: Array.isArray(j.required_skills) ? j.required_skills : [],
          preferred_skills: Array.isArray(j.preferred_skills) ? j.preferred_skills : [],
          requirements: Array.isArray(j.requirements) && j.requirements.length > 0 ? j.requirements : [''],
          status: j.status || 'DRAFT',
        })
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to load job details.')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  // Branch checkbox toggle
  const handleBranchToggle = (branch) => {
    setFormData((prev) => {
      const exists = prev.allowed_branches.includes(branch)
      if (exists) {
        return { ...prev, allowed_branches: prev.allowed_branches.filter((b) => b !== branch) }
      } else {
        return { ...prev, allowed_branches: [...prev.allowed_branches, branch] }
      }
    })
  }

  // Skills tag handling
  const handleAddReqSkill = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      const val = reqSkillInput.trim().replace(/,$/, '')
      if (val && !formData.required_skills.includes(val)) {
        setFormData((prev) => ({ ...prev, required_skills: [...prev.required_skills, val] }))
        setReqSkillInput('')
      }
    }
  }

  const handleRemoveReqSkill = (skill) => {
    setFormData((prev) => ({
      ...prev,
      required_skills: prev.required_skills.filter((s) => s !== skill),
    }))
  }

  const handleAddPrefSkill = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      const val = prefSkillInput.trim().replace(/,$/, '')
      if (val && !formData.preferred_skills.includes(val)) {
        setFormData((prev) => ({ ...prev, preferred_skills: [...prev.preferred_skills, val] }))
        setPrefSkillInput('')
      }
    }
  }

  const handleRemovePrefSkill = (skill) => {
    setFormData((prev) => ({
      ...prev,
      preferred_skills: prev.preferred_skills.filter((s) => s !== skill),
    }))
  }

  // Requirements list handlers
  const handleReqChange = (idx, value) => {
    setFormData((prev) => {
      const updated = [...prev.requirements]
      updated[idx] = value
      return { ...prev, requirements: updated }
    })
  }

  const handleAddReqLine = () => {
    setFormData((prev) => ({ ...prev, requirements: [...prev.requirements, ''] }))
  }

  const handleRemoveReqLine = (idx) => {
    setFormData((prev) => ({
      ...prev,
      requirements: prev.requirements.filter((_, i) => i !== idx),
    }))
  }

  const handleSubmit = async (e, shouldPublish = false) => {
    if (e) e.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')

    if (!formData.title.trim()) {
      setErrorMessage('Role Title is required.')
      return
    }
    if (!formData.description.trim()) {
      setErrorMessage('Job Description is required.')
      return
    }

    const parsedCgpa = formData.minimum_cgpa === '' ? null : parseFloat(formData.minimum_cgpa)
    if (parsedCgpa !== null && (isNaN(parsedCgpa) || parsedCgpa < 0 || parsedCgpa > 10)) {
      setErrorMessage('Minimum CGPA must be between 0.0 and 10.0.')
      return
    }

    const parsedBacklogs = parseInt(formData.maximum_backlogs, 10)
    if (isNaN(parsedBacklogs) || parsedBacklogs < 0) {
      setErrorMessage('Maximum backlogs must be 0 or higher.')
      return
    }

    // If publishing, validate deadline is provided and in the future
    if (shouldPublish) {
      if (!formData.deadline) {
        setErrorMessage('Application deadline is required to publish a job.')
        return
      }
      const deadlineDate = new Date(formData.deadline)
      if (deadlineDate <= new Date()) {
        setErrorMessage('Application deadline must be set in the future.')
        return
      }
    }

    const payload = {
      title: formData.title,
      description: formData.description,
      employment_type: formData.employment_type,
      location: formData.location,
      package_lpa: formData.package_lpa === '' ? null : parseFloat(formData.package_lpa),
      deadline: formData.deadline ? new Date(formData.deadline).toISOString() : null,
      minimum_cgpa: parsedCgpa,
      maximum_backlogs: parsedBacklogs,
      eligible_batch: parseInt(formData.eligible_batch, 10),
      experience_requirement: formData.experience_requirement,
      allowed_branches: formData.allowed_branches,
      required_skills: formData.required_skills,
      preferred_skills: formData.preferred_skills,
      requirements: formData.requirements.filter((r) => r.trim().length > 0),
      status: shouldPublish ? 'OPEN' : formData.status,
    }

    setSaving(true)
    try {
      let res
      if (isEditing) {
        res = await updateJob(id, payload)
        if (shouldPublish && res.success) {
          await publishJob(id)
        }
      } else {
        res = await createJob(payload)
        if (shouldPublish && res.success && res.data?.id) {
          await publishJob(res.data.id)
        }
      }

      if (res.success) {
        setSuccessMessage(isEditing ? 'Job updated successfully!' : 'Job created successfully!')
        setTimeout(() => {
          navigate('/recruiter/jobs')
        }, 1200)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to save job.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-6 max-w-4xl">
        <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-1/3" />
        <div className="h-48 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
        <div className="h-48 bg-gray-200 dark:bg-gray-800 rounded-2xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-4">
        <div>
          <Link
            to="/recruiter/jobs"
            className="text-xs font-semibold text-gray-400 hover:text-indigo-600 transition"
          >
            ← Back to Job Postings
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {isEditing ? 'Edit Job Posting' : 'Create Campus Hiring Drive'}
          </h1>
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

      {/* Main Form */}
      <form className="space-y-8">
        {/* Section 1: Basic Role Info */}
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>💼</span> Role Details
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Job / Position Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                placeholder="e.g. Graduate Software Development Engineer (SDE-1)"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Employment Type
              </label>
              <select
                name="employment_type"
                value={formData.employment_type}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              >
                <option value="FULL_TIME">Full Time (Permanent)</option>
                <option value="INTERNSHIP">Internship</option>
                <option value="INTERN_TO_FTE">Intern to Full-Time</option>
                <option value="CONTRACT">Contract</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Location
              </label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g. Bengaluru, Hyderabad, or Remote"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Annual Package (CTC in LPA)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                name="package_lpa"
                value={formData.package_lpa}
                onChange={handleChange}
                placeholder="e.g. 18.5"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Application Deadline
              </label>
              <input
                type="datetime-local"
                name="deadline"
                value={formData.deadline}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Detailed Job Description *
              </label>
              <textarea
                name="description"
                rows={4}
                value={formData.description}
                onChange={handleChange}
                required
                placeholder="Overview of the engineering challenges, tech stack, day-to-day responsibilities..."
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Academic Eligibility Criteria */}
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>🎯</span> Strict Eligibility Filters (Automated by CampusHire)
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            These rules are strictly evaluated by the eligibility engine. Ineligible students cannot apply.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Minimum CGPA (0-10)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="10"
                name="minimum_cgpa"
                value={formData.minimum_cgpa}
                onChange={handleChange}
                placeholder="e.g. 7.50"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Maximum Allowed Backlogs
              </label>
              <input
                type="number"
                min="0"
                name="maximum_backlogs"
                value={formData.maximum_backlogs}
                onChange={handleChange}
                placeholder="0"
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
                Eligible Graduating Batch
              </label>
              <select
                name="eligible_batch"
                value={formData.eligible_batch}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              >
                <option value={2024}>2024</option>
                <option value={2025}>2025</option>
                <option value={2026}>2026</option>
                <option value={2027}>2027</option>
              </select>
            </div>
          </div>

          {/* Allowed Branches multi-select */}
          <div className="pt-3">
            <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-2">
              Allowed Engineering Branches
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {BRANCH_OPTIONS.map((branch) => {
                const checked = formData.allowed_branches.includes(branch)
                return (
                  <label
                    key={branch}
                    className={`flex items-center gap-2 p-2.5 rounded-lg border text-xs cursor-pointer transition ${
                      checked
                        ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 font-semibold'
                        : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => handleBranchToggle(branch)}
                      className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                    />
                    <span>{branch}</span>
                  </label>
                )
              })}
            </div>
          </div>
        </div>

        {/* Section 3: Technical Skills & Requirements */}
        <div className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>⚡</span> Skills & Candidate Requirements
          </h2>

          {/* Required Skills */}
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
              Required Skills (Must have — Press Enter to add)
            </label>
            <input
              type="text"
              value={reqSkillInput}
              onChange={(e) => setReqSkillInput(e.target.value)}
              onKeyDown={handleAddReqSkill}
              placeholder="e.g. Python, React, SQL..."
              className="w-full px-3.5 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex flex-wrap gap-1.5 mt-2">
              {formData.required_skills.map((s) => (
                <span
                  key={s}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                >
                  {s}
                  <button
                    type="button"
                    onClick={() => handleRemoveReqSkill(s)}
                    className="hover:text-rose-600 font-bold ml-1"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Preferred Skills */}
          <div>
            <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300 mb-1">
              Preferred / Nice to Have Skills
            </label>
            <input
              type="text"
              value={prefSkillInput}
              onChange={(e) => setPrefSkillInput(e.target.value)}
              onKeyDown={handleAddPrefSkill}
              placeholder="e.g. AWS, Docker, Kubernetes..."
              className="w-full px-3.5 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex flex-wrap gap-1.5 mt-2">
              {formData.preferred_skills.map((s) => (
                <span
                  key={s}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                >
                  {s}
                  <button
                    type="button"
                    onClick={() => handleRemovePrefSkill(s)}
                    className="hover:text-rose-600 font-bold ml-1"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Requirements list */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-semibold uppercase text-gray-600 dark:text-gray-300">
                Key Requirements & Qualifications
              </label>
              <button
                type="button"
                onClick={handleAddReqLine}
                className="text-xs font-bold text-indigo-600 hover:underline"
              >
                + Add Requirement Bullet
              </button>
            </div>
            {formData.requirements.map((req, idx) => (
              <div key={idx} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={req}
                  onChange={(e) => handleReqChange(idx, e.target.value)}
                  placeholder={`Requirement #${idx + 1}...`}
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs"
                />
                {formData.requirements.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveReqLine(idx)}
                    className="px-2 text-rose-500 hover:text-rose-700 text-sm font-bold"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Link
            to="/recruiter/jobs"
            className="px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
          >
            Cancel
          </Link>

          <button
            type="button"
            disabled={saving}
            onClick={(e) => handleSubmit(e, false)}
            className="px-6 py-2.5 rounded-xl border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 hover:bg-indigo-100 text-sm font-semibold transition disabled:opacity-50"
          >
            Save as Draft
          </button>

          <button
            type="button"
            disabled={saving}
            onClick={(e) => handleSubmit(e, true)}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <>
                <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                Saving Job...
              </>
            ) : (
              'Publish Opening Now'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
