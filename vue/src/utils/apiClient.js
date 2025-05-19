import axios from 'axios';
import apiConfig from './apiConfig';
import { useAuthStore } from '@/stores/auth'; // Assuming Pinia store for JWT
import { ElMessage } from 'element-plus'; // For user feedback

// Create an Axios instance
const apiClient = axios.create(apiConfig);

// Request interceptor to add JWT token and set dynamic baseURL
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    
    // 增加认证API的调试日志
    const isDebugMode = localStorage.getItem('debug_mode') === 'true';
    const isVerificationApi = config.url?.includes('verification');
    
    if (isDebugMode && isVerificationApi) {
      console.log(`[API请求] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
        headers: config.headers
      });
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
    const apiPath = response.config.url;
    const isDebugMode = localStorage.getItem('debug_mode') === 'true';
    
    if (isDebugMode) {
      console.log(`---API响应(${apiPath})开始---`);
      console.log('API请求URL:', apiPath);
      console.log('请求方法:', response.config.method?.toUpperCase());
      console.log('响应状态:', response.status);
      console.log('响应数据结构:', typeof response.data, Array.isArray(response.data) ? 'array' : '');
    }
    
    // 处理响应数据，统一返回格式
    let result = response.data;
    let meta = {};
    
    // 标准响应格式: {code, data, message}
    if (result !== null && typeof result === 'object' && 'code' in result && 'data' in result) {
      if (isDebugMode) {
        console.log('标准响应格式检测: { code:', result.code, ', message:', result.message || 'none', '}');
      }
      
      // 添加元数据
      meta = {
        code: result.code,
        message: result.message,
        originalResponse: result
      };
      
      // 成功响应
      if (result.code === 0) {
        if (isDebugMode) console.log('成功响应 → 解包装数据');
        
        // 将数据解包装，但保持meta信息
        result = result.data;
        
        // 分页数据处理
        if (result && typeof result === 'object' && 'items' in result && 'pagination' in result) {
          meta.pagination = result.pagination;
          meta.total = result.pagination?.total_items || result.pagination?.total || 0;
          if (isDebugMode) console.log('分页数据 → items:', result.items?.length || 0);
        }
      } else {
        // 业务逻辑错误
        const errorMsg = result.message || `业务错误(code=${result.code})`;
        if (isDebugMode) console.error('业务错误:', errorMsg);
        ElMessage.error(errorMsg);
        return Promise.reject(new Error(errorMsg));
      }
    } 
    // 分页数据但不在标准响应中
    else if (result && typeof result === 'object' && 'items' in result && ('pagination' in result || 'meta' in result)) {
      if (isDebugMode) console.log('分页数据格式 → items:', result.items?.length || 0);
      meta.pagination = result.pagination || (result.meta ? result.meta.pagination : null);
      meta.total = meta.pagination?.total_items || meta.pagination?.total || 0;
    }
    
    // 为任何类型的结果添加__meta属性，包含原始响应信息
    const finalResult = result;
    if (finalResult && typeof finalResult === 'object' && !Array.isArray(finalResult)) {
      Object.defineProperty(finalResult, '__meta', {
        value: meta,
        enumerable: false,
        configurable: true
      });
    } else if (Array.isArray(finalResult)) {
      // 数组类型，创建一个新对象包装它
      const wrappedResult = {
        items: finalResult,
        __meta: meta
      };
      if (isDebugMode) console.log('数组数据 → 包装为 {items: [...]}');
      return wrappedResult;
    }
    
    if (isDebugMode) console.log(`---API响应(${apiPath})结束---`);
    return finalResult;
  },  (error) => {
    const apiPath = error.config?.url || '未知路径';
    console.log(`---API错误(${apiPath})开始---`);
    console.error('API请求失败:', error.message);
    
    const { response } = error;
    let message = '请求失败，请稍后再试';

    if (response) {
      console.error(`错误响应状态: ${response.status} ${response.statusText}`);
      console.error('错误响应数据:', response.data);

      // 处理特定错误码
      switch (response.status) {
        case 400:
          // 尝试从响应中获取详细错误信息
          if (response.data) {
            if (typeof response.data === 'object') {
              message = response.data.message || response.data.error || '请求参数错误';
              
              // 检查是否有字段验证错误
              if (response.data.errors && typeof response.data.errors === 'object') {
                const fieldErrors = [];
                for (const field in response.data.errors) {
                  fieldErrors.push(`${field}: ${response.data.errors[field]}`);
                }
                if (fieldErrors.length > 0) {
                  message += ` (${fieldErrors.join('; ')})`;
                }
              }
            } else {
              message = '请求参数错误';
            }
          }
          break;
        case 401:
          message = '未授权，请重新登录';
          console.log('登录状态已过期，将重定向到登录页面');
          
          // 在统一响应拦截器中设置防抖处理
          const authStore = useAuthStore();
          if (!window._401_redirect_in_progress) {
            window._401_redirect_in_progress = true;
            setTimeout(() => {
              authStore.logout();
              window.location.href = '/login';
              window._401_redirect_in_progress = false;
            }, 300);
          }
          break;
        case 403:
          message = '无权限执行此操作';
          break;
        case 404:
          message = `请求的资源不存在 (${apiPath})`;
          console.log('这可能是后端API尚未实现或路径不正确，请检查API路径');
          break;
        case 429:
          message = '请求过于频繁，请稍后再试';
          break;
        case 500:
          message = response.data?.message || '服务器内部错误，请稍后再试';
          break;
        default:
          message = `请求失败 (${response.status}): ${response.statusText || '未知错误'}`;
      }
    } else if (error.request) {
      // 发出请求但未收到响应
      console.error('没有收到服务器响应:', error.request);
      message = '服务器无响应，请检查网络连接';
    } else {
      // 发送请求前出错
      console.error('请求设置错误:', error.message);
      message = '请求发送失败';
    }

    // 显示错误信息给用户
    ElMessage.error(message);
    console.log(`---API错误(${apiPath})结束---`);
    return Promise.reject(error);
  }
);

export default apiClient;