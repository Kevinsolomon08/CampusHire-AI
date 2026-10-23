// src/api/studentApi.js
// API helper methods for Student module endpoints.

import client from './client'

export const getStudentProfile = async () => {
  const response = await client.get('/students/me')
  return response.data
}

export const updateStudentProfile = async (profileData) => {
  const response = await client.put('/students/me', profileData)
  return response.data
}

export const uploadResume = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await client.post('/students/resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getStudentResume = async () => {
  const response = await client.get('/students/resume')
  return response.data
}

export const getParsedResume = async () => {
  const response = await client.get('/students/me/parsed-resume')
  return response.data
}

export const triggerResumeParse = async (resumeId) => {
  const response = await client.post(`/resumes/${resumeId}/parse`)
  return response.data
}

export const getStudentJobs = async ({ page = 1, page_size = 10, search = '' } = {}) => {
  const params = { page, page_size }
  if (search) params.search = search
  const response = await client.get('/students/jobs', { params })
  return response.data
}

export const getStudentJobDetail = async (jobId) => {
  const response = await client.get(`/students/jobs/${jobId}`)
  return response.data
}

export const applyForJob = async (jobId, resumeId = null) => {
  const response = await client.post(`/applications/${jobId}/apply`, {
    job_id: jobId,
    resume_id: resumeId,
  })
  return response.data
}

export const getStudentApplications = async () => {
  const response = await client.get('/applications')
  return response.data
}

export const getApplicationDetail = async (applicationId) => {
  const response = await client.get(`/applications/${applicationId}`)
  return response.data
}

export const getStudentInterviews = async ({ page = 1, page_size = 20 } = {}) => {
  const params = { page, page_size }
  const response = await client.get('/applications/interviews', { params })
  return response.data
}

export const getStudentNotifications = async (page = 1, page_size = 10) => {
  const response = await client.get('/notifications', {
    params: { page, page_size },
  })
  return response.data
}

export const markNotificationRead = async (notificationId) => {
  const response = await client.patch(`/notifications/${notificationId}/read`)
  return response.data
}

export const getUnreadNotificationCount = async () => {
  const response = await client.get('/notifications/unread/count')
  return response.data
}

/**
 * Fetch AI-ranked job recommendations for the logged-in student.
 * @param {number|null} topN  Optional override for number of results (1–50).
 * @returns {Promise<{success, data: {items, has_resume, message}}>}
 */
export const getRecommendedJobs = async (topN = null) => {
  const params = {}
  if (topN) params.top_n = topN
  const response = await client.get('/students/recommended-jobs', { params })
  return response.data
}
