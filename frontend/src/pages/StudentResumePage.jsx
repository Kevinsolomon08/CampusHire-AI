// src/pages/StudentResumePage.jsx
// Comprehensive Student Resume Management with AI Parsing review and editing.

import React, { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  getParsedResume,
  getStudentResume,
  triggerResumeParse,
  updateStudentProfile,
  uploadResume,
} from '../api/studentApi'

export default function StudentResumePage() {
  const navigate = useNavigate()
  const [currentResume, setCurrentResume] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [savingProfile, setSavingProfile] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [profileSavedMessage, setProfileSavedMessage] = useState('')

  // Parsed Resume Review State
  const [parsedDataAvailable, setParsedDataAvailable] = useState(false)
  const [activeTab, setActiveTab] = useState('skills')
  const [skills, setSkills] = useState([])
  const [newSkill, setNewSkill] = useState('')
  const [educationList, setEducationList] = useState([])
  const [experienceList, setExperienceList] = useState([])
  const [projectList, setProjectList] = useState([])
  const [certList, setCertList] = useState([])
  const [personalInfo, setPersonalInfo] = useState({ name: '', email: '', phone: '' })

  const fileInputRef = useRef(null)

  useEffect(() => {
    loadResumeAndParsedData()
  }, [])

  const loadResumeAndParsedData = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getStudentResume()
      if (res.success && res.data) {
        setCurrentResume(res.data)
        if (res.data.parsed_data && res.data.parsing_status === 'success') {
          populateParsedState(res.data.parsed_data)
        } else if (res.data.parsing_status === 'success') {
          // Fetch from /students/me/parsed-resume if not in resume payload
          await fetchParsedResume()
        }
      } else {
        setCurrentResume(null)
        setParsedDataAvailable(false)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to fetch resume status.')
    } finally {
      setLoading(false)
    }
  }

  const fetchParsedResume = async () => {
    try {
      const parseRes = await getParsedResume()
      if (parseRes.success && parseRes.data?.parsed_data) {
        populateParsedState(parseRes.data.parsed_data)
      }
    } catch (err) {
      // Ignored if parsed data isn't ready
    }
  }

  const populateParsedState = (data) => {
    if (!data) return
    setParsedDataAvailable(true)

    // Skills
    if (Array.isArray(data.skills)) {
      setSkills(data.skills)
    }

    // Education
    if (Array.isArray(data.education)) {
      setEducationList(
        data.education.map((edu) => ({
          degree: edu.degree || '',
          institution: edu.institution || '',
          year: edu.year || 2025,
          score: edu.score || '',
        }))
      )
    }

    // Experience
    if (Array.isArray(data.experience)) {
      setExperienceList(
        data.experience.map((exp) => ({
          role: exp.role || '',
          company: exp.company || '',
          duration: exp.duration || '',
          description: exp.description || '',
        }))
      )
    }

    // Projects
    if (Array.isArray(data.projects)) {
      setProjectList(
        data.projects.map((proj) => ({
          title: proj.title || '',
          tech_stack: Array.isArray(proj.technologies)
            ? proj.technologies.join(', ')
            : proj.tech_stack || '',
          description: proj.description || '',
          link: proj.link || '',
        }))
      )
    }

    // Certifications
    if (Array.isArray(data.certifications)) {
      setCertList(
        data.certifications.map((cert) => {
          if (typeof cert === 'string') {
            return { name: cert, issuer: '' }
          }
          return {
            name: cert.name || '',
            issuer: cert.issuer || '',
          }
        })
      )
    }

    // Personal Info
    if (data.personal_info) {
      setPersonalInfo({
        name: data.personal_info.name || '',
        email: data.personal_info.email || '',
        phone: data.personal_info.phone || '',
      })
    }
  }

  const validateFile = (file) => {
    if (!file) return false

    // Validate type
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setErrorMessage('Invalid file format. Please upload a PDF file only (.pdf).')
      return false
    }

    // Validate size (5MB)
    const maxBytes = 5 * 1024 * 1024
    if (file.size > maxBytes) {
      setErrorMessage(
        `File is too large (${(file.size / (1024 * 1024)).toFixed(2)} MB). Max limit is 5MB.`
      )
      return false
    }

    if (file.size === 0) {
      setErrorMessage('Uploaded file is empty. Please choose a valid PDF file.')
      return false
    }

    return true
  }

  const handleFileSelect = (file) => {
    setErrorMessage('')
    setSuccessMessage('')
    setProfileSavedMessage('')
    if (validateFile(file)) {
      setSelectedFile(file)
    } else {
      setSelectedFile(null)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploading(true)
    setErrorMessage('')
    setSuccessMessage('')
    setProfileSavedMessage('')

    try {
      const res = await uploadResume(selectedFile)
      if (res.success && res.data) {
        setCurrentResume(res.data)
        setSelectedFile(null)
        if (fileInputRef.current) fileInputRef.current.value = ''

        if (res.data.parsing_status === 'success') {
          setSuccessMessage('Resume uploaded and parsed successfully!')
          if (res.data.parsed_data) {
            populateParsedState(res.data.parsed_data)
          } else {
            await fetchParsedResume()
          }
        } else if (res.data.parsing_status === 'failed') {
          setSuccessMessage(
            'Resume uploaded successfully. Automatic parsing was unavailable — you can enter your details manually.'
          )
          setParsedDataAvailable(false)
        } else {
          setSuccessMessage('Resume uploaded successfully!')
        }
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to upload resume.')
    } finally {
      setUploading(false)
    }
  }

  const handleRetryParse = async () => {
    if (!currentResume?.id) return
    setParsing(true)
    setErrorMessage('')
    setSuccessMessage('')
    try {
      const res = await triggerResumeParse(currentResume.id)
      if (res.success && res.data) {
        setCurrentResume((prev) => ({
          ...prev,
          parsing_status: res.data.parsing_status,
          parsed_data: res.data.parsed_data,
        }))
        if (res.data.parsing_status === 'success') {
          setSuccessMessage('Resume parsed successfully!')
          populateParsedState(res.data.parsed_data)
        } else {
          setErrorMessage(
            'Unable to extract text automatically. Please update your profile manually.'
          )
        }
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to parse resume.')
    } finally {
      setParsing(false)
    }
  }

  // --- Skills Editing ---
  const handleAddSkill = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      const trimmed = newSkill.trim().replace(/,$/, '')
      if (trimmed && !skills.includes(trimmed)) {
        setSkills([...skills, trimmed])
        setNewSkill('')
      }
    }
  }

  const handleAddSkillClick = () => {
    const trimmed = newSkill.trim().replace(/,$/, '')
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed])
      setNewSkill('')
    }
  }

  const handleRemoveSkill = (skillToRemove) => {
    setSkills(skills.filter((s) => s !== skillToRemove))
  }

  // --- Education Editing ---
  const handleAddEducation = () => {
    setEducationList([
      ...educationList,
      { degree: '', institution: '', year: 2025, score: '' },
    ])
  }

  const handleUpdateEducation = (index, field, value) => {
    setEducationList((prev) => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const handleRemoveEducation = (index) => {
    setEducationList((prev) => prev.filter((_, i) => i !== index))
  }

  // --- Experience Editing ---
  const handleAddExperience = () => {
    setExperienceList([
      ...experienceList,
      { role: '', company: '', duration: '', description: '' },
    ])
  }

  const handleUpdateExperience = (index, field, value) => {
    setExperienceList((prev) => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const handleRemoveExperience = (index) => {
    setExperienceList((prev) => prev.filter((_, i) => i !== index))
  }

  // --- Projects Editing ---
  const handleAddProject = () => {
    setProjectList([
      ...projectList,
      { title: '', tech_stack: '', description: '', link: '' },
    ])
  }

  const handleUpdateProject = (index, field, value) => {
    setProjectList((prev) => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const handleRemoveProject = (index) => {
    setProjectList((prev) => prev.filter((_, i) => i !== index))
  }

  // --- Certifications Editing ---
  const handleAddCert = () => {
    setCertList([...certList, { name: '', issuer: '' }])
  }

  const handleUpdateCert = (index, field, value) => {
    setCertList((prev) => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const handleRemoveCert = (index) => {
    setCertList((prev) => prev.filter((_, i) => i !== index))
  }

  // --- Save Extracted Data to Student Profile ---
  const handleSaveToProfile = async () => {
    setSavingProfile(true)
    setErrorMessage('')
    setProfileSavedMessage('')

    try {
      const payload = {
        skills,
        education: educationList,
        experience: experienceList,
        projects: projectList,
        certifications: certList,
      }
      if (personalInfo.phone) {
        payload.phone = personalInfo.phone
      }

      const res = await updateStudentProfile(payload)
      if (res.success) {
        setProfileSavedMessage(
          'Extracted information has been successfully saved to your Profile!'
        )
      }
    } catch (err) {
      setErrorMessage(
        err.response?.data?.message || 'Failed to save information to profile.'
      )
    } finally {
      setSavingProfile(false)
    }
  }

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Resume Management
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Upload your PDF resume. Our AI automatically extracts skills, education, and experience to populate your profile.
          </p>
        </div>
        <Link
          to="/student/profile"
          className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 rounded-lg transition self-start sm:self-auto"
        >
          <span>View Full Profile</span>
          <span>→</span>
        </Link>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
          ✓ {successMessage}
        </div>
      )}
      {profileSavedMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300 flex items-center justify-between">
          <span>✓ {profileSavedMessage}</span>
          <Link
            to="/student/profile"
            className="underline font-bold text-emerald-900 dark:text-emerald-200 text-xs ml-4"
          >
            Review Profile →
          </Link>
        </div>
      )}
      {errorMessage && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          ⚠️ {errorMessage}
        </div>
      )}

      {/* Current Active Resume Card */}
      <div className="rounded-2xl border border-gray-200 dark:border-gray-800 p-6 bg-white dark:bg-gray-900 shadow-sm">
        <h2 className="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span>📄</span> Current Active Resume
          </span>
          {currentResume ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              Active Primary
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
              No Resume Uploaded
            </span>
          )}
        </h2>

        {loading ? (
          <div className="animate-pulse flex items-center space-x-4 py-4">
            <div className="rounded-xl bg-gray-200 dark:bg-gray-800 h-12 w-12" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/4" />
            </div>
          </div>
        ) : currentResume ? (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-700/60 gap-4">
              <div className="flex items-center space-x-3.5">
                <div className="h-10 w-10 rounded-lg bg-red-100 dark:bg-red-950/60 flex items-center justify-center text-red-600 dark:text-red-400 font-bold text-xs uppercase">
                  PDF
                </div>
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                    {currentResume.filename}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    Uploaded on {formatDate(currentResume.uploaded_at)}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-3.5 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  Replace Resume
                </button>
                <button
                  disabled={parsing}
                  onClick={handleRetryParse}
                  className="px-3.5 py-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/80 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition disabled:opacity-50"
                >
                  {parsing ? 'Parsing...' : 'Re-parse with AI'}
                </button>
              </div>
            </div>

            {/* AI Status Badge */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-50/70 to-purple-50/70 dark:from-indigo-950/30 dark:to-purple-950/30 border border-indigo-100 dark:border-indigo-900/50">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm">✨</span>
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-800 dark:text-indigo-300">
                    AI Resume Parsing Status
                  </span>
                </div>
                {currentResume.parsing_status === 'success' ? (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 flex items-center gap-1">
                    <span>✓</span> Extracted & Ready
                  </span>
                ) : currentResume.parsing_status === 'failed' ? (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 flex items-center gap-1">
                    <span>⚠️</span> Extraction Incomplete
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 flex items-center gap-1">
                    <span>🔄</span> Pending
                  </span>
                )}
              </div>

              {currentResume.parsing_status === 'failed' && (
                <div className="mt-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 text-xs text-amber-900 dark:text-amber-200 space-y-2">
                  <p>
                    We couldn't automatically read all text from this PDF (e.g. it may be a scanned image or non-standard format). No problem — your resume file is safely saved, and you can fill in your details manually.
                  </p>
                  <div className="flex items-center gap-3">
                    <Link
                      to="/student/profile"
                      className="font-bold underline text-amber-900 dark:text-amber-100 hover:text-indigo-600"
                    >
                      Go to Profile & Enter Manually →
                    </Link>
                    <button
                      onClick={handleRetryParse}
                      disabled={parsing}
                      className="text-xs font-semibold text-indigo-700 dark:text-indigo-300 underline"
                    >
                      Retry Parse
                    </button>
                  </div>
                </div>
              )}

              {currentResume.parsing_status === 'success' && (
                <p className="text-xs text-gray-600 dark:text-gray-300 mt-2">
                  Skills, education, and project details were successfully extracted. Review and edit the extracted information below before saving to your profile.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-sm text-gray-500 dark:text-gray-400">
            You have not uploaded a resume yet. Upload one below to qualify for campus hiring drives.
          </div>
        )}
      </div>

      {/* Upload Drop Zone */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <span>📤</span> Upload New / Updated Resume
        </h2>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
            dragActive
              ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/30'
              : 'border-gray-300 dark:border-gray-700 hover:border-indigo-400 dark:hover:border-indigo-500 bg-white dark:bg-gray-900'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelect(e.target.files[0])
              }
            }}
          />

          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 mb-4 text-2xl">
            📄
          </div>

          <div className="text-sm font-semibold text-gray-900 dark:text-white">
            {selectedFile ? selectedFile.name : 'Click to upload or drag & drop your PDF'}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Standard PDF documents only. Maximum file size: 5MB.
          </p>

          {selectedFile && (
            <div className="mt-3 inline-block text-xs font-semibold px-2.5 py-1 bg-indigo-100 text-indigo-800 dark:bg-indigo-950/80 dark:text-indigo-300 rounded-md">
              Selected: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </div>
          )}
        </div>

        {/* Upload Action */}
        {selectedFile && (
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setSelectedFile(null)
                if (fileInputRef.current) fileInputRef.current.value = ''
              }}
              className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 font-medium"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={uploading}
              onClick={handleUpload}
              className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition disabled:opacity-50 flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  Uploading & Parsing with AI...
                </>
              ) : (
                'Upload & Parse Resume'
              )}
            </button>
          </div>
        )}
      </div>

      {/* Review Extracted Information Section */}
      {parsedDataAvailable && (
        <div className="rounded-2xl border border-indigo-200 dark:border-indigo-900/60 p-6 bg-white dark:bg-gray-900 shadow-md space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg">🤖</span>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                  Review Extracted Information
                </h2>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Auto-extracted from your resume — please review and correct anything inaccurate before saving to your profile.
              </p>
            </div>

            <button
              type="button"
              disabled={savingProfile}
              onClick={handleSaveToProfile}
              className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow transition disabled:opacity-50 flex items-center gap-2 self-start sm:self-auto"
            >
              {savingProfile ? (
                <>
                  <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  Saving to Profile...
                </>
              ) : (
                <>
                  <span>✓</span>
                  <span>Save to Profile</span>
                </>
              )}
            </button>
          </div>

          {/* Personal Info Quick Summary */}
          {(personalInfo.name || personalInfo.email || personalInfo.phone) && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200/60 dark:border-gray-700/60 text-xs">
              <div>
                <span className="text-gray-500 dark:text-gray-400 block font-medium">Extracted Name:</span>
                <span className="font-semibold text-gray-800 dark:text-gray-200">
                  {personalInfo.name || 'Not detected'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400 block font-medium">Extracted Email:</span>
                <span className="font-semibold text-gray-800 dark:text-gray-200">
                  {personalInfo.email || 'Not detected'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400 block font-medium">Extracted Phone:</span>
                <span className="font-semibold text-gray-800 dark:text-gray-200">
                  {personalInfo.phone || 'Not detected'}
                </span>
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex border-b border-gray-200 dark:border-gray-800 space-x-1 overflow-x-auto">
            <button
              type="button"
              onClick={() => setActiveTab('skills')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition whitespace-nowrap ${
                activeTab === 'skills'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/40'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              🛠️ Skills ({skills.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('education')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition whitespace-nowrap ${
                activeTab === 'education'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/40'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              🎓 Education ({educationList.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('experience')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition whitespace-nowrap ${
                activeTab === 'experience'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/40'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              💼 Experience ({experienceList.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('projects')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition whitespace-nowrap ${
                activeTab === 'projects'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/40'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              🚀 Projects ({projectList.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('certifications')}
              className={`px-4 py-2.5 text-xs font-semibold rounded-t-lg transition whitespace-nowrap ${
                activeTab === 'certifications'
                  ? 'border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-950/40'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              📜 Certifications ({certList.length})
            </button>
          </div>

          {/* Tab 1: Skills Tab */}
          {activeTab === 'skills' && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Extracted & Editable Skills
                </label>
                <span className="text-xs text-gray-400">
                  Type a skill and press Enter or comma
                </span>
              </div>

              {/* Skills Tag Area */}
              <div className="flex flex-wrap gap-2 p-3 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-200 dark:border-gray-700 min-h-[60px] items-center">
                {skills.length === 0 ? (
                  <span className="text-xs text-gray-400 italic">
                    No skills added yet. Add skills below.
                  </span>
                ) : (
                  skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-950/80 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                    >
                      {skill}
                      <button
                        type="button"
                        onClick={() => handleRemoveSkill(skill)}
                        className="h-3.5 w-3.5 rounded-full hover:bg-indigo-200 dark:hover:bg-indigo-800 flex items-center justify-center text-[10px] text-indigo-600 dark:text-indigo-300"
                      >
                        ✕
                      </button>
                    </span>
                  ))
                )}
              </div>

              {/* Add Skill Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add skill (e.g. Python, React, PostgreSQL)..."
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={handleAddSkill}
                  className="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3.5 py-2 text-xs text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  type="button"
                  onClick={handleAddSkillClick}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition"
                >
                  Add Skill
                </button>
              </div>
            </div>
          )}

          {/* Tab 2: Education Tab */}
          {activeTab === 'education' && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Extracted Education Records
                </label>
                <button
                  type="button"
                  onClick={handleAddEducation}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  + Add Education Record
                </button>
              </div>

              {educationList.length === 0 ? (
                <div className="text-center py-6 text-xs text-gray-400 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                  No education records found. Click "+ Add Education Record" to add manually.
                </div>
              ) : (
                educationList.map((edu, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/40 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                        Record #{idx + 1}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveEducation(idx)}
                        className="text-xs text-red-500 hover:text-red-700 font-medium"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Degree / Program
                        </label>
                        <input
                          type="text"
                          value={edu.degree}
                          onChange={(e) =>
                            handleUpdateEducation(idx, 'degree', e.target.value)
                          }
                          placeholder="e.g. B.Tech Computer Science"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Institution / University
                        </label>
                        <input
                          type="text"
                          value={edu.institution}
                          onChange={(e) =>
                            handleUpdateEducation(idx, 'institution', e.target.value)
                          }
                          placeholder="e.g. Stanford University"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Graduation Year
                        </label>
                        <input
                          type="number"
                          value={edu.year || ''}
                          onChange={(e) =>
                            handleUpdateEducation(
                              idx,
                              'year',
                              parseInt(e.target.value, 10) || ''
                            )
                          }
                          placeholder="2025"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Score / CGPA / %
                        </label>
                        <input
                          type="text"
                          value={edu.score || ''}
                          onChange={(e) =>
                            handleUpdateEducation(idx, 'score', e.target.value)
                          }
                          placeholder="e.g. 8.8 CGPA or 85%"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Tab 3: Experience Tab */}
          {activeTab === 'experience' && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Extracted Work & Internship Experience
                </label>
                <button
                  type="button"
                  onClick={handleAddExperience}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  + Add Experience Record
                </button>
              </div>

              {experienceList.length === 0 ? (
                <div className="text-center py-6 text-xs text-gray-400 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                  No work experience extracted. Click "+ Add Experience Record" to add manually.
                </div>
              ) : (
                experienceList.map((exp, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/40 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                        Experience #{idx + 1}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveExperience(idx)}
                        className="text-xs text-red-500 hover:text-red-700 font-medium"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Role / Title
                        </label>
                        <input
                          type="text"
                          value={exp.role}
                          onChange={(e) =>
                            handleUpdateExperience(idx, 'role', e.target.value)
                          }
                          placeholder="e.g. Software Engineering Intern"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Company / Organization
                        </label>
                        <input
                          type="text"
                          value={exp.company}
                          onChange={(e) =>
                            handleUpdateExperience(idx, 'company', e.target.value)
                          }
                          placeholder="e.g. Google"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Duration
                        </label>
                        <input
                          type="text"
                          value={exp.duration}
                          onChange={(e) =>
                            handleUpdateExperience(idx, 'duration', e.target.value)
                          }
                          placeholder="e.g. Jun 2024 - Aug 2024"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                        Description & Responsibilities
                      </label>
                      <textarea
                        rows={2}
                        value={exp.description}
                        onChange={(e) =>
                          handleUpdateExperience(idx, 'description', e.target.value)
                        }
                        placeholder="Built real-time data ingestion pipelines using Python and Kafka..."
                        className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Tab 4: Projects Tab */}
          {activeTab === 'projects' && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Extracted Projects
                </label>
                <button
                  type="button"
                  onClick={handleAddProject}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  + Add Project
                </button>
              </div>

              {projectList.length === 0 ? (
                <div className="text-center py-6 text-xs text-gray-400 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                  No projects extracted. Click "+ Add Project" to add your showcase projects.
                </div>
              ) : (
                projectList.map((proj, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/40 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                        Project #{idx + 1}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveProject(idx)}
                        className="text-xs text-red-500 hover:text-red-700 font-medium"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Project Title
                        </label>
                        <input
                          type="text"
                          value={proj.title}
                          onChange={(e) =>
                            handleUpdateProject(idx, 'title', e.target.value)
                          }
                          placeholder="e.g. Distributed Task Queue"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Tech Stack / Keywords
                        </label>
                        <input
                          type="text"
                          value={proj.tech_stack}
                          onChange={(e) =>
                            handleUpdateProject(idx, 'tech_stack', e.target.value)
                          }
                          placeholder="e.g. Python, Redis, Docker, FastAPI"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                        Description & Key Achievements
                      </label>
                      <textarea
                        rows={2}
                        value={proj.description}
                        onChange={(e) =>
                          handleUpdateProject(idx, 'description', e.target.value)
                        }
                        placeholder="Designed high-throughput asynchronous job processor handling 10k req/s..."
                        className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Tab 5: Certifications Tab */}
          {activeTab === 'certifications' && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                  Extracted Certifications
                </label>
                <button
                  type="button"
                  onClick={handleAddCert}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  + Add Certification
                </button>
              </div>

              {certList.length === 0 ? (
                <div className="text-center py-6 text-xs text-gray-400 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                  No certifications detected. Click "+ Add Certification" to add your verified credentials.
                </div>
              ) : (
                certList.map((cert, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/40 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-700 dark:text-gray-300">
                        Certification #{idx + 1}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveCert(idx)}
                        className="text-xs text-red-500 hover:text-red-700 font-medium"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Certificate Name
                        </label>
                        <input
                          type="text"
                          value={cert.name}
                          onChange={(e) =>
                            handleUpdateCert(idx, 'name', e.target.value)
                          }
                          placeholder="e.g. AWS Certified Solutions Architect"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-gray-500 dark:text-gray-400 mb-1">
                          Issuing Organization
                        </label>
                        <input
                          type="text"
                          value={cert.issuer}
                          onChange={(e) =>
                            handleUpdateCert(idx, 'issuer', e.target.value)
                          }
                          placeholder="e.g. Amazon Web Services"
                          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Footer Save Action */}
          <div className="flex flex-col sm:flex-row items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800 gap-3">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Saving updates your active candidate profile visible to campus recruiters.
            </span>
            <button
              type="button"
              disabled={savingProfile}
              onClick={handleSaveToProfile}
              className="px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow transition disabled:opacity-50 flex items-center gap-2"
            >
              {savingProfile ? (
                <>
                  <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  Saving to Profile...
                </>
              ) : (
                <>
                  <span>✓</span>
                  <span>Save to Profile</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
