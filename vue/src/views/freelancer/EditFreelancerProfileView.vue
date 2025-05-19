<template>
  <div class="edit-freelancer-profile page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEditing ? '编辑' : '创建' }}零工档案</span>
          <el-button @click="goBack">返回</el-button>
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
        label-width="120px"
        label-position="right"
        class="profile-form"
        @submit.prevent="submitProfileForm" 
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="profileForm.real_name" placeholder="请输入真实姓名"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="profileForm.gender" placeholder="请选择性别" style="width: 100%;">
                <el-option label="男" value="male"></el-option>
                <el-option label="女" value="female"></el-option>
                <el-option label="其他" value="other"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出生日期" prop="birth_date">
              <el-date-picker 
                v-model="profileForm.birth_date" 
                type="date" 
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              ></el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="头像URL" prop="avatar_url">
          <el-input v-model="profileForm.avatar_url" placeholder="请输入头像图片链接">
            <template #append v-if="profileForm.avatar_url">
                <el-avatar size="small" :src="profileForm.avatar_url" />
            </template>
          </el-input>
          <!-- TODO: 可扩展为文件上传组件 -->
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系邮箱" prop="contact_email">
              <el-input v-model="profileForm.contact_email" placeholder="请输入联系邮箱"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="profileForm.contact_phone" placeholder="请输入联系电话"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="常驻省份" prop="location_province">
              <el-input v-model="profileForm.location_province" placeholder="例如：广东省"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="常驻城市" prop="location_city">
              <el-input v-model="profileForm.location_city" placeholder="例如：深圳市"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="个人简介" prop="bio">
          <el-input 
            type="textarea" 
            v-model="profileForm.bio" 
            :rows="4"
            placeholder="介绍一下您的专业技能、工作经验和期望等..."
          ></el-input>
        </el-form-item>

        <el-divider content-position="left">工作偏好</el-divider>
        <el-row :gutter="20">
            <el-col :span="12">
                <el-form-item label="期望时薪(元)" prop="hourly_rate">
                    <el-input-number v-model="profileForm.hourly_rate" :min="0" placeholder="例如: 100" style="width: 100%;"></el-input-number>
                </el-form-item>
            </el-col>
            <el-col :span="12">
                <el-form-item label="可用状态" prop="availability">
                    <el-select v-model="profileForm.availability" placeholder="您的工作状态" style="width: 100%;">
                        <el-option label="可接受新工作" value="available"></el-option>
                        <el-option label="忙碌中" value="busy"></el-option>
                        <el-option label="暂不接受新工作" value="unavailable"></el-option>
                    </el-select>
                </el-form-item>
            </el-col>
        </el-row>
        <el-form-item label="工作偏好详情" prop="work_preferences_json_string">
          <el-input 
            type="textarea" 
            v-model="profileForm.work_preferences_json_string" 
            :rows="5"
            placeholder='请输入JSON格式的工作偏好，例如：\n{\n  "preferred_categories\": [\"软件开发\", \"平面设计\"],\n  "preferred_time_slots": [\"工作日晚上\", \"周末全天\"],\n  "preferred_location_type": \"remote_only\", \n  "min_project_budget": 500 \n}'
          ></el-input>
          <p class="hint-text">工作偏好需为合法的JSON格式。例如：`{"preferred_categories": ["家政"], "preferred_time_slots":["weekend"]}`</p>
        </el-form-item>

        <el-divider content-position="left">作品集与链接 (可选)</el-divider>
         <el-form-item label="个人网站" prop="personal_website_url">
          <el-input v-model="profileForm.personal_website_url" placeholder="https://example.com"></el-input>
        </el-form-item>
        <el-form-item label="LinkedIn" prop="linkedin_url">
          <el-input v-model="profileForm.linkedin_url" placeholder="https://linkedin.com/in/yourprofile"></el-input>
        </el-form-item>
        <el-form-item label="GitHub" prop="github_url">
          <el-input v-model="profileForm.github_url" placeholder="https://github.com/yourusername"></el-input>
        </el-form-item>
        <el-form-item label="Dribbble" prop="dribbble_url">
          <el-input v-model="profileForm.dribbble_url" placeholder="https://dribbble.com/yourusername"></el-input>
        </el-form-item>
        <el-form-item label="Behance" prop="behance_url">
          <el-input v-model="profileForm.behance_url" placeholder="https://behance.net/yourusername"></el-input>
        </el-form-item>
        <el-form-item label="作品集链接" prop="portfolio_links_string">
          <el-input 
            type="textarea"
            v-model="profileForm.portfolio_links_string"
            :rows="3"
            placeholder="多个链接请用英文逗号 (,) 分隔"
          ></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitProfileForm" :loading="submitting">
            {{ isEditing ? '保存更新' : '创建档案' }}
          </el-button>
          <el-button @click="resetFormFields">重置表单</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, ElLoading, FormInstance, FormRules } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';

