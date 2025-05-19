<!--
  @file EmployerDashboardView.vue
  @description 雇主仪表盘，显示数据概览和快速操作
  @author Fy
  @date 2023-05-23
-->
<template>
  <div class="employer-dashboard page-container">
    <h1 class="page-title">雇主工作台</h1>
    
    <!-- 数据概览卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ dashboardData.total_posted_jobs || 0 }}</div>
            <div class="stats-label">已发布工作</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#409EFF"><Briefcase /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ dashboardData.active_jobs || 0 }}</div>
            <div class="stats-label">进行中工作</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#67C23A"><Clock /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ dashboardData.pending_applications || 0 }}</div>
            <div class="stats-label">待处理申请</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#E6A23C"><DocumentChecked /></el-icon>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content">
            <div class="stats-value">{{ dashboardData.active_orders || 0 }}</div>
            <div class="stats-label">进行中订单</div>
          </div>
          <el-icon class="stats-icon" :size="40" color="#F56C6C"><ShoppingCart /></el-icon>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快速操作区 -->
    <el-row :gutter="20" class="action-row">
      <el-col :md="24">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <h2>快速操作</h2>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="navigateTo('/employer/jobs/post')">
              <el-icon><Plus /></el-icon>发布新工作
            </el-button>
            <el-button type="info" @click="navigateTo('/employer/jobs')">
              <el-icon><Document /></el-icon>管理工作
            </el-button>
            <el-button type="success" @click="navigateTo('/employer/orders')">
              <el-icon><List /></el-icon>查看订单
            </el-button>
            <el-button type="warning" @click="navigateTo('/employer/profile/edit')">
              <el-icon><Setting /></el-icon>编辑档案
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近申请 -->
    <el-row :gutter="20" class="recent-row">
      <el-col :md="12">
        <el-card shadow="never" class="recent-card">
          <template #header>
            <div class="card-header">
              <h2>最新工作申请</h2>
              <el-button text @click="navigateTo('/employer/jobs')">查看全部</el-button>
            </div>
          </template>
          
          <div v-if="loading.recentApplications" class="loading-placeholder">
            <el-skeleton :rows="5" animated />
          </div>
          
          <el-empty 
            v-else-if="recentApplications.length === 0" 
            description="暂无最新申请"
            :image-size="80"
          />
          
          <div v-else class="recent-applications">
            <el-table :data="recentApplications" style="width: 100%">
              <el-table-column label="申请者" min-width="160">
                <template #default="{ row }">
                  <div class="applicant-info">
                    <el-avatar :size="32" :src="row.freelancer.avatar_url">
                      {{ row.freelancer.nickname ? row.freelancer.nickname.substring(0, 1).toUpperCase() : 'U' }}
                    </el-avatar>
                    <span>{{ row.freelancer.nickname || `用户 #${row.freelancer_user_id}` }}</span>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column label="工作" min-width="180" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ row.job.title }}
                </template>
              </el-table-column>
              
              <el-table-column label="申请时间" min-width="100">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              
              <el-table-column label="状态" min-width="90">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="操作" min-width="120" fixed="right">
                <template #default="{ row }">
                  <el-button 
                    size="small" 
                    @click="navigateTo(`/employer/jobs/${row.job_id}/applicants`)"
                  >
                    查看
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      
      <el-col :md="12">
        <el-card shadow="never" class="recent-card">
          <template #header>
            <div class="card-header">
              <h2>近期工作</h2>
              <el-button text @click="navigateTo('/employer/jobs')">查看全部</el-button>
            </div>
          </template>
          
          <div v-if="loading.recentJobs" class="loading-placeholder">
            <el-skeleton :rows="5" animated />
          </div>
          
          <el-empty 
            v-else-if="recentJobs.length === 0" 
            description="暂无工作"
            :image-size="80"
          />
          
          <div v-else class="recent-jobs">
            <el-table :data="recentJobs" style="width: 100%">
              <el-table-column label="工作标题" min-width="180" show-overflow-tooltip>
                <template #default="{ row }">
                  <router-link :to="`/jobs/${row.id}`" class="job-title-link">
                    {{ row.title }}
                  </router-link>
                </template>
              </el-table-column>
              
              <el-table-column label="薪资" min-width="120">
                <template #default="{ row }">
                  {{ row.salary_amount }}元/{{ getSalaryTypeText(row.salary_type) }}
                </template>
              </el-table-column>
              
              <el-table-column label="状态" min-width="90">
                <template #default="{ row }">
                  <el-tag :type="getJobStatusType(row.status)">{{ getJobStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="申请人数" min-width="90" align="center">
                <template #default="{ row }">
                  <router-link 
                    v-if="row.application_count > 0"
                    :to="`/employer/jobs/${row.id}/applicants`" 
                    class="applicant-link"
                  >
                    {{ row.application_count }}
                  </router-link>
                  <span v-else>0</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Briefcase, Clock, DocumentChecked, ShoppingCart, Plus, Document, List, Setting } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';
import { getPaginatedData } from '@/utils/http';
import dayjs from 'dayjs';

// 定义类型接口
interface JobItem {
  id: number;
  title: string;
  status: string;
  created_at: string;
  salary_amount: number;
  salary_type: string;
  application_count: number;
  [key: string]: any;
}

interface ApplicationItem {
  job_id: number;
  freelancer_user_id: number;
  status: string;
  created_at: string;
  job: {
    title: string;
    [key: string]: any;
  };
  freelancer: {
    nickname?: string;
    avatar_url?: string;
    [key: string]: any;
  };
  [key: string]: any;
}

// 路由与状态管理
const router = useRouter();
const authStore = useAuthStore();

// 加载状态
const loading = reactive({
  dashboard: false,
  recentJobs: false,
  recentApplications: false
});

// 仪表盘数据
const dashboardData = reactive({
  total_posted_jobs: 0,
  active_jobs: 0,
  pending_applications: 0,
  active_orders: 0
});

// 最近申请和工作
const recentApplications = ref<ApplicationItem[]>([]);
const recentJobs = ref<JobItem[]>([]);

// 获取仪表盘数据
const fetchDashboardData = async () => {
  loading.dashboard = true;
  try {
    const dashboardResponse = await apiClient.get('employer/dashboard');
    
    // 更新仪表盘数据
    if (dashboardResponse && typeof dashboardResponse === 'object') {
      Object.assign(dashboardData, dashboardResponse);
    }
  } catch (error) {
    console.error('获取仪表盘数据失败:', error);
  } finally {
    loading.dashboard = false;
  }
};

// 获取最新申请
const fetchRecentApplications = async () => {
  loading.recentApplications = true;
  try {
    const params = { limit: 5 }; // 只获取最新的5条
    const response = await apiClient.get('employer/recent-applications', { params });
    
    const { items = [] } = getPaginatedData(response);
    recentApplications.value = items as ApplicationItem[];
  } catch (error) {
    console.error('获取最新申请失败:', error);
    recentApplications.value = [];
  } finally {
    loading.recentApplications = false;
  }
};

// 获取最近工作
const fetchRecentJobs = async () => {
  loading.recentJobs = true;
  try {
    const params = {
      page: 1,
      per_page: 5,
      sort_by: 'created_at_desc'
    };
    
    const response = await apiClient.get('jobs/my-posted', { params });
    console.log('Dashboard最近工作响应:', response);
    
    const { items = [] } = getPaginatedData(response);
    recentJobs.value = items as JobItem[];
  } catch (error) {
    console.error('获取最近工作失败:', error);
    recentJobs.value = [];
  } finally {
    loading.recentJobs = false;
  }
};

// 导航到指定路径
const navigateTo = (path: string) => {
  router.push(path);
};

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 获取申请状态显示文本 
const getStatusText = (status: string) => {
  const statusMap: {[key: string]: string} = {
    pending: '待处理',
    accepted: '已接受',
    rejected: '已拒绝',
    cancelled: '已取消'
  };
  return statusMap[status] || status;
};

// 获取申请状态标签类型
const getStatusType = (status: string) => {
  const typeMap: {[key: string]: string} = {
    pending: 'warning',
    accepted: 'success',
    rejected: 'danger',
    cancelled: 'info'
  };
  return typeMap[status] || 'info';
};

// 获取工作状态显示文本
const getJobStatusText = (status: string) => {
  const statusMap: {[key: string]: string} = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    active: '进行中',
    cancelled: '已取消',
    completed: '已完成',
    expired: '已过期'
  };
  return statusMap[status] || status;
};

