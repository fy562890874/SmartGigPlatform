<template>
  <div class="login-container">
    <el-card class="login-card" shadow="always">
      <template #header>
        <div class="card-header">
          <span>欢迎登录智慧零工平台</span>
        </div>
      </template>
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="手机号/账号" prop="phone_number">
          <el-input
            v-model="loginForm.phone_number"
            placeholder="请输入手机号或账号"
            :prefix-icon="User"
            clearable
            size="large"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            :prefix-icon="Lock"
            clearable
            size="large"
          />
        </el-form-item>
        
        <el-form-item label="验证码" prop="captcha">
          <div class="captcha-row">
            <el-input
              v-model="loginForm.captcha"
              placeholder="请输入验证码"
              clearable
              size="large"
            />
            <div class="captcha-image" @click="refreshCaptcha">
              <img :src="captchaImage" alt="点击刷新验证码" title="点击刷新验证码" />
            </div>
          </div>
        </el-form-item>
        
        <el-form-item>
          <div class="form-actions">
            <el-checkbox v-model="loginForm.rememberMe">7天内自动登录</el-checkbox>
            <el-link type="primary" @click="goToForgotPassword">忘记密码?</el-link>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleLogin"
            :loading="loading"
            class="login-button"
            size="large"
          >
            登 录
          </el-button>
        </el-form-item>
        <el-form-item>
           <div class="register-link">
             <span>还没有账号? </span>
             <el-link type="primary" @click="goToRegister">立即注册</el-link>
           </div>
        </el-form-item>
        <!-- Optional: Third-party login -->
        <!-- <el-divider>其他登录方式</el-divider>
        <div class="third-party-login">
          <el-button circle :icon="ChatDotRound" />
          <el-button circle :icon="Platform" />
        </div> -->
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElCard, ElForm, ElFormItem, ElInput, ElButton, ElCheckbox, ElLink, ElMessage, ElDivider, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, ChatDotRound, Platform } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { generateRandomString, generateCaptchaImage } from '@/utils/captcha'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  phone_number: '',
  password: '',
  captcha: '',
  rememberMe: false,
})

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

const loginRules = reactive<FormRules>({
  phone_number: [{ required: true, message: '请输入手机号或账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  captcha: [
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
  ]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // 调用authStore登录方法，连接到后端API
        await authStore.login(loginForm.phone_number, loginForm.password, loginForm.captcha)
        ElMessage.success('登录成功')
        // 重定向到原计划页面或首页
        const redirect = router.currentRoute.value.query.redirect as string || '/'
        router.push(redirect)
      } catch (error: any) {
        console.error('Login failed:', error)
        ElMessage.error(error.response?.data?.message || '登录失败，请检查账号或密码')
        // 刷新验证码
        refreshCaptcha()
      } finally {
        loading.value = false
      }
    } else {
      console.log('表单验证失败')
    }
  })
}

function goToRegister() {
  router.push('/auth/register')
}

function goToForgotPassword() {
  router.push('/auth/forgot-password')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px); /* Adjust based on header/footer height */
  background-color: var(--background-color);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--border-color-light);
}

.card-header {
  text-align: center;
  font-size: 1.5em;
  font-weight: 500;
  color: var(--primary-red);
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.login-button {
  width: 100%;
}

.register-link {
  width: 100%;
  text-align: center;
  font-size: 14px;
  color: var(--muted-text-color);
}

.register-link .el-link {
  vertical-align: baseline; /* Align link with text */
}

.captcha-row {
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

.third-party-login {
  display: flex;
  justify-content: center;
  gap: 20px;
}

/* Ensure icons have proper color */
.el-input__prefix .el-icon {
  color: var(--el-text-color-placeholder);
}
</style>