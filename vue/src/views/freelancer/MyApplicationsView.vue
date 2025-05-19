<!--
  @file MyApplicationsView.vue
  @description 零工查看和管理自己提交的工作申请
  @author Fy
  @date 2023-05-20
-->
<template>
  <div class="my-applications page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>我的工作申请</h1>
        </div>
      </template>
      
      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filterParams.status" placeholder="所有状态" clearable @change="fetchApplications">
            <el-option label="待处理" value="pending"></el-option>
            <el-option label="已接受" value="accepted"></el-option>
            <el-option label="已拒绝" value="rejected"></el-option>
            <el-option label="已取消" value="cancelled"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchApplications">筛选</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      
      <!-- 申请列表 -->
      <div v-else>
        <!-- 空状态 -->
        <el-empty
          v-if="applications.length === 0"
          description="暂无工作申请记录"
        >
          <el-button type="primary" @click="goToJobList">浏览工作</el-button>
        </el-empty>
        
        <!-- 申请卡片列表 -->
        <div v-else class="application-list">
          <el-card
            v-for="app in applications"
            :key="app.id"
            class="application-card"
            shadow="hover"
          >
            <div class="application-header">
              <div class="job-info">
                <h3 @click="viewJobDetail(app.job_info.id)" class="job-title">
                  {{ app.job_info.title }}
                </h3>
                <el-tag
                  :type="getStatusType(app.status)"
                  effect="light"
                  size="small"
                >
                  {{ formatStatus(app.status) }}
                </el-tag>
              </div>
              <span class="application-date">申请时间: {{ formatDate(app.created_at) }}</span>
            </div>
            
            <div class="application-content">
              <p v-if="app.application_message" class="message">
                申请留言: {{ app.application_message }}
              </p>
              <p v-if="app.rejection_reason && app.status === 'rejected'" class="reason">
                拒绝原因: {{ app.rejection_reason }}
              </p>
              <p v-if="app.status === 'accepted'" class="success-message">
                雇主已接受您的申请！请查看订单详情。
              </p>
            </div>
            
            <div class="application-actions">
              <el-button
                size="small"
                @click="viewApplicationDetail(app.id)"
              >
                查看详情
              </el-button>
              <el-button
                v-if="app.status === 'pending'"
                type="danger"
                size="small"
                plain
                @click="confirmCancelApplication(app)"
              >
                取消申请
              </el-button>
            </div>
          </el-card>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-container" v-if="totalItems > 0">
          <el-pagination
            background
            layout="prev, pager, next, jumper, total"
            :total="totalItems"
            :page-size="filterParams.per_page"
            :current-page="filterParams.page"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </el-card>
    
    <!-- 取消申请确认对话框 -->
    <el-dialog
      v-model="cancelDialogVisible"
      title="取消申请"
      width="30%"
    >
      <p>确定要取消此工作申请吗？</p>
      <el-form>
        <el-form-item label="取消原因">
          <el-input
            v-model="cancelReason"
            type="textarea"
            :rows="3"
            placeholder="可选填写取消原因"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCancelApplication" :loading="cancelLoading">
            确定取消申请
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import apiClient from '@/utils/apiClient';

// 路由
const router = useRouter();

// 状态变量
const loading = ref(false);
const applications = ref<any[]>([]);
const totalItems = ref(0);
const totalPages = ref(1);
const cancelDialogVisible = ref(false);
const cancelReason = ref('');
const cancelLoading = ref(false);
const currentApplication = ref<any>(null);

// 筛选参数
const filterParams = reactive({
  status: '', // 默认不筛选状态
  page: 1,
  per_page: 10
});

// 获取工作申请列表
const fetchApplications = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get('job-applications/my', {
      params: filterParams
    });
    
    applications.value = response.data.items;
    totalItems.value = response.data.pagination.total_items;
    totalPages.value = response.data.pagination.total_pages;
  } catch (error) {
    console.error('获取工作申请列表失败:', error);
    // 错误已由apiClient处理
  } finally {
    loading.value = false;
  }
};

// 查看工作详情
const viewJobDetail = (jobId: number) => {
  router.push(`/jobs/${jobId}`);
};

// 查看申请详情
const viewApplicationDetail = (applicationId: number) => {
  router.push(`/freelancer/applications/${applicationId}`);
};

// 前往工作列表
const goToJobList = () => {
  router.push('/jobs');
};

// 确认取消申请
const confirmCancelApplication = (application: any) => {
  currentApplication.value = application;
  cancelReason.value = '';
  cancelDialogVisible.value = true;
};

// 提交取消申请
const submitCancelApplication = async () => {
  if (!currentApplication.value) return;
  
  cancelLoading.value = true;
  try {
    await apiClient.post(`job-applications/${currentApplication.value.id}/cancel`, {
      reason: cancelReason.value
    });
    
    ElMessage.success('申请已成功取消');
    cancelDialogVisible.value = false;
    
    // 更新申请列表
    fetchApplications();
  } catch (error) {
    console.error('取消申请失败:', error);
    // 错误已由apiClient处理
  } finally {
    cancelLoading.value = false;
  }
};

// 页码变化处理
const handlePageChange = (page: number) => {
  filterParams.page = page;
  fetchApplications();
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

// 获取状态对应的类型
const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    'pending': 'warning',
    'accepted': 'success',
    'rejected': 'danger',
    'cancelled': 'info'
  };
  return typeMap[status] || 'info';
};

// 格式化日期
const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// 页面加载时获取数据
onMounted(() => {
  fetchApplications();
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

.filter-form {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9fa;
  border-radius: 4px;
}

.loading-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.application-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.application-card {
  margin-bottom: 0;
}

.application-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.job-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.job-title {
  margin: 0;
  cursor: pointer;
  color: #409EFF;
}

.job-title:hover {
  text-decoration: underline;
}

.application-date {
  font-size: 0.85em;
  color: #909399;
}

.application-content {
  padding: 10px 0;
  color: #606266;
}

.message, .reason {
  margin: 5px 0;
  white-space: pre-wrap;
}

.reason {
  color: #F56C6C;
}

.success-message {
  color: #67C23A;
  font-weight: bold;
}

.application-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
