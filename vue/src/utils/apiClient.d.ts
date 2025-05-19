import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

declare module '@/utils/apiClient' {
  const apiClient: AxiosInstance;
  export default apiClient;
}

// Export common Axios types if they are frequently used by components
// This allows components to type their catch blocks for Axios errors, for example.
export type { AxiosRequestConfig, AxiosResponse, AxiosError };
