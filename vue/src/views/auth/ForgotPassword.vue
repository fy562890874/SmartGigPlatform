<template>
  <div class="forgot-container">
    <el-card class="forgot-card">
      <h2 class="forgot-title">找回密码</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入注册手机号" clearable size="large" />
        </el-form-item>
        
        <el-form-item label="验证码" prop="code">
          <div class="code-row">
            <el-input v-model="form.code" placeholder="请输入验证码" clearable size="large" style="flex:1;" />
            <div class="captcha-image" @click="refreshCaptcha">
              <img :src="captchaImage" alt="点击刷新验证码" title="点击刷新验证码" />
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="新密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入新密码" show-password clearable size="large" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入新密码" show-password clearable size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleReset" class="forgot-btn" size="large" style="width:100%">
            {{ loading ? '重置中...' : '重置密码' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="forgot-links">
        <router-link to="/auth/login">返回登录</router-link>
        <router-link to="/auth/register">注册新账号</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { post } from '@/utils/http'
import { generateRandomString, generateCaptchaImage } from '@/utils/captcha'

const form = reactive({
  phone: '',
  code: '',
  password: '',
  confirmPassword: ''
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
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
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
  ]
}

const formRef = ref()
const loading = ref(false)
const router = useRouter()

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

async function handleReset() {
  // @ts-ignore
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      await post('/auth/reset_password', {
        phone_number: form.phone,
        new_password: form.password
      })
      
      ElMessage.success('密码重置成功，请重新登录')
      router.push('/auth/login')
    } catch (error) {
      console.error('密码重置失败:', error)
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
.forgot-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-color);
}
.forgot-card {
  width: 400px;
  padding: 32px 36px;
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}
.forgot-title {
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
.forgot-btn {
  width: 100%;
}
.forgot-links {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
  font-size: 14px;
}
.forgot-links a {
  color: var(--secondary-blue);
}
.forgot-links a:hover {
  color: var(--accent-gold);
}
</style>