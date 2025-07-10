import { logger } from './logger'

export type WSMessageType = 
  | 'agent_message'
  | 'agent_status'
  | 'file_update'
  | 'file_save'
  | 'console_output'
  | 'task_update'
  | 'error'
  | 'ping'
  | 'pong'
  | 'terminal_output'
  | 'terminal_command'
  | 'terminal_interrupt'
  | 'command_complete'
  | 'code_execute'

export interface WSMessage {
  type: WSMessageType
  payload: any
  timestamp: string
  id?: string
}

export type WSEventHandler = (message: WSMessage) => void

interface WSConfig {
  url: string
  reconnect: boolean
  reconnectInterval: number
  maxReconnectAttempts: number
  heartbeatInterval: number
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private config: WSConfig
  private eventHandlers: Map<WSMessageType, Set<WSEventHandler>> = new Map()
  private reconnectAttempts = 0
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private isIntentionallyClosed = false
  private messageQueue: WSMessage[] = []
  private connectionPromise: Promise<void> | null = null

  constructor(config: Partial<WSConfig> = {}) {
    this.config = {
      url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config
    }
  }

  async connect(token: string, projectId?: string): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise
    }

    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        this.isIntentionallyClosed = false
        
        // Build WebSocket URL with auth token and optional project ID
        const url = new URL(this.config.url)
        url.searchParams.set('token', token)
        if (projectId) {
          url.searchParams.set('project_id', projectId)
        }

        logger.info('WebSocket connecting', { url: url.toString() })
        this.ws = new WebSocket(url.toString())

        this.ws.onopen = () => {
          logger.info('WebSocket connected')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.flushMessageQueue()
          this.connectionPromise = null
          resolve()
        }

        this.ws.onclose = (event) => {
          logger.info('WebSocket closed', { code: event.code, reason: event.reason })
          this.stopHeartbeat()
          this.connectionPromise = null
          
          if (!this.isIntentionallyClosed && this.config.reconnect) {
            this.scheduleReconnect(token, projectId)
          }
        }

        this.ws.onerror = (error) => {
          logger.error('WebSocket error', { error })
          this.connectionPromise = null
          reject(error)
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            logger.error('Failed to parse WebSocket message', { error, data: event.data })
          }
        }
      } catch (error) {
        this.connectionPromise = null
        reject(error)
      }
    })

    return this.connectionPromise
  }

  disconnect(): void {
    this.isIntentionallyClosed = true
    this.stopHeartbeat()
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    
    logger.info('WebSocket disconnected')
  }

  send(message: Omit<WSMessage, 'timestamp'>): void {
    const fullMessage: WSMessage = {
      ...message,
      timestamp: new Date().toISOString(),
      id: crypto.randomUUID()
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(fullMessage))
      logger.debug('WebSocket message sent', { type: message.type })
    } else {
      // Queue message if not connected
      this.messageQueue.push(fullMessage)
      logger.debug('WebSocket message queued', { type: message.type })
    }
  }

  on(type: WSMessageType, handler: WSEventHandler): () => void {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, new Set())
    }
    
    this.eventHandlers.get(type)!.add(handler)
    
    // Return unsubscribe function
    return () => {
      this.eventHandlers.get(type)?.delete(handler)
    }
  }

  private handleMessage(message: WSMessage): void {
    logger.debug('WebSocket message received', { type: message.type })
    
    // Handle ping/pong
    if (message.type === 'ping') {
      this.send({ type: 'pong', payload: {} })
      return
    }
    
    // Call registered handlers
    const handlers = this.eventHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          logger.error('WebSocket handler error', { error, messageType: message.type })
        }
      })
    }
  }

  private scheduleReconnect(token: string, projectId?: string): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      logger.error('WebSocket max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    )

    logger.info(`WebSocket reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    
    this.reconnectTimer = window.setTimeout(() => {
      this.connect(token, projectId)
    }, delay)
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', payload: {} })
      }
    }, this.config.heartbeatInterval)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()!
      this.ws.send(JSON.stringify(message))
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}

// Singleton instance
let wsInstance: WebSocketService | null = null

export const getWebSocketService = (): WebSocketService => {
  if (!wsInstance) {
    wsInstance = new WebSocketService()
  }
  return wsInstance
}

// React hook for WebSocket
import { useEffect, useCallback } from 'react'

export const useWebSocket = (
  projectId?: string,
  handlers?: Partial<Record<WSMessageType, WSEventHandler>>
) => {
  const ws = getWebSocketService()

  useEffect(() => {
    const unsubscribers: Array<() => void> = []
    
    // Register handlers
    if (handlers) {
      Object.entries(handlers).forEach(([type, handler]) => {
        if (handler) {
          const unsubscribe = ws.on(type as WSMessageType, handler)
          unsubscribers.push(unsubscribe)
        }
      })
    }
    
    // Connect if not already connected
    const token = localStorage.getItem('auth_token')
    if (token && !ws.isConnected) {
      ws.connect(token, projectId).catch(error => {
        logger.error('Failed to connect WebSocket', { error })
      })
    }
    
    // Cleanup
    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe())
    }
  }, [projectId, handlers])

  const sendMessage = useCallback((type: WSMessageType, payload: any) => {
    ws.send({ type, payload })
  }, [])

  return {
    isConnected: ws.isConnected,
    sendMessage,
    disconnect: () => ws.disconnect()
  }
} 