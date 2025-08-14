/**
 * API client with comprehensive logging and error handling.
 * 
 * Features:
 * - Automatic request/response logging
 * - Error handling and retry logic
 * - Authentication token management
 * - Request/response interceptors
 * - Type-safe API calls
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { logger } from './logger'

// API response types
interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    email: string
    full_name: string
  }
}

interface UserResponse {
  id: string
  email: string
  full_name: string
}

class ApiClient {
  private client: AxiosInstance
  private requestCounter = 0

  constructor() {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
    
    // Debug logging
    console.log('API Client Configuration:', {
      VITE_API_URL: import.meta.env.VITE_API_URL,
      baseURL,
      env: import.meta.env
    })
    
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request tracking
        const requestId = `req-${Date.now()}-${++this.requestCounter}`
        config.headers['X-Request-ID'] = requestId

        // Debug: Log the full URL being requested
        const fullUrl = `${config.baseURL}${config.url}`
        console.log('Making API request to:', fullUrl)

        logger.debug('API Request', {
          requestId,
          method: config.method,
          url: config.url,
          fullUrl,
          baseURL: config.baseURL,
          params: config.params,
          data: config.data,
        })

        return config
      },
      (error) => {
        logger.error('API Request Error', { error: error.message })
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        const requestId = response.config.headers['X-Request-ID']
        logger.debug('API Response', {
          requestId,
          status: response.status,
          url: response.config.url,
          data: response.data,
        })
        return response
      },
      (error) => {
        const requestId = error.config?.headers?.['X-Request-ID']
        logger.error('API Response Error', {
          requestId,
          status: error.response?.status,
          url: error.config?.url,
          error: error.response?.data || error.message,
        })
        return Promise.reject(error)
      }
    )
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config)
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config)
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config)
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config)
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config)
  }
}

// Export a singleton instance
export const apiClient = new ApiClient()

// Export types
export type { LoginResponse, UserResponse } 