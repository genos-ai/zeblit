import React, { useState } from 'react'
import { Bot, Code, Database, Briefcase, Building, Server } from 'lucide-react'
import { logger } from '../lib/logger'

interface Agent {
  id: string
  name: string
  shortName: string
  icon: React.ReactNode
  status: 'idle' | 'working' | 'completed'
}

export const AgentTabs: React.FC = () => {
  const [activeAgent, setActiveAgent] = useState('dev-manager')

  const agents: Agent[] = [
    {
      id: 'dev-manager',
      name: 'Development Manager',
      shortName: 'DevMgr',
      icon: <Bot className="w-4 h-4" />,
      status: 'idle'
    },
    {
      id: 'product-manager',
      name: 'Product Manager',
      shortName: 'PM',
      icon: <Briefcase className="w-4 h-4" />,
      status: 'idle'
    },
    {
      id: 'data-analyst',
      name: 'Data Analyst',
      shortName: 'Data',
      icon: <Database className="w-4 h-4" />,
      status: 'idle'
    },
    {
      id: 'engineer',
      name: 'Senior Engineer',
      shortName: 'Eng',
      icon: <Code className="w-4 h-4" />,
      status: 'working'
    },
    {
      id: 'architect',
      name: 'Architect',
      shortName: 'Arch',
      icon: <Building className="w-4 h-4" />,
      status: 'idle'
    },
    {
      id: 'platform-engineer',
      name: 'Platform Engineer',
      shortName: 'Platform',
      icon: <Server className="w-4 h-4" />,
      status: 'completed'
    }
  ]

  const handleAgentClick = (agentId: string) => {
    logger.info('Agent tab clicked', { agentId })
    setActiveAgent(agentId)
  }

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'working':
        return 'text-yellow-400'
      case 'completed':
        return 'text-green-400'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <div className="h-full flex items-center px-4 space-x-2">
      {agents.map((agent) => (
        <button
          key={agent.id}
          onClick={() => handleAgentClick(agent.id)}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded transition-colors ${
            activeAgent === agent.id
              ? 'bg-gray-700 text-white'
              : 'hover:bg-gray-800 text-gray-400'
          }`}
          title={agent.name}
        >
          <span className={getStatusColor(agent.status)}>{agent.icon}</span>
          <span className="text-sm">{agent.shortName}</span>
          {agent.status === 'working' && (
            <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
          )}
        </button>
      ))}
    </div>
  )
} 