// 获取工作状态标签类型
const getJobStatusType = (status: string) => {
  const typeMap: {[key: string]: string} = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    active: 'success',
    cancelled: 'info',
    completed: 'success',
    expired: 'info'
  };
  return typeMap[status] || 'info';
};

// 获取薪资类型文本
const getSalaryTypeText = (type: string) => {
  const typeMap: {[key: string]: string} = {
    fixed: '固定',
    hourly: '小时',
    daily: '天',
    weekly: '周',
    monthly: '月'
  };
  return typeMap[type] || type;
};
</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 15px;
}

.page-title {
  font-size: 1.8em;
  margin-bottom: 20px;
  font-weight: bold;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  position: relative;
  height: 120px;
  overflow: hidden;
  margin-bottom: 20px;
}

.stats-content {
  position: relative;
  z-index: 1;
}

.stats-value {
  font-size: 2em;
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
}

.stats-label {
  font-size: 1em;
  color: #606266;
}

.stats-icon {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.2;
}

.action-row {
  margin-bottom: 20px;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.recent-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  font-size: 1.2em;
  margin: 0;
  font-weight: bold;
}

.loading-placeholder {
  padding: 10px 0;
}

.recent-card {
  height: 420px;
  margin-bottom: 20px;
}

.applicant-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.job-title-link,
.applicant-link {
  color: #409EFF;
  text-decoration: none;
}

.job-title-link:hover,
.applicant-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .quick-actions {
    flex-direction: column;
  }
  
  .quick-actions .el-button {
    width: 100%;
  }
  
  .recent-card {
    height: auto;
  }
}
</style>