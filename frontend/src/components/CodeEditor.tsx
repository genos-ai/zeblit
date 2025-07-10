import React, { useRef, useEffect, useState } from 'react'
import * as monaco from 'monaco-editor'
import { FileCode, Save, Play } from 'lucide-react'
import { logger } from '../lib/logger'

export const CodeEditor: React.FC = () => {
  const editorRef = useRef<HTMLDivElement>(null)
  const monacoRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)
  const [fileName] = useState('App.tsx')

  useEffect(() => {
    if (editorRef.current) {
      // Initialize Monaco Editor
      const editor = monaco.editor.create(editorRef.current, {
        value: `// Welcome to Zeblit AI Development Platform
import React from 'react'

function App() {
  return (
    <div className="app">
      <h1>Hello, World!</h1>
      <p>Start building your application with AI assistance.</p>
    </div>
  )
}

export default App`,
        language: 'typescript',
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: {
          enabled: false
        },
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        wrappingStrategy: 'advanced',
        glyphMargin: false,
        folding: true,
        lineDecorationsWidth: 0,
        lineNumbersMinChars: 4
      })

      monacoRef.current = editor

      // Log editor changes
      editor.onDidChangeModelContent(() => {
        logger.debug('Editor content changed', { fileName })
      })

      return () => {
        editor.dispose()
      }
    }
  }, [fileName])

  const handleSave = () => {
    if (monacoRef.current) {
      const content = monacoRef.current.getValue()
      logger.info('File saved', { fileName, contentLength: content.length })
      // TODO: Implement actual save functionality
    }
  }

  const handleRun = () => {
    logger.info('Run button clicked', { fileName })
    // TODO: Implement run functionality
  }

  return (
    <div className="flex flex-col h-full">
      {/* Editor Header */}
      <div className="h-10 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4">
        <div className="flex items-center space-x-2">
          <FileCode className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-300">{fileName}</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleSave}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title="Save (Ctrl+S)"
          >
            <Save className="w-4 h-4 text-gray-300" />
          </button>
          <button
            onClick={handleRun}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title="Run"
          >
            <Play className="w-4 h-4 text-green-400" />
          </button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1" ref={editorRef} />
    </div>
  )
} 