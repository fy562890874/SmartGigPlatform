// e:\SmartGigPlatform\Vue\src\utils\apiConfig.js
// Configuration for backend API connection

/**
 * API配置文件
 * 管理API请求的基础配置
 */

const apiConfig = {
  // API基础URL
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1',
  
  // 请求超时时间(毫秒)
  timeout: 15000,
  
  // 获取完整API URL
  getApiUrl(endpoint) {
    // 确保endpoint不以/开头
    const path = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
    return `${this.baseUrl}/${path}`;
  }
};

export default apiConfig;
