import React, { useState } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { logger } from '../lib/logger'

interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  agentType?: string
  timestamp: Date
}

export const AgentChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'agent',
      content: 'Hello! I\'m the Development Manager. How can I help you build your application today?',
      agentType: 'Development Manager',
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')

  const handleSend = () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    logger.info('User sent message', { message: inputValue })
    setMessages(prev => [...prev, userMessage])
    setInputValue('')

    // Simulate agent response
    setTimeout(() => {
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: 'I understand. Let me help you with that...',
        agentType: 'Development Manager',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, agentMessage])
    }, 1000)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Agent Chat</h2>
        <p className="text-sm text-gray-400">Development Manager</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex space-x-2 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className="flex-shrink-0">
                {message.role === 'user' ? (
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                ) : (
                  <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
              <div>
                {message.agentType && (
                  <p className="text-xs text-gray-400 mb-1">{message.agentType}</p>
                )}
                <div
                  className={`rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-100'
                  }`}
                >
                  {message.content}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
} 