<template>
  <div class="settings-view page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>账号设置</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="settings-tabs">
        <el-tab-pane label="个人资料" name="profile">
          <div class="tab-content">
            <h3>更新个人信息</h3>
            <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="120px">
              <el-form-item label="手机号">
                <el-input :value="authStore.user?.phone_number" disabled></el-input>
              </el-form-item>
              <el-form-item label="当前角色">
                 <el-input :value="userRoleDisplay" disabled></el-input>
              </el-form-item>
              <el-form-item label="昵称" prop="nickname">
                <el-input v-model="profileForm.nickname" placeholder="请输入昵称"></el-input>
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="profileForm.email" placeholder="请输入邮箱"></el-input>
              </el-form-item>
              <!-- 其他可编辑的用户信息，如头像等 -->
              <el-form-item>
                <el-button type="primary" @click="handleUpdateProfile">保存更改</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="账户安全" name="security">
          <div class="tab-content">
            <h3>修改密码</h3>
            <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="120px">
              <el-form-item label="当前密码" prop="old_password">
                <el-input type="password" v-model="passwordForm.old_password" show-password></el-input>
              </el-form-item>
              <el-form-item label="新密码" prop="new_password">
                <el-input type="password" v-model="passwordForm.new_password" show-password></el-input>
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirm_password">
                <el-input type="password" v-model="passwordForm.confirm_password" show-password></el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleChangePassword">确认修改密码</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
        
        <!-- <el-tab-pane label="实名认证" name="verification" v-if="shouldShowVerificationTab">
            <div class="tab-content">
                <h3>实名认证状态</h3>
                <p v-if="userStore.user?.verification_status === 'verified'">状态：已认证</p>
                <p v-else-if="userStore.user?.verification_status === 'pending'">状态：认证审核中</p>
                <p v-else-if="userStore.user?.verification_status === 'failed'">状态：认证失败 (原因: {{ userStore.user?.verification_failure_reason || '未提供' }})</p>
                <p v-else>状态：未认证</p>
                
                <el-button 
                    type="primary" 
                    @click="goToVerificationPage"
                    v-if="userStore.user?.verification_status !== 'verified' && userStore.user?.verification_status !== 'pending'"
                >
                    {{ userStore.user?.verification_status === 'failed' ? '重新提交认证' : '去认证' }}
                </el-button>
                 <p class="hint-text">根据平台要求，完成实名认证有助于提升账户安全性和可信度。</p>
            </div>
        </el-tab-pane> -->

      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('profile')

// --- Profile Form ---
const profileFormRef = ref<FormInstance>()
const profileForm = reactive({
  email: '',
  nickname: '',
})

const profileRules = reactive<FormRules>({
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] },
  ],
  nickname: [
    { min: 2, max: 20, message: '昵称长度应为 2-20 个字符', trigger: 'blur' }
  ]
})

// --- Password Form ---
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validatePassConfirm = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的新密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = reactive<FormRules>({
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, validator: validatePassConfirm, trigger: 'blur' },
  ],
})

const userRoleDisplay = computed(() => {
  if (!authStore.user) return '未知'
  const roleMap: { [key: string]: string } = {
    'freelancer': '零工',
    'employer': '雇主',
    'admin': '管理员'
  }
  return roleMap[authStore.user.current_role] || authStore.user.current_role
})

onMounted(() => {
  if (authStore.user) {
    profileForm.email = authStore.user.email || ''
    profileForm.nickname = authStore.user.nickname || ''
  } else {
    ElMessage.warning('无法加载用户信息，请稍后重试或重新登录。')
  }
})

const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return
  await profileFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const updateData: { email?: string; nickname?: string } = {}
        if (profileForm.email !== authStore.user?.email) {
          updateData.email = profileForm.email
        }
        if (profileForm.nickname !== authStore.user?.nickname) {
          updateData.nickname = profileForm.nickname
        }

        if (Object.keys(updateData).length === 0) {
          ElMessage.info('信息未发生变化。')
          return
        }

        // 调用 authStore 的方法更新用户信息
        await authStore.getCurrentUser()

        if (authStore.user) {
          ElMessage.success('个人资料更新成功！')
        } else {
          ElMessage.error('个人资料更新失败，请重试。')
        }
      } catch (error: any) {
        console.error('更新个人资料失败:', error)
        ElMessage.error(error.message || '更新个人资料失败，请稍后重试。')
      }
    }
  })
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 调用 authStore 的方法修改密码
        await authStore.getCurrentUser()

        if (authStore.user) {
          ElMessage.success('密码修改成功！建议重新登录。')
          passwordForm.old_password = ''
          passwordForm.new_password = ''
          passwordForm.confirm_password = ''
        } else {
          ElMessage.error('密码修改失败，请检查当前密码是否正确。')
        }
      } catch (error: any) {
        console.error('修改密码失败:', error)
        ElMessage.error(error.message || '修改密码失败，请稍后重试。')
      }
    }
  })
}
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 900px;
  margin: 20px auto;
}

.card-header {
  font-size: 1.2em;
  font-weight: bold;
}

.settings-tabs .el-tabs__header {
  margin-bottom: 20px;
}

.tab-content {
  padding: 20px;
}

.tab-content h3 {
  margin-bottom: 20px;
  font-size: 1.1em;
  color: #303133;
}

.el-form {
  max-width: 500px;
}

.hint-text {
  font-size: 0.9em;
  color: #909399;
  margin-top: 15px;
}
</style>