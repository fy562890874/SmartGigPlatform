import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { get, post } from '@/utils/http'

// 定义接口类型
interface UserData {
  id: number
  uuid: string
  phone_number: string
  email: string | null
  nickname: string | null
  current_role: string
  available_roles: string[]
  status: string
  last_login_at: string | null
  registered_at: string
}

interface LoginResponse {
  access_token: string
  user: UserData
}

// 设置API基础URL
const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = ref(false)
  const user = ref<UserData | null>(null) 
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
      const requestData = {
        phone_number: phoneNumber,
        password: password
      }
      
      const response = await post<LoginResponse>('/auth/login', requestData)
      
      // 直接处理API响应数据，apiClient已经解包
      if (response && response.access_token && response.user) {
        token.value = response.access_token
        user.value = response.user
        userRoles.value = response.user.available_roles && Array.isArray(response.user.available_roles) 
                          ? response.user.available_roles 
                          : (response.user.current_role ? [response.user.current_role] : []);
        isLoggedIn.value = true
        
        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
        return response
      } else {
        console.error('Login response data is not in expected format:', response);
        throw new Error('登录失败，服务器返回数据格式错误');
      }
    } catch (error: any) {
      console.error('Login failed:', error.response?.data?.message || error.message);
      throw error; 
    }
  }
  
  async function register(phoneNumber: string, password: string, userType: string = 'freelancer') {
    try {
      const response = await post('/auth/register', {
        phone_number: phoneNumber,
        password: password,
        user_type: userType
      })
      
      // 注册成功后可以自动登录或返回结果
      return response
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
  
  // 获取当前用户信息
  async function getCurrentUser() {
    if (!token.value) {
      init();
      if (!token.value) return;
    }
    
    try {
      const userData = await get<UserData>('/users/me');
      
      if (userData) {
        user.value = userData;
        userRoles.value = userData.available_roles && Array.isArray(userData.available_roles)
                          ? userData.available_roles
                          : (userData.current_role ? [userData.current_role] : []);
        isLoggedIn.value = true;
        localStorage.setItem('user', JSON.stringify(user.value));
      } else {
        console.warn('Failed to get current user or data format incorrect, logging out.');
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