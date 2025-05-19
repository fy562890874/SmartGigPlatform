<!--
  @file EditEmployerProfileView.vue
  @description 雇主用户编辑个人档案页面
  @author Fy
  @date 2023-05-23
-->
<template>
  <div class="edit-employer-profile page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>编辑雇主档案</h1>
        </div>
      </template>
      
      <div v-if="loading.profile" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>
      
      <el-tabs v-else v-model="activeTab" class="profile-tabs">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form 
            ref="basicFormRef" 
            :model="profileForm.basic" 
            :rules="basicRules" 
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="雇主类型" prop="profile_type">
              <el-radio-group v-model="profileForm.basic.profile_type" :disabled="profileLoaded">
                <el-radio label="individual">个人雇主</el-radio>
                <el-radio label="company">企业雇主</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="profileForm.basic.real_name" placeholder="请输入真实姓名" />
            </el-form-item>
            
            <el-form-item label="显示昵称" prop="nickname">
              <el-input v-model="profileForm.basic.nickname" placeholder="请输入您希望展示的昵称" />
            </el-form-item>
            
            <el-form-item label="联系邮箱" prop="contact_email">
              <el-input v-model="profileForm.basic.contact_email" placeholder="请输入联系邮箱" />
            </el-form-item>
            
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="profileForm.basic.contact_phone" placeholder="请输入联系电话" />
            </el-form-item>
            
            <el-form-item label="常驻省份" prop="location_province">
              <el-input v-model="profileForm.basic.location_province" placeholder="例如：浙江省" />
            </el-form-item>
            
            <el-form-item label="常驻城市" prop="location_city">
              <el-input v-model="profileForm.basic.location_city" placeholder="例如：杭州市" />
            </el-form-item>
            
            <el-form-item label="常驻区县" prop="location_district">
              <el-input v-model="profileForm.basic.location_district" placeholder="例如：西湖区" />
            </el-form-item>
            
            <el-form-item label="详细地址" prop="location_address">
              <el-input 
                v-model="profileForm.basic.location_address" 
                type="textarea" 
                :rows="2" 
                placeholder="请输入详细地址"
              />
            </el-form-item>
            
            <el-form-item label="头像">
              <el-upload
                class="avatar-uploader"
                action="#"
                :http-request="uploadAvatar"
                :show-file-list="false"
                accept="image/jpeg,image/png,image/jpg"
              >
                <img v-if="profileForm.basic.avatar_url" :src="profileForm.basic.avatar_url" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
              <div class="upload-hint">点击上传头像（JPG/PNG格式，最大2MB）</div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveBasicInfo" :loading="loading.saveBasic">保存基本信息</el-button>
              <el-button @click="resetBasicForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 企业信息（仅企业雇主显示） -->
        <el-tab-pane 
          v-if="profileForm.basic.profile_type === 'company'" 
          label="企业信息" 
          name="company"
        >
          <el-form 
            ref="companyFormRef" 
            :model="profileForm.company" 
            :rules="companyRules" 
            label-width="150px"
            class="profile-form"
          >
            <el-form-item label="公司名称" prop="company_name">
              <el-input v-model="profileForm.company.company_name" placeholder="请输入公司名称" />
            </el-form-item>
            
            <el-form-item label="统一社会信用代码" prop="business_license_number">
              <el-input v-model="profileForm.company.business_license_number" placeholder="请输入统一社会信用代码" />
            </el-form-item>
            
            <el-form-item label="公司详细地址" prop="company_address">
              <el-input 
                v-model="profileForm.company.company_address" 
                type="textarea" 
                :rows="2" 
                placeholder="请输入公司详细地址"
              />
            </el-form-item>
            
            <el-form-item label="公司简介" prop="company_description">
              <el-input 
                v-model="profileForm.company.company_description" 
                type="textarea" 
                :rows="4" 
                placeholder="请简要介绍公司情况..."
              />
            </el-form-item>
            
            <el-form-item label="营业执照照片" prop="business_license_photo">
              <el-upload
                class="license-uploader"
                action="#"
                :http-request="uploadLicensePhoto"
                :show-file-list="false"
                accept="image/jpeg,image/png,image/jpg"
              >
                <img 
                  v-if="profileForm.company.business_license_photo_url" 
                  :src="profileForm.company.business_license_photo_url" 
                  class="license-photo" 
                />
                <div v-else class="upload-placeholder">
                  <el-icon class="upload-icon"><Plus /></el-icon>
                  <div>点击上传营业执照</div>
                </div>
              </el-upload>
              <div class="upload-hint">请上传清晰的营业执照照片（JPG/PNG格式，最大5MB）</div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveCompanyInfo" :loading="loading.saveCompany">保存企业信息</el-button>
              <el-button @click="resetCompanyForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 简介与描述 -->
        <el-tab-pane label="简介与描述" name="description">
          <el-form 
            ref="descFormRef" 
            :model="profileForm.description" 
            :rules="descriptionRules" 
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="自我介绍" prop="bio">
              <el-input 
                v-model="profileForm.description.bio" 
                type="textarea" 
                :rows="6" 
                placeholder="简要介绍您的背景、行业经验等..."
              />
            </el-form-item>
            
            <el-form-item label="招聘偏好" prop="hiring_preference">
              <el-input 
                v-model="profileForm.description.hiring_preference" 
                type="textarea" 
                :rows="4" 
                placeholder="描述您在招聘方面的偏好，例如希望招聘什么类型的人才..."
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveDescription" :loading="loading.saveDesc">保存简介</el-button>
              <el-button @click="resetDescForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 联系方式与链接 -->
        <el-tab-pane label="联系与链接" name="contacts">
          <el-form 
            ref="contactsFormRef" 
            :model="profileForm.contacts" 
            :rules="contactsRules" 
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="官方网站" prop="website_url">
              <el-input v-model="profileForm.contacts.website_url" placeholder="https://example.com" />
            </el-form-item>
            
            <el-form-item label="LinkedIn" prop="linkedin_url">
              <el-input v-model="profileForm.contacts.linkedin_url" placeholder="https://linkedin.com/in/yourname" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveContacts" :loading="loading.saveContacts">保存联系信息</el-button>
              <el-button @click="resetContactsForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, FormInstance } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';

