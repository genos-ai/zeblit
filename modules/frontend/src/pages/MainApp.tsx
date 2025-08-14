import React from 'react'
import { Header } from '../components/Header'
import { AgentChat } from '../components/AgentChat'
import { CodeEditor } from '../components/CodeEditor'
import { AppPreview } from '../components/AppPreview'
import { AgentTabs } from '../components/AgentTabs'

export const MainApp: React.FC = () => {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100">
      {/* Header */}
      <Header />
      
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Agent Chat */}
        <div className="w-96 border-r border-gray-700 flex flex-col">
          <AgentChat />
        </div>
        
        {/* Center Panel - Code Editor */}
        <div className="flex-1 flex flex-col">
          <CodeEditor />
        </div>
        
        {/* Right Panel - App Preview */}
        <div className="w-96 border-l border-gray-700 flex flex-col">
          <AppPreview />
        </div>
      </div>
      
      {/* Bottom Panel - Agent Tabs */}
      <div className="h-12 border-t border-gray-700">
        <AgentTabs />
      </div>
    </div>
  )
} 