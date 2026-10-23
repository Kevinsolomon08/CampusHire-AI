// src/api/recruiterApi.js
// API client methods for Company, Recruiter, and Job management.

import client from './client'

export const getRecruiterProfile = async () => {
  const response = await client.get('/recruiters/me')
  return response.data
}

export const createCompany = async (companyData) => {
  const response = await client.post('/companies', companyData)
  return response.data
}

export const getCompany = async (companyId) => {
  const response = await client.get(`/companies/${companyId}`)
  return response.data
}

export const updateCompany = async (companyId, companyData) => {
  const response = await client.put(`/companies/${companyId}`, companyData)
  return response.data
}

export const getRecruiterJobs = async ({ page = 1, page_size = 10, status = '', search = '' } = {}) => {
  const params = { page, page_size }
  if (status && status !== 'ALL') params.status = status
  if (search) params.search = search
  const response = await client.get('/recruiters/jobs', { params })
  return response.data
}

export const getJobDetail = async (jobId) => {
  const response = await client.get(`/jobs/${jobId}`)
  return response.data
}

export const createJob = async (jobData) => {
  const response = await client.post('/jobs', jobData)
  return response.data
}

export const updateJob = async (jobId, jobData) => {
  const response = await client.put(`/jobs/${jobId}`, jobData)
  return response.data
}

export const deleteJob = async (jobId) => {
  const response = await client.delete(`/jobs/${jobId}`)
  return response.data
}

export const publishJob = async (jobId) => {
  const response = await client.post(`/jobs/${jobId}/publish`)
  return response.data
}

export const closeJob = async (jobId) => {
  const response = await client.post(`/jobs/${jobId}/close`)
  return response.data
}

export const getJobApplicants = async ({
  jobId,
  page = 1,
  page_size = 20,
  branch = '',
  min_cgpa = null,
  max_backlogs = null,
  batch = null,
  status = '',
  min_ai_score = null,
  sort_by = 'rank',
} = {}) => {
  const params = { page, page_size, sort_by }
  if (branch) params.branch = branch
  if (min_cgpa !== null && min_cgpa !== '') params.min_cgpa = min_cgpa
  if (max_backlogs !== null && max_backlogs !== '') params.max_backlogs = max_backlogs
  if (batch !== null && batch !== '') params.batch = batch
  if (status) params.status = status
  if (min_ai_score !== null && min_ai_score !== '') params.min_ai_score = min_ai_score
  const response = await client.get(`/applications/jobs/${jobId}/applications`, { params })
  return response.data
}

export const recalculateJobScores = async (jobId) => {
  const response = await client.post(`/applications/jobs/${jobId}/recalculate-scores`)
  return response.data
}

export const getApplicationMatchAnalysis = async (applicationId) => {
  const response = await client.get(`/applications/${applicationId}/match-analysis`)
  return response.data
}

export const exportJobApplicantsCsv = async ({ jobId, topK = null }) => {
  const params = { format: 'csv' }
  if (topK !== null && topK !== undefined && topK !== '') {
    params.top_k = parseInt(topK)
  }
  const response = await client.get(`/applications/jobs/${jobId}/applications/export`, {
    params,
    responseType: 'blob',
  })

  // Extract filename from Content-Disposition header if available
  let filename = `job_${jobId}_top_candidates.csv`
  const disposition = response.headers['content-disposition'] || response.headers['Content-Disposition']
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/)
    if (match && match[1]) {
      filename = match[1]
    }
  }

  // Create temporary URL and trigger browser download
  const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)

  return true
}

export const updateApplicationStatus = async (applicationId, newStatus, remarks = null) => {
  const response = await client.patch(`/applications/${applicationId}/status`, {
    new_status: newStatus,
    remarks,
  })
  return response.data
}

export const scheduleInterview = async (applicationId, interviewData) => {
  const response = await client.post(`/applications/${applicationId}/interviews`, interviewData)
  return response.data
}

export const updateInterview = async (interviewId, interviewData) => {
  const response = await client.put(`/applications/interviews/${interviewId}`, interviewData)
  return response.data
}

export const getRecruiterInterviews = async ({ page = 1, page_size = 20 } = {}) => {
  const params = { page, page_size }
  const response = await client.get('/applications/interviews', { params })
  return response.data
}

export const getRecruiterNotifications = async (page = 1, page_size = 10) => {
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
