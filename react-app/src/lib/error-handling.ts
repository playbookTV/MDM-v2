/**
 * Centralized error handling utilities
 */

export interface AppError extends Error {
  code?: string
  statusCode?: number
  context?: Record<string, any>
}

export class APIError extends Error implements AppError {
  code: string
  statusCode: number
  context?: Record<string, any>

  constructor(
    message: string,
    statusCode: number = 500,
    code: string = 'API_ERROR',
    context?: Record<string, any>
  ) {
    super(message)
    this.name = 'APIError'
    this.code = code
    this.statusCode = statusCode
    this.context = context
  }
}

export class ValidationError extends Error implements AppError {
  code: string = 'VALIDATION_ERROR'
  statusCode: number = 400
  context?: Record<string, any>

  constructor(message: string, context?: Record<string, any>) {
    super(message)
    this.name = 'ValidationError'
    this.context = context
  }
}

export class NetworkError extends Error implements AppError {
  code: string = 'NETWORK_ERROR'
  statusCode: number = 0
  context?: Record<string, any>

  constructor(message: string = 'Network connection failed', context?: Record<string, any>) {
    super(message)
    this.name = 'NetworkError'
    this.context = context
  }
}

/**
 * Enhanced fetch wrapper with consistent error handling
 */
export const apiRequest = async <T>(
  url: string,
  options?: RequestInit & { timeout?: number }
): Promise<T> => {
  const { timeout = 30000, ...fetchOptions } = options || {}
  
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      let errorCode = `HTTP_${response.status}`
      
      try {
        const errorData = await response.json()
        if (errorData.error?.message) {
          errorMessage = errorData.error.message
        }
        if (errorData.error?.code) {
          errorCode = errorData.error.code
        }
      } catch {
        // If we can't parse error response, use default message
      }
      
      throw new APIError(
        errorMessage,
        response.status,
        errorCode,
        { url, status: response.status }
      )
    }
    
    return await response.json()
  } catch (error) {
    clearTimeout(timeoutId)
    
    if (error instanceof APIError) {
      throw error
    }
    
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new NetworkError('Request timeout', { url, timeout })
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new NetworkError('Network connection failed', { url, originalError: error.message })
    }
    
    // Re-throw other errors as-is
    throw error
  }
}

/**
 * Retry mechanism for failed operations
 */
export const withRetry = async <T>(
  operation: () => Promise<T>,
  options: {
    maxAttempts?: number
    delayMs?: number
    backoff?: boolean
    retryCondition?: (error: Error) => boolean
  } = {}
): Promise<T> => {
  const {
    maxAttempts = 3,
    delayMs = 1000,
    backoff = true,
    retryCondition = (error) => error instanceof NetworkError || 
                                 (error instanceof APIError && error.statusCode >= 500)
  } = options
  
  let lastError: Error
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as Error
      
      if (attempt === maxAttempts || !retryCondition(lastError)) {
        throw lastError
      }
      
      const delay = backoff ? delayMs * Math.pow(2, attempt - 1) : delayMs
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  throw lastError!
}

/**
 * Error logging utility
 */
export const logError = (error: Error, context?: Record<string, any>) => {
  const errorInfo = {
    name: error.name,
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString(),
    ...context,
    ...(error as AppError).context,
  }
  
  console.error('Application Error:', errorInfo)
  
  // In production, you might want to send this to a logging service
  // Example: sendToLoggingService(errorInfo)
}

/**
 * Error boundary hook for React components
 */
export const useErrorHandler = () => {
  return (error: Error, context?: Record<string, any>) => {
    logError(error, context)
    
    // You might want to show a toast notification here
    // Example: showErrorToast(error.message)
  }
}