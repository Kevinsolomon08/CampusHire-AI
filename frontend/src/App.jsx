// src/App.jsx
// Main application router with authentication guards, role layouts, and redirects.

import React from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import PlacementOfficerLayout from './layouts/PlacementOfficerLayout'
import RecruiterLayout from './layouts/RecruiterLayout'
import StudentLayout from './layouts/StudentLayout'
import LoginPage from './pages/LoginPage'
import PlacementDashboard from './pages/PlacementDashboard'
import RecruiterDashboard from './pages/RecruiterDashboard'
import RecruiterCompanyPage from './pages/RecruiterCompanyPage'
import RecruiterJobsPage from './pages/RecruiterJobsPage'
import RecruiterJobFormPage from './pages/RecruiterJobFormPage'
import RecruiterApplicantsPage from './pages/RecruiterApplicantsPage'
import RecruiterInterviewsPage from './pages/RecruiterInterviewsPage'
import RegisterPage from './pages/RegisterPage'
import StudentDashboard from './pages/StudentDashboard'
import StudentProfilePage from './pages/StudentProfilePage'
import StudentResumePage from './pages/StudentResumePage'
import StudentJobsPage from './pages/StudentJobsPage'
import StudentJobDetailPage from './pages/StudentJobDetailPage'
import StudentApplicationsPage from './pages/StudentApplicationsPage'
import StudentApplicationDetailPage from './pages/StudentApplicationDetailPage'
import StudentInterviewsPage from './pages/StudentInterviewsPage'
import StudentNotificationsPage from './pages/StudentNotificationsPage'
import RecruiterNotificationsPage from './pages/RecruiterNotificationsPage'
import PlacementStudentsPage from './pages/PlacementStudentsPage'
import PlacementCompaniesPage from './pages/PlacementCompaniesPage'
import PlacementJobsPage from './pages/PlacementJobsPage'
import PlacementApplicationsPage from './pages/PlacementApplicationsPage'
import PlacementInterviewsPage from './pages/PlacementInterviewsPage'
import PlacementReportsPage from './pages/PlacementReportsPage'
import { useAuthStore } from './store/authStore'

// Smart index component redirecting users to their role dashboard if logged in
function RootIndexRedirect() {
  const { isAuthenticated, role } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (role === 'STUDENT') {
    return <Navigate to="/student/dashboard" replace />
  }
  if (role === 'RECRUITER') {
    return <Navigate to="/recruiter/dashboard" replace />
  }
  if (role === 'PLACEMENT_OFFICER') {
    return <Navigate to="/placement/dashboard" replace />
  }

  return <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Authentication Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected Student Portal */}
        <Route
          path="/student/dashboard"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentDashboard />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/profile"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentProfilePage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/resume"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentResumePage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/jobs"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentJobsPage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/jobs/:id"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentJobDetailPage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/applications"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentApplicationsPage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/applications/:id"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentApplicationDetailPage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/interviews"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentInterviewsPage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/notifications"
          element={
            <ProtectedRoute allowedRoles={['STUDENT']}>
              <StudentLayout>
                <StudentNotificationsPage />
              </StudentLayout>
            </ProtectedRoute>
          }
        />

        {/* Protected Recruiter Portal */}
        <Route
          path="/recruiter/dashboard"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterDashboard />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/company"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterCompanyPage />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/jobs"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterJobsPage />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/jobs/create"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterJobFormPage />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/jobs/:id"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterJobFormPage />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/jobs/:id/applicants"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterApplicantsPage />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/interviews"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterInterviewsPage />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/notifications"
          element={
            <ProtectedRoute allowedRoles={['RECRUITER']}>
              <RecruiterLayout>
                <RecruiterNotificationsPage />
              </RecruiterLayout>
            </ProtectedRoute>
          }
        />

        {/* Protected Placement Officer Portal */}
        <Route
          path="/placement/dashboard"
          element={
            <ProtectedRoute allowedRoles={['PLACEMENT_OFFICER']}>
              <PlacementOfficerLayout>
                <PlacementDashboard />
              </PlacementOfficerLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/students"
          element={
            <ProtectedRoute allowedRoles={['PLACEMENT_OFFICER']}>
              <PlacementOfficerLayout>
                <PlacementStudentsPage />
              </PlacementOfficerLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/companies"
          element={
            <ProtectedRoute allowedRoles={['PLACEMENT_OFFICER']}>
              <PlacementOfficerLayout>
                <PlacementCompaniesPage />
              </PlacementOfficerLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/jobs"
          element={
            <ProtectedRoute allowedRoles={['PLACEMENT_OFFICER']}>
              <PlacementOfficerLayout>
                <PlacementJobsPage />
              </PlacementOfficerLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/applications"
          element={
            <ProtectedRoute allowedRoles={['PLACEMENT_OFFICER']}>
              <PlacementOfficerLayout>
                <PlacementApplicationsPage />
              </PlacementOfficerLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/interviews"
          element={
            <ProtectedRoute allowedRoles={['PLACEMENT_OFFICER']}>
              <PlacementOfficerLayout>
                <PlacementInterviewsPage />
              </PlacementOfficerLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/placement/reports"
          element={
            <ProtectedRoute allowedRoles={['PLACEMENT_OFFICER']}>
              <PlacementOfficerLayout>
                <PlacementReportsPage />
              </PlacementOfficerLayout>
            </ProtectedRoute>
          }
        />

        {/* Index / Fallback */}
        <Route path="/" element={<RootIndexRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
