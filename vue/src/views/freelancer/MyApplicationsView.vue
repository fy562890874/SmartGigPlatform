<template>
  <div class="my-applications page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>我的工作申请</span>
          <div class="header-actions">
            <el-select v-model="statusFilter" placeholder="筛选状态" clearable @change="filterApplications">
              <el-option label="待处理" value="pending" />
              <el-option label="已接受" value="accepted" />
              <el-option label="已拒绝" value="rejected" />
              <el-option label="已取消" value="canceled" />
            </el-select>
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="applications.length === 0" class="empty-container">
        <el-empty description="暂无申请记录" />
      </div>
      
      <div v-else class="applications-list">
        <el-table 
          :data="applications" 
          style="width: 100%"
          :default-sort="{ prop: 'created_at', order: 'descending' }"
          row-key="id"
          @row-click="viewApplicationDetails"
        >
          <el-table-column prop="job_info.title" label="工作标题" min-width="180">
            <template #default="scope">
              <el-link type="primary" @click.stop="goToJobDetail(scope.row.job_id)">
                {{ scope.row.job_info?.title || '未知工作' }}
              </el-link>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="120">
            <template #default="scope">
              <el-tag 
                :type="getApplicationStatusType(scope.row.status)" 
                size="small"
                effect="light"
              >
                {{ formatApplicationStatus(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="申请时间" width="160" sortable>
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="130" fixed="right">
            <template #default="scope">
              <el-button 
                v-if="scope.row.status === 'pending'" 
                type="danger" 
                size="small" 
                @click.stop="openCancelDialog(scope.row)"
              >
                取消申请
              </el-button>
              <el-button 
                v-else
                type="primary" 
                size="small" 
                @click.stop="viewApplicationDetails(scope.row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:currentPage="currentPage"
            :page-size="pageSize"
            :total="totalItems"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 查看详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="申请详情"
      width="500px"
    >
      <div v-if="selectedApplication" class="application-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="工作名称">
            <el-link type="primary" @click="goToJobDetail(selectedApplication.job_id)">
              {{ selectedApplication.job_info?.title || '未知工作' }}
            </el-link>
          </el-descriptions-item>
          <el-descriptions-item label="申请状态">
            <el-tag :type="getApplicationStatusType(selectedApplication.status)" effect="light">
              {{ formatApplicationStatus(selectedApplication.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="申请时间">
            {{ formatDate(selectedApplication.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="处理时间" v-if="selectedApplication.processed_at">
            {{ formatDate(selectedApplication.processed_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="申请留言" v-if="selectedApplication.application_message">
            {{ selectedApplication.application_message }}
          </el-descriptions-item>
          <el-descriptions-item label="拒绝原因" v-if="selectedApplication.status === 'rejected' && selectedApplication.rejection_reason">
            {{ selectedApplication.rejection_reason }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button 
            v-if="selectedApplication.status === 'pending'" 
            type="danger" 
            @click="confirmCancel"
          >
            取消申请
          </el-button>
          <el-button 
            v-if="selectedApplication.status === 'rejected'" 
            type="primary" 
            @click="reapplyToJob(selectedApplication.job_id)"
          >
            重新申请
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 取消申请对话框 -->
    <el-dialog
      v-model="cancelDialogVisible"
      title="取消申请"
      width="400px"
    >
      <el-form :model="cancelForm" label-position="top">
        <el-form-item label="取消原因（可选）">
          <el-input 
            v-model="cancelForm.reason" 
            type="textarea" 
            rows="3"
            placeholder="请输入取消原因（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="confirmCancel">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';
import dayjs from 'dayjs';

const router = useRouter();
const authStore = useAuthStore();

// 状态数据
const applications = ref<any[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const statusFilter = ref('');

// 详情对话框状态
const detailDialogVisible = ref(false);
const selectedApplication = ref<any>(null);

// 取消申请对话框状态
const cancelDialogVisible = ref(false);
const cancelForm = reactive({
  reason: ''
});
const submitting = ref(false);

// 获取申请列表
const fetchApplications = async () => {
  loading.value = true;
  try {
    // 获取token
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您需要先登录');
      router.push('/auth/login');
      return;
    }
    
    // 构造API请求参数
    const params: Record<string, any> = {
      page: currentPage.value,
      per_page: pageSize.value
    };
    
    if (statusFilter.value) {
      params.status = statusFilter.value;
    }
    
    // 发起请求
    const response = await axios.get(apiConfig.getApiUrl('/job-applications/my'), {
      headers: {
        Authorization: `Bearer ${token}`
      },
      params
    });
    
    // 处理响应
    if (response.data && response.data.code === 0) {
      applications.value = response.data.data.items;
      totalItems.value = response.data.data.pagination.total_items;
    } else {
      ElMessage.error(response.data?.message || '获取申请列表失败');
    }
  } catch (error: any) {
    console.error('获取申请列表错误:', error);
    ElMessage.error(error.response?.data?.message || '获取申请列表时发生错误');
  } finally {
    loading.value = false;
  }
};

// 查看申请详情
const viewApplicationDetails = (row: any) => {
  selectedApplication.value = row;
  detailDialogVisible.value = true;
};

// 跳转到工作详情页
const goToJobDetail = (jobId: number) => {
  router.push(`/jobs/${jobId}`);
};

// 状态筛选
const filterApplications = () => {
  currentPage.value = 1; // 重置到第一页
  fetchApplications();
};

// 页码变更
const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchApplications();
};

// 打开取消申请对话框
const openCancelDialog = (application: any) => {
  selectedApplication.value = application;
  cancelForm.reason = '';
  cancelDialogVisible.value = true;
};

// 确认取消申请
const confirmCancel = async () => {
  if (!selectedApplication.value) return;
  
  submitting.value = true;
  try {
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您需要先登录');
      return;
    }
    
    const response = await axios.post(
      apiConfig.getApiUrl(`/job-applications/${selectedApplication.value.id}/cancel`),
      { reason: cancelForm.reason },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.data && response.data.code === 0) {
      ElMessage.success('已成功取消申请');
      cancelDialogVisible.value = false;
      detailDialogVisible.value = false;
      fetchApplications(); // 重新加载申请列表
    } else {
      ElMessage.error(response.data?.message || '取消申请失败');
    }
  } catch (error: any) {
    console.error('取消申请错误:', error);
    ElMessage.error(error.response?.data?.message || '取消申请时发生错误');
  } finally {
    submitting.value = false;
  }
};

// 重新申请工作
const reapplyToJob = (jobId: number) => {
  detailDialogVisible.value = false;
  router.push(`/jobs/${jobId}`);
};

// 格式化申请状态
const formatApplicationStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'pending': '待处理',
    'accepted': '已接受',
    'rejected': '已拒绝',
    'canceled': '已取消'
  };
  return statusMap[status] || status;
};

// 获取状态对应的样式类型
const getApplicationStatusType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    'pending': '',
    'accepted': 'success',
    'rejected': 'danger',
    'canceled': 'info'
  };
  return typeMap[status] || 'info';
};

// 格式化日期
const formatDate = (dateString: string): string => {
  if (!dateString) return '未设置';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 组件挂载时加载数据
onMounted(() => {
  if (authStore.isLoggedIn) {
    fetchApplications();
  } else {
    ElMessage.warning('请先登录');
    router.push('/auth/login');
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions .el-select {
  width: 150px;
}

.loading-container,
.empty-container {
  padding: 40px 0;
  text-align: center;
}

.applications-list {
  margin-top: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.application-detail {
  padding: 10px;
}

.dialog-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
