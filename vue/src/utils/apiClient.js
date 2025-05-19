import axios from 'axios';
import apiConfig from './apiConfig';
import { useAuthStore } from '@/stores/auth'; // Assuming Pinia store for JWT
import { ElMessage } from 'element-plus'; // For user feedback

// Create an Axios instance
const apiClient = axios.create({
  // baseURL will be set dynamically by the interceptor using apiConfig.getApiUrl
  timeout: apiConfig.timeout,
});

// Request interceptor to add JWT token and set dynamic baseURL
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const token = authStore.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 处理URL - 如果不是完整URL，则使用apiConfig.getApiUrl构建
    if (!config.url.startsWith('http')) {
      config.url = apiConfig.getApiUrl(config.url);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
apiClient.interceptors.response.use(
  (response) => {
    // 处理API成功响应 (status 2xx)
    if (response.data.code === 0) {
      // 成功响应码为0
      return response.data;
    }
    // 返回完整响应以便调用方处理可能的非标准响应
    return response;
  },
  (error) => {
    // 处理API错误响应
    let message = '服务器错误，请稍后再试';
    
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response;
      
      if (status === 401) {
        // 处理认证错误
        const authStore = useAuthStore();
        if (authStore.isLoggedIn) {
          authStore.logout();
          ElMessage.error('您的登录已过期，请重新登录');
          window.location.href = '/login';
        } else {
          message = '请先登录';
        }
      } else if (status === 403) {
        message = '您没有权限执行此操作';
      } else if (status === 404) {
        message = '请求的资源不存在';
      } else if (status === 422 || status === 400) {
        // 输入验证错误
        message = data.message || '提交的数据无效';
      } else {
        // 其他服务器错误
        message = data.message || `服务器错误 (${status})`;
      }
    } else if (error.request) {
      // 请求已发送但未收到响应
      message = '服务器无响应，请检查网络连接';
    }
    
    // 显示错误消息
    ElMessage.error(message);
    
    // 传递错误到调用方，以便进一步处理
    return Promise.reject(error);
  }
);

export default apiClient;