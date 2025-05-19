<!--
  @file Register.vue
  @description 用户注册页面。支持手机号注册、图形验证码、密码、确认密码、身份选择，注册后自动登录并跳转主页。
  @author [Your Name]
  @date 2025-04-27
  @routePath '/auth/register'
  @relatedRoutes '/auth/login'（登录）、'/auth/forgot-password'（忘记密码）、'/'（主页）
-->
<template>
  <div class="register-view">
    <el-card class="register-card">
      <h2 class="register-title">注册新账号</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent>
        <!-- 手机号 -->
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" clearable size="large" />
        </el-form-item>
        
        <!-- 图形验证码 -->
        <el-form-item label="验证码" prop="code">
          <div class="code-row">
            <el-input v-model="form.code" placeholder="请输入验证码" clearable size="large" style="flex:1;" />
            <div class="captcha-image" @click="refreshCaptcha">
              <img :src="captchaImage" alt="点击刷新验证码" title="点击刷新验证码" />
            </div>
          </div>
        </el-form-item>
        
        <!-- 密码 -->
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password clearable size="large" />
        </el-form-item>
        <!-- 确认密码 -->
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" show-password clearable size="large" />
        </el-form-item>
        <!-- 身份选择 -->
        <el-form-item label="注册身份" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio label="freelancer">零工提供者</el-radio>
            <el-radio label="employer">用工需求方</el-radio>
          </el-radio-group>
        </el-form-item>
        <!-- 注册按钮 -->
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" class="register-btn" size="large" style="width:100%">
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-links">
        <router-link to="/auth/login">已有账号？去登录</router-link>
        <router-link to="/auth/forgot-password">忘记密码</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { post } from '@/utils/http'
import { generateRandomString, generateCaptchaImage } from '@/utils/captcha'

const form = reactive({
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
  role: 'freelancer' // Changed 'worker' to 'freelancer'
})

const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { 
      validator: (rule: any, value: string, callback: any) => {
        if (value.toLowerCase() !== captchaCode.value.toLowerCase()) {
          callback(new Error('验证码不正确'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: any) => {
        if (value !== form.password) {
          callback(new Error('两次密码输入不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  role: [
    { required: true, message: '请选择注册身份', trigger: 'change' }
  ]
}

const formRef = ref()
const loading = ref(false)
const router = useRouter()
const authStore = useAuthStore()

// 验证码相关
const captchaCode = ref('')
const captchaImage = ref('')

// 生成新的验证码
const refreshCaptcha = () => {
  captchaCode.value = generateRandomString(4)
  captchaImage.value = generateCaptchaImage(captchaCode.value)
}

// 页面加载时生成验证码
onMounted(() => {
  refreshCaptcha()
})

async function handleRegister() {
  // @ts-ignore
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      // 调用后端注册API
      await authStore.register(form.phone, form.password, form.role)
      ElMessage.success('注册成功，已自动登录')
      router.push('/')
    } catch (error) {
      console.error('注册失败:', error)
      // HTTP 拦截器会处理错误提示
      // 刷新验证码
      refreshCaptcha()
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-color);
}
.register-card {
  width: 400px;
  padding: 32px 36px;
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}
.register-title {
  text-align: center;
  margin-bottom: 24px;
  color: var(--primary-red);
}
.code-row {
  display: flex;
  gap: 12px;
}
.captcha-image {
  width: 120px;
  height: 40px;
  overflow: hidden;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.captcha-image img {
  width: 100%;
  height: 100%;
}
.register-btn {
  width: 100%;
}
.register-links {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
  font-size: 14px;
}
.register-links a {
  color: var(--secondary-blue);
}
.register-links a:hover {
  color: var(--accent-gold);
}
</style>