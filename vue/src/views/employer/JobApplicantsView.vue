<template>
  <div class="job-applicants page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>工作申请管理</span>
          <div class="header-actions">
            <el-select v-model="statusFilter" placeholder="筛选状态" clearable @change="filterApplications">
              <el-option label="全部" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="已接受" value="accepted" />
              <el-option label="已拒绝" value="rejected" />
              <el-option label="已取消" value="canceled" />
            </el-select>
          </div>
        </div>
      </template>

      <div v-if="!jobId">
        <el-empty description="请选择一个工作查看申请"></el-empty>
      </div>

      <div v-else-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="applications.length === 0" class="empty-container">
        <el-empty description="暂无申请记录" />
      </div>

      <div v-else class="applicants-list">
        <el-table 
          :data="applications" 
          style="width: 100%"
          :default-sort="{ prop: 'created_at', order: 'descending' }"
          row-key="id"
          @row-click="viewApplicationDetails"
        >
          <el-table-column
            prop="freelancer_info.nickname"
            label="申请人" 
            min-width="120"
          >
            <template #default="scope">
              <div class="applicant-info">
                <el-avatar :size="32" :src="scope.row.freelancer_info?.avatar_url || defaultAvatar"></el-avatar>
                <span>{{ scope.row.freelancer_info?.nickname || '无名用户' }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="application_message" label="申请留言" min-width="180" show-overflow-tooltip />

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

          <el-table-column label="操作" width="160" fixed="right">
            <template #default="scope">
              <div v-if="scope.row.status === 'pending'">
                <el-button 
                  type="success" 
                  size="small" 
                  @click.stop="acceptApplication(scope.row)"
                >
                  接受
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click.stop="openRejectDialog(scope.row)"
                >
                  拒绝
                </el-button>
              </div>
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
          <el-descriptions-item label="申请人">
            <div class="applicant-info">
              <el-avatar :size="40" :src="selectedApplication.freelancer_info?.avatar_url || defaultAvatar"></el-avatar>
              <span>{{ selectedApplication.freelancer_info?.nickname || '无名用户' }}</span>
            </div>
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
          <div v-if="selectedApplication.status === 'pending'">
            <el-button 
              type="success" 
              @click="acceptApplication(selectedApplication)"
            >
              接受
            </el-button>
            <el-button 
              type="danger" 
              @click="openRejectDialog(selectedApplication)"
            >
              拒绝
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 拒绝申请对话框 -->
    <el-dialog
      v-model="rejectDialogVisible"
      title="拒绝申请"
      width="400px"
    >
      <el-form :model="rejectForm" label-position="top">
        <el-form-item label="拒绝原因（可选）">
          <el-input 
            v-model="rejectForm.reason" 
            type="textarea" 
            rows="3"
            placeholder="请输入拒绝原因（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="rejectDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="processing" @click="rejectApplication">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';
import dayjs from 'dayjs';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// 默认头像
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

// 状态数据
const applications = ref<any[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const statusFilter = ref('');
const processing = ref(false);

// 详情对话框状态
const detailDialogVisible = ref(false);
const selectedApplication = ref<any>(null);

// 拒绝对话框状态
const rejectDialogVisible = ref(false);
const rejectForm = reactive({
  reason: ''
});

// 从路由参数获取工作ID
const jobId = computed(() => {
  return Number(route.params.jobId) || 0;
});

// 获取申请列表
const fetchApplications = async () => {
  if (!jobId.value) return;
  
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
    const response = await axios.get(
      apiConfig.getApiUrl(`/job-applications/jobs/${jobId.value}/list`), 
      {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params
      }
    );
    
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

// 打开拒绝申请对话框
const openRejectDialog = (application: any) => {
  selectedApplication.value = application;
  rejectForm.reason = '';
  rejectDialogVisible.value = true;
};

// 接受申请
const acceptApplication = async (application: any) => {
  if (!application) return;
  
  try {
    await ElMessageBox.confirm('确定接受该申请？接受后将创建订单', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    processing.value = true;
    const token = authStore.token;
    
    const response = await axios.put(
      apiConfig.getApiUrl(`/job-applications/${application.id}/process`),
      { status: 'accepted' },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    if (response.data && response.data.code === 0) {
      ElMessage.success('已接受申请');
      detailDialogVisible.value = false;
      fetchApplications(); // 重新加载申请列表
      
      // 如果创建了订单，可以提示订单ID
      if (response.data.data.created_order_id) {
        ElMessage({
          message: `已创建订单 #${response.data.data.created_order_id}`,
          type: 'success',
          duration: 5000
        });
      }
    } else {
      ElMessage.error(response.data?.message || '处理申请失败');
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('接受申请错误:', error);
      ElMessage.error(error.response?.data?.message || '接受申请时发生错误');
    }
  } finally {
    processing.value = false;
  }
};

// 拒绝申请
const rejectApplication = async () => {
  if (!selectedApplication.value) return;
  
  processing.value = true;
  try {
    const token = authStore.token;
    
    const response = await axios.put(
      apiConfig.getApiUrl(`/job-applications/${selectedApplication.value.id}/process`),
      { 
        status: 'rejected',
        reason: rejectForm.reason || undefined
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    if (response.data && response.data.code === 0) {
      ElMessage.success('已拒绝申请');
      rejectDialogVisible.value = false;
      detailDialogVisible.value = false;
      fetchApplications(); // 重新加载申请列表
    } else {
      ElMessage.error(response.data?.message || '拒绝申请失败');
    }
  } catch (error: any) {
    console.error('拒绝申请错误:', error);
    ElMessage.error(error.response?.data?.message || '拒绝申请时发生错误');
  } finally {
    processing.value = false;
  }
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
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/auth/login');
    return;
  }
  
  if (authStore.user?.current_role !== 'employer') {
    ElMessage.warning('仅雇主可以查看申请管理');
    router.push('/');
    return;
  }
  
  if (jobId.value) {
    fetchApplications();
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

.applicants-list {
  margin-top: 10px;
}

.applicant-info {
  display: flex;
  align-items: center;
  gap: 8px;
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
