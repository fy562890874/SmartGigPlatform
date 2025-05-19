import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { get, post as apiPost } from '@/utils/http'

// 设置API基础URL
const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = ref(false)
  const user = ref<any>(null) 
  const userRoles = ref<string[]>([])
  const token = ref<string | null>(null)
  
  // 初始化时从localStorage读取token和用户信息
  function init() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
        // 确保 user.value 和 user.value.available_roles 存在
        if (user.value && user.value.available_roles) {
          userRoles.value = user.value.available_roles
        } else {
          userRoles.value = [] // 如果没有角色信息，则设置为空数组
        }
        isLoggedIn.value = true
        
        // 设置axios默认Authorization头
        axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      } catch (e) {
        console.error('Failed to parse user from localStorage', e);
        // 如果解析失败，清除损坏的 localStorage 数据
        logout(); 
      }
    }
  }
    async function login(phoneNumber: string, password: string, captcha?: string) {
    try {
      interface LoginResponseWrapper {
        code: number;
        message: string;
        data: {
          access_token: string;
          user: {
            id: number;
            uuid: string;
            phone_number: string;
            email: string | null;
            nickname: string | null;
            current_role: string;
            available_roles: string[];
            status: string;
            last_login_at: string | null;
            registered_at: string;
          };
        };
      }
      
      const requestData: any = {
        phone_number: phoneNumber,
        password: password
      }
      
      const response = await apiPost<LoginResponseWrapper>('/auth/login', requestData)
      
      if (response && response.code === 0 && response.data && response.data.access_token && response.data.user) {
        const actualData = response.data;
        token.value = actualData.access_token
        user.value = actualData.user
        userRoles.value = actualData.user.available_roles && Array.isArray(actualData.user.available_roles) 
                          ? actualData.user.available_roles 
                          : (actualData.user.current_role ? [actualData.user.current_role] : []);
        isLoggedIn.value = true
        
        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      } else {
        console.error('Login response data is not in expected format or request failed:', response);
        throw new Error(response?.message || '登录失败，服务器返回数据格式错误或请求失败');
      }
    } catch (error: any) {
      console.error('Login failed:', error.response?.data?.message || error.message);
      throw error; 
    }
  }
  async function register(phoneNumber: string, password: string, userType: string = 'freelancer') {
    try {
      interface RegisterResponseData { // This is the actual user data after registration
        id: number;
        uuid: string;
        phone_number: string;
        current_role: string;
        available_roles: string[];
        // ... 其他用户字段
      }
      interface RegisterResponseWrapper {
        code: number;
        message: string;
        data: RegisterResponseData; 
      }

      const response = await apiPost<RegisterResponseWrapper>('/auth/register', {
        phone_number: phoneNumber,
        password: password,
        user_type: userType
      })
      
      if (response && response.code === 0 && response.data) {
        console.log('Registration successful', response.data);
        // Decide if auto-login is needed or if user should be redirected to login
        // For now, let's assume registration implies the user needs to login separately
        // or if the backend is designed to auto-login, it should return token here.
        // If auto-login is intended and backend returns token & user upon registration:
        // (This part depends on backend's /auth/register response for a successful case)
        // if (response.data.access_token && response.data.user) { // Example if register returns token
        //   token.value = response.data.access_token;
        //   user.value = response.data.user;
        //   userRoles.value = response.data.user.available_roles || [];
        //   isLoggedIn.value = true;
        //   localStorage.setItem('token', token.value);
        //   localStorage.setItem('user', JSON.stringify(user.value));
        //   axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`;
        // }
      } else {
        console.error('Registration response data is not in expected format or request failed:', response);
        throw new Error(response?.message || '注册失败，服务器返回数据格式错误或请求失败');
      }

    } catch (error: any) {
      console.error('Registration failed:', error.response?.data?.message || error.message);
      throw error;
    }
  }

  function logout() {
    isLoggedIn.value = false
    user.value = null
    userRoles.value = []
    token.value = null
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    delete axios.defaults.headers.common['Authorization']
  }
  // 获取当前用户信息 (通常在应用加载时调用，或路由守卫中)
  async function getCurrentUser() {
    if (!token.value) {
      init();
      if (!token.value) return;
    }
    
    try {
      interface UserProfileData {
        id: number;
        uuid: string;
        phone_number: string;
        email: string | null;
        nickname: string | null;
        current_role: string;
        available_roles: string[];
        status: string;
        last_login_at: string | null;
        registered_at: string;
      }
      // The 'get' helper is assumed to return UserProfileData directly (the content of response.data.data)
      // if successful and handling the wrapper internally.
      // If 'get' returns the full GetUserResponseWrapper, the previous edit was correct and this one should be reverted.
      const userData = await get<UserProfileData>('/users/me');
      
      if (userData) { // Check if userData is truthy (exists and not null/undefined)
        user.value = userData;
        userRoles.value = userData.available_roles && Array.isArray(userData.available_roles)
                          ? userData.available_roles
                          : (userData.current_role ? [userData.current_role] : []);
        isLoggedIn.value = true;
        localStorage.setItem('user', JSON.stringify(user.value));
      } else {
        // This case might be hit if 'get' returns null on error or if API response was not as expected (e.g. code !== 0)
        // but was not an exception that 'get' re-threw.
        console.warn('Failed to get current user or data format incorrect, logging out. Response was not usable.');
        logout();
      }
    } catch (error: any) {
      console.error('Failed to fetch current user:', error.response?.data?.message || error.message);
      if (error.response && (error.response.status === 401 || error.response.status === 403)) {
        logout();
      }
    }
  }

  // 初始化
  init()

  return { isLoggedIn, user, userRoles, token, login, logout, register, getCurrentUser }
})