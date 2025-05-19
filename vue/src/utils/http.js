import apiClient from './apiClient'

/**
 * 发送GET请求
 * @param {string} url - 请求路径
 * @param {object} [params] - 查询参数
 * @param {object} [config] - Axios配置
 * @returns {Promise<any>} - 响应数据
 */
export async function get(url, params = {}, config = {}) {
  try {
    // 自动将params添加到config中
    const finalConfig = { ...config };
    if (Object.keys(params).length > 0) {
      finalConfig.params = params;
    }
    return await apiClient.get(url, finalConfig);
  } catch (error) {
    console.error('GET请求错误:', error);
    throw error;
  }
}

/**
 * 发送POST请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求数据
 * @param {object} [config] - Axios配置
 * @returns {Promise<any>} - 响应数据
 */
export async function post(url, data = {}, config = {}) {
  try {
    return await apiClient.post(url, data, config);
  } catch (error) {
    console.error('POST请求错误:', error);
    throw error;
  }
}

/**
 * 发送PUT请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求数据
 * @param {object} [config] - Axios配置
 * @returns {Promise<any>} - 响应数据
 */
export async function put(url, data = {}, config = {}) {
  try {
    return await apiClient.put(url, data, config);
  } catch (error) {
    console.error('PUT请求错误:', error);
    throw error;
  }
}

/**
 * 发送DELETE请求
 * @param {string} url - 请求路径
 * @param {object} [config] - Axios配置
 * @returns {Promise<any>} - 响应数据
 */
export async function del(url, config = {}) {
  try {
    return await apiClient.delete(url, config);
  } catch (error) {
    console.error('DELETE请求错误:', error);
    throw error;
  }
}

/**
 * 获取分页数据辅助函数
 * @param {any} response - API响应
 * @returns {{items: Array, pagination: Object}} - 标准化的分页数据
 */
export function getPaginatedData(response) {
  if (!response) return { items: [], pagination: { total: 0 } };
  
  // 调试信息
  const debug = localStorage.getItem('debug_mode') === 'true';
  if (debug) {
    console.log('getPaginatedData 输入:', response);
  }

  // 已经是标准格式
  if (response.items && (response.pagination || response.__meta?.pagination)) {
    if (debug) console.log('检测到标准格式：包含items和pagination');
    return {
      items: response.items,
      pagination: response.pagination || response.__meta?.pagination || { total: 0 }
    };
  }
  
  // 处理Flask API直接返回的平铺分页格式（items, page, per_page, total_pages, total_items）
  if (response.items && typeof response.page !== 'undefined' && typeof response.per_page !== 'undefined') {
    if (debug) console.log('检测到Flask API平铺分页格式');
    return {
      items: response.items,
      pagination: {
        page: response.page,
        per_page: response.per_page,
        total_pages: response.total_pages || 0,
        total_items: response.total_items || 0,
        total: response.total_items || 0 // 添加total作为total_items的别名，兼容性更好
      }
    };
  }
  
  // 数组类型结果
  if (Array.isArray(response)) {
    if (debug) console.log('检测到数组格式');
    return {
      items: response,
      pagination: { total: response.length }
    };
  }
  
  // 嵌套在data属性中
  if (response.data && response.data.items) {
    if (debug) console.log('检测到嵌套在data中的数据');
    // 处理data中的平铺分页格式（page、per_page 等和items同级）
    if (typeof response.data.page !== 'undefined' && typeof response.data.per_page !== 'undefined') {
      return {
        items: response.data.items,
        pagination: {
          page: response.data.page,
          per_page: response.data.per_page,
          total_pages: response.data.total_pages || 0,
          total_items: response.data.total_items || 0,
          total: response.data.total_items || 0
        }
      };
    }
    
    // 常规嵌套分页数据
    return {
      items: response.data.items,
      pagination: response.data.pagination || { total: response.data.items.length }
    };
  }
  
  if (debug) {
    console.warn('无法识别的分页数据格式:', response);
  }
  return {
    items: Array.isArray(response) ? response : [],
    pagination: { total: 0 }
  };
}

// 导出apiClient实例，以便在需要时直接使用
export { apiClient } 