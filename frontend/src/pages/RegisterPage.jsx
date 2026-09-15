// src/pages/RegisterPage.jsx
// Registration page supporting STUDENT, RECRUITER, and PLACEMENT_OFFICER roles.

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

export default function RegisterPage() {
  const navigate = useNavigate()
  const loginStore = useAuthStore((s) => s.login)

  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: {
      name: '',
      email: '',
      password: '',
      role: 'STUDENT',
      // Student specific
      roll_number: '',
      branch: 'Computer Science',
      year: new Date().getFullYear(),
      // Recruiter specific
      company_name: '',
      designation: '',
    },
  })

  const selectedRole = watch('role')

  const onSubmit = async (formData) => {
    setApiError('')
    setLoading(true)

    try {
      const payload = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        role: formData.role,
      }

      if (formData.role === 'STUDENT') {
        if (formData.roll_number) payload.roll_number = formData.roll_number
        if (formData.branch) payload.branch = formData.branch
        if (formData.year) payload.year = parseInt(formData.year, 10)
      } else if (formData.role === 'RECRUITER') {
        if (formData.company_name) payload.company_name = formData.company_name
        if (formData.designation) payload.designation = formData.designation
      }

      // 1. Call Register API
      await client.post('/auth/register', payload)

      // 2. Automatically log in for seamless onboarding
      const loginRes = await client.post('/auth/login', {
        email: formData.email,
        password: formData.password,
      })

      const authData = loginRes.data?.data
      if (authData?.access_token && authData?.user) {
        loginStore(authData.access_token, authData.user)

        // 3. Redirect to role dashboard
        const role = authData.user.role
        if (role === 'STUDENT') {
          navigate('/student/dashboard', { replace: true })
        } else if (role === 'RECRUITER') {
          navigate('/recruiter/dashboard', { replace: true })
        } else if (role === 'PLACEMENT_OFFICER') {
          navigate('/placement/dashboard', { replace: true })
        } else {
          navigate('/login', { replace: true })
        }
      } else {
        navigate('/login', { replace: true })
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.message ||
        err.message ||
        'Registration failed. Please check your information.'
      setApiError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-bold text-xl shadow-lg shadow-indigo-500/25">
          CH
        </div>
        <h1 className="mt-4 text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Campus<span className="text-indigo-600 dark:text-indigo-400">Hire</span>
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Create an account to join the recruitment platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-white dark:bg-slate-900 py-8 px-6 shadow-xl shadow-slate-200/50 dark:shadow-none border border-slate-200 dark:border-slate-800 sm:rounded-2xl sm:px-10">
          {apiError && (
            <div
              id="register-error-alert"
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
            {/* Role Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                I am registering as:
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'STUDENT', label: 'Student' },
                  { id: 'RECRUITER', label: 'Recruiter' },
                  { id: 'PLACEMENT_OFFICER', label: 'Placement Officer' },
                ].map((roleOption) => {
                  const isChecked = selectedRole === roleOption.id
                  return (
                    <label
                      key={roleOption.id}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center cursor-pointer transition text-xs font-semibold ${
                        isChecked
                          ? 'border-indigo-600 bg-indigo-50/70 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-500 shadow-sm'
                          : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                      }`}
                    >
                      <input
                        type="radio"
                        value={roleOption.id}
                        {...register('role', { required: 'Please select a role' })}
                        className="sr-only"
                      />
                      <span>{roleOption.label}</span>
                    </label>
                  )
                })}
              </div>
            </div>

            {/* Name */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Full Name
              </label>
              <div className="mt-1">
                <input
                  id="name"
                  type="text"
                  placeholder="Jane Doe"
                  {...register('name', {
                    required: 'Name is required',
                    minLength: { value: 2, message: 'Minimum 2 characters' },
                  })}
                  className={`block w-full rounded-xl border px-3.5 py-2.5 text-slate-900 dark:text-white bg-slate-50 dark:bg-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm transition ${
                    errors.name
                      ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500'
                      : 'border-slate-300 dark:border-slate-700'
                  }`}
                />
                {errors.name && (
                  <p className="mt-1.5 text-xs text-rose-600 dark:text-rose-400">
                    {errors.name.message}
                  </p>
                )}
              </div>
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Email Address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  type="email"
                  placeholder="jane@university.edu"
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

            {/* Password */}
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

            {/* Role-specific fields */}
            {selectedRole === 'STUDENT' && (
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      htmlFor="roll_number"
                      className="block text-xs font-medium text-slate-700 dark:text-slate-300"
                    >
                      Roll Number (Optional)
                    </label>
                    <input
                      id="roll_number"
                      type="text"
                      placeholder="e.g. 21CS045"
                      {...register('roll_number')}
                      className="mt-1 block w-full rounded-xl border border-slate-300 dark:border-slate-700 px-3.5 py-2 text-sm bg-slate-50 dark:bg-slate-800"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="year"
                      className="block text-xs font-medium text-slate-700 dark:text-slate-300"
                    >
                      Graduation Year
                    </label>
                    <input
                      id="year"
                      type="number"
                      placeholder="2026"
                      {...register('year')}
                      className="mt-1 block w-full rounded-xl border border-slate-300 dark:border-slate-700 px-3.5 py-2 text-sm bg-slate-50 dark:bg-slate-800"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="branch"
                    className="block text-xs font-medium text-slate-700 dark:text-slate-300"
                  >
                    Department / Branch
                  </label>
                  <input
                    id="branch"
                    type="text"
                    placeholder="e.g. Computer Science & Engineering"
                    {...register('branch')}
                    className="mt-1 block w-full rounded-xl border border-slate-300 dark:border-slate-700 px-3.5 py-2 text-sm bg-slate-50 dark:bg-slate-800"
                  />
                </div>
              </div>
            )}

            {selectedRole === 'RECRUITER' && (
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-4">
                <div>
                  <label
                    htmlFor="company_name"
                    className="block text-xs font-medium text-slate-700 dark:text-slate-300"
                  >
                    Company / Organization
                  </label>
                  <input
                    id="company_name"
                    type="text"
                    placeholder="e.g. Acme Innovations"
                    {...register('company_name')}
                    className="mt-1 block w-full rounded-xl border border-slate-300 dark:border-slate-700 px-3.5 py-2 text-sm bg-slate-50 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label
                    htmlFor="designation"
                    className="block text-xs font-medium text-slate-700 dark:text-slate-300"
                  >
                    Job Title / Designation
                  </label>
                  <input
                    id="designation"
                    type="text"
                    placeholder="e.g. Lead Technical Recruiter"
                    {...register('designation')}
                    className="mt-1 block w-full rounded-xl border border-slate-300 dark:border-slate-700 px-3.5 py-2 text-sm bg-slate-50 dark:bg-slate-800"
                  />
                </div>
              </div>
            )}

            {/* Submit */}
            <div className="pt-2">
              <button
                id="register-submit-button"
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {loading ? 'Creating account...' : 'Create account'}
              </button>
            </div>
          </form>

          {/* Footer */}
          <div className="mt-6 border-t border-slate-200 dark:border-slate-800 pt-6 text-center text-sm">
            <span className="text-slate-600 dark:text-slate-400">
              Already have an account?{' '}
            </span>
            <Link
              to="/login"
              className="font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
