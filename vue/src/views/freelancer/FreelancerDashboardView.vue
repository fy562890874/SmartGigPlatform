<template>
  <div class="freelancer-dashboard page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>我的仪表盘</span>
          <div class="action-buttons">
            <el-button type="primary" @click="goToEditProfile">编辑我的档案</el-button>
            <el-button type="info" @click="router.push('/my-orders')">我的订单</el-button>
          </div>
        </div>
      </template>

      <div v-if="loadingProfile || loadingSkills" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>
      <el-empty description="您还没有创建零工档案。" v-else-if="!profileExists && !loadingProfile">
        <el-button type="success" @click="goToEditProfile">创建我的零工档案</el-button>
      </el-empty>
      <div v-else-if="freelancerProfile" class="profile-details">
        <el-descriptions title="基础信息" :column="2" border class="profile-section">
          <el-descriptions-item label="真实姓名">{{ freelancerProfile.real_name || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ freelancerProfile.nickname || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ formatGender(freelancerProfile.gender) }}</el-descriptions-item>
          <el-descriptions-item label="出生日期">{{ freelancerProfile.birth_date || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ freelancerProfile.contact_email || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ freelancerProfile.contact_phone || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="常驻省份">{{ freelancerProfile.location_province || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="常驻城市">{{ freelancerProfile.location_city || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="头像">
            <el-avatar v-if="freelancerProfile.avatar_url" :size="60" :src="freelancerProfile.avatar_url" />
            <span v-else>未上传</span>
          </el-descriptions-item>
           <el-descriptions-item label="档案验证状态">
            <el-tag :type="getVerificationStatusType(freelancerProfile.verification_status)">
              {{ formatVerificationStatus(freelancerProfile.verification_status) }}
            </el-tag>
            <el-button 
              v-if="freelancerProfile.verification_status !== 'verified' && freelancerProfile.verification_status !== 'pending'"
              type="warning" 
              size="small"
              style="margin-left: 10px;"
              @click="goToVerificationPage"
            >
              {{ freelancerProfile.verification_status === 'failed' ? '重新提交认证' : '去认证' }}
            </el-button>
          </el-descriptions-item>
        </el-descriptions>

        <div class="profile-section">
          <h4>个人简介</h4>
          <p class="bio-text">{{ freelancerProfile.bio || '暂无简介。' }}</p>
        </div>
        
        <div class="profile-section">
          <div class="section-header">
            <h4>我的技能</h4>
            <el-button type="text" @click="goToManageSkills">管理技能</el-button>
          </div>
          <div v-if="freelancerSkills.length">
            <el-tag 
              v-for="skill in freelancerSkills" 
              :key="skill.id" 
              class="skill-tag"
              type="success"
            >
              {{ skill.skill_name }} ({{ skill.experience_level }})
            </el-tag>
          </div>
          <el-empty description="您还没有添加任何技能。" v-else-if="!loadingSkills" />
        </div>

        <el-descriptions title="工作偏好" :column="1" border class="profile-section">
          <el-descriptions-item label="期望时薪 (元)">{{ freelancerProfile.hourly_rate || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="可用状态">{{ formatAvailability(freelancerProfile.availability) }}</el-descriptions-item>
          <el-descriptions-item label="工作偏好详情">
            <pre class="work-preference-json">{{ freelancerProfile.work_preferences ? JSON.stringify(freelancerProfile.work_preferences, null, 2) : '未设置' }}</pre>
          </el-descriptions-item>
        </el-descriptions>

        <el-descriptions title="作品集与链接" :column="1" border class="profile-section">
          <el-descriptions-item label="个人网站">{{ freelancerProfile.personal_website_url || '未提供' }}</el-descriptions-item>
          <el-descriptions-item label="LinkedIn">{{ freelancerProfile.linkedin_url || '未提供' }}</el-descriptions-item>
          <el-descriptions-item label="GitHub">{{ freelancerProfile.github_url || '未提供' }}</el-descriptions-item>
          <el-descriptions-item label="Dribbble">{{ freelancerProfile.dribbble_url || '未提供' }}</el-descriptions-item>
          <el-descriptions-item label="Behance">{{ freelancerProfile.behance_url || '未提供' }}</el-descriptions-item>
          <el-descriptions-item label="作品集链接">
            <div v-if="freelancerProfile.portfolio_links && freelancerProfile.portfolio_links.length">
              <ul>
                <li v-for="(link, index) in freelancerProfile.portfolio_links" :key="index">
                  <a :href="link" target="_blank" rel="noopener noreferrer">{{ link }}</a>
                </li>
              </ul>
            </div>
            <span v-else>未提供</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';

const router = useRouter();
const authStore = useAuthStore();

const freelancerProfile = ref<any>(null);
const freelancerSkills = ref<any[]>([]);
const loadingProfile = ref(true);
const loadingSkills = ref(true);
const profileExists = ref(false);

// 获取零工档案数据
const fetchFreelancerProfile = async () => {
  loadingProfile.value = true;
  try {
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      return;
    }

    // 使用axios直接请求API
    const response = await axios.get(apiConfig.getApiUrl('profiles/freelancer/me'), {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    // 处理响应数据
    if (response.data && response.data.code === 0 && response.data.data) {
      freelancerProfile.value = response.data.data;
      profileExists.value = true;
    } else {
      profileExists.value = false;
      freelancerProfile.value = null;
    }
  } catch (error: any) {
    console.error('获取零工档案失败:', error);
    
    // 处理404错误（未创建档案）
    if (error.response && error.response.status === 404) {
      profileExists.value = false;
      freelancerProfile.value = null;
    } else {
      ElMessage.error(error.response?.data?.message || '获取零工档案失败，请稍后再试。');
    }
  } finally {
    loadingProfile.value = false;
  }
};

// 获取零工技能数据
const fetchFreelancerSkills = async () => {
  loadingSkills.value = true;
  try {
    const token = authStore.token;
    if (!token) {
      return;
    }

    // 使用axios直接请求API
    const response = await axios.get('http://127.0.0.1:5000/api/v1/profiles/freelancer/me/skills', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    // 处理响应数据
    if (response.data && response.data.code === 0) {
      if (Array.isArray(response.data.data)) {
        freelancerSkills.value = response.data.data;
      } else if (response.data.data && Array.isArray(response.data.data.skills)) {
        freelancerSkills.value = response.data.data.skills;
      } else {
        freelancerSkills.value = [];
      }
    } else {
      freelancerSkills.value = [];
    }
  } catch (error: any) {
    console.error('获取零工技能失败:', error);
    
    // 只在档案存在但获取技能失败时显示错误
    if (profileExists.value) {
      ElMessage.error('获取技能列表失败。');
    }
    
    freelancerSkills.value = [];
  } finally {
    loadingSkills.value = false;
  }
};

// 页面跳转函数
const goToEditProfile = () => {
  router.push('/freelancer/edit-profile');
};

const goToManageSkills = () => {
  router.push('/freelancer/manage-skills');
};

const goToVerificationPage = () => {
  router.push('/verifications/submit');
};

// 格式化函数
const formatGender = (gender: string | null) => {
  if (!gender) return '未设置';
  const genderMap: { [key: string]: string } = {
    male: '男',
    female: '女',
    other: '其他',
  };
  return genderMap[gender.toLowerCase()] || '未知';
};

const formatAvailability = (availability: string | null) => {
  if (!availability) return '未设置';
  const availabilityMap: { [key: string]: string } = {
    available: '可接受新工作',
    busy: '忙碌中',
    unavailable: '暂不接受新工作',
  };
  return availabilityMap[availability.toLowerCase()] || '未知';
};

const formatVerificationStatus = (status: string | null | undefined) => {
  if (!status) return '未验证';
  const statusMap: { [key: string]: string } = {
    not_verified: '未验证',
    pending: '审核中',
    verified: '已认证',
    failed: '认证失败',
  };
  return statusMap[status] || status;
};

const getVerificationStatusType = (status: string | null | undefined) => {
  if (!status) return 'info';
  const statusTypeMap: { [key: string]: '' | 'success' | 'warning' | 'danger' | 'info' } = {
    not_verified: 'info',
    pending: 'warning',
    verified: 'success',
    failed: 'danger',
  };
  return statusTypeMap[status] || 'info';
};

// 组件挂载时执行
onMounted(() => {
  if (authStore.isLoggedIn) {
    fetchFreelancerProfile().then(() => {
      if (profileExists.value) {
        fetchFreelancerSkills();
      } else {
        loadingSkills.value = false;
      }
    });
  } else {
    ElMessage.warning('请先登录。');
    router.push('/login');
    loadingProfile.value = false;
    loadingSkills.value = false;
  }
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1000px;
  margin: 20px auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.2em;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.loading-state,
.profile-details {
  padding: 20px;
}

.profile-section {
  margin-top: 20px;
  margin-bottom: 30px; /* Added margin for better separation */
}

.profile-section h4 {
  margin-bottom: 15px;
  font-size: 1.1em;
  color: #303133;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.bio-text {
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap; /* 保留换行和空格 */
  background-color: #f9f9f9; /* Slight background for bio */
  padding: 10px;
  border-radius: 4px;
}

.skill-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.work-preference-json {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  white-space: pre-wrap;
}

.status-verified { color: #67C23A; font-weight: bold; }
.status-pending { color: #E6A23C; font-weight: bold; }
.status-failed { color: #F56C6C; font-weight: bold; }
.status-not_verified, .status-null { color: #909399; }

.el-empty {
  padding: 20px 0; /* Reduced padding for empty states within sections */
}

.el-avatar {
  border: 1px solid #eee;
}

/* Ensure el-descriptions content is well-aligned and readable */
.el-descriptions {
    margin-top: 20px;
}
.el-descriptions-item__label {
    font-weight: bold;
}
</style>