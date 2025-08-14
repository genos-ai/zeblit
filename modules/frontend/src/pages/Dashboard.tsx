import React, { useState, useEffect } from 'react'
import { Link } from 'wouter'
import { Plus, Folder, Clock, GitBranch, ExternalLink } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { apiClient } from '../lib/api-client'
import { logger } from '../lib/logger'

// Import mock data for Replit
const MOCK_MODE = import.meta.env.VITE_MOCK_MODE === 'true'
const mockProjects = MOCK_MODE ? [
  {
    id: "1",
    name: "AI Chat Assistant",
    description: "A sophisticated chatbot powered by GPT-4 with custom training on company documentation",
    framework: "Next.js",
    language: "TypeScript",
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-20T14:45:00Z",
    status: "active",
    container_status: "running",
    git_initialized: true,
  },
  {
    id: "2",
    name: "E-commerce Dashboard",
    description: "Real-time analytics dashboard for monitoring sales, inventory, and customer behavior",
    framework: "React",
    language: "JavaScript",
    created_at: "2024-01-10T08:00:00Z",
    updated_at: "2024-01-18T16:20:00Z",
    status: "active",
    container_status: "stopped",
    git_initialized: true,
  },
  {
    id: "3",
    name: "ML Model API",
    description: "FastAPI service for serving machine learning models with automatic scaling",
    framework: "FastAPI",
    language: "Python",
    created_at: "2024-01-05T12:00:00Z",
    updated_at: "2024-01-12T09:30:00Z",
    status: "active",
    container_status: "running",
    git_initialized: true,
  },
  {
    id: "4",
    name: "Mobile App Backend",
    description: "GraphQL API backend for a social media mobile application",
    framework: "Express",
    language: "TypeScript",
    created_at: "2023-12-20T15:45:00Z",
    updated_at: "2024-01-08T11:15:00Z",
    status: "active",
    container_status: "starting",
    git_initialized: false,
  }
] : []

interface Project {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
  status: 'active' | 'archived'
  container_status: 'running' | 'stopped' | 'starting' | null
  git_initialized: boolean
}

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      if (MOCK_MODE) {
        // Use mock data in Replit
        await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate loading
        setProjects(mockProjects as Project[])
        logger.info('Mock projects loaded', { count: mockProjects.length })
      } else {
        // Real API call
        const response = await apiClient.get<{items: Project[], total: number, skip: number, limit: number}>('/projects')
        setProjects(response.data.items)
        logger.info('Projects fetched', { count: response.data.items.length })
      }
    } catch (err: any) {
      logger.error('Failed to fetch projects', { error: err.message })
      setError('Failed to load projects. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const getContainerStatusColor = (status: string | null) => {
    switch (status) {
      case 'running':
        return 'text-green-500'
      case 'stopped':
        return 'text-red-500'
      case 'starting':
        return 'text-yellow-500'
      default:
        return 'text-gray-500'
    }
  }

  const getContainerStatusText = (status: string | null) => {
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Not created'
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-white">Zeblit</h1>
              <span className="ml-4 text-gray-400">AI Development Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-300">Welcome, {user?.full_name || user?.email || 'Demo User'}</span>
              <button
                onClick={logout}
                className="text-gray-400 hover:text-white transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Title and Actions */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white">Your Projects</h2>
            <p className="mt-1 text-gray-400">
              Create and manage your AI-powered development projects
            </p>
          </div>
          <Link href="/projects/new" className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            <Plus className="h-5 w-5 mr-2" />
            New Project
          </Link>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-400">Loading projects...</p>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-500 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && projects.length === 0 && (
          <div className="text-center py-12 bg-gray-800 rounded-lg">
            <Folder className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-300 mb-2">No projects yet</h3>
            <p className="text-gray-500 mb-6">
              Get started by creating your first AI-powered project
            </p>
            <Link href="/projects/new" className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
              <Plus className="h-5 w-5 mr-2" />
              Create Your First Project
            </Link>
          </div>
        )}

        {/* Projects Grid */}
        {!isLoading && !error && projects.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`} className="block bg-gray-800 rounded-lg p-6 hover:bg-gray-700 transition-colors border border-gray-700 hover:border-gray-600">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-1">
                      {project.name}
                    </h3>
                    <p className="text-gray-400 text-sm line-clamp-2">
                      {project.description || 'No description'}
                    </p>
                  </div>
                  <ExternalLink className="h-5 w-5 text-gray-500 ml-2 flex-shrink-0" />
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center text-gray-400">
                    <Clock className="h-4 w-4 mr-2" />
                    Created {formatDate(project.created_at)}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div
                        className={`h-2 w-2 rounded-full mr-2 ${
                          project.container_status === 'running'
                            ? 'bg-green-500'
                            : 'bg-gray-500'
                        }`}
                      />
                      <span className={getContainerStatusColor(project.container_status)}>
                        {getContainerStatusText(project.container_status)}
                      </span>
                    </div>

                    {project.git_initialized && (
                      <div className="flex items-center text-gray-400">
                        <GitBranch className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                </div>

                {project.status === 'archived' && (
                  <div className="mt-3 inline-flex items-center px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                    Archived
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
} 