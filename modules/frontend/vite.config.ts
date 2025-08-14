import { defineConfig, loadEnv, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Custom plugin to log build events
function buildLogger(): Plugin {
  const logDir = path.resolve(__dirname, '../logs/frontend')
  const buildLogFile = path.join(logDir, 'build.log')
  const errorLogFile = path.join(logDir, 'errors.log')

  // Ensure log directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true })
  }

  const log = (message: string, isError = false) => {
    const timestamp = new Date().toISOString()
    const logEntry = `[${timestamp}] ${message}\n`
    
    // Write to appropriate log file
    const logFile = isError ? errorLogFile : buildLogFile
    fs.appendFileSync(logFile, logEntry)
    
    // Also log to console
    if (isError) {
      console.error(message)
    } else {
      console.log(message)
    }
  }

  return {
    name: 'build-logger',
    
    buildStart() {
      log('=== Build started ===')
    },
    
    buildEnd() {
      log('=== Build completed successfully ===')
    },
    
    closeBundle() {
      log('=== Bundle closed ===')
    },
    
    configureServer(server) {
      // Log dev server events
      server.middlewares.use((req: any, res: any, next: any) => {
        if (req.url?.includes('/@vite/client')) {
          // Skip Vite client requests
          return next()
        }
        
        // Log HTTP errors
        const originalEnd = res.end
        res.end = function(...args: any[]) {
          if (res.statusCode >= 400) {
            log(`HTTP ${res.statusCode}: ${req.method} ${req.url}`, res.statusCode >= 500)
          }
          return originalEnd.apply(res, args)
        }
        
        next()
      })
      
      // Log WebSocket errors
      server.ws.on('error', (err: Error) => {
        log(`WebSocket error: ${err.message}`, true)
      })
    }
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file from parent directory (project root)
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  
  return {
    plugins: [react(), buildLogger()],
    
    // Define env variables that should be exposed to the client
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL),
      'import.meta.env.VITE_WS_URL': JSON.stringify(env.VITE_WS_URL),
      'import.meta.env.VITE_APP_NAME': JSON.stringify(env.VITE_APP_NAME),
      'import.meta.env.VITE_APP_VERSION': JSON.stringify(env.VITE_APP_VERSION),
    },
    
    // Add custom error handling
    server: {
      hmr: {
        overlay: true // Show errors in browser
      }
    },
    
    build: {
      // Generate source maps for better error tracking
      sourcemap: true,
      
      // Report compressed size
      reportCompressedSize: true,
      
      // Optimize chunk size
      chunkSizeWarningLimit: 1000,
      
      rollupOptions: {
        onwarn(warning, warn) {
          // Log warning to our custom logger
          console.warn(`Build warning: ${warning.message}`)
          warn(warning)
        },
        
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'monaco': ['@monaco-editor/react', 'monaco-editor'],
            'ui-vendor': ['lucide-react', 'wouter'],
            'query': ['@tanstack/react-query', 'axios']
          }
        }
      },
      
      // Optimize dependencies
      commonjsOptions: {
        transformMixedEsModules: true
      },
      
      // Minification options
      minify: 'terser'
    },
    
    // Optimize dependencies
    optimizeDeps: {
      include: ['react', 'react-dom', '@tanstack/react-query', 'axios', 'lucide-react']
    }
  }
})
