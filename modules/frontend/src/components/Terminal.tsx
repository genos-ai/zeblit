import React, { useState, useRef, useEffect } from 'react'
import type { KeyboardEvent } from 'react'
import { Terminal as TerminalIcon } from 'lucide-react'
import { useWebSocket } from '../lib/websocket'
import { logger } from '../lib/logger'

interface TerminalProps {
  projectId: string
  className?: string
}

interface TerminalLine {
  id: string
  type: 'input' | 'output' | 'error'
  content: string
  timestamp: Date
}

export const Terminal: React.FC<TerminalProps> = ({ projectId, className = '' }) => {
  const [lines, setLines] = useState<TerminalLine[]>([
    {
      id: '1',
      type: 'output',
      content: 'Welcome to Zeblit Terminal',
      timestamp: new Date()
    },
    {
      id: '2',
      type: 'output',
      content: 'Type "help" for available commands',
      timestamp: new Date()
    }
  ])
  const [currentCommand, setCurrentCommand] = useState('')
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isExecuting, setIsExecuting] = useState(false)
  
  const terminalRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // WebSocket handlers
  const { sendMessage } = useWebSocket(projectId, {
    terminal_output: (message) => {
      const newLine: TerminalLine = {
        id: crypto.randomUUID(),
        type: message.payload.is_error ? 'error' : 'output',
        content: message.payload.output,
        timestamp: new Date(message.timestamp)
      }
      setLines(prev => [...prev, newLine])
      setIsExecuting(false)
    },
    
    command_complete: (message) => {
      if (message.payload.exit_code !== 0) {
        const errorLine: TerminalLine = {
          id: crypto.randomUUID(),
          type: 'error',
          content: `Command exited with code ${message.payload.exit_code}`,
          timestamp: new Date()
        }
        setLines(prev => [...prev, errorLine])
      }
      setIsExecuting(false)
    }
  })

  // Auto-scroll to bottom when new lines are added
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [lines])

  // Focus input when terminal is clicked
  const handleTerminalClick = () => {
    inputRef.current?.focus()
  }

  const executeCommand = (command: string) => {
    if (!command.trim()) return

    // Add command to history
    setCommandHistory(prev => [...prev, command])
    setHistoryIndex(-1)

    // Add input line to terminal
    const inputLine: TerminalLine = {
      id: crypto.randomUUID(),
      type: 'input',
      content: `$ ${command}`,
      timestamp: new Date()
    }
    setLines(prev => [...prev, inputLine])

    // Handle built-in commands
    if (command === 'clear') {
      setLines([])
      setCurrentCommand('')
      return
    }

    if (command === 'help') {
      const helpLines: TerminalLine[] = [
        {
          id: crypto.randomUUID(),
          type: 'output',
          content: 'Available commands:',
          timestamp: new Date()
        },
        {
          id: crypto.randomUUID(),
          type: 'output',
          content: '  clear    - Clear the terminal',
          timestamp: new Date()
        },
        {
          id: crypto.randomUUID(),
          type: 'output',
          content: '  help     - Show this help message',
          timestamp: new Date()
        },
        {
          id: crypto.randomUUID(),
          type: 'output',
          content: '  pwd      - Print working directory',
          timestamp: new Date()
        },
        {
          id: crypto.randomUUID(),
          type: 'output',
          content: '  ls       - List files',
          timestamp: new Date()
        },
        {
          id: crypto.randomUUID(),
          type: 'output',
          content: '  python   - Run Python interpreter',
          timestamp: new Date()
        }
      ]
      setLines(prev => [...prev, ...helpLines])
      setCurrentCommand('')
      return
    }

    // Send command to backend for execution
    setIsExecuting(true)
    sendMessage('terminal_command', {
      project_id: projectId,
      command: command
    })
    
    logger.info('Terminal command executed', { command })
    setCurrentCommand('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      executeCommand(currentCommand)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 
          ? commandHistory.length - 1 
          : Math.max(0, historyIndex - 1)
        setHistoryIndex(newIndex)
        setCurrentCommand(commandHistory[newIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex !== -1) {
        const newIndex = historyIndex + 1
        if (newIndex >= commandHistory.length) {
          setHistoryIndex(-1)
          setCurrentCommand('')
        } else {
          setHistoryIndex(newIndex)
          setCurrentCommand(commandHistory[newIndex])
        }
      }
    } else if (e.key === 'c' && e.ctrlKey) {
      // Ctrl+C to cancel current command
      if (isExecuting) {
        sendMessage('terminal_interrupt', { project_id: projectId })
        const interruptLine: TerminalLine = {
          id: crypto.randomUUID(),
          type: 'output',
          content: '^C',
          timestamp: new Date()
        }
        setLines(prev => [...prev, interruptLine])
        setIsExecuting(false)
      }
      setCurrentCommand('')
    } else if (e.key === 'l' && e.ctrlKey) {
      // Ctrl+L to clear
      e.preventDefault()
      setLines([])
    }
  }

  const getLineColor = (type: TerminalLine['type']) => {
    switch (type) {
      case 'input':
        return 'text-blue-400'
      case 'error':
        return 'text-red-400'
      default:
        return 'text-gray-300'
    }
  }

  return (
    <div 
      className={`bg-gray-900 text-gray-300 font-mono text-sm overflow-hidden flex flex-col ${className}`}
      onClick={handleTerminalClick}
    >
      {/* Terminal Header */}
      <div className="bg-gray-800 px-4 py-2 flex items-center border-b border-gray-700">
        <TerminalIcon className="h-4 w-4 mr-2 text-gray-400" />
        <span className="text-gray-400 text-xs">Terminal - {projectId.slice(0, 8)}</span>
      </div>

      {/* Terminal Output */}
      <div 
        ref={terminalRef}
        className="flex-1 overflow-y-auto p-4 space-y-1"
      >
        {lines.map((line) => (
          <div 
            key={line.id} 
            className={`whitespace-pre-wrap break-all ${getLineColor(line.type)}`}
          >
            {line.content}
          </div>
        ))}
        
        {/* Current Input Line */}
        <div className="flex items-center">
          <span className="text-blue-400 mr-2">$</span>
          <input
            ref={inputRef}
            type="text"
            value={currentCommand}
            onChange={(e) => setCurrentCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isExecuting}
            className="flex-1 bg-transparent outline-none text-gray-300"
            spellCheck={false}
            autoComplete="off"
            placeholder={isExecuting ? 'Executing...' : 'Type a command...'}
          />
          {isExecuting && (
            <div className="ml-2 flex space-x-1">
              <div className="w-1 h-4 bg-gray-400 animate-pulse"></div>
              <div className="w-1 h-4 bg-gray-400 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-1 h-4 bg-gray-400 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
          )}
        </div>
      </div>

      {/* Terminal Status Bar */}
      <div className="bg-gray-800 px-4 py-1 text-xs text-gray-500 border-t border-gray-700 flex justify-between">
        <span>Ready</span>
        <span>{lines.length} lines</span>
      </div>
    </div>
  )
} 