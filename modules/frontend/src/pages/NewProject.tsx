import React, { useState, useEffect } from 'react'
import { useLocation } from 'wouter'
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  Loader2, 
  Lock, 
  Globe, 
  Rocket 
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { apiClient } from '../lib/api-client'
import { logger } from '../lib/logger'

interface ProjectTemplate {
  id: string
  name: string
  description: string
  framework: string
  language: string
  tags: string[]
  icon_url?: string
  preview_url?: string
  settings: Record<string, any>
  popularity_score: number
  created_at: string
}

interface ProjectFormData {
  name: string
  description: string
  template_id?: string
  language: string
  framework?: string
  is_public: boolean
}

export const NewProject: React.FC = () => {
  const [, setLocation] = useLocation()
  const { user } = useAuth()
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(true)
  const [error, setError] = useState('')
  const [templates, setTemplates] = useState<ProjectTemplate[]>([])
  
  const [formData, setFormData] = useState<ProjectFormData>({
    name: '',
    description: '',
    template_id: undefined,
    language: 'python',
    framework: undefined,
    is_public: false
  })

  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null)

  const totalSteps = 3

  // Fetch templates from backend
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setIsLoadingTemplates(true)
        const response = await apiClient.get('/projects/templates')
        setTemplates(response.data || [])
        logger.info('Fetched project templates', { count: response.data?.length })
      } catch (err: any) {
        logger.error('Failed to fetch templates', { error: err.message })
        setError('Failed to load project templates. Please try again.')
      } finally {
        setIsLoadingTemplates(false)
      }
    }

    fetchTemplates()
  }, [])

  // Template icon mapping (fallback since backend might not have icons)
  const getTemplateIcon = (template: ProjectTemplate): string => {
    if (template.icon_url) return template.icon_url
    
    // Fallback based on framework/name
    if (template.framework?.toLowerCase().includes('react')) return '⚛️'
    if (template.framework?.toLowerCase().includes('fastapi')) return '🔌'
    if (template.framework?.toLowerCase().includes('django')) return '🐍'
    if (template.framework?.toLowerCase().includes('next')) return '🌐'
    if (template.name.toLowerCase().includes('cli')) return '⚡'
    if (template.name.toLowerCase().includes('ml') || template.name.toLowerCase().includes('machine')) return '🤖'
    if (template.name.toLowerCase().includes('blank')) return '📄'
    return '🏗️'
  }

  const handleTemplateSelect = (template: ProjectTemplate) => {
    setSelectedTemplate(template)
    setFormData(prev => ({
      ...prev,
      template_id: template.id,
      language: template.language,
      framework: template.framework
    }))
  }

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(prev => prev + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1)
    }
  }

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1:
        return selectedTemplate !== null
      case 2:
        return formData.name.trim().length >= 3
      case 3:
        return true // Review step is always valid
      default:
        return false
    }
  }

  const handleSubmit = async () => {
    setError('')
    setIsLoading(true)

    try {
      const response = await apiClient.post('/projects', {
        name: formData.name,
        description: formData.description,
        template_id: formData.template_id,
        language: formData.language,
        framework: formData.framework,
        is_public: formData.is_public
      })

      logger.info('Project created successfully', { projectId: response.data.id })
      
      // Redirect to project page
      setLocation(`/projects/${response.data.id}`)
    } catch (err: any) {
      logger.error('Failed to create project', { error: err.message })
      
      // Handle different error response formats
      let errorMessage = 'Failed to create project. Please try again.'
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          // Handle validation errors array
          errorMessage = detail.map(error => error.msg || error.message || String(error)).join(', ')
        } else if (typeof detail === 'object') {
          errorMessage = detail.msg || detail.message || JSON.stringify(detail)
        }
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const renderStepIndicator = () => {
    return (
      <div className="flex items-center justify-center mb-8">
        {[1, 2, 3].map((step) => (
          <React.Fragment key={step}>
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                step < currentStep
                  ? 'bg-green-600 border-green-600'
                  : step === currentStep
                  ? 'bg-blue-600 border-blue-600'
                  : 'bg-gray-800 border-gray-600'
              }`}
            >
              {step < currentStep ? (
                <Check className="h-5 w-5 text-white" />
              ) : (
                <span className="text-white font-semibold">{step}</span>
              )}
            </div>
            {step < 3 && (
              <div
                className={`w-24 h-1 ${
                  step < currentStep ? 'bg-green-600' : 'bg-gray-700'
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    )
  }

  const renderStep1 = () => (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">Choose a Template</h2>
      <p className="text-gray-400 mb-6">
        Select a template to get started quickly, or start from scratch
      </p>

      {isLoadingTemplates ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-12 w-12 text-blue-500 animate-spin" />
          <p className="ml-4 text-gray-400">Loading templates...</p>
        </div>
      ) : error ? (
        <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-500 px-4 py-3 rounded">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {templates.map((template) => (
            <button
              key={template.id}
              onClick={() => handleTemplateSelect(template)}
              className={`p-6 rounded-lg border-2 text-left transition-all ${
                selectedTemplate?.id === template.id
                  ? 'border-blue-500 bg-blue-500 bg-opacity-10'
                  : 'border-gray-700 hover:border-gray-600 bg-gray-800'
              }`}
            >
              <div className="flex items-start">
                <span className="text-3xl mr-4">{getTemplateIcon(template)}</span>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white mb-1">
                    {template.name}
                  </h3>
                  <p className="text-sm text-gray-400 mb-3">
                    {template.description}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {template.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )

  const renderStep2 = () => (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">Project Details</h2>
      <p className="text-gray-400 mb-6">
        Give your project a name and description
      </p>

      <div className="space-y-6 max-w-lg">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
            Project Name *
          </label>
          <input
            id="name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="my-awesome-project"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Must be at least 3 characters. Use lowercase letters, numbers, and hyphens.
          </p>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-2">
            Description
          </label>
          <textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            rows={4}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="A brief description of your project..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Visibility
          </label>
          <div className="space-y-2">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="visibility"
                checked={!formData.is_public}
                onChange={() => setFormData(prev => ({ ...prev, is_public: false }))}
                className="mr-3 text-blue-600 focus:ring-blue-500"
              />
              <Lock className="h-4 w-4 mr-2 text-gray-400" />
              <div>
                <span className="text-white">Private</span>
                <p className="text-xs text-gray-500">Only you can see this project</p>
              </div>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="visibility"
                checked={formData.is_public}
                onChange={() => setFormData(prev => ({ ...prev, is_public: true }))}
                className="mr-3 text-blue-600 focus:ring-blue-500"
              />
              <Globe className="h-4 w-4 mr-2 text-gray-400" />
              <div>
                <span className="text-white">Public</span>
                <p className="text-xs text-gray-500">Anyone can view this project</p>
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">Review & Create</h2>
      <p className="text-gray-400 mb-6">
        Review your project settings before creating
      </p>

      {error && (
        <div className="mb-6 bg-red-500 bg-opacity-10 border border-red-500 text-red-500 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="bg-gray-800 rounded-lg p-6 space-y-4 max-w-lg">
        <div>
          <span className="text-sm text-gray-400">Template</span>
          <p className="text-white font-medium">
            {selectedTemplate?.icon_url ? (
              <img src={selectedTemplate.icon_url} alt={selectedTemplate.name} className="inline h-5 w-5 mr-2 rounded-full" />
            ) : selectedTemplate ? (
              <span className="text-3xl mr-2">{getTemplateIcon(selectedTemplate)}</span>
            ) : null}
            {selectedTemplate?.name}
          </p>
        </div>

        <div>
          <span className="text-sm text-gray-400">Project Name</span>
          <p className="text-white font-medium">{formData.name || 'Not set'}</p>
        </div>

        {formData.description && (
          <div>
            <span className="text-sm text-gray-400">Description</span>
            <p className="text-white">{formData.description}</p>
          </div>
        )}

        <div>
          <span className="text-sm text-gray-400">Language</span>
          <p className="text-white font-medium">{formData.language}</p>
        </div>

        {formData.framework && (
          <div>
            <span className="text-sm text-gray-400">Framework</span>
            <p className="text-white font-medium">{formData.framework}</p>
          </div>
        )}

        <div>
          <span className="text-sm text-gray-400">Visibility</span>
          <p className="text-white font-medium flex items-center">
            {formData.is_public ? (
              <>
                <Globe className="h-4 w-4 mr-1" /> Public
              </>
            ) : (
              <>
                <Lock className="h-4 w-4 mr-1" /> Private
              </>
            )}
          </p>
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-500 bg-opacity-10 border border-blue-500 rounded-lg max-w-lg">
        <p className="text-sm text-blue-400">
          <Rocket className="inline h-4 w-4 mr-1" />
          Your project will be created with a development container and AI agents ready to help you build!
        </p>
      </div>
    </div>
  )

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return renderStep1()
      case 2:
        return renderStep2()
      case 3:
        return renderStep3()
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => setLocation('/dashboard')}
                className="text-gray-400 hover:text-white transition-colors mr-4"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <h1 className="text-xl font-bold text-white">Create New Project</h1>
            </div>
            <span className="text-gray-400">
              Step {currentStep} of {totalSteps}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderStepIndicator()}
        
        <div className="bg-gray-850 rounded-lg p-8">
          {renderCurrentStep()}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className={`flex items-center px-4 py-2 rounded-md font-medium ${
              currentStep === 1
                ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                : 'bg-gray-700 text-white hover:bg-gray-600'
            }`}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </button>

          {currentStep < totalSteps ? (
            <button
              onClick={handleNext}
              disabled={!validateStep(currentStep)}
              className={`flex items-center px-4 py-2 rounded-md font-medium ${
                validateStep(currentStep)
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-800 text-gray-500 cursor-not-allowed'
              }`}
            >
              Next
              <ArrowRight className="h-4 w-4 ml-2" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isLoading || !validateStep(currentStep)}
              className={`flex items-center px-4 py-2 rounded-md font-medium ${
                !isLoading && validateStep(currentStep)
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-800 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Create Project
                </>
              )}
            </button>
          )}
        </div>
      </main>
    </div>
  )
} 