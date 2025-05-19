import { AxiosInstance, AxiosRequestConfig } from 'axios';

interface ApiClient extends AxiosInstance {
  /**
   * 发送GET请求并直接返回数据（不是AxiosResponse）
   * @param url 请求URL
   * @param config 请求配置
   * @returns 直接返回响应数据
   */
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;

  /**
   * 发送POST请求并直接返回数据（不是AxiosResponse）
   * @param url 请求URL
   * @param data 请求数据
   * @param config 请求配置
   * @returns 直接返回响应数据
   */
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;

  /**
   * 发送PUT请求并直接返回数据（不是AxiosResponse）
   * @param url 请求URL
   * @param data 请求数据
   * @param config 请求配置
   * @returns 直接返回响应数据
   */
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;

  /**
   * 发送DELETE请求并直接返回数据（不是AxiosResponse）
   * @param url 请求URL
   * @param config 请求配置
   * @returns 直接返回响应数据
   */
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;
}

declare const apiClient: ApiClient;
export default apiClient;
