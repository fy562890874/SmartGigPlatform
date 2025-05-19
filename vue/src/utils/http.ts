import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, ElLoading } from 'element-plus';
import router from '@/router';

// 定义通用响应格式类型
export interface ApiResponse<T = any> {
  code?: number;
  data?: T;
  message?: string;
}

// 定义分页响应格式
export interface PaginationData {
  page: number;
  per_page: number;
  total?: number;
  total_items?: number;
  total_pages?: number;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  pagination: PaginationData;
  __meta?: {
    pagination?: PaginationData;
    code?: number;
    message?: string;
    [key: string]: any;
  }
}

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
    
    const data = response.data;
    let result: any = data;
    
    // 处理Flask API标准响应格式 - 包含 code 和 data 字段的情况
    if (data && typeof data === 'object' && 'code' in data) {
      // 成功的响应 (code === 0)
      if (data.code === 0 && 'data' in data) {
        result = data.data;
        
        // 添加元数据
        if (result && typeof result === 'object' && !Array.isArray(result)) {
          Object.defineProperty(result, '__meta', {
            value: {
              code: data.code,
              message: data.message,
              originalResponse: data
            },
            enumerable: false
          });
        }
      } 
      // 业务错误
      else if (data.code !== 0) {
        ElMessage.error(data.message || `业务错误(${data.code})`);
        return Promise.reject({
          response: {
            data,
            status: 400
          }
        });
      }
    }
    
    // 处理Flask API标准分页响应格式
    // 例如: {"items": [...], "page": 1, "per_page": 10, "total_pages": 5, "total_items": 48}
    if (result && 
        typeof result === 'object' && 
        'items' in result && 
        typeof result.page !== 'undefined' && 
        typeof result.per_page !== 'undefined') {
      
      Object.defineProperty(result, '__meta', {
        value: {
          pagination: {
            page: result.page,
            per_page: result.per_page,
            total_pages: result.total_pages,
            total_items: result.total_items,
            total: result.total_items // 兼容旧格式
          }
        },
        enumerable: false
      });
    }
    
    // 处理其他常见分页格式
    else if (result && 
             typeof result === 'object' && 
             'items' in result && 
             ('pagination' in result || 'meta' in result)) {
      const pagination = result.pagination || (result.meta ? result.meta.pagination : null);
      if (pagination) {
        Object.defineProperty(result, '__meta', {
          value: {
            pagination,
            total: pagination.total_items || pagination.total || 0
          },
          enumerable: false
        });
      }
    }
    
    return result;
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
  const finalConfig = { ...config };
  if (params && Object.keys(params).length > 0) {
    finalConfig.params = params;
  }
  
  return http.get<T>(url, finalConfig).then(data => {
    if (useCache) {
      // 缓存结果
      cache.set(cacheKey, {
        data,
        expiry: Date.now() + cacheTTL
      });
    }
    return data as T;
  });
};

// 封装POST请求
export const post = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return http.post<T>(url, data, config).then(response => response as unknown as T);
};

// 封装PUT请求
export const put = <T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> => {
  return http.put<T>(url, data, config).then(response => response as unknown as T);
};

// 封装DELETE请求
export const del = <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return http.delete<T>(url, config).then(response => response as unknown as T);
};

/**
 * 辅助函数，从任何响应中提取分页数据
 * @param response API响应
 * @returns 标准化的分页数据
 */
