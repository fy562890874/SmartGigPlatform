<template>
  <div class="employer-dashboard page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>我的雇主仪表盘</span>
          <div class="action-buttons">
            <el-button type="primary" :icon="EditPen" @click="goToEditProfile">编辑档案</el-button>
            <el-button type="info" @click="router.push('/my-orders')">我的订单</el-button>
          </div>
        </div>
      </template>

      <div v-if="loadingProfile" class="loading-state">
        <el-skeleton :rows="12" animated />
      </div>
      <el-empty description="暂未创建雇主档案，请先创建。" v-else-if="!profileExistsAndLoaded">
        <el-button type="success" @click="goToEditProfile">创建我的雇主档案</el-button>
      </el-empty>
      <div v-else-if="employerProfile" class="profile-details">
        <el-descriptions :title="`档案类型: ${profileTypeDisplay(employerProfile.profile_type)}`" :column="2" border>
          <el-descriptions-item label="用户ID">{{ employerProfile.user_id }}</el-descriptions-item>
          <el-descriptions-item label="昵称/简称">{{ employerProfile.nickname || authStore.user?.nickname || '未填写' }}</el-descriptions-item>
          
          <el-descriptions-item label="真实姓名">{{ employerProfile.real_name || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ employerProfile.contact_phone || '未填写' }}</el-descriptions-item>
          
          <el-descriptions-item label="所在地" :span="2">
            {{ locationDisplay(employerProfile) }}
          </el-descriptions-item>

          <el-descriptions-item label="头像/Logo">
            <el-avatar v-if="employerProfile.avatar_url" :src="employerProfile.avatar_url" :size="60" shape="square" />
            <span v-else>未设置</span>
          </el-descriptions-item>
          <el-descriptions-item label="认证状态">
            <el-tag :type="verificationStatusType(employerProfile.verification_status)">
              {{ verificationStatusDisplay(employerProfile.verification_status) }}
            </el-tag>
             <el-button 
                v-if="employerProfile.verification_status !== 'verified' && employerProfile.verification_status !== 'pending'"
                type="warning" 
                size="small"
                style="margin-left: 10px;"
                @click="goToVerificationPage"
            >
                {{ employerProfile.verification_status === 'failed' ? '重新提交认证' : '去认证' }}
            </el-button>
          </el-descriptions-item>

          <el-descriptions-item label="信用分">{{ employerProfile.credit_score ?? 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="平均评分">{{ employerProfile.average_rating ?? 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="累计发布工作数">{{ employerProfile.total_jobs_posted ?? 0 }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="employerProfile.profile_type === 'company'">
          <el-divider />
          <el-descriptions title="公司信息" :column="1" border>
            <el-descriptions-item label="公司名称">{{ employerProfile.company_name || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="统一社会信用代码">{{ employerProfile.business_license_number || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="公司地址">{{ employerProfile.company_address || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="公司简介">{{ employerProfile.company_description || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="营业执照照片">
              <el-image 
                v-if="employerProfile.business_license_photo_url"
                style="width: 100px; height: 100px"
                :src="employerProfile.business_license_photo_url" 
                :preview-src-list="[employerProfile.business_license_photo_url]"
                fit="cover"
              />
              <span v-else>未上传</span>
            </el-descriptions-item>
          </el-descriptions>
        </template>

      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { EditPen } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';

// 路由和状态管理
const router = useRouter();
const authStore = useAuthStore();

// 页面状态
const loadingProfile = ref(true);
const employerProfile = ref<any>(null);
const profileExistsAndLoaded = computed(() => employerProfile.value !== null);

// 获取雇主档案数据
const fetchEmployerProfile = async () => {
  loadingProfile.value = true;

  try {
    // 获取认证token
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      return;
    }

    // 直接使用axios请求API
    const response = await axios.get(apiConfig.getApiUrl('profiles/employer/me'), {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    // 处理API响应
    if (response.data && response.data.code === 0) {
      employerProfile.value = response.data.data;
    } else {
      console.error('获取雇主档案失败:', response.data);
      employerProfile.value = null;
    }
  } catch (error: any) {
    console.error('获取雇主档案失败:', error);
    
    // 处理404错误（未创建档案）
    if (error.response && error.response.status === 404) {
      employerProfile.value = null;
    } else {
      ElMessage.error(error.response?.data?.message || '获取雇主档案失败，请稍后重试');
    }
  } finally {
    loadingProfile.value = false;
  }
};

// 页面跳转函数
const goToEditProfile = () => {
  router.push('/employer/edit-profile');
};

const goToVerificationPage = () => {
  router.push('/verifications/submit');
};

// 格式化显示函数
const profileTypeDisplay = (type: string) => {
  const types: Record<string, string> = {
    'individual': '个人雇主',
    'company': '企业雇主'
  };
  return types[type] || type;
};

const verificationStatusDisplay = (status: string | null | undefined) => {
  if (!status) return '未认证';
  
  const statusMap: Record<string, string> = {
    'not_verified': '未认证',
    'pending': '审核中',
    'verified': '已认证',
    'failed': '认证失败'
  };
  
  return statusMap[status] || status;
};

const verificationStatusType = (status: string | null | undefined) => {
  if (!status) return 'info';
  
  const typeMap: Record<string, 'info' | 'success' | 'warning' | 'danger'> = {
    'not_verified': 'info',
    'pending': 'warning',
    'verified': 'success',
    'failed': 'danger'
  };
  
  return typeMap[status] || 'info';
};

const locationDisplay = (profile: any) => {
  const parts = [];
  
  if (profile.location_province) parts.push(profile.location_province);
  if (profile.location_city) parts.push(profile.location_city);
  if (profile.location_district) parts.push(profile.location_district);
  
  return parts.length > 0 ? parts.join(' ') : '未填写';
};

// 组件挂载时执行
onMounted(() => {
  // 检查用户是否登录
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  // 获取雇主档案数据
  fetchEmployerProfile();
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

.el-descriptions {
    margin-top: 20px;
}

.el-avatar,
.el-image {
    border: 1px solid #eee;
    border-radius: 4px;
}

.el-empty {
    padding: 40px 0;
}
</style>