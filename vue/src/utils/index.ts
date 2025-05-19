/**
 * 工具函数集合
 * 
 * API调用最佳实践:
 * 
 * 1. 直接使用http工具函数:
 *    import { get, post, put, del, getPaginatedData } from '@/utils/http';
 *    
 *    // 示例：获取数据
 *    const data = await get('/users');
 *    
 *    // 示例：获取分页数据
 *    const response = await get('/jobs');
 *    const { items, pagination } = getPaginatedData(response);
 *    
 * 2. 使用apiClient:
 *    import apiClient from '@/utils/apiClient';
 *    
 *    // 示例
 *    const response = await apiClient.get('/users');
 *    
 * 3. API响应格式:
 *    所有API响应都将被处理为以下格式之一:
 *    
 *    - 直接数据: 对象或数组
 *    - 分页数据: { items: [...], pagination: {...} }
 *    
 *    所有响应数据都会附加__meta属性(不可枚举)，可通过以下方式访问:
 *    const meta = response.__meta;
 */

// 导出所有工具函数
export * from './http';
export { default as http } from './http';
export { default as apiClient } from './apiClient';
import apiConfig from './apiConfig';
export { apiConfig };
export * from './captcha';

// 启用API调试模式
export function enableApiDebug(enabled = true) {
  return apiConfig.setDebugMode(enabled);
}