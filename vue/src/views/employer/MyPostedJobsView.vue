<!--
  @file MyPostedJobsView.vue
  @description 雇主查看和管理已发布的工作
  @author Fy
  @date 2023-05-22
-->
<template>
  <div class="my-posted-jobs page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>我发布的工作</h1>
          <el-button type="primary" @click="goToPostJob">发布新工作</el-button>
        </div>
      </template>
      
      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filterParams.status" placeholder="所有状态" clearable @change="fetchJobs">
            <el-option label="待审核" value="pending" />
            <el-option label="审核通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="进行中" value="active" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="搜索">
          <el-input
            v-model="filterParams.keyword"
            placeholder="输入标题搜索"
            clearable
            @keyup.enter="fetchJobs"
          >
            <template #append>
              <el-button @click="fetchJobs">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>
      
      <!-- 空状态 -->
      <el-empty
        v-else-if="jobs.length === 0"
        description="您还没有发布任何工作"
      >
        <el-button type="primary" @click="goToPostJob">立即发布</el-button>
      </el-empty>
      
      <!-- 工作列表 -->
      <div v-else class="job-list">
        <el-table :data="jobs" style="width: 100%" border>
          <el-table-column prop="title" label="工作标题" min-width="200">
            <template #default="{ row }">
              <router-link :to="`/jobs/${row.id}`" class="job-title-link">{{ row.title }}</router-link>
              <el-tag v-if="row.is_urgent" type="danger" size="small" class="urgent-tag">紧急</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="job_category" label="类别" min-width="100" />
          
          <el-table-column label="薪资" min-width="130">
            <template #default="{ row }">
              {{ row.salary_amount }}元/{{ getSalaryTypeText(row.salary_type) }}
              <span v-if="row.salary_negotiable">(可协商)</span>
            </template>
          </el-table-column>
          
          <el-table-column label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
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
          
          <el-table-column label="发布时间" min-width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" min-width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                size="small" 
                @click="viewJobDetails(row.id)"
              >
                查看
              </el-button>
              
              <el-button 
                v-if="canEditJob(row)" 
                size="small" 
                type="primary" 
                @click="editJob(row.id)"
              >
                编辑
              </el-button>
              
              <el-button 
                v-if="row.status === 'pending' || row.status === 'draft'" 
                size="small" 
                type="danger" 
                @click="cancelJob(row.id)"
              >
                取消
              </el-button>
              
              <el-button 
                v-if="row.status === 'active'" 
                size="small" 
                type="warning" 
                @click="completeJob(row.id)"
              >
                完成
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:currentPage="pagination.page"
            v-model:page-size="pagination.per_page"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="pagination.total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
    
    <!-- 确认对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="30%"
    >
      <span>{{ dialogMessage }}</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAction" :loading="actionLoading">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';
import dayjs from 'dayjs';

// 路由与状态管理
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// 工作列表数据
const jobs = ref([]);
const loading = ref(false);
const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
});

// 筛选参数
const filterParams = reactive({
  status: '',
  keyword: '',
});

// 对话框控制
const dialogVisible = ref(false);
const dialogTitle = ref('');
const dialogMessage = ref('');
const actionLoading = ref(false);
const currentJobId = ref(null);
const currentAction = ref('');

// 获取雇主发布的工作
const fetchJobs = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filterParams
    };
    
    const response = await apiClient.get('jobs/my-posted', { params });
    
    // apiClient已处理成功响应
    jobs.value = response.data.items;
    pagination.total = response.data.pagination.total_items;
  } catch (error) {
    console.error('获取发布的工作失败:', error);
    // apiClient已处理错误消息
  } finally {
    loading.value = false;
  }
};

// 查看工作详情
const viewJobDetails = (jobId) => {
  router.push(`/jobs/${jobId}`);
};

// 编辑工作
const editJob = (jobId) => {
  router.push(`/employer/jobs/${jobId}/edit`);
};

// 取消工作
const cancelJob = (jobId) => {
  currentJobId.value = jobId;
  currentAction.value = 'cancel';
  dialogTitle.value = '取消工作';
  dialogMessage.value = '确认要取消这个工作吗？取消后将无法恢复，且已申请的人员将收到通知。';
  dialogVisible.value = true;
};

// 完成工作
const completeJob = (jobId) => {
  currentJobId.value = jobId;
  currentAction.value = 'complete';
  dialogTitle.value = '完成工作';
  dialogMessage.value = '确认将此工作标记为已完成吗？';
  dialogVisible.value = true;
};

// 确认操作
const confirmAction = async () => {
  if (!currentJobId.value) return;
  
  actionLoading.value = true;
  try {
    let endpoint = '';
    let successMessage = '';
    
    if (currentAction.value === 'cancel') {
      endpoint = `jobs/${currentJobId.value}/cancel`;
      successMessage = '工作已成功取消';
    } else if (currentAction.value === 'complete') {
      endpoint = `jobs/${currentJobId.value}/complete`;
      successMessage = '工作已标记为完成';
    }
    
    if (endpoint) {
      await apiClient.post(endpoint);
      ElMessage.success(successMessage);
      fetchJobs(); // 刷新列表
    }
  } catch (error) {
    console.error('操作失败:', error);
  } finally {
    actionLoading.value = false;
    dialogVisible.value = false;
  }
};

// 判断工作是否可编辑
const canEditJob = (job) => {
  return ['draft', 'pending', 'rejected'].includes(job.status);
};

// 分页处理
const handleSizeChange = (val) => {
  pagination.per_page = val;
  fetchJobs();
};

const handleCurrentChange = (val) => {
  pagination.page = val;
  fetchJobs();
};

// 跳转到发布工作页面
const goToPostJob = () => {
  router.push('/employer/jobs/post');
};

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 获取状态显示文本
const getStatusText = (status) => {
  const statusMap = {
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

// 获取状态标签类型
const getStatusType = (status) => {
  const typeMap = {
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
const getSalaryTypeText = (type) => {
  const typeMap = {
    fixed: '固定',
    hourly: '小时',
    daily: '天',
    weekly: '周',
    monthly: '月'
  };
  return typeMap[type] || type;
};

// 监听路由参数变化
watch(() => route.query.refresh, (val) => {
  if (val === 'true') {
    fetchJobs();
    // 清除URL参数
    router.replace({ query: {} });
  }
});

// 组件挂载
onMounted(() => {
  // 检查用户角色是否为雇主
  if (!authStore.isLoggedIn || authStore.user?.current_role !== 'employer') {
    ElMessage.warning('请先以雇主身份登录');
    router.push('/login');
    return;
  }
  
  // 获取发布的工作
  fetchJobs();
});
</script>

<style scoped>
.page-container {
  max-width: 1200px;
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

.filter-form {
  margin-bottom: 20px;
}

.job-list {
  margin-top: 20px;
}

.job-title-link {
  color: #409EFF;
  text-decoration: none;
  font-weight: 500;
}

.job-title-link:hover {
  text-decoration: underline;
}

.urgent-tag {
  margin-left: 8px;
}

.applicant-link {
  color: #409EFF;
  text-decoration: none;
}

.applicant-link:hover {
  text-decoration: underline;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
