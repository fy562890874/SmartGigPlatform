<!--
  @file EditFreelancerProfileView.vue
  @description 零工用户编辑个人档案页面
  @author Fy
  @date 2023-05-21
-->
<template>
  <div class="edit-freelancer-profile page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>编辑零工个人档案</h1>
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
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="profileForm.basic.real_name" placeholder="请输入真实姓名" />
            </el-form-item>
            
            <el-form-item label="显示昵称" prop="nickname">
              <el-input v-model="profileForm.basic.nickname" placeholder="请输入您希望展示的昵称" />
            </el-form-item>
            
            <el-form-item label="性别" prop="gender">
              <el-radio-group v-model="profileForm.basic.gender">
                <el-radio label="male">男</el-radio>
                <el-radio label="female">女</el-radio>
                <el-radio label="other">其他</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="出生日期" prop="birth_date">
              <el-date-picker
                v-model="profileForm.basic.birth_date"
                type="date"
                placeholder="选择出生日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disableFutureDates"
              />
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
        
        <!-- 个人简介 -->
        <el-tab-pane label="个人简介" name="bio">
          <el-form 
            ref="bioFormRef" 
            :model="profileForm.bio" 
            :rules="bioRules" 
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="自我介绍" prop="bio">
              <el-input 
                v-model="profileForm.bio.bio" 
                type="textarea" 
                :rows="6" 
                placeholder="简要介绍自己的经历、技能和专长..."
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveBio" :loading="loading.saveBio">保存个人简介</el-button>
              <el-button @click="resetBioForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 工作偏好 -->
        <el-tab-pane label="工作偏好" name="preferences">
          <el-form 
            ref="preferencesFormRef" 
            :model="profileForm.preferences" 
            :rules="preferencesRules" 
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="可接受状态" prop="availability">
              <el-select v-model="profileForm.preferences.availability" placeholder="请选择您当前的接单状态">
                <el-option label="可接受新工作" value="available" />
                <el-option label="有限接受" value="limited" />
                <el-option label="暂不接受" value="unavailable" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="期望时薪(元)" prop="hourly_rate">
              <el-input-number 
                v-model="profileForm.preferences.hourly_rate" 
                :min="0" 
                :precision="2" 
                :step="10"
                placeholder="您期望的小时薪资" 
              />
            </el-form-item>
            
            <el-form-item label="工作类型偏好" prop="preferred_job_types">
              <el-checkbox-group v-model="profileForm.preferences.preferred_job_types">
                <el-checkbox label="remote">远程工作</el-checkbox>
                <el-checkbox label="onsite">现场工作</el-checkbox>
                <el-checkbox label="hybrid">混合模式</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="可工作时间" prop="available_hours">
              <el-checkbox-group v-model="profileForm.preferences.available_hours">
                <el-checkbox label="weekday_morning">工作日上午</el-checkbox>
                <el-checkbox label="weekday_afternoon">工作日下午</el-checkbox>
                <el-checkbox label="weekday_evening">工作日晚上</el-checkbox>
                <el-checkbox label="weekend_morning">周末上午</el-checkbox>
                <el-checkbox label="weekend_afternoon">周末下午</el-checkbox>
                <el-checkbox label="weekend_evening">周末晚上</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="工作偏好说明" prop="work_preferences_note">
              <el-input 
                v-model="profileForm.preferences.work_preferences_note" 
                type="textarea" 
                :rows="4" 
                placeholder="补充说明您的工作偏好，如时间安排、工作环境要求等"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="savePreferences" :loading="loading.savePreferences">保存工作偏好</el-button>
              <el-button @click="resetPreferencesForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 作品与链接 -->
        <el-tab-pane label="作品与链接" name="portfolio">
          <el-form 
            ref="portfolioFormRef" 
            :model="profileForm.portfolio" 
            :rules="portfolioRules" 
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="个人网站" prop="personal_website_url">
              <el-input v-model="profileForm.portfolio.personal_website_url" placeholder="https://example.com" />
            </el-form-item>
            
            <el-form-item label="LinkedIn" prop="linkedin_url">
              <el-input v-model="profileForm.portfolio.linkedin_url" placeholder="https://linkedin.com/in/yourname" />
            </el-form-item>
            
            <el-form-item label="GitHub" prop="github_url">
              <el-input v-model="profileForm.portfolio.github_url" placeholder="https://github.com/username" />
            </el-form-item>
            
            <el-form-item label="其他作品链接">
              <div v-for="(link, index) in profileForm.portfolio.portfolio_links" :key="index" class="portfolio-link-item">
                <el-input v-model="profileForm.portfolio.portfolio_links[index]" placeholder="https://example.com/yourwork" />
                <el-button type="danger" icon="Delete" @click="removePortfolioLink(index)" />
              </div>
              <el-button type="primary" plain @click="addPortfolioLink">添加作品链接</el-button>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="savePortfolio" :loading="loading.savePortfolio">保存作品与链接</el-button>
              <el-button @click="resetPortfolioForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, FormInstance } from 'element-plus';
