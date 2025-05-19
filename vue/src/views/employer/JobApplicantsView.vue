<!--
  @file JobApplicantsView.vue
  @description 雇主查看工作申请者及管理申请状态
  @author Fy
  @date 2023-05-22
-->
<template>
  <div class="job-applicants page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title-section">
            <h1>申请者管理</h1>
            <h2 v-if="job" class="job-title">{{ job.title }}</h2>
          </div>
          <el-button @click="goBack">返回</el-button>
        </div>
      </template>
      
      <!-- 加载状态 -->
      <div v-if="loading.job || loading.applicants" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>
      
      <!-- 无申请者状态 -->
      <el-empty
        v-else-if="applicants.length === 0"
        description="暂无申请者"
      >
        <div class="actions">
          <el-button @click="goBack">返回工作列表</el-button>
        </div>
      </el-empty>
      
      <!-- 申请者列表 -->
      <template v-else>
        <!-- 筛选条件 -->
        <el-form :inline="true" class="filter-form">
          <el-form-item label="状态">
            <el-select v-model="filterParams.status" placeholder="所有状态" clearable @change="fetchApplicants">
              <el-option label="待处理" value="pending" />
              <el-option label="已接受" value="accepted" />
              <el-option label="已拒绝" value="rejected" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select v-model="filterParams.sort_by" placeholder="申请时间" @change="fetchApplicants">
              <el-option label="最新申请" value="created_at_desc" />
              <el-option label="最早申请" value="created_at_asc" />
              <el-option label="匹配度高到低" value="score_desc" />
            </el-select>
          </el-form-item>
        </el-form>
        
        <div class="applicants-list">
          <el-table :data="applicants" style="width: 100%" border>
            <el-table-column label="申请者" min-width="180">
              <template #default="{ row }">
                <div class="applicant-info">
                  <el-avatar :src="row.freelancer.avatar_url || ''" :size="40">
                    {{ row.freelancer.nickname ? row.freelancer.nickname.substring(0, 1).toUpperCase() : 'U' }}
                  </el-avatar>
                  <div class="applicant-details">
                    <div class="applicant-name">{{ row.freelancer.nickname || `用户 #${row.freelancer_user_id}` }}</div>
                    <div class="application-date">申请于 {{ formatDateTime(row.created_at) }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column label="期望薪资" min-width="100" align="center">
              <template #default="{ row }">
                <div v-if="row.expected_salary">{{ row.expected_salary }}元/{{ getSalaryTypeText(job.salary_type) }}</div>
                <div v-else>接受发布薪资</div>
              </template>
            </el-table-column>
            
            <el-table-column label="状态" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" min-width="250" fixed="right">
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  @click="viewProfile(row.freelancer_user_id)"
                >
                  查看档案
                </el-button>
                
                <el-button
                  v-if="row.status === 'pending'"
                  type="success"
                  size="small"
                  @click="acceptApplicant(row)"
                >
                  接受
                </el-button>
                
                <el-button
                  v-if="row.status === 'pending'"
                  type="danger"
                  size="small"
                  @click="rejectApplicant(row)"
                >
                  拒绝
                </el-button>
                
                <el-button
                  v-if="row.status === 'accepted' && job.status === 'active'"
                  type="primary"
                  size="small"
                  @click="createOrder(row)"
                >
                  创建订单
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
      </template>
    </el-card>
    
    <!-- 接受/拒绝申请者对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="30%"
    >
      <el-form :model="responseForm" label-position="top">
        <el-form-item label="留言给申请者(可选)">
          <el-input
            v-model="responseForm.message"
            type="textarea"
            :rows="4"
            placeholder="可以输入留言给申请者..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button 
            :type="currentAction === 'accept' ? 'success' : 'danger'"
            @click="confirmResponse"
            :loading="responseLoading"
          >
            确认{{ currentAction === 'accept' ? '接受' : '拒绝' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 创建订单对话框 -->
    <el-dialog
      v-model="orderDialogVisible"
      title="创建订单"
      width="50%"
    >
      <el-form :model="orderForm" :rules="orderRules" ref="orderFormRef" label-width="100px">
        <el-form-item label="订单标题" prop="title">
          <el-input v-model="orderForm.title" placeholder="请输入订单标题" />
        </el-form-item>
        
        <el-form-item label="订单金额" prop="amount">
          <el-input-number v-model="orderForm.amount" :min="1" :precision="2" :step="100" style="width: 100%" />
        </el-form-item>
        
        <el-form-item label="开始日期" prop="start_time">
          <el-date-picker
            v-model="orderForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="结束日期" prop="end_time">
          <el-date-picker
            v-model="orderForm.end_time"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="订单说明" prop="description">
          <el-input
            v-model="orderForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入订单详细说明..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="orderDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitOrderForm" :loading="orderLoading">创建订单</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, FormInstance } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';
import dayjs from 'dayjs';

// 路由与状态管理
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const orderFormRef = ref<FormInstance>();

// 获取路由参数
const jobId = computed(() => {
  return route.params.id ? parseInt(route.params.id as string) : null;
});

// 加载状态
const loading = reactive({
  job: true,
  applicants: true
});

// 工作信息
const job = ref(null);

// 申请者列表
const applicants = ref([]);
const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
});

// 筛选参数
const filterParams = reactive({
  status: '',
  sort_by: 'created_at_desc'
});

// 对话框控制
const dialogVisible = ref(false);
const dialogTitle = ref('');
const currentAction = ref('');
const selectedApplicant = ref(null);
const responseLoading = ref(false);
const responseForm = reactive({
  message: ''
});

// 订单对话框控制
const orderDialogVisible = ref(false);
const orderLoading = ref(false);
const orderForm = reactive({
  title: '',
  amount: 0,
  start_time: '',
  end_time: '',
  description: '',
  job_application_id: null
});

// 订单表单验证规则
const orderRules = {
  title: [
    { required: true, message: '请输入订单标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度应在5到100个字符之间', trigger: 'blur' }
  ],
  amount: [
    { required: true, message: '请输入订单金额', trigger: 'blur' },
    { type: 'number', min: 1, message: '金额必须大于0', trigger: 'blur' }
  ],
  start_time: [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入订单说明', trigger: 'blur' },
    { min: 10, max: 500, message: '说明长度应在10到500个字符之间', trigger: 'blur' }
  ]
};

// 获取工作详情
const fetchJobDetails = async () => {
  if (!jobId.value) return;
  
  loading.job = true;
  try {
    const response = await apiClient.get(`jobs/${jobId.value}`);
    job.value = response.data;
  } catch (error) {
    console.error('获取工作详情失败:', error);
    ElMessage.error('无法获取工作详情');
  } finally {
    loading.job = false;
  }
};

// 获取申请者列表
const fetchApplicants = async () => {
  if (!jobId.value) return;
  
  loading.applicants = true;
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filterParams
    };
    
    const response = await apiClient.get(`jobs/${jobId.value}/applications`, { params });
    
    applicants.value = response.data.items;
    pagination.total = response.data.pagination.total_items;
  } catch (error) {
    console.error('获取申请者列表失败:', error);
    ElMessage.error('无法获取申请者列表');
  } finally {
    loading.applicants = false;
  }
};