// 路由与状态管理
const router = useRouter();
const authStore = useAuthStore();

// 表单引用
const basicFormRef = ref<FormInstance>();
const companyFormRef = ref<FormInstance>();
const descFormRef = ref<FormInstance>();
const contactsFormRef = ref<FormInstance>();

// 标签页状态
const activeTab = ref('basic');

// 加载状态
const loading = reactive({
  profile: true,
  saveBasic: false,
  saveCompany: false,
  saveDesc: false,
  saveContacts: false
});

// 是否已加载档案
const profileLoaded = ref(false);

// 个人档案表单数据
const profileForm = reactive({
  basic: {
    profile_type: 'individual',
    real_name: '',
    nickname: '',
    contact_email: '',
    contact_phone: '',
    location_province: '',
    location_city: '',
    location_district: '',
    location_address: '',
    avatar_url: ''
  },
  company: {
    company_name: '',
    business_license_number: '',
    company_address: '',
    company_description: '',
    business_license_photo_url: ''
  },
  description: {
    bio: '',
    hiring_preference: ''
  },
  contacts: {
    website_url: '',
    linkedin_url: ''
  }
});

// 表单验证规则
const basicRules = {
  profile_type: [
    { required: true, message: '请选择雇主类型', trigger: 'change' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请输入显示昵称', trigger: 'blur' }
  ],
  contact_email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  contact_phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码', trigger: 'blur' }
  ]
};

const companyRules = {
  company_name: [
    { required: true, message: '请输入公司名称', trigger: 'blur' }
  ],
  business_license_number: [
    { required: true, message: '请输入统一社会信用代码', trigger: 'blur' }
  ],
  company_address: [
    { required: true, message: '请输入公司详细地址', trigger: 'blur' }
  ]
};

const descriptionRules = {
  bio: [
    { max: 1000, message: '简介长度应不超过1000个字符', trigger: 'blur' }
  ],
  hiring_preference: [
    { max: 500, message: '招聘偏好长度应不超过500个字符', trigger: 'blur' }
  ]
};

const contactsRules = {
  website_url: [
    { pattern: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w.-]*)*\/?$/, message: '请输入有效的网址', trigger: 'blur' }
  ],
  linkedin_url: [
    { pattern: /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w-]+\/?$/, message: '请输入有效的LinkedIn链接', trigger: 'blur' }
  ]
};

// 获取雇主档案
const fetchEmployerProfile = async () => {
  loading.profile = true;
  try {
    const response = await apiClient.get('profiles/employer/me');
    
    // 填充基本信息表单
    const profileData = response.data;
    profileLoaded.value = true;
    
    // 基本信息
    profileForm.basic.profile_type = profileData.profile_type || 'individual';
    profileForm.basic.real_name = profileData.real_name || '';
    profileForm.basic.nickname = profileData.nickname || '';
    profileForm.basic.contact_email = profileData.contact_email || '';
    profileForm.basic.contact_phone = profileData.contact_phone || '';
    profileForm.basic.location_province = profileData.location_province || '';
    profileForm.basic.location_city = profileData.location_city || '';
    profileForm.basic.location_district = profileData.location_district || '';
    profileForm.basic.location_address = profileData.location_address || '';
    profileForm.basic.avatar_url = profileData.avatar_url || '';
    
    // 公司信息（如果是企业雇主）
    if (profileData.profile_type === 'company') {
      profileForm.company.company_name = profileData.company_name || '';
      profileForm.company.business_license_number = profileData.business_license_number || '';
      profileForm.company.company_address = profileData.company_address || '';
      profileForm.company.company_description = profileData.company_description || '';
      profileForm.company.business_license_photo_url = profileData.business_license_photo_url || '';
    }
    
    // 简介与描述
    profileForm.description.bio = profileData.bio || '';
    profileForm.description.hiring_preference = profileData.hiring_preference || '';
    
    // 联系方式与链接
    profileForm.contacts.website_url = profileData.website_url || '';
    profileForm.contacts.linkedin_url = profileData.linkedin_url || '';
    
  } catch (error) {
    console.error('获取雇主档案失败:', error);
    // 如果是404错误，表示档案不存在，使用默认值
    profileLoaded.value = false;
  } finally {
    loading.profile = false;
  }
};

