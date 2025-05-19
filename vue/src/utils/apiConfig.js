// e:\SmartGigPlatform\Vue\src\utils\apiConfig.js
// Configuration for backend API connection
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000'; // As specified for the backend
const API_VERSION = '/api/v1'; // From Flask app's v1_blueprint

const apiConfig = {
  baseURL: API_BASE_URL,
  version: API_VERSION,
  timeout: 10000, // Default timeout for API requests in milliseconds

  /**
   * Constructs the full API URL for a given path.
   * @param {string} path - The API endpoint path (e.g., "/jobs", "users/profile").
   * @returns {string} The full API URL.
   */
  getApiUrl: (path) => {
    // 确保路径以斜杠开头，但去掉末尾斜杠（Flask 路由重定向问题）
    let formattedPath = path.startsWith('/') ? path : `/${path}`;
    // 去掉尾部斜杠，避免 Flask 路由重定向
    if (formattedPath.length > 1 && formattedPath.endsWith('/')) {
      formattedPath = formattedPath.slice(0, -1);
    }
    return `${apiConfig.baseURL}${apiConfig.version}${formattedPath}`;
  }
};

export default apiConfig;
