<template>
  <div class="my-posted-jobs page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>我发布的工作</span>
          <div class="header-actions">
            <el-button type="primary" @click="goToPostJob">发布新工作</el-button>
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="jobs.length === 0" class="empty-container">
        <el-empty description="您还没有发布任何工作">
          <el-button type="primary" @click="goToPostJob">立即发布</el-button>
        </el-empty>
      </div>
      
      <div v-else class="jobs-list">
        <el-table
          :data="jobs"
          style="width: 100%"
          :default-sort="{ prop: 'created_at', order: 'descending' }"
          @row-click="goToJobDetail"
        >
          <el-table-column prop="title" label="工作标题" min-width="200" show-overflow-tooltip />
          
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getJobStatusType(scope.row.status)" size="small">
                {{ formatJobStatus(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="applicants_count" label="申请人数" width="100" align="center">
            <template #default="scope">
              <el-badge :value="scope.row.applicants_count || 0" :max="99" type="primary">
                <el-button size="small" plain @click.stop="goToJobApplicants(scope.row.id)">
                  查看申请
                </el-button>
              </el-badge>
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="发布时间" width="160" sortable>
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <el-button 
                type="primary" 
                size="small" 
                plain
                @click.stop="goToJobDetail(scope.row)"
              >
                查看
              </el-button>
              
              <el-button 
                v-if="isJobEditable(scope.row.status)"
                type="warning" 
                size="small" 
                plain
                @click.stop="goToEditJob(scope.row.id)"
              >
                编辑
              </el-button>
              
              <el-button 
                v-if="scope.row.status === 'open'"
                type="danger" 
                size="small" 
                plain
                @click.stop="confirmCloseJob(scope.row)"
              >
                关闭
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
    
    <!-- 关闭工作对话框 -->
    <el-dialog
      v-model="closeJobDialogVisible"
      title="关闭工作"
      width="400px"
    >
      <el-form :model="closeJobForm" label-position="top">
        <el-form-item label="关闭原因（可选）">
          <el-input 
            v-model="closeJobForm.reason" 
            type="textarea" 
            rows="3"
            placeholder="请输入关闭原因（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeJobDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="processing" @click="closeJob">确认</el-button>
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
const jobs = ref<any[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const processing = ref(false);

// 关闭工作对话框
const closeJobDialogVisible = ref(false);
const selectedJob = ref<any>(null);
const closeJobForm = reactive({
  reason: ''
});

// 获取发布的工作列表
const fetchMyPostedJobs = async () => {
  loading.value = true;
  try {
    // 获取token
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您需要先登录');
      router.push('/auth/login');
      return;
    }
    
    // 发起请求
    const response = await axios.get(
      apiConfig.getApiUrl('/jobs/my'), 
      {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params: {
          page: currentPage.value,
          per_page: pageSize.value
        }
      }
    );
    
    // 处理响应
    if (response.data && response.data.code === 0) {
      jobs.value = response.data.data.items;
      totalItems.value = response.data.data.pagination.total_items;
    } else {
      ElMessage.error(response.data?.message || '获取工作列表失败');
    }
  } catch (error: any) {
    console.error('获取工作列表错误:', error);
    ElMessage.error(error.response?.data?.message || '获取工作列表时发生错误');
  } finally {
    loading.value = false;
  }
};

// 页码变更
const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchMyPostedJobs();
};

// 跳转到工作详情页
const goToJobDetail = (row: any) => {
  router.push(`/jobs/${row.id}`);
};

// 跳转到申请人列表
const goToJobApplicants = (jobId: number) => {
  router.push(`/jobs/${jobId}/applicants`);
};

// 跳转到编辑工作页
const goToEditJob = (jobId: number) => {
  router.push(`/jobs/edit/${jobId}`);
};

// 跳转到发布工作页
const goToPostJob = () => {
  router.push('/jobs/new');
};

// 确认关闭工作
const confirmCloseJob = (job: any) => {
  selectedJob.value = job;
  closeJobForm.reason = '';
  closeJobDialogVisible.value = true;
};

// 关闭工作
const closeJob = async () => {
  if (!selectedJob.value) return;
  
  processing.value = true;
  try {
    const token = authStore.token;
    
    const response = await axios.put(
      apiConfig.getApiUrl(`/jobs/${selectedJob.value.id}/status`),
      { 
        status: 'closed',
        reason: closeJobForm.reason || undefined
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    if (response.data && response.data.code === 0) {
      ElMessage.success('工作已关闭');
      closeJobDialogVisible.value = false;
      fetchMyPostedJobs(); // 重新加载工作列表
    } else {
      ElMessage.error(response.data?.message || '关闭工作失败');
    }
  } catch (error: any) {
    console.error('关闭工作错误:', error);
    ElMessage.error(error.response?.data?.message || '关闭工作时发生错误');
  } finally {
    processing.value = false;
  }
};

// 格式化工作状态
const formatJobStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'open': '招聘中',
    'closed': '已关闭',
    'filled': '已满员',
    'cancelled': '已取消'
  };
  return statusMap[status] || status;
};

// 获取状态对应的样式类型
const getJobStatusType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    'open': 'success',
    'closed': 'info',
    'filled': 'warning',
    'cancelled': 'danger'
  };
  return typeMap[status] || 'info';
};

// 判断工作是否可编辑
const isJobEditable = (status: string): boolean => {
  return status === 'open';
};

// 格式化日期
const formatDate = (dateString: string): string => {
  if (!dateString) return '未设置';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 组件挂载时加载数据
onMounted(() => {
  if (authStore.isLoggedIn) {
    fetchMyPostedJobs();
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

.loading-container,
.empty-container {
  padding: 40px 0;
  text-align: center;
}

.jobs-list {
  margin-top: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