import { Plus, Delete } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';

// 路由与状态管理
const router = useRouter();
const authStore = useAuthStore();

// 表单引用
const basicFormRef = ref<FormInstance>();
const bioFormRef = ref<FormInstance>();
const preferencesFormRef = ref<FormInstance>();
const portfolioFormRef = ref<FormInstance>();

// 标签页状态
const activeTab = ref('basic');

// 加载状态
const loading = reactive({
  profile: true,
  saveBasic: false,
  saveBio: false,
  savePreferences: false,
  savePortfolio: false
});

// 个人档案表单数据
const profileForm = reactive({
  basic: {
    real_name: '',
    nickname: '',
    gender: '',
    birth_date: '',
    contact_email: '',
    contact_phone: '',
    location_province: '',
    location_city: '',
    location_district: '',
    location_address: '',
    avatar_url: ''
  },
  bio: {
    bio: ''
  },
  preferences: {
    availability: '',
    hourly_rate: 0,
    preferred_job_types: [] as string[],
    available_hours: [] as string[],
    work_preferences_note: ''
  },
  portfolio: {
    personal_website_url: '',
    linkedin_url: '',
    github_url: '',
    portfolio_links: [] as string[]
  }
});

// 表单验证规则
const basicRules = {
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请输入显示昵称', trigger: 'blur' }
  ],
  gender: [
    { required: true, message: '请选择性别', trigger: 'change' }
  ],
  contact_email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  contact_phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码', trigger: 'blur' }
  ]
};

const bioRules = {
  bio: [
    { required: true, message: '请填写个人简介', trigger: 'blur' },
    { min: 10, max: 1000, message: '简介长度应在10-1000个字符之间', trigger: 'blur' }
  ]
};

const preferencesRules = {
  availability: [
    { required: true, message: '请选择可接受状态', trigger: 'change' }
  ],
  hourly_rate: [
    { type: 'number', message: '请输入有效的小时费率', trigger: 'blur' }
  ]
};

const portfolioRules = {
  personal_website_url: [
    { pattern: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w.-]*)*\/?$/, message: '请输入有效的网址', trigger: 'blur' }
  ],
  linkedin_url: [
    { pattern: /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w-]+\/?$/, message: '请输入有效的LinkedIn链接', trigger: 'blur' }
  ],
  github_url: [
    { pattern: /^(https?:\/\/)?(www\.)?github\.com\/[\w-]+\/?$/, message: '请输入有效的GitHub链接', trigger: 'blur' }
  ]
};

// 获取零工档案
const fetchFreelancerProfile = async () => {
  loading.profile = true;
  try {
    const profileData = await apiClient.get('profiles/freelancer/me');
    
    // 基本信息
    profileForm.basic.real_name = profileData?.real_name || '';
    profileForm.basic.nickname = profileData?.nickname || '';
    profileForm.basic.gender = profileData?.gender || '';
    profileForm.basic.birth_date = profileData?.birth_date || '';
    profileForm.basic.contact_email = profileData?.contact_email || '';
    profileForm.basic.contact_phone = profileData?.contact_phone || '';
    profileForm.basic.location_province = profileData?.location_province || '';
    profileForm.basic.location_city = profileData?.location_city || '';
    profileForm.basic.location_district = profileData?.location_district || '';
    profileForm.basic.location_address = profileData?.location_address || '';
    profileForm.basic.avatar_url = profileData?.avatar_url || '';
    
    // 个人简介
    profileForm.bio.bio = profileData?.bio || '';
    
    // 工作偏好
    profileForm.preferences.availability = profileData?.availability || '';
    profileForm.preferences.hourly_rate = profileData?.hourly_rate || 0;
    
    // 尝试解析工作偏好JSON
    try {
      if (profileData?.work_preferences) {
        let workPreferences;
        
        if (typeof profileData.work_preferences === 'string') {
          workPreferences = JSON.parse(profileData.work_preferences);
        } else if (typeof profileData.work_preferences === 'object') {
          workPreferences = profileData.work_preferences;
        }
        
        if (workPreferences) {
          profileForm.preferences.preferred_job_types = workPreferences.preferred_job_types || [];
          profileForm.preferences.available_hours = workPreferences.available_hours || [];
          profileForm.preferences.work_preferences_note = workPreferences.note || '';
        }
      }
    } catch (e) {
      console.error('解析工作偏好失败:', e);
    }
    
    // 作品与链接
    profileForm.portfolio.personal_website_url = profileData?.personal_website_url || '';
    profileForm.portfolio.linkedin_url = profileData?.linkedin_url || '';
    profileForm.portfolio.github_url = profileData?.github_url || '';
    profileForm.portfolio.portfolio_links = profileData?.portfolio_links || [];
    
  } catch (error) {
    console.error('获取零工档案失败:', error);
    ElMessage.warning('无法获取档案信息，创建新档案');
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
    
    const response = await apiClient.post('profiles/freelancer/me/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    // 更新头像URL
    profileForm.basic.avatar_url = response?.avatar_url || '';
    ElMessage.success('头像上传成功');
    onSuccess(response);
  } catch (error) {
    console.error('头像上传失败:', error);
    onError('上传失败');
  }
};

// 禁用未来日期
const disableFutureDates = (time: Date) => {
  return time.getTime() > Date.now();
};

// 保存基本信息
const saveBasicInfo = async () => {
  if (!basicFormRef.value) return;
  
  await basicFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.saveBasic = true;
      try {
        await apiClient.put('profiles/freelancer/me', profileForm.basic);
        ElMessage.success('基本信息保存成功');
      } catch (error) {
        console.error('保存基本信息失败:', error);
      } finally {
        loading.saveBasic = false;
      }
    }
  });
};

