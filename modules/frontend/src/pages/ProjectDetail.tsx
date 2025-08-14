import React, { useState, useEffect, useRef } from 'react'
import { useParams, useLocation } from 'wouter'
import { 
  ArrowLeft, 
  Play, 
  Save, 
  GitBranch, 
  Terminal as TerminalIcon,
  MessageSquare,
  FileText,
  Globe,
  Settings,
  ChevronLeft,
  ChevronRight,
  Wifi,
  WifiOff
} from 'lucide-react'
import Editor from '@monaco-editor/react'
import { useAuth } from '../contexts/AuthContext'
import { useWebSocketContext } from '../contexts/WebSocketContext'
import { useWebSocket } from '../lib/websocket'
import { apiClient } from '../lib/api-client'
import { logger } from '../lib/logger'
import { Terminal } from '../components/Terminal'

interface Project {
  id: string
  name: string
  description: string
  language: string
  framework?: string
  status: string
  git_initialized: boolean
  container_status?: string
}

interface Agent {
  id: string
  name: string
  type: string
  status: 'idle' | 'thinking' | 'working'
  lastMessage?: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  content: string
  agentType?: string
  timestamp: string
}

const MOCK_AGENTS: Agent[] = [
  { id: '1', name: 'Dev Manager', type: 'dev_manager', status: 'idle' },
  { id: '2', name: 'Product Manager', type: 'product_manager', status: 'idle' },
  { id: '3', name: 'Data Analyst', type: 'data_analyst', status: 'idle' },
  { id: '4', name: 'Engineer', type: 'engineer', status: 'idle' },
  { id: '5', name: 'Architect', type: 'architect', status: 'idle' },
  { id: '6', name: 'Platform Eng', type: 'platform_engineer', status: 'idle' },
]