const router = useRouter();
const authStore = useAuthStore();

const profileFormRef = ref<FormInstance>();
const profileForm = reactive({
  real_name: '',
  nickname: '',
  gender: null as string | null,
  birth_date: null as string | null,
  bio: '',
  avatar_url: '',
  location_province: '',
  location_city: '',
  contact_email: '',
  contact_phone: '',
  hourly_rate: null as number | null,
  availability: null as string | null,
  work_preferences_json_string: '',
  portfolio_links_string: '',
  linkedin_url: '',
  github_url: '',
  dribbble_url: '',
  behance_url: '',
  personal_website_url: '',
});

const loadingInitialData = ref(false);
const submitting = ref(false);
const isEditing = ref(false); // To determine if creating or editing

// Validation rules
const profileRules = reactive<FormRules>({
  real_name: [{ required: true, message: '真实姓名不能为空', trigger: 'blur' }],
  nickname: [{ min: 2, max: 20, message: '昵称长度在 2 到 20 个字符', trigger: 'blur' }],
  birth_date: [{ type: 'date', message: '请选择有效的出生日期', trigger: 'change', transform: (value) => value ? new Date(value) : null }],
  contact_email: [{ type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] }],
  contact_phone: [
    { 
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入有效的中国大陆手机号码',
      trigger: ['blur', 'change'] 
    }
  ],
  avatar_url: [{ type: 'url', message: '请输入有效的URL', trigger: 'blur' }],
  hourly_rate: [{ type: 'number', min: 0, message: '时薪必须为非负数', trigger: 'blur'}],
  work_preferences_json_string: [
    {
      validator: (rule, value, callback) => {
        if (value) {
          try {
            JSON.parse(value);
            callback();
          } catch (e) {
            callback(new Error('工作偏好必须是有效的JSON格式'));
          }
        } else {
          callback(); // Allow empty
        }
      },
      trigger: 'blur',
    },
  ],
  personal_website_url: [{ type: 'url', message: '请输入有效的个人网站URL', trigger: 'blur' }],
  linkedin_url: [{ type: 'url', message: '请输入有效的LinkedIn URL', trigger: 'blur' }],
  github_url: [{ type: 'url', message: '请输入有效的GitHub URL', trigger: 'blur' }],
  dribbble_url: [{ type: 'url', message: '请输入有效的Dribbble URL', trigger: 'blur' }],
  behance_url: [{ type: 'url', message: '请输入有效的Behance URL', trigger: 'blur' }],
});

