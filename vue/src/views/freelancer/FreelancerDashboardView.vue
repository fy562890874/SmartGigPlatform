<!--
  @file FreelancerDashboardView.vue
  @description 零工用户的仪表盘页面，显示数据概览和快速操作
  @author Fy
  @date 2023-05-21
-->
<template>
  <div class="freelancer-dashboard page-container">
    <h1 class="page-title">零工工作台</h1>
    
    <!-- 数据概览卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ dashboardData.pending_applications || 0 }}</div>
            <div class="stats-label">待处理申请</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#409EFF"><Document /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ dashboardData.active_orders || 0 }}</div>
            <div class="stats-label">进行中订单</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#67C23A"><ShoppingCart /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ dashboardData.completed_orders || 0 }}</div>
            <div class="stats-label">已完成订单</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#E6A23C"><CircleCheck /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ formatCurrency(dashboardData.total_earnings || 0) }}</div>
            <div class="stats-label">总收入</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#F56C6C"><Money /></el-icon>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快速操作卡片 -->
    <el-row :gutter="20" class="action-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="action-card" @click="navigateTo('freelancer-profile')">
          <template #header>
            <div class="card-header">
              <span>完善个人资料</span>
              <el-icon><EditPen /></el-icon>
            </div>
          </template>
          <div class="card-content">
            <p v-if="profileComplete" class="status-complete">
              <el-icon><CircleCheck /></el-icon> 您的个人资料已完善
            </p>
            <p v-else class="status-incomplete">
              <el-icon><Warning /></el-icon> 完善您的个人资料以提高接单机会
            </p>
            <el-button type="primary" plain size="small">{{ profileComplete ? '查看资料' : '去完善' }}</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="action-card" @click="navigateTo('manage-skills')">
          <template #header>
            <div class="card-header">
              <span>管理技能</span>
              <el-icon><Star /></el-icon>
            </div>
          </template>
          <div class="card-content">
            <p>已添加技能: <span class="highlight">{{ dashboardData.skills_count || 0 }}</span> 项</p>
            <el-button type="primary" plain size="small">管理我的技能</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="action-card" @click="navigateTo('verification')">
          <template #header>
            <div class="card-header">
              <span>实名认证</span>
              <el-icon><Lock /></el-icon>
            </div>
          </template>
          <div class="card-content">
            <p v-if="isVerified" class="status-complete">
              <el-icon><CircleCheck /></el-icon> 已完成实名认证
            </p>
            <p v-else-if="verificationPending" class="status-pending">
              <el-icon><Loading /></el-icon> 认证审核中
            </p>
            <p v-else class="status-incomplete">
              <el-icon><Warning /></el-icon> 未完成实名认证
            </p>
            <el-button type="primary" plain size="small">
              {{ isVerified ? '查看认证' : verificationPending ? '查看审核进度' : '去认证' }}
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近工作申请 -->
    <el-card shadow="hover" class="table-card">
      <template #header>
        <div class="card-header">
          <span>最近申请的工作</span>
          <el-button type="primary" text @click="navigateTo('my-applications')">查看全部</el-button>
        </div>
      </template>
      <div v-if="loading.applications" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="recentApplications.length === 0" class="empty-container">
        <el-empty description="暂无工作申请记录" />
      </div>
      <el-table v-else :data="recentApplications" style="width: 100%">
        <el-table-column prop="job_info.title" label="工作标题">
          <template #default="scope">
            <el-link type="primary" @click="viewJobDetail(scope.row.job_info.id)">
              {{ scope.row.job_info.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ formatStatus(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="170">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 进行中的订单 -->
    <el-card shadow="hover" class="table-card">
      <template #header>
        <div class="card-header">
          <span>进行中的订单</span>
          <el-button type="primary" text @click="navigateTo('my-orders')">查看全部</el-button>
        </div>
      </template>
      <div v-if="loading.orders" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="activeOrders.length === 0" class="empty-container">
        <el-empty description="暂无进行中的订单" />
      </div>
      <el-table v-else :data="activeOrders" style="width: 100%">
        <el-table-column prop="job.title" label="工作标题">
          <template #default="scope">
            <el-link type="primary" @click="viewJobDetail(scope.row.job_id)">
              {{ scope.row.job.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="employer.nickname" label="雇主" width="120" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getOrderStatusType(scope.row.status)" size="small">
              {{ formatOrderStatus(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" @click="viewOrderDetail(scope.row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 推荐的工作 -->
    <el-card shadow="hover" class="table-card">
      <template #header>
        <div class="card-header">
          <span>为您推荐的工作</span>
          <el-button type="primary" text @click="navigateTo('jobs')">浏览更多</el-button>
        </div>
      </template>
      <div v-if="loading.recommendedJobs" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="recommendedJobs.length === 0" class="empty-container">
        <el-empty description="暂无推荐工作" />
      </div>
      <el-row v-else :gutter="20" class="job-cards">
        <el-col v-for="job in recommendedJobs" :key="job.id" :xs="24" :sm="12" :md="8">
          <el-card shadow="hover" class="job-card" @click="viewJobDetail(job.id)">
            <h3 class="job-title">{{ job.title }}</h3>
            <div class="job-tags">
              <el-tag v-if="job.is_urgent" type="danger" size="small" effect="plain">急聘</el-tag>
              <el-tag size="small" effect="plain">{{ job.job_category }}</el-tag>
            </div>
            <div class="job-info">
              <p><el-icon><Money /></el-icon> {{ formatPayInfo(job) }}</p>
              <p><el-icon><Location /></el-icon> {{ job.location_city || job.location_address }}</p>
            </div>
            <div class="job-footer">
              <span class="job-date">{{ formatTimeAgo(job.created_at) }}</span>
              <el-button size="small" type="primary" plain @click.stop="viewJobDetail(job.id)">查看详情</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';
import { 
  Document, ShoppingCart, CircleCheck, Money, EditPen, 
  Star, Lock, Warning, Loading, Location 
} from '@element-plus/icons-vue';

// 路由和状态管理
const router = useRouter();
const authStore = useAuthStore();

// 加载状态
const loading = reactive({
  dashboard: false,
  applications: false,
  orders: false,
  recommendedJobs: false
});

// 数据
const dashboardData = ref<any>({});
const recentApplications = ref<any[]>([]);
const activeOrders = ref<any[]>([]);
const recommendedJobs = ref<any[]>([]);

// 计算属性
const profileComplete = computed(() => {
  return dashboardData.value.profile_complete === true;
});

const isVerified = computed(() => {
  return dashboardData.value.verification_status === 'approved';
});

const verificationPending = computed(() => {
  return dashboardData.value.verification_status === 'pending';
});

// 获取仪表盘数据
const fetchDashboardData = async () => {
  loading.dashboard = true;
  try {
    const response = await apiClient.get('profiles/freelancer/dashboard');
    dashboardData.value = response.data;
  } catch (error) {
    console.error('获取仪表盘数据失败:', error);
  } finally {
    loading.dashboard = false;
  }
};

// 获取最近的申请
const fetchRecentApplications = async () => {
  loading.applications = true;
  try {
    const response = await apiClient.get('job-applications/my', {
      params: { page: 1, per_page: 5 }
    });
    recentApplications.value = response.data.items;
  } catch (error) {
    console.error('获取最近申请失败:', error);
  } finally {
    loading.applications = false;
  }
};

// 获取进行中的订单
const fetchActiveOrders = async () => {
  loading.orders = true;
  try {
    const response = await apiClient.get('orders', {
      params: { 
        page: 1, 
        per_page: 5,
        status: 'active',
        role: 'freelancer'
      }
    });
    activeOrders.value = response.data.items;
  } catch (error) {
    console.error('获取进行中订单失败:', error);
  } finally {
    loading.orders = false;
  }
};

// 获取推荐工作
const fetchRecommendedJobs = async () => {
  loading.recommendedJobs = true;
  try {
    const response = await apiClient.get('jobs/recommendations', {
      params: { count: 6 }
    });
    recommendedJobs.value = response.data.items;
  } catch (error) {
    console.error('获取推荐工作失败:', error);
  } finally {
    loading.recommendedJobs = false;
  }
};

// 导航到不同页面
const navigateTo = (route: string) => {
  switch (route) {
    case 'freelancer-profile':
      router.push('/freelancer/profile');
      break;
    case 'manage-skills':
      router.push('/freelancer/skills');
      break;
    case 'verification':
      router.push('/verifications/records');
      break;
    case 'my-applications':
      router.push('/freelancer/applications');
      break;
    case 'my-orders':
      router.push('/orders');
      break;
    case 'jobs':
      router.push('/jobs');
      break;
    default:
      router.push('/');
  }
};

// 查看工作详情
const viewJobDetail = (jobId: number) => {
  router.push(`/jobs/${jobId}`);
};

// 查看订单详情
const viewOrderDetail = (orderId: number) => {
  router.push(`/orders/${orderId}`);
};

// 格式化状态显示
const formatStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'pending': '待处理',
    'accepted': '已接受',
    'rejected': '已拒绝',
    'cancelled': '已取消'
  };
  return statusMap[status] || status;
};

// 获取状态类型
const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    'pending': 'warning',
    'accepted': 'success',
    'rejected': 'danger',
    'cancelled': 'info'
  };
  return typeMap[status] || 'info';
};

// 格式化订单状态
const formatOrderStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'created': '已创建',
    'in_progress': '进行中',
    'completed': '已完成',
    'confirmed': '已确认',
    'cancelled': '已取消',
    'disputed': '有争议'
  };
  return statusMap[status] || status;
};

// 获取订单状态类型
const getOrderStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    'created': 'info',
    'in_progress': 'warning',
    'completed': 'success',
    'confirmed': 'success',
    'cancelled': 'danger',
    'disputed': 'danger'
  };
  return typeMap[status] || 'info';
};

// 格式化日期
const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// 格式化相对时间
const formatTimeAgo = (dateString: string): string => {
  if (!dateString) return '';
  
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.round(diffMs / 1000);
  const diffMin = Math.round(diffSec / 60);
  const diffHour = Math.round(diffMin / 60);
  const diffDay = Math.round(diffHour / 24);
  
  if (diffSec < 60) return `${diffSec}秒前`;
  if (diffMin < 60) return `${diffMin}分钟前`;
  if (diffHour < 24) return `${diffHour}小时前`;
  if (diffDay < 30) return `${diffDay}天前`;
  
  return formatDate(dateString);
};

// 格式化薪资信息
const formatPayInfo = (job: any): string => {
  const amount = job.salary_amount || 0;
  const type = job.salary_type || 'fixed';
  
  let typeText = '';
  switch (type) {
    case 'hourly': typeText = '元/小时'; break;
    case 'daily': typeText = '元/天'; break;
    case 'weekly': typeText = '元/周'; break;
    case 'monthly': typeText = '元/月'; break;
    case 'negotiable': return '薪资面议';
    default: typeText = '元'; // fixed
  }
  
  return `${amount}${typeText}`;
};

// 格式化货币
const formatCurrency = (amount: number): string => {
  return `¥${amount.toFixed(2)}`;
};

// 初始化页面数据
onMounted(() => {
  if (authStore.isLoggedIn && authStore.user?.current_role === 'freelancer') {
    fetchDashboardData();
    fetchRecentApplications();
    fetchActiveOrders();
    fetchRecommendedJobs();
  }
});
</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 24px;
  color: #303133;
}

