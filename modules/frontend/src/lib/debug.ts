/**
 * Debug utilities for Zeblit frontend development
 */

import { logger } from './logger'

interface DebugOptions {
  collapsed?: boolean
  showTrace?: boolean
}

/**
 * Debug context for React components
 */
export class ComponentDebugger {
  private componentName: string
  private renderCount = 0

  constructor(componentName: string) {
    this.componentName = componentName
  }

  logRender(props?: any, state?: any) {
    this.renderCount++
    logger.debug(`[${this.componentName}] Render #${this.renderCount}`, {
      props,
      state,
      timestamp: new Date().toISOString()
    })
  }

  logMount() {
    logger.debug(`[${this.componentName}] Mounted`)
  }

  logUnmount() {
    logger.debug(`[${this.componentName}] Unmounted after ${this.renderCount} renders`)
  }

  logEffect(effectName: string, dependencies?: any[]) {
    logger.debug(`[${this.componentName}] Effect: ${effectName}`, { dependencies })
  }
}

/**
 * Performance timer for debugging slow operations
 */
export class Timer {
  private startTime: number
  private name: string
  private marks: Map<string, number> = new Map()

  constructor(name: string) {
    this.name = name
    this.startTime = performance.now()
    logger.debug(`[Timer] ${name} started`)
  }

  mark(label: string) {
    const elapsed = performance.now() - this.startTime
    this.marks.set(label, elapsed)
    logger.debug(`[Timer] ${this.name} - ${label}: ${elapsed.toFixed(2)}ms`)
  }

  end() {
    const totalTime = performance.now() - this.startTime
    const marks = Array.from(this.marks.entries())
    
    logger.info(`[Timer] ${this.name} completed`, {
      totalTime: `${totalTime.toFixed(2)}ms`,
      marks: marks.map(([label, time]) => ({ label, time: `${time.toFixed(2)}ms` }))
    })
    
    return totalTime
  }
}

/**
 * Debug group for organizing related logs
 */
export function debugGroup(label: string, fn: () => void, options: DebugOptions = {}) {
  const { collapsed = true, showTrace = false } = options
  
  if (collapsed) {
    console.groupCollapsed(`🔍 ${label}`)
  } else {
    console.group(`🔍 ${label}`)
  }
  
  if (showTrace) {
    console.trace('Stack trace')
  }
  
  try {
    fn()
  } finally {
    console.groupEnd()
  }
}

/**
 * Assert with better error messages
 */
export function debugAssert(condition: any, message: string, data?: any): asserts condition {
  if (!condition) {
    logger.error(`Assertion failed: ${message}`, data)
    console.error('Assertion failed:', message, data)
    throw new Error(`Assertion failed: ${message}`)
  }
}

/**
 * Track API calls for debugging
 */
export class APIDebugger {
  private static requests = new Map<string, any>()

  static trackRequest(id: string, config: any) {
    this.requests.set(id, {
      config,
      startTime: performance.now(),
      timestamp: new Date().toISOString()
    })
  }

  static trackResponse(id: string, response: any) {
    const request = this.requests.get(id)
    if (request) {
      const duration = performance.now() - request.startTime
      logger.debug('API Call Complete', {
        id,
        method: request.config.method,
        url: request.config.url,
        duration: `${duration.toFixed(2)}ms`,
        status: response.status,
        size: JSON.stringify(response.data).length
      })
      this.requests.delete(id)
    }
  }

  static getActiveRequests() {
    return Array.from(this.requests.entries()).map(([id, req]) => ({
      id,
      ...req,
      pending: `${(performance.now() - req.startTime).toFixed(2)}ms`
    }))
  }
}

/**
 * React Hook Debugger
 */
export function useDebugValue(value: any, label?: string) {
  if (process.env.NODE_ENV === 'development') {
    const debugLabel = label || 'Debug Value'
    logger.debug(`[Hook] ${debugLabel}:`, value)
  }
}

/**
 * Memory leak detector
 */
export class MemoryLeakDetector {
  private intervals: Set<number> = new Set()
  private timeouts: Set<number> = new Set()
  private listeners: Map<string, number> = new Map()

  trackInterval(id: number) {
    this.intervals.add(id)
  }

  trackTimeout(id: number) {
    this.timeouts.add(id)
  }

  trackListener(type: string) {
    const count = this.listeners.get(type) || 0
    this.listeners.set(type, count + 1)
  }

  removeInterval(id: number) {
    this.intervals.delete(id)
  }

  removeTimeout(id: number) {
    this.timeouts.delete(id)
  }

  removeListener(type: string) {
    const count = this.listeners.get(type) || 0
    if (count > 0) {
      this.listeners.set(type, count - 1)
    }
  }

  report() {
    const report = {
      activeIntervals: this.intervals.size,
      activeTimeouts: this.timeouts.size,
      listeners: Object.fromEntries(this.listeners)
    }
    
    if (this.intervals.size > 0 || this.timeouts.size > 0) {
      logger.warn('Potential memory leaks detected', report)
    }
    
    return report
  }
}

/**
 * Global debug object for console access
 */
export const ZeblitDebug = {
  logger,
  Timer,
  APIDebugger,
  MemoryLeakDetector: new MemoryLeakDetector(),
  
  // Utility functions
  inspectProps: (component: any) => {
    console.log('Component Props:', component.props)
    console.log('Component State:', component.state)
  },
  
  // Performance helpers
  measureRender: (componentName: string, fn: () => void) => {
    const timer = new Timer(`Render: ${componentName}`)
    fn()
    timer.end()
  },
  
  // Network helpers
  showActiveRequests: () => APIDebugger.getActiveRequests(),
  
  // Memory helpers
  checkMemoryLeaks: () => ZeblitDebug.MemoryLeakDetector.report()
}

// Make debug tools available globally in development
if (process.env.NODE_ENV === 'development') {
  (window as any).ZeblitDebug = ZeblitDebug
  console.log('🔧 Zeblit Debug Tools loaded. Access via window.ZeblitDebug')
} 