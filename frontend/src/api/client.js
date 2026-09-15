// src/api/client.js
// Pre-configured axios instance for all CampusHire API calls.
// Attaches JWT to outgoing requests and redirects to /login on 401.

import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request interceptor — attach JWT to Authorization header
// ---------------------------------------------------------------------------
client.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token || localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// Response interceptor — handle 401 Unauthorized globally
// ---------------------------------------------------------------------------
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear auth store
      useAuthStore.getState().logout()

      // Avoid redirect loops if already on login/register
      const currentPath = window.location.pathname
      if (currentPath !== '/login' && currentPath !== '/register') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default client