.stats-row, .action-row {
  margin-bottom: 24px;
}

.stats-card {
  height: 120px;
  display: flex;
  position: relative;
  overflow: hidden;
}

.stats-content {
  z-index: 1;
}

.stats-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stats-label {
  font-size: 14px;
  color: #909399;
}

.stats-icon {
  position: absolute;
  bottom: -10px;
  right: 10px;
  opacity: 0.1;
  transform: scale(1.5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-card {
  height: 150px;
  margin-bottom: 16px;
}

.card-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  height: 100%;
}

.status-complete {
  color: #67C23A;
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-incomplete {
  color: #F56C6C;
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-pending {
  color: #E6A23C;
  display: flex;
  align-items: center;
  gap: 5px;
}

.highlight {
  font-weight: bold;
  color: #409EFF;
}

.table-card {
  margin-bottom: 24px;
}

.loading-container, .empty-container {
  padding: 20px;
  display: flex;
  justify-content: center;
}

.job-cards {
  margin-top: 16px;
}

.job-card {
  cursor: pointer;
  height: 100%;
  transition: transform 0.2s;
}

.job-card:hover {
  transform: translateY(-5px);
}

.job-title {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.job-tags {
  margin-bottom: 10px;
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.job-info {
  margin-bottom: 10px;
}

.job-info p {
  margin: 5px 0;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  color: #606266;
}

.job-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.job-date {
  font-size: 12px;
  color: #909399;
}

@media (max-width: 768px) {
  .stats-row {
    margin-bottom: 0;
  }
  
  .stats-card, .action-card {
    margin-bottom: 16px;
  }
}
</style>