export function getPaginatedData<T>(response: any): PaginatedResponse<T> {
  if (!response) return { items: [], pagination: { page: 1, per_page: 10, total: 0 } };
  
  // 调试信息
  const debug = localStorage.getItem('debug_mode') === 'true';
  if (debug) {
    console.log('getPaginatedData 输入:', {
      type: typeof response,
      isArray: Array.isArray(response),
      keys: response && typeof response === 'object' ? Object.keys(response) : [],
      hasMeta: response && typeof response === 'object' && response.__meta ? '是' : '否',
      hasItems: response && typeof response === 'object' && 'items' in response ? '是' : '否'
    });
  }

  // 处理通过apiClient.js处理后包含__meta的对象
  if (response && typeof response === 'object' && response.__meta) {
    // 如果有items属性，说明是分页数据或数组集合
    if (response.items && Array.isArray(response.items)) {
      if (debug) console.log('检测到apiClient处理过的items+__meta格式');
      return {
        items: response.items,
        pagination: {
          page: response.__meta.pagination?.page || 1,
          per_page: response.__meta.pagination?.per_page || response.items.length,
          total_pages: response.__meta.pagination?.total_pages || 1,
          total_items: response.__meta.pagination?.total_items || response.__meta.total || response.items.length,
          total: response.__meta.pagination?.total_items || response.__meta.total || response.items.length
        }
      };
    }
    // 如果是经过apiClient处理的对象数据，不是集合
    else {
      if (debug) console.log('检测到apiClient处理过的单个对象，封装为items');
      // 将单个对象包装为数组
      return {
        items: [response],
        pagination: { page: 1, per_page: 1, total: 1 }
      };
    }
  }
  
  // 处理Flask RESTx API返回的标准格式
  // 例如 {"items": [], "page": 1, "per_page": 10, "total_pages": 1, "total_items": 0}
  if (response.items && typeof response.page !== 'undefined') {
    if (debug) console.log('检测到Flask API标准分页格式');
    return {
      items: response.items,
      pagination: {
        page: response.page,
        per_page: response.per_page,
        total_pages: response.total_pages,
        total_items: response.total_items,
        total: response.total_items // 兼容旧格式
      }
    };
  }
  
  // 已经是标准格式
  if (response.items && (response.pagination || response.__meta?.pagination)) {
    if (debug) console.log('检测到已带pagination的标准格式');
    return {
      items: response.items,
      pagination: response.pagination || response.__meta?.pagination || { page: 1, per_page: 10, total: 0 }
    };
  }
  
  // 数组类型结果
  if (Array.isArray(response)) {
    if (debug) console.log('检测到数组格式');
    return {
      items: response,
      pagination: { page: 1, per_page: response.length, total: response.length }
    };
  }
  
  // 嵌套在data属性中的常见格式
  if (response.data) {
    // 如果data是数组，视为不分页结果
    if (Array.isArray(response.data)) {
      if (debug) console.log('检测到{data: [...]}格式');
      return {
        items: response.data,
        pagination: { page: 1, per_page: response.data.length, total: response.data.length }
      };
    }
    // 如果data有items字段，处理分页
    else if (response.data.items) {
      if (debug) console.log('检测到{data: {items: [...]}格式');
      return {
        items: response.data.items,
        pagination: {
          page: response.data.page || 1,
          per_page: response.data.per_page || response.data.items.length,
          total_items: response.data.total_items || response.data.items.length,
          total_pages: response.data.total_pages || 1,
          total: response.data.total_items || response.data.items.length
        }
      };
    }
    // data是单个对象的情况，包装为items
    else if (typeof response.data === 'object') {
      if (debug) console.log('检测到{data: {}}格式，将单个对象包装为数组');
      return {
        items: [response.data],
        pagination: { page: 1, per_page: 1, total: 1 }
      };
    }
  }

  // 处理订单API特定的格式 - 基于观察到的错误
  if (response && typeof response === 'object') {
    // 检查是否为订单对象 (有status, order_amount等特征)
    if ('id' in response && 
        'status' in response && 
        ('order_amount' in response || 
         'freelancer_user_id' in response || 
         'employer_user_id' in response)) {
      if (debug) console.log('检测到单个订单对象，封装为items数组');
      return {
        items: [response],
        pagination: { page: 1, per_page: 1, total: 1 }
      };
    }
    
    // 尝试从对象中找出数组属性作为可能的列表数据
    const possibleItems = Object.entries(response).find(([key, value]) => 
      Array.isArray(value) && (key === 'list' || key === 'records' || key === 'rows' || key === 'data')
    );
    
    if (possibleItems) {
      const [key, items] = possibleItems;
      if (debug) console.log(`检测到可能的列表数据: ${key}`);
      return {
        items: items as T[],
        pagination: { 
          page: response.page || response.current || 1,
          per_page: response.per_page || response.pageSize || (items as unknown[]).length,
          total: response.total || response.count || (items as unknown[]).length
        }
      };
    }
  }
  
  // 最终的后备处理：如果无法识别格式，返回空数组并在开发模式下警告
  if (debug) {
    console.warn('无法识别的分页数据格式:', response);
  }
  
  return {
    items: Array.isArray(response) ? response : [],
    pagination: { page: 1, per_page: 10, total: 0 }
  };
}

export default http;
