<template>
  <div class="edit-employer-profile page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEditing ? '编辑' : '创建' }}雇主档案</span>
          <el-button @click="router.back()">返回</el-button>
        </div>
      </template>

      <div v-if="loadingInitialData" class="loading-state">
        <el-skeleton :rows="15" animated />
      </div>
      <el-form 
        v-else
        :model="profileForm"
        :rules="profileRules" 
        ref="profileFormRef" 
        label-width="150px"
        label-position="right"
        class="profile-form"
      >
        <el-form-item label="档案类型" prop="profile_type">
          <el-radio-group v-model="profileForm.profile_type" @change="handleProfileTypeChange">
            <el-radio label="individual">个人雇主</el-radio>
            <el-radio label="company">企业雇主</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="昵称/简称" prop="nickname">
          <el-input v-model="profileForm.nickname" placeholder="您的昵称或公司简称"></el-input>
        </el-form-item>

        <el-form-item :label="profileForm.profile_type === 'individual' ? '真实姓名' : '法人/联系人姓名'" prop="real_name">
          <el-input v-model="profileForm.real_name" :placeholder="profileForm.profile_type === 'individual' ? '您的真实姓名' : '公司法人或主要联系人姓名'"></el-input>
        </el-form-item>

        <el-form-item label="头像/Logo URL" prop="avatar_url">
          <el-input v-model="profileForm.avatar_url" placeholder="可粘贴图片链接">
             <template #append v-if="profileForm.avatar_url">
                <el-avatar shape="square" size="small" :src="profileForm.avatar_url" />
            </template>
          </el-input>
          <!-- TODO: 考虑支持文件上传 -->
        </el-form-item>

        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="profileForm.contact_phone" placeholder="用于接收通知和沟通"></el-input>
        </el-form-item>

        <el-form-item label="所在省份" prop="location_province">
          <el-input v-model="profileForm.location_province" placeholder="例如：北京市"></el-input>
        </el-form-item>
        <el-form-item label="所在城市" prop="location_city">
          <el-input v-model="profileForm.location_city" placeholder="例如：北京市"></el-input>
        </el-form-item>
        <el-form-item label="所在区县" prop="location_district">
          <el-input v-model="profileForm.location_district" placeholder="例如：朝阳区 (可选)"></el-input>
        </el-form-item>

        <template v-if="profileForm.profile_type === 'company'">
          <el-divider content-position="left">企业信息 (企业雇主必填)</el-divider>
          <el-form-item label="公司全称" prop="company_name">
            <el-input v-model="profileForm.company_name" placeholder="请输入公司完整名称"></el-input>
          </el-form-item>
          <el-form-item label="统一社会信用代码" prop="business_license_number">
            <el-input v-model="profileForm.business_license_number" placeholder="18位统一社会信用代码"></el-input>
          </el-form-item>
          <el-form-item label="公司地址" prop="company_address">
            <el-input v-model="profileForm.company_address" placeholder="请输入公司详细办公地址"></el-input>
          </el-form-item>
          <el-form-item label="公司简介" prop="company_description">
            <el-input type="textarea" :rows="3" v-model="profileForm.company_description" placeholder="简要介绍一下您的公司"></el-input>
          </el-form-item>
          <el-form-item label="营业执照照片URL" prop="business_license_photo_url">
            <el-input v-model="profileForm.business_license_photo_url" placeholder="请上传营业执照照片并填写链接">
                <template #append v-if="profileForm.business_license_photo_url">
                    <el-image style="width: 30px; height: 30px" :src="profileForm.business_license_photo_url" :preview-src-list="[profileForm.business_license_photo_url]" fit="cover" />
                </template>
            </el-input>
            <!-- TODO: 考虑支持文件上传 -->
          </el-form-item>
        </template>
        
        <el-form-item>
          <el-button type="primary" @click="submitProfileForm" :loading="submitting">
            {{ isEditing ? '保存更新' : '创建档案' }}
          </el-button>
          <el-button @click="resetForm">重置表单</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, FormInstance, FormRules } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';

const router = useRouter();
const authStore = useAuthStore();
const profileFormRef = ref<FormInstance>();
const loadingInitialData = ref(true);
const submitting = ref(false);
const isEditing = ref(false);

// 表单数据
const profileForm = reactive({
  profile_type: 'individual',
  nickname: '',
  real_name: '',
  avatar_url: '',
  contact_phone: '',
  location_province: '',
  location_city: '',
  location_district: '',
  company_name: '',
  business_license_number: '',
  company_address: '',
  company_description: '',
  business_license_photo_url: ''
});

