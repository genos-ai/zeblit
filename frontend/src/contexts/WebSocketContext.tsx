import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useAuth } from './AuthContext'
import { getWebSocketService, WSMessage, WSMessageType } from '../lib/websocket'
import { logger } from '../lib/logger'

interface WebSocketContextType {
  isConnected: boolean
  sendMessage: (type: WSMessageType, payload: any) => void
  subscribeToProject: (projectId: string) => void
  unsubscribeFromProject: (projectId: string) => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  }
  return context
}

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const ws = getWebSocketService()

  useEffect(() => {
    if (isAuthenticated && user) {
      const token = localStorage.getItem('auth_token')
      if (token) {
        // Connect WebSocket when authenticated
        ws.connect(token)
          .then(() => {
            setIsConnected(true)
            logger.info('WebSocket connected in context')
          })
          .catch(error => {
            logger.error('Failed to connect WebSocket in context', { error })
            setIsConnected(false)
          })

        // Listen for connection status changes
        const statusHandler = () => {
          setIsConnected(ws.isConnected)
        }

        // Check connection status periodically
        const statusInterval = setInterval(statusHandler, 1000)

        return () => {
          clearInterval(statusInterval)
        }
      }
    } else {
      // Disconnect when not authenticated
      ws.disconnect()
      setIsConnected(false)
    }
  }, [isAuthenticated, user])

  const sendMessage = useCallback((type: WSMessageType, payload: any) => {
    ws.send({ type, payload })
  }, [])

  const subscribeToProject = useCallback((projectId: string) => {
    if (currentProjectId !== projectId) {
      // Unsubscribe from previous project
      if (currentProjectId) {
        sendMessage('project_unsubscribe' as WSMessageType, { project_id: currentProjectId })
      }
      
      // Subscribe to new project
      sendMessage('project_subscribe' as WSMessageType, { project_id: projectId })
      setCurrentProjectId(projectId)
      logger.info('Subscribed to project', { projectId })
    }
  }, [currentProjectId, sendMessage])

  const unsubscribeFromProject = useCallback((projectId: string) => {
    if (currentProjectId === projectId) {
      sendMessage('project_unsubscribe' as WSMessageType, { project_id: projectId })
      setCurrentProjectId(null)
      logger.info('Unsubscribed from project', { projectId })
    }
  }, [currentProjectId, sendMessage])

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        sendMessage,
        subscribeToProject,
        unsubscribeFromProject
      }}
    >
      {children}
    </WebSocketContext.Provider>
  )
} 