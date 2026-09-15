// src/store/authStore.js
// Zustand store for authentication state management with localStorage persistence.

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      role: null,
      isAuthenticated: false,

      login: (token, user) => {
        // Also keep token in raw localStorage for non-react modules if needed
        localStorage.setItem('access_token', token)
        set({
          token,
          user,
          role: user?.role ?? null,
          isAuthenticated: true,
        })
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({
          token: null,
          user: null,
          role: null,
          isAuthenticated: false,
        })
      },

      setUser: (user) => {
        set({
          user,
          role: user?.role ?? null,
        })
      },
    }),
    {
      name: 'campushire_auth', // key in localStorage
    }
  )
)