export const ProjectDetail: React.FC = () => {
  const params = useParams()
  const id = params.id as string
  const [, setLocation] = useLocation()
  const { user } = useAuth()
  const { isConnected: wsConnected, subscribeToProject, unsubscribeFromProject } = useWebSocketContext()
  
  // Layout state
  const [leftPanelWidth, setLeftPanelWidth] = useState(320)
  const [rightPanelWidth, setRightPanelWidth] = useState(400)
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false)
  const [isRightPanelCollapsed, setIsRightPanelCollapsed] = useState(false)
  
  // Project state
  const [project, setProject] = useState<Project | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Editor state
  const [code, setCode] = useState('# Welcome to Zeblit!\n\nprint("Hello, AI-powered development!")')
  const [currentFile, setCurrentFile] = useState('main.py')
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  
  // Agent state
  const [agents, setAgents] = useState<Agent[]>(MOCK_AGENTS)
  const [selectedAgent, setSelectedAgent] = useState(MOCK_AGENTS[0])
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [isAgentTyping, setIsAgentTyping] = useState(false)
  
  // Console state
  const [consoleOutput, setConsoleOutput] = useState<string[]>([])
  
  // Refs
  const leftResizeRef = useRef<HTMLDivElement>(null)
  const rightResizeRef = useRef<HTMLDivElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // WebSocket handlers
  const { sendMessage } = useWebSocket(id, {
    agent_message: (message) => {
      const chatMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: message.payload.content,
        agentType: message.payload.agent_type,
        timestamp: message.timestamp
      }
      setChatHistory(prev => [...prev, chatMsg])
      setIsAgentTyping(false)
      logger.info('Received agent message', { agentType: message.payload.agent_type })
    },
    
    agent_status: (message) => {
      const { agent_type, status } = message.payload
      setAgents(prev => prev.map(agent => 
        agent.type === agent_type ? { ...agent, status } : agent
      ))
      logger.info('Agent status update', { agentType: agent_type, status })
    },
    
    console_output: (message) => {
      setConsoleOutput(prev => [...prev, message.payload.output])
    },
    
    file_update: (message) => {
      const { file_path, content } = message.payload
      if (file_path === currentFile) {
        setCode(content)
        setHasUnsavedChanges(false)
      }
    }
  })

  useEffect(() => {
    fetchProject()
    
    // Subscribe to project updates
    if (id) {
      subscribeToProject(id)
      
      return () => {
        unsubscribeFromProject(id)
      }
    }
  }, [id, subscribeToProject, unsubscribeFromProject])

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  const fetchProject = async () => {
    try {
      setIsLoading(true)
      setError('')
      const response = await apiClient.get<Project>(`/projects/${id}`)
      setProject(response.data)
      logger.info('Project loaded', { projectId: id })
    } catch (err: any) {
      logger.error('Failed to load project', { error: err.message })
      setError('Failed to load project')
    } finally {
      setIsLoading(false)
    }
  }

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setCode(value)
      setHasUnsavedChanges(true)
    }
  }

  const handleSave = async () => {
    sendMessage('file_save', {
      project_id: id,
      file_path: currentFile,
      content: code
    })
    logger.info('Saving file', { file: currentFile })
    setHasUnsavedChanges(false)
  }

  const handleRun = async () => {
    sendMessage('code_execute', {
      project_id: id,
      file_path: currentFile
    })
    logger.info('Running code')
    setConsoleOutput([])
  }

  const handleSendMessage = () => {
    if (!chatMessage.trim()) return
    
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: chatMessage,
      timestamp: new Date().toISOString()
    }
    
    setChatHistory(prev => [...prev, userMsg])
    setChatMessage('')
    setIsAgentTyping(true)
    
    // Send to selected agent
    sendMessage('agent_message', {
      project_id: id,
      agent_type: selectedAgent.type,
      content: chatMessage
    })
  }

  // Resize handlers
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (leftResizeRef.current?.dataset.resizing === 'true') {
        const newWidth = e.clientX
        setLeftPanelWidth(Math.max(200, Math.min(600, newWidth)))
      }
      if (rightResizeRef.current?.dataset.resizing === 'true') {
        const newWidth = window.innerWidth - e.clientX
        setRightPanelWidth(Math.max(300, Math.min(800, newWidth)))
      }
    }

    const handleMouseUp = () => {
      if (leftResizeRef.current) leftResizeRef.current.dataset.resizing = 'false'
      if (rightResizeRef.current) rightResizeRef.current.dataset.resizing = 'false'
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading project...</p>
        </div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || 'Project not found'}</p>
          <button
            onClick={() => setLocation('/dashboard')}
            className="text-blue-500 hover:text-blue-400"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 flex-shrink-0">
        <div className="flex items-center justify-between h-14 px-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setLocation('/dashboard')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <h1 className="text-lg font-semibold text-white">{project.name}</h1>
            <GitBranch className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-400">main</span>
            {wsConnected ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-red-500" />
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={handleSave}
              disabled={!hasUnsavedChanges}
              className={`flex items-center px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                hasUnsavedChanges
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-700 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Save className="h-4 w-4 mr-1.5" />
              Save
            </button>
            <button
              onClick={handleRun}
              className="flex items-center px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium transition-colors"
            >
              <Play className="h-4 w-4 mr-1.5" />
              Run
            </button>
            <button className="text-gray-400 hover:text-white transition-colors">
              <Settings className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Agent Chat */}
        <div 
          className={`bg-gray-850 border-r border-gray-700 flex flex-col transition-all duration-300 ${
            isLeftPanelCollapsed ? 'w-12' : ''
          }`}
          style={{ width: isLeftPanelCollapsed ? '48px' : `${leftPanelWidth}px` }}
        >
          {isLeftPanelCollapsed ? (
            <button
              onClick={() => setIsLeftPanelCollapsed(false)}
              className="h-full flex items-center justify-center text-gray-400 hover:text-white"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          ) : (
            <>
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h2 className="font-semibold text-white flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2" />
                  Agent Chat
                </h2>
                <button
                  onClick={() => setIsLeftPanelCollapsed(true)}
                  className="text-gray-400 hover:text-white"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
              </div>
              
              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-gray-500 mt-8">
                    <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Start a conversation with {selectedAgent.name}</p>
                    <p className="text-sm mt-2">Ask for help with your code!</p>
                  </div>
                ) : (
                  <>
                    {chatHistory.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-2 ${
                            msg.role === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-700 text-gray-100'
                          }`}
                        >
                          {msg.role === 'agent' && msg.agentType && (
                            <div className="text-xs text-gray-400 mb-1">
                              {agents.find(a => a.type === msg.agentType)?.name}
                            </div>
                          )}
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {isAgentTyping && (
                      <div className="flex justify-start">
                        <div className="bg-gray-700 text-gray-100 rounded-lg px-4 py-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </>
                )}
              </div>
              
              {/* Chat Input */}
              <div className="p-4 border-t border-gray-700">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask the AI agents..."
                    className="flex-1 px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!wsConnected}
                    className={`px-4 py-2 rounded-md transition-colors ${
                      wsConnected
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    Send
                  </button>
                </div>
              </div>
            </>
          )}
          
          {/* Resize Handle */}
          {!isLeftPanelCollapsed && (
            <div
              ref={leftResizeRef}
              onMouseDown={() => leftResizeRef.current!.dataset.resizing = 'true'}
              className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500 transition-colors"
            />
          )}
        </div>

        {/* Center - Code Editor */}
        <div className="flex-1 flex flex-col bg-gray-900">
          {/* File Tabs */}
          <div className="bg-gray-800 border-b border-gray-700 flex items-center px-2 h-10">
            <div className="flex items-center bg-gray-700 rounded px-3 py-1">
              <FileText className="h-4 w-4 mr-2 text-gray-400" />
              <span className="text-sm text-white">{currentFile}</span>
              {hasUnsavedChanges && <span className="ml-2 text-yellow-500">•</span>}
            </div>
          </div>
          
          {/* Monaco Editor */}
          <div className="flex-1">
            <Editor
              height="100%"
              defaultLanguage="python"
              theme="vs-dark"
              value={code}
              onChange={handleEditorChange}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                rulers: [80],
                wordWrap: 'on',
                automaticLayout: true,
              }}
            />
          </div>
        </div>

        {/* Right Panel - Preview */}
        <div
          className={`bg-gray-850 border-l border-gray-700 flex flex-col transition-all duration-300 ${
            isRightPanelCollapsed ? 'w-12' : ''
          }`}
          style={{ width: isRightPanelCollapsed ? '48px' : `${rightPanelWidth}px` }}
        >
          {isRightPanelCollapsed ? (
            <button
              onClick={() => setIsRightPanelCollapsed(false)}
              className="h-full flex items-center justify-center text-gray-400 hover:text-white"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
          ) : (
            <>
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <h2 className="font-semibold text-white flex items-center">
                  <Globe className="h-5 w-5 mr-2" />
                  Preview
                </h2>
                <button
                  onClick={() => setIsRightPanelCollapsed(true)}
                  className="text-gray-400 hover:text-white"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
              
              {/* Preview Content */}
              <div className="flex-1 bg-white">
                <div className="h-full flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Preview will appear here</p>
                    <p className="text-sm mt-2">Run your code to see the output</p>
                  </div>
                </div>
              </div>
              
              {/* Console Output */}
              <Terminal 
                projectId={id || ''} 
                className="h-64 border-t border-gray-700"
              />
            </>
          )}
          
          {/* Resize Handle */}
          {!isRightPanelCollapsed && (
            <div
              ref={rightResizeRef}
              onMouseDown={() => rightResizeRef.current!.dataset.resizing = 'true'}
              className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500 transition-colors"
            />
          )}
        </div>
      </div>

      {/* Bottom - Agent Status Tabs */}
      <div className="bg-gray-800 border-t border-gray-700 h-12 flex items-center px-4 space-x-1 flex-shrink-0">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => setSelectedAgent(agent)}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors flex items-center ${
              selectedAgent.id === agent.id
                ? 'bg-gray-700 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            <div className={`w-2 h-2 rounded-full mr-2 ${
              agent.status === 'working' ? 'bg-green-500 animate-pulse' :
              agent.status === 'thinking' ? 'bg-yellow-500 animate-pulse' :
              'bg-gray-500'
            }`} />
            {agent.name}
          </button>
        ))}
      </div>
    </div>
  )
} 