import React from 'react'
import { Settings, GitBranch, User, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { logger } from '../lib/logger'

export const Header: React.FC = () => {
  const { user, logout } = useAuth()
  logger.debug('Header component rendered')

  return (
    <header className="h-14 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
      {/* Left side - Logo and Project Name */}
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-bold text-white">Zeblit</h1>
        <span className="text-gray-400">|</span>
        <span className="text-gray-300">My Project</span>
      </div>

      {/* Right side - User Info, Git Status, Settings */}
      <div className="flex items-center space-x-6">
        {/* Git Status */}
        <div className="flex items-center space-x-2 text-gray-300">
          <GitBranch className="w-4 h-4" />
          <span className="text-sm">main</span>
          <span className="text-xs text-green-400">✓</span>
        </div>

        {/* User Info */}
        <div className="flex items-center space-x-2 text-gray-300">
          <User className="w-4 h-4" />
          <span className="text-sm">{user?.full_name || 'Guest User'}</span>
        </div>

        {/* Settings */}
        <button 
          className="p-2 hover:bg-gray-700 rounded transition-colors"
          onClick={() => logger.info('Settings clicked')}
          title="Settings"
        >
          <Settings className="w-5 h-5 text-gray-300" />
        </button>

        {/* Logout */}
        <button 
          className="p-2 hover:bg-gray-700 rounded transition-colors"
          onClick={logout}
          title="Logout"
        >
          <LogOut className="w-5 h-5 text-gray-300" />
        </button>
      </div>
    </header>
  )
} 