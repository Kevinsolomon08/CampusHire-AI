// src/api/adminApi.js
// API client methods for Admin/Placement Officer endpoints.

import client from './client'

export const getDashboard = async () => {
  const response = await client.get('/admin/dashboard')
  return response.data
}

export const getStatistics = async () => {
  const response = await client.get('/admin/statistics')
  return response.data
}

export const getStudents = async ({
  page = 1,
  page_size = 10,
  search = '',
  department = '',
  batch = null,
} = {}) => {
  const params = { page, page_size }
  if (search) params.search = search
  if (department) params.department = department
  if (batch !== null) params.batch = batch
  const response = await client.get('/admin/students', { params })
  return response.data
}

export const getCompanies = async ({
  page = 1,
  page_size = 10,
  search = '',
} = {}) => {
  const params = { page, page_size }
  if (search) params.search = search
  const response = await client.get('/admin/companies', { params })
  return response.data
}

export const getJobs = async ({
  page = 1,
  page_size = 10,
  search = '',
  company_id = null,
  status = '',
} = {}) => {
  const params = { page, page_size }
  if (search) params.search = search
  if (company_id !== null) params.company_id = company_id
  if (status) params.status = status
  const response = await client.get('/admin/jobs', { params })
  return response.data
}

export const getApplications = async ({
  page = 1,
  page_size = 10,
  search = '',
  app_status = '',
  company_id = null,
  department = '',
} = {}) => {
  const params = { page, page_size }
  if (search) params.search = search
  if (app_status) params.app_status = app_status
  if (company_id !== null) params.company_id = company_id
  if (department) params.department = department
  const response = await client.get('/admin/applications', { params })
  return response.data
}

export const getInterviews = async ({
  page = 1,
  page_size = 10,
  search = '',
  result_status = '',
  company_id = null,
} = {}) => {
  const params = { page, page_size }
  if (search) params.search = search
  if (result_status) params.result_status = result_status
  if (company_id !== null) params.company_id = company_id
  const response = await client.get('/admin/interviews', { params })
  return response.data
}

export const getReports = async ({
  batch = null,
  department = '',
  company_id = null,
  job_id = null,
} = {}) => {
  const params = {}
  if (batch !== null && batch !== '') params.batch = batch
  if (department) params.department = department
  if (company_id !== null && company_id !== '') params.company_id = company_id
  if (job_id !== null && job_id !== '') params.job_id = job_id
  const response = await client.get('/admin/reports', { params })
  return response.data
}

export const downloadReportCsv = async ({
  batch = null,
  department = '',
  company_id = null,
  job_id = null,
} = {}) => {
  const params = { format: 'csv' }
  if (batch !== null && batch !== '') params.batch = batch
  if (department) params.department = department
  if (company_id !== null && company_id !== '') params.company_id = company_id
  if (job_id !== null && job_id !== '') params.job_id = job_id
  const response = await client.get('/admin/reports', {
    params,
    responseType: 'blob',
  })
  return response.data
}

