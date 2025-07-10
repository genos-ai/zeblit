/**
 * Frontend logging system with comprehensive error tracking and debugging capabilities.
 * 
 * Features:
 * - Multiple log levels (debug, info, warn, error)
 * - Structured logging with context
 * - Error boundary integration
 * - Network request logging
 * - Performance monitoring
 * - Console styling for development
 * - Remote logging preparation
 */

export const LogLevel = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
} as const;

export type LogLevelType = typeof LogLevel[keyof typeof LogLevel];

interface LogContext {
  [key: string]: any;
}

interface LogEntry {
  level: LogLevelType;
  message: string;
  timestamp: string;
  context?: LogContext;
  error?: Error;
  stack?: string;
}

export class Logger {
  private static instance: Logger;
  private logLevel: LogLevelType = LogLevel.DEBUG;
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private logBuffer: LogEntry[] = [];
  private flushInterval: number | null = null;
  private isDevelopment = import.meta.env.DEV;

  private constructor() {
    // Set up global error handlers
    this.setupGlobalErrorHandlers();
    this.startLogFlushing();
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private setupGlobalErrorHandlers() {
    // Catch unhandled errors
    window.addEventListener('error', (event) => {
      this.error('Unhandled error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error,
      });
    });

    // Catch unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection', {
        reason: event.reason,
        promise: event.promise,
      });
    });
  }

  setLogLevel(level: LogLevelType) {
    this.logLevel = level;
  }

  private shouldLog(level: LogLevelType): boolean {
    return level >= this.logLevel;
  }

  private formatMessage(level: LogLevelType, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const levelName = Object.keys(LogLevel).find(key => LogLevel[key as keyof typeof LogLevel] === level) || 'UNKNOWN';
    
    if (context) {
      return `[${timestamp}] [${levelName}] ${message} ${JSON.stringify(context, null, 2)}`;
    }
    return `[${timestamp}] [${levelName}] ${message}`;
  }

  private getConsoleStyle(level: LogLevelType): string {
    switch (level) {
      case LogLevel.DEBUG:
        return 'color: #888; font-weight: normal;';
      case LogLevel.INFO:
        return 'color: #2196F3; font-weight: normal;';
      case LogLevel.WARN:
        return 'color: #FF9800; font-weight: bold;';
      case LogLevel.ERROR:
        return 'color: #F44336; font-weight: bold;';
      default:
        return '';
    }
  }

  private log(level: LogLevelType, message: string, context?: LogContext, error?: Error) {
    if (!this.shouldLog(level)) return;

    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
      error,
      stack: error?.stack,
    };

    // Store log entry
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Add to buffer for backend
    this.logBuffer.push(entry);

    // Console output
    const formattedMessage = this.formatMessage(level, message, context);
    const consoleMethod = level === LogLevel.ERROR ? 'error' : level === LogLevel.WARN ? 'warn' : 'log';
    
    if (this.isDevelopment) {
      console[consoleMethod](`%c${formattedMessage}`, this.getConsoleStyle(level));
      if (error) {
        console.error(error);
      }
    } else {
      console[consoleMethod](formattedMessage);
    }

    // Send to remote logging service in production
    if (!this.isDevelopment && level >= LogLevel.WARN) {
      this.sendToRemote(entry);
    }
  }

  debug(message: string, context?: LogContext) {
    this.log(LogLevel.DEBUG, message, context);
  }

  info(message: string, context?: LogContext) {
    this.log(LogLevel.INFO, message, context);
  }

  warn(message: string, context?: LogContext) {
    this.log(LogLevel.WARN, message, context);
  }

  error(message: string, context?: LogContext | Error, error?: Error) {
    if (context instanceof Error) {
      this.log(LogLevel.ERROR, message, undefined, context);
    } else {
      this.log(LogLevel.ERROR, message, context, error);
    }
  }

  // Network request logging
  logRequest(method: string, url: string, options?: RequestInit) {
    this.debug(`API Request: ${method} ${url}`, {
      method,
      url,
      headers: options?.headers,
      body: options?.body,
    });
  }

  logResponse(method: string, url: string, status: number, duration: number, data?: any) {
    const level = status >= 400 ? LogLevel.ERROR : LogLevel.DEBUG;
    this.log(level, `API Response: ${method} ${url} - ${status}`, {
      method,
      url,
      status,
      duration: `${duration}ms`,
      data: this.isDevelopment ? data : undefined,
    });
  }

  // Performance logging
  logPerformance(operation: string, duration: number, metadata?: LogContext) {
    const level = duration > 1000 ? LogLevel.WARN : LogLevel.DEBUG;
    this.log(level, `Performance: ${operation}`, {
      duration: `${duration}ms`,
      ...metadata,
    });
  }

  // Component lifecycle logging
  logComponentMount(componentName: string, props?: any) {
    this.debug(`Component mounted: ${componentName}`, {
      props: this.isDevelopment ? props : undefined,
    });
  }

  logComponentUnmount(componentName: string) {
    this.debug(`Component unmounted: ${componentName}`);
  }

  logComponentError(componentName: string, error: Error, errorInfo?: any) {
    this.error(`Component error: ${componentName}`, {
      component: componentName,
      errorInfo,
    }, error);
  }

  // Get logs for debugging
  getLogs(level?: LogLevelType): LogEntry[] {
    if (level !== undefined) {
      return this.logs.filter(log => log.level === level);
    }
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
  }

  // Export logs for debugging
  exportLogs(): string {
    const logs = this.logs.map(() => {
      // TODO: Format logs for export
      return ''
    }).join('\n')
    return logs
  }

  // Send logs to remote service
  private async sendToRemote(entry: LogEntry) {
    try {
      // TODO: Implement remote logging
      // await fetch('/api/logs', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(entry),
      // });
    } catch (error) {
      // Don't log errors about logging to avoid infinite loop
      console.error('Failed to send log to remote:', error);
    }
  }

  private startLogFlushing() {
    // Flush logs to backend every 5 seconds
    this.flushInterval = window.setInterval(() => {
      this.flushLogsToBackend();
    }, 5000);

    // Also flush on page unload
    window.addEventListener('beforeunload', () => {
      this.flushLogsToBackend();
    });
  }

  private async flushLogsToBackend() {
    if (this.logBuffer.length === 0) return;

    const logsToSend = [...this.logBuffer];
    this.logBuffer = [];

    try {
      // Transform logs to match backend schema
      const transformedLogs = logsToSend.map(log => ({
        timestamp: log.timestamp,
        level: Object.keys(LogLevel).find(key => LogLevel[key as keyof typeof LogLevel] === log.level) || 'INFO',
        message: log.message,
        data: log.context || null,
        error: log.error ? {
          message: log.error.message,
          name: log.error.name,
          stack: log.error.stack
        } : null
      }));

      // Send logs to backend endpoint
      // Fix: VITE_API_URL already includes /api/v1
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${apiUrl}/logs/frontend-logs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logs: transformedLogs,
          userAgent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        // If failed, add logs back to buffer
        this.logBuffer.unshift(...logsToSend);
      }
    } catch (error) {
      // If network error, add logs back to buffer
      this.logBuffer.unshift(...logsToSend);
      console.error('Failed to send logs to backend:', error);
    }
  }

  // Clean up method
  destroy() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
    }
    this.flushLogsToBackend();
  }
}

// Export singleton instance
export const logger = Logger.getInstance();

// Export convenience functions
export const logDebug = (message: string, context?: LogContext) => logger.debug(message, context);
export const logInfo = (message: string, context?: LogContext) => logger.info(message, context);
export const logWarn = (message: string, context?: LogContext) => logger.warn(message, context);
export const logError = (message: string, context?: LogContext | Error, error?: Error) => logger.error(message, context, error);

// React hook for component logging
export const useComponentLogger = (componentName: string) => {
  return {
    debug: (message: string, context?: LogContext) => 
      logger.debug(`[${componentName}] ${message}`, context),
    info: (message: string, context?: LogContext) => 
      logger.info(`[${componentName}] ${message}`, context),
    warn: (message: string, context?: LogContext) => 
      logger.warn(`[${componentName}] ${message}`, context),
    error: (message: string, context?: LogContext | Error, error?: Error) => 
      logger.error(`[${componentName}] ${message}`, context, error),
    logMount: (props?: any) => logger.logComponentMount(componentName, props),
    logUnmount: () => logger.logComponentUnmount(componentName),
    logError: (error: Error, errorInfo?: any) => logger.logComponentError(componentName, error, errorInfo),
  };
}; 