import React, { createContext, useContext, useState, useEffect } from 'react'
import { apiClient } from '../lib/api-client'
import type { LoginResponse, UserResponse } from '../lib/api-client'
import { logger } from '../lib/logger'

interface User {
  id: string
  email: string
  full_name: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check authentication on mount
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      setIsLoading(false)
      return
    }

    try {
      const response = await apiClient.get<UserResponse>('/users/me')
      setUser(response.data)
      logger.info('User authenticated', { userId: response.data.id })
    } catch (error) {
      logger.error('Auth check failed', { error })
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<LoginResponse>('/auth/login', { email, password })
    
    localStorage.setItem('auth_token', response.data.access_token)
    localStorage.setItem('user', JSON.stringify(response.data.user))
    
    setUser(response.data.user)
    logger.info('User logged in', { userId: response.data.user.id })
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    setUser(null)
    logger.info('User logged out')
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        checkAuth
      }}
    >
      {children}
    </AuthContext.Provider>
  )
} 