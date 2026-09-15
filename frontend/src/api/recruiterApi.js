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
  sort_by = 'applied_at',
} = {}) => {
  const params = { page, page_size, sort_by }
  if (branch) params.branch = branch
  if (min_cgpa !== null) params.min_cgpa = min_cgpa
  if (max_backlogs !== null) params.max_backlogs = max_backlogs
  if (batch !== null) params.batch = batch
  if (status) params.status = status
  const response = await client.get(`/applications/jobs/${jobId}/applications`, { params })
  return response.data
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
