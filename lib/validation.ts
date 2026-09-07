/**
 * Input validation and sanitization utilities
 */

export const validation = {
  /**
   * Sanitize file upload
   */
  validateCsvFile: (file: File): { valid: boolean; error?: string } => {
    // Check file type
    if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
      return { valid: false, error: 'Only CSV files are allowed' };
    }

    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      return { valid: false, error: 'File size must be less than 50MB' };
    }

    // Check file name
    if (!file.name || file.name.length > 255) {
      return { valid: false, error: 'Invalid file name' };
    }

    return { valid: true };
  },

  /**
   * Validate table name
   */
  validateTableName: (name: string): { valid: boolean; error?: string } => {
    if (!name || name.trim().length === 0) {
      return { valid: false, error: 'Table name is required' };
    }

    if (name.length > 255) {
      return { valid: false, error: 'Table name must be 255 characters or less' };
    }

    // Allow letters, numbers, underscores only
    if (!/^[a-zA-Z0-9_]+$/.test(name)) {
      return { valid: false, error: 'Table name can only contain letters, numbers, and underscores' };
    }

    // Cannot start with number
    if (/^[0-9]/.test(name)) {
      return { valid: false, error: 'Table name cannot start with a number' };
    }

    return { valid: true };
  },

  /**
   * Validate column name
   */
  validateColumnName: (name: string): { valid: boolean; error?: string } => {
    if (!name || name.trim().length === 0) {
      return { valid: false, error: 'Column name is required' };
    }

    if (name.length > 255) {
      return { valid: false, error: 'Column name must be 255 characters or less' };
    }

    if (!/^[a-zA-Z0-9_]+$/.test(name)) {
      return { valid: false, error: 'Column name can only contain letters, numbers, and underscores' };
    }

    return { valid: true };
  },

  /**
   * Validate query string
   */
  validateQueryString: (query: string): { valid: boolean; error?: string } => {
    if (!query || query.trim().length === 0) {
      return { valid: false, error: 'Query is required' };
    }

    if (query.length > 5000) {
      return { valid: false, error: 'Query must be 5000 characters or less' };
    }

    return { valid: true };
  },

  /**
   * Sanitize HTML to prevent XSS
   */
  sanitizeHtml: (html: string): string => {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  },

  /**
   * Validate email
   */
  validateEmail: (email: string): { valid: boolean; error?: string } => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return { valid: false, error: 'Invalid email address' };
    }
    return { valid: true };
  },
};
