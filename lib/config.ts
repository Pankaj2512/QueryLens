/**
 * Application configuration
 */

export const config = {
  // API Configuration
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
    retryDelay: 1000, // 1 second
  },

  // File Upload Configuration
  upload: {
    maxFileSize: 50 * 1024 * 1024, // 50MB
    allowedFormats: ['.csv'],
    allowedMimeTypes: ['text/csv'],
  },

  // Table Configuration
  table: {
    maxColumns: 100,
    maxRows: 100000,
    maxTableNameLength: 255,
    maxColumnNameLength: 255,
  },

  // Query Configuration
  query: {
    maxLength: 5000,
    defaultTimeout: 30000,
  },

  // UI Configuration
  ui: {
    toastDuration: 3000,
    confirmDialogDuration: 5000,
  },

  // Security
  security: {
    enableCSRFProtection: true,
    enableXSSProtection: true,
    enableInputSanitization: true,
  },

  // Logging
  logging: {
    enabled: process.env.NODE_ENV === 'development',
    level: process.env.LOG_LEVEL || 'info',
  },

  // Feature Flags
  features: {
    manualTableBuilder: true,
    csvUpload: true,
    queryHistory: true,
    queryExecution: true,
  },
};

// Validate configuration
export const validateConfig = () => {
  if (!config.api.baseUrl) {
    console.warn('[Config] API base URL is not configured, using default');
  }
};