// 获取现有档案数据
const fetchProfileData = async () => {
  loadingInitialData.value = true;
  try {
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      return;
    }

    const response = await axios.get(apiConfig.getApiUrl('profiles/freelancer/me'), {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    // 处理API响应
    if (response.data && response.data.code === 0 && response.data.data) {
      const profileData = response.data.data;
      isEditing.value = true;
      
      // 填充表单数据
      Object.keys(profileForm).forEach(key => {
        // 这些字段需要特殊处理
        if (['work_preferences_json_string', 'portfolio_links_string'].includes(key)) return;
        
        if (key in profileData && profileData[key] !== null && profileData[key] !== undefined) {
          (profileForm as any)[key] = profileData[key as keyof typeof profileData];
        }
      });
      
      // 处理工作偏好 JSON
      if (profileData.work_preferences) {
        profileForm.work_preferences_json_string = JSON.stringify(profileData.work_preferences, null, 2);
      }
      
      // 处理作品集链接数组
      if (profileData.portfolio_links && Array.isArray(profileData.portfolio_links)) {
        profileForm.portfolio_links_string = profileData.portfolio_links.join(', ');
      }
      
    } else {
      isEditing.value = false; // 没有数据，所以是创建模式
      ElMessage.info('您还没有零工档案，请填写创建。');
    }
  } catch (error: any) {
    console.error('获取零工档案失败:', error);
    
    if (error.response && error.response.status === 404) {
      isEditing.value = false; // 404表示无档案，进入创建模式
      ElMessage.info('您还没有零工档案，请填写创建。');
    } else {
      ElMessage.error(error.response?.data?.message || '获取档案信息失败，请稍后重试。');
    }
  } finally {
    loadingInitialData.value = false;
  }
};

// 提交表单
const submitProfileForm = async () => {
  if (!profileFormRef.value) return;
  
  await profileFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true;
      let loadingInstance = ElLoading.service({ text: isEditing.value ? '正在保存...' : '正在创建...' });

      try {
        const token = authStore.token;
        if (!token) {
          ElMessage.error('您尚未登录或登录已过期');
          router.push('/login');
          loadingInstance.close();
          return;
        }
        
        // 准备要提交的数据
        const payload: any = {
          real_name: profileForm.real_name || null,
          nickname: profileForm.nickname || null,
          gender: profileForm.gender,
          birth_date: profileForm.birth_date || null,
          bio: profileForm.bio || null,
          avatar_url: profileForm.avatar_url || null,
          location_province: profileForm.location_province || null,
          location_city: profileForm.location_city || null,
          contact_email: profileForm.contact_email || null,
          contact_phone: profileForm.contact_phone || null,
          hourly_rate: profileForm.hourly_rate,
          availability: profileForm.availability,
          personal_website_url: profileForm.personal_website_url || null,
          linkedin_url: profileForm.linkedin_url || null,
          github_url: profileForm.github_url || null,
          dribbble_url: profileForm.dribbble_url || null,
          behance_url: profileForm.behance_url || null,
        };

        // 处理工作偏好 JSON 字段
        if (profileForm.work_preferences_json_string) {
          try {
            payload.work_preferences = JSON.parse(profileForm.work_preferences_json_string);
          } catch (e) {
            ElMessage.error('工作偏好JSON格式无效。');
            submitting.value = false;
            loadingInstance.close();
            return;
          }
        } else {
          payload.work_preferences = null;
        }

        // 处理作品集链接数组
        if (profileForm.portfolio_links_string) {
          payload.portfolio_links = profileForm.portfolio_links_string.split(',').map(link => link.trim()).filter(link => link);
        } else {
          payload.portfolio_links = [];
        }

        // 发送请求到后端API
        const response = await axios.put('http://127.0.0.1:5000/api/v1/profiles/freelancer/me', payload, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.data && response.data.code === 0) {
          ElMessage.success(isEditing.value ? '零工档案更新成功！' : '零工档案创建成功！');
          router.push('/freelancer/dashboard');
        } else {
          ElMessage.error(response.data?.message || '保存失败，请稍后重试');
        }
      } catch (error: any) {
        console.error('保存零工档案失败:', error);
        let errorMessage = '保存失败，请稍后重试';
        
        if (error.response) {
          if (error.response.data && error.response.data.message) {
            errorMessage = `保存失败: ${error.response.data.message}`;
          } else if (error.response.data && error.response.data.errors) {
            errorMessage = "保存失败：";
            const errors = error.response.data.errors;
            for (const field in errors) {
              errorMessage += `${errors[field].join(', ')} `;
            }
          }
        }
        
        ElMessage.error(errorMessage);
      } finally {
        submitting.value = false;
        loadingInstance.close();
      }
    } else {
      ElMessage.error('请检查表单填写是否正确。');
    }
  });
};

// 重置表单
const resetFormFields = () => {
  if (profileFormRef.value) {
    profileFormRef.value.resetFields();
  }
  
  if (isEditing.value) {
    fetchProfileData(); 
  } else {
    Object.keys(profileForm).forEach(key => {
      const k = key as keyof typeof profileForm;
      if (['hourly_rate', 'gender', 'availability', 'birth_date'].includes(k as string)) {
        (profileForm as any)[k] = null;
      } else {
        (profileForm as any)[k] = '';
      }
    });
  }
};

// 返回按钮
const goBack = () => {
  router.back();
};

// 组件挂载时执行
onMounted(() => {
  // 检查用户是否登录
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录。');
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
  max-width: 1000px; /* Increased max-width for better layout with two columns */
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

.el-select, .el-date-picker, .el-input-number {
    width: 100%;
}

.hint-text {
  font-size: 0.85em;
  color: #909399;
  margin-top: 5px;
  line-height: 1.4;
}

.el-divider {
    margin-top: 30px;
    margin-bottom: 20px;
}
</style>


