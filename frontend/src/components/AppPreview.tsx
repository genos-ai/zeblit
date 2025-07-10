import React, { useState } from 'react'
import { RefreshCw, ExternalLink, Smartphone, Monitor } from 'lucide-react'
import { logger } from '../lib/logger'

export const AppPreview: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [viewMode, setViewMode] = useState<'desktop' | 'mobile'>('desktop')
  const previewUrl = 'http://localhost:3000' // This will be dynamic based on user's container

  const handleRefresh = () => {
    logger.info('Preview refresh clicked')
    setIsLoading(true)
    // Simulate refresh
    setTimeout(() => setIsLoading(false), 1000)
  }

  const handleOpenExternal = () => {
    logger.info('Open external clicked', { url: previewUrl })
    window.open(previewUrl, '_blank')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Preview Header */}
      <div className="h-10 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-300">Preview</span>
          <span className="text-xs text-gray-500">{previewUrl}</span>
        </div>
        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <div className="flex bg-gray-700 rounded">
            <button
              onClick={() => setViewMode('desktop')}
              className={`p-1.5 ${viewMode === 'desktop' ? 'bg-gray-600' : ''} rounded-l transition-colors`}
              title="Desktop View"
            >
              <Monitor className="w-4 h-4 text-gray-300" />
            </button>
            <button
              onClick={() => setViewMode('mobile')}
              className={`p-1.5 ${viewMode === 'mobile' ? 'bg-gray-600' : ''} rounded-r transition-colors`}
              title="Mobile View"
            >
              <Smartphone className="w-4 h-4 text-gray-300" />
            </button>
          </div>
          
          <button
            onClick={handleRefresh}
            className={`p-1.5 hover:bg-gray-700 rounded transition-colors ${isLoading ? 'animate-spin' : ''}`}
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4 text-gray-300" />
          </button>
          <button
            onClick={handleOpenExternal}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="w-4 h-4 text-gray-300" />
          </button>
        </div>
      </div>

      {/* Preview Content */}
      <div className="flex-1 bg-white relative">
        {isLoading && (
          <div className="absolute inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-10">
            <div className="text-white">Loading...</div>
          </div>
        )}
        
        <div className={`h-full ${viewMode === 'mobile' ? 'max-w-sm mx-auto' : ''}`}>
          {/* For now, show a placeholder. In production, this will be an iframe */}
          <div className="h-full flex items-center justify-center bg-gray-100 text-gray-600">
            <div className="text-center">
              <Monitor className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">App Preview</h3>
              <p className="text-sm">Your application will appear here</p>
              <p className="text-xs mt-2 text-gray-500">Container not yet running</p>
            </div>
          </div>
          
          {/* This will be replaced with an iframe when container is running
          <iframe
            src={previewUrl}
            className="w-full h-full border-0"
            title="App Preview"
            sandbox="allow-scripts allow-same-origin allow-forms"
          />
          */}
        </div>
      </div>
    </div>
  )
} 