// 保存个人简介
const saveBio = async () => {
  if (!bioFormRef.value) return;
  
  await bioFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.saveBio = true;
      try {
        await apiClient.put('profiles/freelancer/me', {
          bio: profileForm.bio.bio
        });
        ElMessage.success('个人简介保存成功');
      } catch (error) {
        console.error('保存个人简介失败:', error);
      } finally {
        loading.saveBio = false;
      }
    }
  });
};

// 保存工作偏好
const savePreferences = async () => {
  if (!preferencesFormRef.value) return;
  
  await preferencesFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.savePreferences = true;
      try {
        // 构造工作偏好对象
        const workPreferences = {
          preferred_job_types: profileForm.preferences.preferred_job_types,
          available_hours: profileForm.preferences.available_hours,
          note: profileForm.preferences.work_preferences_note
        };
        
        await apiClient.put('profiles/freelancer/me', {
          availability: profileForm.preferences.availability,
          hourly_rate: profileForm.preferences.hourly_rate,
          work_preferences: JSON.stringify(workPreferences)
        });
        
        ElMessage.success('工作偏好保存成功');
      } catch (error) {
        console.error('保存工作偏好失败:', error);
      } finally {
        loading.savePreferences = false;
      }
    }
  });
};

// 保存作品与链接
const savePortfolio = async () => {
  if (!portfolioFormRef.value) return;
  
  await portfolioFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.savePortfolio = true;
      try {
        await apiClient.put('profiles/freelancer/me', {
          personal_website_url: profileForm.portfolio.personal_website_url,
          linkedin_url: profileForm.portfolio.linkedin_url,
          github_url: profileForm.portfolio.github_url,
          portfolio_links: profileForm.portfolio.portfolio_links
        });
        
        ElMessage.success('作品与链接保存成功');
      } catch (error) {
        console.error('保存作品与链接失败:', error);
      } finally {
        loading.savePortfolio = false;
      }
    }
  });
};

// 添加作品链接
const addPortfolioLink = () => {
  profileForm.portfolio.portfolio_links.push('');
};

// 移除作品链接
const removePortfolioLink = (index: number) => {
  profileForm.portfolio.portfolio_links.splice(index, 1);
};

// 重置表单
const resetBasicForm = () => {
  if (basicFormRef.value) {
    basicFormRef.value.resetFields();
  }
};

const resetBioForm = () => {
  if (bioFormRef.value) {
    bioFormRef.value.resetFields();
  }
};

const resetPreferencesForm = () => {
  if (preferencesFormRef.value) {
    preferencesFormRef.value.resetFields();
  }
};

const resetPortfolioForm = () => {
  if (portfolioFormRef.value) {
    portfolioFormRef.value.resetFields();
  }
};

// 组件挂载
onMounted(() => {
  if (authStore.isLoggedIn && authStore.user?.current_role === 'freelancer') {
    fetchFreelancerProfile();
  } else {
    ElMessage.warning('请先以零工身份登录');
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

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.portfolio-link-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}
</style>