// 查看零工档案
const viewProfile = (freelancerId) => {
  router.push(`/freelancers/${freelancerId}`);
};

// 接受申请者
const acceptApplicant = (applicant) => {
  selectedApplicant.value = applicant;
  currentAction.value = 'accept';
  dialogTitle.value = '接受申请';
  responseForm.message = '';
  dialogVisible.value = true;
};

// 拒绝申请者
const rejectApplicant = (applicant) => {
  selectedApplicant.value = applicant;
  currentAction.value = 'reject';
  dialogTitle.value = '拒绝申请';
  responseForm.message = '';
  dialogVisible.value = true;
};

// 确认回复申请
const confirmResponse = async () => {
  if (!selectedApplicant.value) return;
  
  responseLoading.value = true;
  try {
    const endpoint = `job-applications/${selectedApplicant.value.id}/${currentAction.value === 'accept' ? 'accept' : 'reject'}`;
    
    await apiClient.post(endpoint, {
      message: responseForm.message || undefined
    });
    
    ElMessage.success(`已${currentAction.value === 'accept' ? '接受' : '拒绝'}申请者`);
    fetchApplicants(); // 刷新列表
  } catch (error) {
    console.error('处理申请失败:', error);
  } finally {
    responseLoading.value = false;
    dialogVisible.value = false;
  }
};

// 创建订单
const createOrder = (applicant) => {
  selectedApplicant.value = applicant;
  
  // 预填订单表单
  orderForm.title = `${job.value.title} - 订单`;
  orderForm.amount = applicant.expected_salary || job.value.salary_amount;
  orderForm.start_time = job.value.start_time;
  orderForm.end_time = job.value.end_time;
  orderForm.description = job.value.description;
  orderForm.job_application_id = applicant.id;
  
  orderDialogVisible.value = true;
};

// 提交订单表单
const submitOrderForm = async () => {
  if (!orderFormRef.value) return;
  
  await orderFormRef.value.validate(async (valid) => {
    if (valid) {
      orderLoading.value = true;
      try {
        await apiClient.post('orders', orderForm);
        
        ElMessage.success('订单创建成功');
        orderDialogVisible.value = false;
        fetchApplicants(); // 刷新申请者列表
      } catch (error) {
        console.error('创建订单失败:', error);
      } finally {
        orderLoading.value = false;
      }
    } else {
      ElMessage.error('请完成必填项并修正表单错误');
    }
  });
};

// 分页处理
const handleSizeChange = (val) => {
  pagination.per_page = val;
  fetchApplicants();
};

const handleCurrentChange = (val) => {
  pagination.page = val;
  fetchApplicants();
};

// 返回上一页
const goBack = () => {
  router.back();
};

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 获取状态显示文本
const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    accepted: '已接受',
    rejected: '已拒绝',
    cancelled: '已取消'
  };
  return statusMap[status] || status;
};

// 获取状态标签类型
const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    accepted: 'success',
    rejected: 'danger',
    cancelled: 'info'
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

// 组件挂载
onMounted(() => {
  // 检查用户角色是否为雇主
  if (!authStore.isLoggedIn || authStore.user?.current_role !== 'employer') {
    ElMessage.warning('请先以雇主身份登录');
    router.push('/login');
    return;
  }
  
  // 检查是否有工作ID
  if (!jobId.value) {
    ElMessage.error('无效的工作ID');
    router.push('/employer/jobs');
    return;
  }
  
  // 获取工作和申请者信息
  fetchJobDetails();
  fetchApplicants();
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

.title-section {
  display: flex;
  flex-direction: column;
}

.title-section h1 {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0;
}

.job-title {
  font-size: 1.1em;
  margin: 5px 0 0;
  color: #606266;
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

.applicants-list {
  margin-top: 20px;
}

.applicant-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.applicant-details {
  display: flex;
  flex-direction: column;
}

.applicant-name {
  font-weight: bold;
}

.application-date {
  font-size: 0.8em;
  color: #909399;
}

.actions {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
