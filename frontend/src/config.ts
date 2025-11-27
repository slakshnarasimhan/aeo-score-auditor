/**
 * Application configuration
 * Dynamically detects API URL based on current hostname
 */

function getApiUrl(): string {
  // If running in browser, detect from current hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // Use same hostname as frontend, just different port
    return `http://${hostname}:8000`;
  }
  
  // Server-side: use environment variable or default
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

export const API_URL = getApiUrl();

// For production deployment
export const IS_PRODUCTION = process.env.NODE_ENV === 'production';

// Export for easy access
export const config = {
  apiUrl: API_URL,
  isProduction: IS_PRODUCTION,
};

export default config;

