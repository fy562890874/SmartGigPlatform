// e:\SmartGigPlatform\Vue\src\utils\apiConfig.js
// Configuration for backend API connection

/**
 * API配置文件
 * 管理API请求的基础配置
 */

const config = {
  baseURL: '/api/v1', // 正确的API基础URL路径
  timeout: 15000, // 请求超时时间
  withCredentials: true, // 支持跨域请求时发送Cookie
  
  /**
   * 获取完整的API URL
   * @param {string} path - API路径
   * @returns {string} 完整的API URL
   */
  getApiUrl(path) {
    // 确保path不以/开头，以避免路径重复
    if (path.startsWith('/')) {
      path = path.substring(1);
    }
    return `${this.baseURL}/${path}`;
  },

  /**
   * 启用调试模式
   * @param {boolean} enabled - 是否启用
   */
  setDebugMode(enabled = true) {
    localStorage.setItem('debug_mode', enabled.toString());
    console.log(`API调试模式: ${enabled ? '开启' : '关闭'}`);
  },

  /**
   * 检查调试模式状态
   * @returns {boolean} 调试模式状态
   */
  isDebugMode() {
    return localStorage.getItem('debug_mode') === 'true';
  }
};

export default config;
