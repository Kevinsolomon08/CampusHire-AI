// src/pages/LoginPage.jsx
// CampusHire Login page built with react-hook-form, role redirection, and error handling.

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const loginStore = useAuthStore((s) => s.login)

  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const onSubmit = async (formData) => {
    setApiError('')
    setLoading(true)

    try {
      const response = await client.post('/auth/login', {
        email: formData.email,
        password: formData.password,
      })

      const data = response.data?.data
      if (data?.access_token && data?.user) {
        // Save to Zustand & localStorage
        loginStore(data.access_token, data.user)

        // Redirect based on role
        const role = data.user.role
        if (location.state?.from?.pathname) {
          navigate(location.state.from.pathname, { replace: true })
        } else if (role === 'STUDENT') {
          navigate('/student/dashboard', { replace: true })
        } else if (role === 'RECRUITER') {
          navigate('/recruiter/dashboard', { replace: true })
        } else if (role === 'PLACEMENT_OFFICER') {
          navigate('/placement/dashboard', { replace: true })
        } else {
          navigate('/', { replace: true })
        }
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.message ||
        err.message ||
        'Unable to log in. Please check your credentials.'
      setApiError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        {/* Logo */}
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-bold text-xl shadow-lg shadow-indigo-500/25">
          CH
        </div>
        <h1 className="mt-4 text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Campus<span className="text-indigo-600 dark:text-indigo-400">Hire</span>
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Sign in to your account to continue
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-6 shadow-xl shadow-slate-200/50 dark:shadow-none border border-slate-200 dark:border-slate-800 sm:rounded-2xl sm:px-10">
          {apiError && (
            <div
              id="login-error-alert"
              className="mb-6 rounded-xl bg-rose-50 dark:bg-rose-950/40 p-4 border border-rose-200 dark:border-rose-900/50 text-sm text-rose-700 dark:text-rose-300 flex items-start space-x-3"
            >
              <svg
                className="h-5 w-5 text-rose-500 flex-shrink-0 mt-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>{apiError}</div>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="name@university.edu"
                  {...register('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /\S+@\S+\.\S+/,
                      message: 'Enter a valid email address',
                    },
                  })}
                  className={`block w-full rounded-xl border px-3.5 py-2.5 text-slate-900 dark:text-white bg-slate-50 dark:bg-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm transition ${
                    errors.email
                      ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500'
                      : 'border-slate-300 dark:border-slate-700'
                  }`}
                />
                {errors.email && (
                  <p className="mt-1.5 text-xs text-rose-600 dark:text-rose-400">
                    {errors.email.message}
                  </p>
                )}
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters',
                    },
                  })}
                  className={`block w-full rounded-xl border px-3.5 py-2.5 text-slate-900 dark:text-white bg-slate-50 dark:bg-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm transition ${
                    errors.password
                      ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500'
                      : 'border-slate-300 dark:border-slate-700'
                  }`}
                />
                {errors.password && (
                  <p className="mt-1.5 text-xs text-rose-600 dark:text-rose-400">
                    {errors.password.message}
                  </p>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                id="login-submit-button"
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>

          {/* Footer note */}
          <div className="mt-6 border-t border-slate-200 dark:border-slate-800 pt-6 text-center text-sm">
            <span className="text-slate-600 dark:text-slate-400">
              Don't have an account yet?{' '}
            </span>
            <Link
              to="/register"
              className="font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
