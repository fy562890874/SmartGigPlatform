<!--
  @file SettingsView.vue
  @description 用户设置页面，包括账号基本信息设置、密码修改等功能
  @author Fy
  @date 2023-05-20
-->
<template>
  <div class="settings-view page-container">
    <el-card shadow="never" class="settings-card">
      <template #header>
        <div class="card-header">
          <h1>账号设置</h1>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <!-- 基本信息设置 -->
        <el-tab-pane label="基本信息" name="basic-info">
          <el-form 
            ref="basicInfoFormRef" 
            :model="basicInfoForm" 
            :rules="basicInfoRules" 
            label-width="120px"
            v-loading="loading.basicInfo"
          >
            <el-form-item label="邮箱地址" prop="email">
              <el-input v-model="basicInfoForm.email" placeholder="您的邮箱地址" />
            </el-form-item>
            
            <!-- 根据需要添加其他基本字段 -->
            
            <el-form-item>
              <el-button type="primary" @click="updateBasicInfo">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 密码修改 -->
        <el-tab-pane label="修改密码" name="change-password">
          <el-form 
            ref="passwordFormRef" 
            :model="passwordForm" 
            :rules="passwordRules" 
            label-width="120px"
            v-loading="loading.password"
          >
            <el-form-item label="当前密码" prop="old_password">
              <el-input 
                v-model="passwordForm.old_password" 
                type="password" 
                placeholder="请输入当前密码" 
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input 
                v-model="passwordForm.new_password" 
                type="password" 
                placeholder="请输入新密码" 
                show-password
              />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input 
                v-model="passwordForm.confirm_password" 
                type="password" 
                placeholder="请再次输入新密码" 
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword">确认修改</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 角色切换 -->
        <el-tab-pane label="角色切换" name="switch-role">
          <div class="role-switch-container" v-loading="loading.roleSwitch">
            <p class="current-role">当前角色: <strong>{{ formatRole(authStore.user?.current_role) }}</strong></p>
            
            <div class="role-options">
              <el-radio-group v-model="selectedRole" @change="handleRoleSelect">
                <el-radio label="freelancer">零工</el-radio>
                <el-radio label="employer">雇主</el-radio>
              </el-radio-group>
            </div>
            
            <div class="role-actions">
              <el-button 
                type="primary" 
                @click="switchRole" 
                :disabled="!selectedRole || selectedRole === authStore.user?.current_role"
              >
                切换到{{ formatRole(selectedRole) }}角色
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, FormInstance, FormRules } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';

// 定义用户数据类型
interface UserData {
  email?: string;
  current_role?: string;
  available_roles?: string[];
  [key: string]: any;
}

// 表单引用
const basicInfoFormRef = ref<FormInstance>();
const passwordFormRef = ref<FormInstance>();

// 获取auth store实例
const authStore = useAuthStore();

// 标签页状态
const activeTab = ref('basic');

// 加载和提交状态
const loading = reactive({
  basicInfo: false,
  password: false,
  roleSwitch: false
});
const submitting = ref(false);

// 基本信息表单
const basicInfoForm = reactive({
  email: '',
  phone: '',
  current_role: ''
});

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
});

// 基本信息验证规则
const basicInfoRules = reactive<FormRules>({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] }
  ]
});

// 密码表单验证规则
const passwordRules = reactive<FormRules>({
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
});

// 当前可用角色和选择的角色
const selectedRole = ref('');
const availableRoles = ref<string[]>([]);

// 获取用户信息
const fetchUserInfo = async () => {
  loading.basicInfo = true;
  try {
    const userData = await apiClient.get<UserData>('/user/me');
    
    // 填充表单数据
    basicInfoForm.email = userData?.email || '';
    selectedRole.value = userData?.current_role || '';
    
    // 设置可选角色
    availableRoles.value = userData?.available_roles || [];
    
    // 如果用户没有当前角色但有可用角色，设置第一个可用角色为当前角色
    if (!selectedRole.value && availableRoles.value.length > 0) {
      selectedRole.value = availableRoles.value[0];
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
  } finally {
    loading.basicInfo = false;
  }
};

// 更新用户信息
const updateBasicInfo = async () => {
  submitting.value = true;
  try {
    await apiClient.put('/user/me', basicInfoForm);
    
    ElMessage.success('更新成功');
    
    // 如果角色改变了，更新 authStore
    if (selectedRole.value && selectedRole.value !== authStore.user?.current_role) {
      if (authStore.user) {
        authStore.user.current_role = selectedRole.value;
      }
    }
  } catch (error) {
    console.error('更新用户信息失败:', error);
  } finally {
    submitting.value = false;
  }
};

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return;
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.password = true;
      try {
        await apiClient.put('/user/password', {
          current_password: passwordForm.old_password,
          new_password: passwordForm.new_password
        });
        
        ElMessage.success('密码已成功修改');
        passwordForm.old_password = '';
        passwordForm.new_password = '';
        passwordForm.confirm_password = '';
      } catch (error) {
        console.error('密码修改失败:', error);
      } finally {
        loading.password = false;
      }
    }
  });
};

// 验证密码表单
const validatePasswordForm = () => {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次输入的密码不一致');
    return false;
  }
  return true;
};

// 格式化角色名称
const formatRole = (role?: string) => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    freelancer: '零工',
    employer: '雇主',
  };
  return role ? (roleMap[role] || role) : '未知';
};

// 角色选择
const handleRoleSelect = (value: string) => {
  selectedRole.value = value;
};

// 切换角色
const switchRole = async () => {
  if (!selectedRole.value || selectedRole.value === authStore.user?.current_role) {
    return;
  }

  loading.roleSwitch = true;
  try {
    await apiClient.put('/users/me/role', {
      current_role: selectedRole.value
    });
    
    // 更新 Pinia store 中的用户角色
    if (authStore.user) {
      authStore.user = { ...authStore.user, current_role: selectedRole.value };
    }

    ElMessage.success(`已切换到${formatRole(selectedRole.value)}角色`);
  } catch (error) {
    console.error('切换角色失败:', error);
  } finally {
    loading.roleSwitch = false;
  }
};

// 页面加载
onMounted(() => {
  fetchUserInfo();
});
</script>

<style scoped>
.page-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 15px;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h1 {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0;
}

.role-switch-container {
  padding: 20px 0;
}

.current-role {
  margin-bottom: 20px;
  font-size: 16px;
}

.role-options {
  margin-bottom: 20px;
}

.role-actions {
  margin-top: 30px;
}
</style>