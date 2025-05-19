import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, ElLoading } from 'element-plus';
import router from '@/router';

// 创建loading实例
let loadingInstance: any = null;
// 正在请求的数量
let requestCount = 0;

// 显示loading
const showLoading = () => {
  if (requestCount === 0 && !loadingInstance) {
    loadingInstance = ElLoading.service({
      fullscreen: true,
      lock: true,
      text: '加载中...',
      background: 'rgba(0, 0, 0, 0.7)'
    });
  }
  requestCount++;
};

// 隐藏loading
const hideLoading = () => {
  requestCount--;
  if (requestCount <= 0) {
    loadingInstance?.close();
    loadingInstance = null;
  }
};

// 创建axios实例
const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 10000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 判断是否需要显示loading
    if (config.headers?.showLoading !== false) {
      showLoading();
    }
    
    // 获取token并设置请求头
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.set('Authorization', `Bearer ${authStore.token}`);
    }
    
    return config;
  },
  (error: AxiosError) => {
    hideLoading();
    return Promise.reject(error);
  }
);

// 响应拦截器
http.interceptors.response.use(
  (response: AxiosResponse) => {
    hideLoading();
    
    // 直接返回数据
    return response;
  },
  (error: AxiosError) => {
    hideLoading();
    
    if (!error.response) {
      // 网络错误
      ElMessage.error('网络异常，请检查您的网络连接');
      return Promise.reject(error);
    }
    
    const status = error.response.status;
    const data: any = error.response.data;
    const message = data?.message || '请求失败';
    
    switch (status) {
      case 400:
        ElMessage.error(message || '请求参数错误');
        break;
      case 401:
        // 未授权或token过期
        ElMessage.error('登录状态已过期，请重新登录');
        const authStore = useAuthStore();
        authStore.logout();
        router.push('/login');
        break;
      case 403:
        ElMessage.error(message || '没有权限执行此操作');
        break;
      case 404:
        ElMessage.error(message || '请求的资源不存在');
        break;
      case 409:
        ElMessage.error(message || '资源冲突，请求无法完成');
        break;
      case 422:
        // 数据验证错误
        if (data.errors && typeof data.errors === 'object') {
          // 如果有详细的验证错误信息
          const errorMessages = Object.values(data.errors).flat().join(', ');
          ElMessage.error(errorMessages || message);
        } else {
          ElMessage.error(message || '提交的数据无效');
        }
        break;
      case 500:
        ElMessage.error(message || '服务器内部错误');
        break;
      default:
        ElMessage.error(message || `请求失败(${status})`);
    }
    
    return Promise.reject(error);
  }
);

// 简单的内存缓存实现
interface CacheItem {
  data: any;
  expiry: number;
}

const cache = new Map<string, CacheItem>();

// 封装GET请求 (支持缓存)
export const get = <T>(url: string, params?: object, config?: AxiosRequestConfig & { cache?: boolean; cacheTTL?: number }): Promise<T> => {
  // 提取缓存相关配置
  const useCache = config?.cache !== false; // 默认使用缓存
  const cacheTTL = config?.cacheTTL || 60000; // 默认缓存60秒
  
  // 生成缓存键
  const cacheKey = `${url}:${JSON.stringify(params || {})}`;
  
  // 检查是否存在有效缓存
  if (useCache && cache.has(cacheKey)) {
    const cacheItem = cache.get(cacheKey)!;
    if (cacheItem.expiry > Date.now()) {
      return Promise.resolve(cacheItem.data);
    } else {
      // 缓存过期，删除
      cache.delete(cacheKey);
    }
  }
  
  // 没有有效缓存，发送实际请求
  return http.get(url, { params, ...config }).then(res => {
    if (useCache) {
      // 缓存结果
      cache.set(cacheKey, {
        data: res.data,
        expiry: Date.now() + cacheTTL
      });
    }
    return res.data;
  });
};

// 封装POST请求
export const post = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return http.post(url, data, config).then(res => res.data);
};

// 封装PUT请求
export const put = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return http.put(url, data, config).then(res => res.data);
};

// 封装DELETE请求
export const del = <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return http.delete(url, config).then(res => res.data);
};

export default http;