// 上传头像
const uploadAvatar = async (options: any) => {
  const { file, onSuccess, onError } = options;
  
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像文件不能超过2MB');
    onError('文件过大');
    return;
  }
  
  try {
    // 创建一个FormData对象
    const formData = new FormData();
    formData.append('avatar', file);
    
    const response = await apiClient.post('profiles/employer/me/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    // 更新头像URL
    profileForm.basic.avatar_url = response.data.avatar_url;
    ElMessage.success('头像上传成功');
    onSuccess(response);
  } catch (error) {
    console.error('头像上传失败:', error);
    onError('上传失败');
  }
};

// 上传营业执照照片
const uploadLicensePhoto = async (options: any) => {
  const { file, onSuccess, onError } = options;
  
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('营业执照照片不能超过5MB');
    onError('文件过大');
    return;
  }
  
  try {
    // 创建一个FormData对象
    const formData = new FormData();
    formData.append('license', file);
    
    const response = await apiClient.post('profiles/employer/me/license', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    // 更新营业执照照片URL
    profileForm.company.business_license_photo_url = response.data.business_license_photo_url;
    ElMessage.success('营业执照照片上传成功');
    onSuccess(response);
  } catch (error) {
    console.error('营业执照照片上传失败:', error);
    onError('上传失败');
  }
};

// 保存基本信息
const saveBasicInfo = async () => {
  if (!basicFormRef.value) return;
  
  await basicFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.saveBasic = true;
      try {
        // 处理雇主类型，如果已经加载过档案，则不能修改雇主类型
        const payload = { ...profileForm.basic };
        if (profileLoaded.value) {
          delete payload.profile_type;
        }
        
        await apiClient.put('profiles/employer/me', payload);
        ElMessage.success('基本信息保存成功');
        
        // 如果是新创建且选择了公司类型，自动切换到公司信息标签
        if (!profileLoaded.value && profileForm.basic.profile_type === 'company') {
          activeTab.value = 'company';
          profileLoaded.value = true;
        }
      } catch (error) {
        console.error('保存基本信息失败:', error);
      } finally {
        loading.saveBasic = false;
      }
    }
  });
};

// 保存公司信息
const saveCompanyInfo = async () => {
  if (!companyFormRef.value) return;
  
  await companyFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.saveCompany = true;
      try {
        await apiClient.put('profiles/employer/me', profileForm.company);
        ElMessage.success('企业信息保存成功');
      } catch (error) {
        console.error('保存企业信息失败:', error);
      } finally {
        loading.saveCompany = false;
      }
    }
  });
};

// 保存简介与描述
const saveDescription = async () => {
  if (!descFormRef.value) return;
  
  await descFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.saveDesc = true;
      try {
        await apiClient.put('profiles/employer/me', profileForm.description);
        ElMessage.success('简介与描述保存成功');
      } catch (error) {
        console.error('保存简介与描述失败:', error);
      } finally {
        loading.saveDesc = false;
      }
    }
  });
};

// 保存联系方式与链接
const saveContacts = async () => {
  if (!contactsFormRef.value) return;
  
  await contactsFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.saveContacts = true;
      try {
        await apiClient.put('profiles/employer/me', profileForm.contacts);
        ElMessage.success('联系方式与链接保存成功');
      } catch (error) {
        console.error('保存联系方式与链接失败:', error);
      } finally {
        loading.saveContacts = false;
      }
    }
  });
};

// 重置表单
const resetBasicForm = () => {
  if (basicFormRef.value) {
    basicFormRef.value.resetFields();
  }
};

const resetCompanyForm = () => {
  if (companyFormRef.value) {
    companyFormRef.value.resetFields();
  }
};

const resetDescForm = () => {
  if (descFormRef.value) {
    descFormRef.value.resetFields();
  }
};

const resetContactsForm = () => {
  if (contactsFormRef.value) {
    contactsFormRef.value.resetFields();
  }
};

// 组件挂载
onMounted(() => {
  if (authStore.isLoggedIn && authStore.user?.current_role === 'employer') {
    fetchEmployerProfile();
  } else {
    ElMessage.warning('请先以雇主身份登录');
    router.push('/login');
  }
});
</script>

<style scoped>
.page-container {
  max-width: 1000px;
  margin: 20px auto;
  padding: 0 15px;
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

.loading-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-tabs {
  margin-top: 20px;
}

.profile-form {
  max-width: 800px;
  margin: 20px auto;
}

.avatar-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 178px;
  height: 178px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-uploader:hover {
  border-color: #409EFF;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.license-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 320px;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.license-uploader:hover {
  border-color: #409EFF;
}

.license-photo {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c939d;
}

.upload-icon {
  font-size: 36px;
  margin-bottom: 10px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>