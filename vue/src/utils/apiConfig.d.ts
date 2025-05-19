// e:\SmartGigPlatform\Vue\src\utils\apiConfig.d.ts

interface ApiConfig {
  baseURL: string;
  version: string;
  timeout: number;
  getApiUrl: (path: string) => string;
}

declare const apiConfig: ApiConfig;
export default apiConfig;