// 表单验证规则
const profileRules = reactive<FormRules>({
  profile_type: [
    { required: true, message: '请选择档案类型', trigger: 'change' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  contact_phone: [
    { 
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入有效的手机号码',
      trigger: 'blur' 
    }
  ],
  company_name: [
    { 
      required: true, 
      message: '请输入公司名称', 
      trigger: 'blur',
      // 仅当档案类型为company时验证
      validator: (rule, value, callback) => {
        if (profileForm.profile_type === 'company' && !value) {
          callback(new Error('企业雇主必须填写公司名称'));
        } else {
          callback();
        }
      }
    }
  ],
  business_license_number: [
    {
      required: true,
      message: '请输入统一社会信用代码',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (profileForm.profile_type === 'company' && !value) {
          callback(new Error('企业雇主必须填写统一社会信用代码'));
        } else {
          callback();
        }
      }
    }
  ]
});

// 切换档案类型
const handleProfileTypeChange = (value: string) => {
  // 切换时可以添加一些额外逻辑，如清空公司相关字段等
  if (value === 'individual') {
    profileForm.company_name = '';
    profileForm.business_license_number = '';
    profileForm.company_address = '';
    profileForm.company_description = '';
    profileForm.business_license_photo_url = '';
  }
};

// 获取现有档案数据
const fetchProfileData = async () => {
  loadingInitialData.value = true;
  
  try {
    // 构造API请求
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      return;
    }
    
    // 使用axios直接请求API
    const response = await axios.get(apiConfig.getApiUrl('profiles/employer/me'), {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    // 处理响应数据
    if (response.data && response.data.code === 0 && response.data.data) {
      // API返回成功，用返回的数据填充表单
      const profileData = response.data.data;
      isEditing.value = true;
      
      // 填充表单数据
      Object.keys(profileForm).forEach(key => {
        if (key in profileData && profileData[key] !== null && profileData[key] !== undefined) {
          profileForm[key as keyof typeof profileForm] = profileData[key];
        }
      });
      
    } else {
      // API可能返回了成功状态但数据异常
      isEditing.value = false;
      ElMessage.info('您尚未创建雇主档案，请填写创建。');
    }
  } catch (error: any) {
    console.error('获取雇主档案失败:', error);
    
    if (error.response && error.response.status === 404) {
      // 404表示当前用户还没有雇主档案
      isEditing.value = false;
      ElMessage.info('您尚未创建雇主档案，请填写创建。');
    } else {
      // 其他错误
      ElMessage.error(error.response?.data?.message || '获取档案信息失败，请稍后重试');
    }
  } finally {
    loadingInitialData.value = false;
  }
};

// 提交表单
const submitProfileForm = async () => {
  if (!profileFormRef.value) return;
  
  await profileFormRef.value.validate(async (valid, fields) => {
    if (valid) {
      submitting.value = true;
      
      try {
        const token = authStore.token;
        if (!token) {
          ElMessage.error('您尚未登录或登录已过期');
          router.push('/login');
          return;
        }
        
        // 准备要提交的数据
        const payload = { ...profileForm };
        
        // 发送PUT请求创建或更新档案
        const response = await axios.put('http://127.0.0.1:5000/api/v1/profiles/employer/me', payload, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.data && response.data.code === 0) {
          // 请求成功
          ElMessage.success(isEditing.value ? '雇主档案更新成功！' : '雇主档案创建成功！');
          router.push('/employer/dashboard');
        } else {
          // 请求虽然返回但API报告错误
          ElMessage.error(response.data?.message || '保存失败，请稍后重试');
        }
      } catch (error: any) {
        console.error('保存雇主档案失败:', error);
        let errorMsg = '保存失败，请稍后重试';
        
        if (error.response) {
          const { status, data } = error.response;
          
          if (status === 400 && data.errors) {
            // 处理验证错误
            const validationErrors = Object.values(data.errors).flat().join('; ');
            errorMsg = `表单验证失败: ${validationErrors}`;
          } else if (data && data.message) {
            errorMsg = data.message;
          }
        }
        
        ElMessage.error(errorMsg);
      } finally {
        submitting.value = false;
      }
    } else {
      ElMessage.error('表单验证失败，请检查输入');
      console.log('验证失败的字段:', fields);
    }
  });
};

// 重置表单
const resetForm = () => {
  if (profileFormRef.value) {
    profileFormRef.value.resetFields();
  }
  
  // 如果是编辑模式，重新获取原始数据
  if (isEditing.value) {
    fetchProfileData();
  } 
  // 如果是创建模式，重置为默认值
  else {
    profileForm.profile_type = 'individual';
    profileForm.nickname = '';
    profileForm.real_name = '';
    profileForm.avatar_url = '';
    profileForm.contact_phone = '';
    profileForm.location_province = '';
    profileForm.location_city = '';
    profileForm.location_district = '';
    profileForm.company_name = '';
    profileForm.business_license_number = '';
    profileForm.company_address = '';
    profileForm.company_description = '';
    profileForm.business_license_photo_url = '';
  }
};

// 组件挂载时获取数据
onMounted(() => {
  // 检查用户是否登录
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  // 获取现有档案数据
  fetchProfileData();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 800px;
  margin: 20px auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.2em;
  font-weight: bold;
}

.loading-state {
    padding: 20px;
}

.profile-form {
  padding: 20px 0;
}

.el-form-item {
    margin-bottom: 22px;
}

.el-select, .el-date-picker {
    width: 100%;
}

.hint-text {
  font-size: 0.85em;
  color: #909399;
  margin-top: 5px;
  line-height: 1.4;
}
</style>