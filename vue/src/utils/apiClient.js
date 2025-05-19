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

    // Construct the full URL using apiConfig.getApiUrl for all requests
    // This ensures that even if a relative path is given to apiClient.get(), post(), etc.,
    // it's correctly prefixed with the base URL and API version.
    if (config.url) {
        // Prevent double-slashing if config.url already starts with a slash
        const requestPath = config.url.startsWith('/') ? config.url.substring(1) : config.url;
        config.url = apiConfig.getApiUrl(requestPath);
    } else {
        // Fallback or error if URL is not provided, though Axios typically requires a URL.
        console.error('Axios request config missing URL');
        // Potentially set a default or throw an error
    }
    
    return config;
  },
  (error) => {
    ElMessage.error('Error in request setup.');
    return Promise.reject(error);
  }
);

// Response interceptor for centralized error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      let message = data?.message || 'An API error occurred.';

      switch (status) {
        case 400:
          message = data?.error || 'Bad Request. Please check your input.';
          if (data?.errors) { // Handle validation errors from Flask-RESTx
            const validationMessages = Object.values(data.errors).flat().join(' ');
            message = `${message} ${validationMessages}`;
          }
          break;
        case 401: // Unauthorized
          message = 'Unauthorized. Please log in again.';
          // Example: redirect to login or trigger re-authentication
          // const authStore = useAuthStore();
          // authStore.logout(); 
          // window.location.href = '/login'; // Or use Vue Router
          break;
        case 403: // Forbidden
          message = 'Forbidden. You do not have permission to access this resource.';
          break;
        case 404: // Not Found
          message = 'Resource not found.';
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          message = `Server error (${status}). Please try again later.`;
          break;
        default:
          // For other errors, use the message from the response if available
          break;
      }
      ElMessage.error(message);
    } else if (error.request) {
      // The request was made but no response was received
      ElMessage.error('Network error or server not responding.');
    } else {
      // Something happened in setting up the request that triggered an Error
      ElMessage.error('An unexpected error occurred.');
    }
    return Promise.reject(error);
  }
);

export default apiClient;