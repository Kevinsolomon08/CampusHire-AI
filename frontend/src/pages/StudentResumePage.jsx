// src/pages/StudentResumePage.jsx
// Resume upload page with drag-and-drop, PDF validation, and active status display.

import React, { useEffect, useRef, useState } from 'react'
import { getStudentResume, uploadResume } from '../api/studentApi'

export default function StudentResumePage() {
  const [currentResume, setCurrentResume] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const fileInputRef = useRef(null)

  useEffect(() => {
    loadResume()
  }, [])

  const loadResume = async () => {
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await getStudentResume()
      if (res.success && res.data) {
        setCurrentResume(res.data)
      } else {
        setCurrentResume(null)
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to fetch resume status.')
    } finally {
      setLoading(false)
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
      setErrorMessage(`File is too large (${(file.size / (1024 * 1024)).toFixed(2)} MB). Max limit is 5MB.`)
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

    try {
      const res = await uploadResume(selectedFile)
      if (res.success && res.data) {
        setSuccessMessage('Resume uploaded and verified successfully!')
        setCurrentResume(res.data)
        setSelectedFile(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Failed to upload resume.')
    } finally {
      setUploading(false)
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
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Resume Management
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Upload your official PDF resume for recruiters to review during campus hiring.
        </p>
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
          <div>
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
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3.5 py-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-white dark:bg-gray-800 border border-indigo-200 dark:border-indigo-800/80 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-950/50 transition self-start sm:self-auto"
              >
                Replace Resume
              </button>
            </div>

            <div className="mt-4 p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-400">
                  AI Resume Parsing & Skill Extraction
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-300">
                  Phase 2 Planned
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Automated skill taxonomy mapping and candidate scoring: <span className="font-semibold text-amber-600 dark:text-amber-400">Pending AI analysis</span>
              </p>
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
                  Uploading & Verifying PDF...
                </>
              ) : (
                'Upload Resume'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
