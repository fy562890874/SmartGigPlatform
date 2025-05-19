// e:\SmartGigPlatform\Vue\src\utils\apiConfig.d.ts

interface ApiConfig {
  baseURL: string;
  timeout: number;
  withCredentials: boolean;
  
  /**
   * 获取完整的API URL
   * @param path - API路径
   * @returns 完整的API URL
   */
  getApiUrl: (path: string) => string;

  /**
   * 启用或禁用调试模式
   * @param enabled - 是否启用
   */
  setDebugMode: (enabled?: boolean) => void;

  /**
   * 检查调试模式状态
   * @returns 调试模式状态
   */
  isDebugMode: () => boolean;
}

declare const apiConfig: ApiConfig;
export default apiConfig;
