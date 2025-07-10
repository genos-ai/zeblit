import React, { useState, useEffect } from 'react'
import { Link, useSearch } from 'wouter'
import { Mail, Lock, LogIn, CheckCircle } from 'lucide-react'
import { apiClient } from '../lib/api-client'
import type { LoginResponse } from '../lib/api-client'
import { logger } from '../lib/logger'

export const Login: React.FC = () => {
  const searchParams = useSearch()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)

  useEffect(() => {
    // Check if redirected from successful registration
    const params = new URLSearchParams(searchParams)
    if (params.get('registered') === 'true') {
      setShowSuccess(true)
      // Hide success message after 5 seconds
      const timer = setTimeout(() => setShowSuccess(false), 5000)
      return () => clearTimeout(timer)
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      // OAuth2 expects form data with username (email) and password
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const response = await apiClient.post<LoginResponse>('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      if (response.data.access_token) {
        // Store token
        localStorage.setItem('auth_token', response.data.access_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
        
        logger.info('User logged in successfully', { email })
        
        // Redirect to dashboard
        window.location.href = '/dashboard'
      }
    } catch (err: any) {
      logger.error('Login failed', { error: err.message })
      setError(err.response?.data?.detail || 'Invalid email or password')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-2">Zeblit</h1>
          <h2 className="text-2xl font-semibold text-gray-300">Welcome back</h2>
          <p className="mt-2 text-gray-400">Sign in to your account</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {showSuccess && (
            <div className="bg-green-500 bg-opacity-10 border border-green-500 text-green-500 px-4 py-3 rounded flex items-center">
              <CheckCircle className="h-5 w-5 mr-2" />
              Account created successfully! Please sign in.
            </div>
          )}

          {error && (
            <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-500 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none relative block w-full pl-10 pr-3 py-2 border border-gray-600 placeholder-gray-400 text-white bg-gray-800 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Enter your email"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none relative block w-full pl-10 pr-3 py-2 border border-gray-600 placeholder-gray-400 text-white bg-gray-800 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Enter your password"
                />
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <LogIn className="h-5 w-5 mr-2" />
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-center text-sm">
            <span className="text-gray-400">Don't have an account? </span>
            <Link href="/register" className="font-medium text-blue-500 hover:text-blue-400">
              Sign up
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
} 