/**
 * Application configuration
 */

// Get API URL from environment or use default
// For network access, set this to your machine's IP address
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// For production deployment
export const IS_PRODUCTION = process.env.NODE_ENV === 'production';

// Export for easy access
export const config = {
  apiUrl: API_URL,
  isProduction: IS_PRODUCTION,
};

export default config;

