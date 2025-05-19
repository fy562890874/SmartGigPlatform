<template>
  <div class="order-detail-view page-container">
    <el-page-header @back="router.back()" title="返回订单列表" />

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="20" animated />
    </div>

    <div v-else-if="!order" class="no-order">
      <el-empty description="未找到订单信息" />
      <el-button type="primary" @click="router.push('/my-orders')">返回订单列表</el-button>
    </div>

    <template v-else>
      <el-card shadow="never" class="order-card">
        <template #header>
          <div class="card-header">
            <div>
              <h2 class="order-title">订单详情 #{{ order.id }}</h2>
              <div class="order-status-badge" :class="getStatusClass(order.status)">
                {{ formatStatus(order.status) }}
              </div>
            </div>
            <div class="order-action-buttons">
              <!-- 展示订单操作按钮 -->
              <OrderActionPanel 
                :order="order" 
                :current-role="currentUserRole" 
                @action-performed="handleActionPerformed"
                @update-work-times="openWorkTimeModal = true" 
              />
            </div>
          </div>
        </template>

        <!-- 订单主要信息 -->
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <div class="info-section">
              <h3>工作信息</h3>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="工作标题">
                  <router-link :to="`/jobs/${order.job_id}`" class="job-link">
                    {{ order.job?.title || '未知工作' }}
                  </router-link>
                </el-descriptions-item>
                <el-descriptions-item label="计划开始时间">
                  {{ formatDateTime(order.start_time_scheduled) }}
                </el-descriptions-item>
                <el-descriptions-item label="计划结束时间">
                  {{ formatDateTime(order.end_time_scheduled) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="order.start_time_actual" label="实际开始时间">
                  {{ formatDateTime(order.start_time_actual) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="order.end_time_actual" label="实际结束时间">
                  {{ formatDateTime(order.end_time_actual) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="order.work_duration_actual" label="实际工时">
                  {{ order.work_duration_actual }} 小时
                </el-descriptions-item>
                <el-descriptions-item v-if="order.cancellation_reason" label="取消原因">
                  {{ order.cancellation_reason }}
                  <span v-if="order.cancelled_by">({{ formatCancelledBy(order.cancelled_by) }})</span>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>

          <el-col :xs="24" :sm="12">
            <div class="info-section">
              <h3>金额信息</h3>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="订单总额">
                  <span class="amount">¥{{ order.order_amount?.toFixed(2) || '0.00' }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="平台服务费">
                  ¥{{ order.platform_fee?.toFixed(2) || '0.00' }}
                </el-descriptions-item>
                <el-descriptions-item label="零工实际收入">
                  <span class="amount">¥{{ order.freelancer_income?.toFixed(2) || '0.00' }}</span>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="mt-20">
          <el-col :xs="24" :sm="12">
            <div class="info-section">
              <h3>零工信息</h3>
              <div class="user-info">
                <el-avatar 
                  :size="60" 
                  :src="order.freelancer?.avatar_url || ''" 
                  :fallback-src="defaultAvatar"
                />
                <div class="user-details">
                  <div class="user-name">{{ order.freelancer?.nickname || '未知用户' }}</div>
                  <div class="user-status">
                    确认状态: 
                    <el-tag :type="getConfirmationStatusType(order.freelancer_confirmation_status)">
                      {{ formatConfirmationStatus(order.freelancer_confirmation_status) }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </el-col>

          <el-col :xs="24" :sm="12">
            <div class="info-section">
              <h3>雇主信息</h3>
              <div class="user-info">
                <el-avatar 
                  :size="60" 
                  :src="order.employer?.avatar_url || ''" 
                  :fallback-src="defaultAvatar"
                />
                <div class="user-details">
                  <div class="user-name">{{ order.employer?.nickname || '未知用户' }}</div>
                  <div class="user-status">
                    确认状态: 
                    <el-tag :type="getConfirmationStatusType(order.employer_confirmation_status)">
                      {{ formatConfirmationStatus(order.employer_confirmation_status) }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <div class="info-section">
          <h3>订单时间线</h3>
          <el-timeline>
            <el-timeline-item 
              timestamp="订单创建" 
              placement="top" 
              :color="getTimelineColor('created')"
            >
              <p>订单创建于 {{ formatDateTime(order.created_at) }}</p>
            </el-timeline-item>
            
            <el-timeline-item 
              v-if="order.start_time_actual"
              timestamp="开始工作" 
              placement="top"
              :color="getTimelineColor('started')"
            >
              <p>工作开始于 {{ formatDateTime(order.start_time_actual) }}</p>
            </el-timeline-item>
            
            <el-timeline-item 
              v-if="order.end_time_actual"
              timestamp="工作完成" 
              placement="top"
              :color="getTimelineColor('completed')"
            >
              <p>工作完成于 {{ formatDateTime(order.end_time_actual) }}</p>
              <p>总工时: {{ order.work_duration_actual || '未记录' }} 小时</p>
            </el-timeline-item>
            
            <el-timeline-item 
              v-if="order.status === 'completed'"
              timestamp="订单完成" 
              placement="top"
              color="#67C23A"
            >
              <p>订单已完成</p>
            </el-timeline-item>
            
            <el-timeline-item 
              v-if="order.status === 'cancelled'"
              timestamp="订单取消" 
              placement="top"
              color="#F56C6C"
            >
              <p>订单已取消</p>
              <p v-if="order.cancellation_reason">取消原因: {{ order.cancellation_reason }}</p>
              <p v-if="order.cancelled_by">取消方: {{ formatCancelledBy(order.cancelled_by) }}</p>
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-card>
    </template>

    <!-- 修改工作时间的模态框 -->
    <OrderTimeUpdateModal
      v-if="order"
      v-model="openWorkTimeModal"
      :order-id="orderId"
      :initial-start-time="order.start_time_actual"
      :initial-end-time="order.end_time_actual"
      @success="handleActionPerformed"
    />

    <!-- 取消订单的模态框 -->
    <el-dialog
      v-model="cancelDialogVisible"
      title="取消订单"
      width="500px"
    >
      <el-form :model="cancelForm" ref="cancelFormRef" label-width="100px">
        <el-form-item 
          label="取消原因" 
          prop="reason" 
          :rules="[{ required: true, message: '请填写取消原因', trigger: 'blur' }]"
        >
          <el-input 
            v-model="cancelForm.reason" 
            type="textarea" 
            :rows="3" 
            placeholder="请说明您取消订单的原因"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmCancelOrder" :loading="submitting">
          确认取消订单
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';
import dayjs from 'dayjs';
import OrderActionPanel from '@/components/order/OrderActionPanel.vue';
import OrderTimeUpdateModal from '@/components/order/OrderTimeUpdateModal.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// 默认头像
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

// 状态变量
const orderId = ref(Number(route.params.orderId || 0));
const loading = ref(true);
const order = ref<any>(null);
const jobApplication = ref<any>(null);
const currentUserRole = ref('');
const openWorkTimeModal = ref(false);
const cancelDialogVisible = ref(false);
const cancelForm = reactive({
  reason: ''
});
const cancelFormRef = ref<FormInstance>();
const submitting = ref(false);
const actionLoading = ref(false);

// 获取订单详情
const fetchOrderDetails = async () => {
  if (!orderId.value) return;
  
  loading.value = true;
  try {
    // 获取当前用户角色
    if (authStore.user && authStore.user.current_role) {
      currentUserRole.value = authStore.user.current_role;
    }
    
    // 设置调试模式
    const isDebug = localStorage.getItem('debug_mode') === 'true';
    
    // 获取订单详情
    const orderData = await apiClient.get(`/orders/${orderId.value}`);
    
    if (isDebug) {
      console.log('OrderDetailView 收到的订单数据:', orderData);
    }
    
    if (orderData) {
      // 检查数据格式，如果是数组或包含items数组，则取第一个元素
      if (Array.isArray(orderData)) {
        if (orderData.length > 0) {
          order.value = orderData[0];
          if (isDebug) {
            console.log('从数组中提取第一个订单:', order.value);
          }
        } else {
          throw new Error('未找到订单数据');
        }
      } else if (orderData.items && Array.isArray(orderData.items) && orderData.items.length > 0) {
        order.value = orderData.items[0];
        if (isDebug) {
          console.log('从items数组中提取第一个订单:', order.value);
        }
      } else {
        // 直接使用对象
        order.value = orderData;
      }
      
      // 获取关联的工作申请
      if (order.value.application_id) {
        try {
          const applicationData = await apiClient.get(`/job-applications/${order.value.application_id}`);
          jobApplication.value = applicationData;
          
          if (isDebug) {
            console.log('获取到关联的工作申请:', jobApplication.value);
          }
        } catch (appError: any) {
          console.warn('获取关联工作申请失败:', appError);
          // 这不是致命错误，可以继续
        }
      }
    } else {
      ElMessage.error('获取订单详情失败：无效的响应数据');
      router.push('/orders');
    }
  } catch (error: any) {
    console.error('获取订单详情失败:', error);
    if (error.response?.status === 404) {
      ElMessage.error('订单不存在或已被删除');
      router.push('/orders');
    } else if (error.response?.status === 403) {
      ElMessage.error('您无权访问此订单');
      router.push('/orders');
    } else {
      ElMessage.error(error.response?.data?.message || error.message || '获取订单详情失败');
    }
  } finally {
    loading.value = false;
  }
};

// 格式化和样式函数
const formatDateTime = (dateStr: string | null | undefined) => {
  if (!dateStr) return '未设置';
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm');
};

const formatStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending_payment': '待付款',
    'pending_start': '待开工',
    'in_progress': '进行中',
    'pending_confirmation': '待确认',
    'completed': '已完成',
    'cancelled': '已取消',
    'refunded': '已退款',
    'disputed': '申诉中'
  };
  return statusMap[status] || status;
};

const getStatusClass = (status: string) => {
  const classMap: Record<string, string> = {
    'pending_payment': 'status-warning',
    'pending_start': 'status-info',
    'in_progress': 'status-primary',
    'pending_confirmation': 'status-warning',
    'completed': 'status-success',
    'cancelled': 'status-danger',
    'refunded': 'status-danger',
    'disputed': 'status-danger'
  };
  return classMap[status] || 'status-default';
};

const formatConfirmationStatus = (status: string | null | undefined) => {
  if (!status) return '未确认';
  const statusMap: Record<string, string> = {
    'pending': '待确认',
    'confirmed': '已确认',
    'rejected': '已拒绝'
  };
  return statusMap[status] || status;
};

const getConfirmationStatusType = (status: string | null | undefined) => {
  if (!status) return 'info';
  const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    'pending': 'info',
    'confirmed': 'success',
    'rejected': 'danger'
  };
  return typeMap[status] || 'info';
};

const formatCancelledBy = (cancelledBy: string) => {
  return cancelledBy === 'freelancer' ? '零工' : 
         cancelledBy === 'employer' ? '雇主' : 
         cancelledBy === 'system' ? '系统' : 
         cancelledBy || '未知';
};

const getTimelineColor = (phase: string) => {
  const colorMap: Record<string, string> = {
    'created': '#409EFF',
    'started': '#E6A23C',
    'completed': '#67C23A'
  };
  return colorMap[phase] || '#909399';
};

// 事件处理函数
const handleActionPerformed = () => {
  fetchOrderDetails(); // 重新获取订单数据
};

// 打开取消订单对话框
const openCancelDialog = () => {
  cancelForm.reason = '';
  cancelDialogVisible.value = true;
};

// 确认取消订单
const confirmCancelOrder = async () => {
  if (!cancelFormRef.value) return;
  
  await cancelFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请填写取消原因');
      return;
    }

    submitting.value = true;
    try {
      await handleOrderAction('cancel_order', { cancellation_reason: cancelForm.reason });
      cancelDialogVisible.value = false;
    } finally {
      submitting.value = false;
    }
  });
};

// 处理订单操作
const handleOrderAction = async (action: string, additionalData = {}) => {
  try {
    actionLoading.value = true;
    
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      return;
    }

    const payload = {
      action,
      ...additionalData
    };
    
    // 直接使用 apiClient 的封装方法
    const result = await apiClient.post(`/orders/${orderId.value}/actions`, payload);
    
    ElMessage.success('操作成功');
    fetchOrderDetails(); // 刷新订单详情
  } catch (error: any) {
    console.error(`处理订单${action}操作失败:`, error);
    
    // 针对不同错误类型处理
    if (error.response?.status === 409) {
      ElMessage.error(error.response?.data?.message || '操作与当前订单状态冲突');
    } else if (error.response?.status === 403) {
      ElMessage.error('您无权执行此操作');
    } else if (error.response?.status === 400) {
      ElMessage.error(error.response?.data?.message || '请求参数错误');
    } else {
      ElMessage.error(error.response?.data?.message || '操作失败，请稍后重试');
    }
  } finally {
    actionLoading.value = false;
  }
};

// 组件挂载时
onMounted(() => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }

  if (!orderId.value) {
    ElMessage.error('未指定订单ID');
    router.push('/my-orders');
    return;
  }

  fetchOrderDetails();

  // 检查URL参数，若有action=complete_work，则打开工作时间模态框
  if (route.query.action === 'complete_work') {
    openWorkTimeModal.value = true;
  }
});

// 暴露方法给子组件
defineExpose({
  openCancelDialog
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1000px;
  margin: 20px auto;
}

.loading-state {
  padding: 20px;
}

.no-order {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 40px 0;
}

.order-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 20px;
}

.order-title {
  margin: 0 0 10px 0;
  font-size: 1.4em;
}

.order-status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
}

.status-primary { background-color: #ecf5ff; color: #409eff; }
.status-success { background-color: #f0f9eb; color: #67c23a; }
.status-warning { background-color: #fdf6ec; color: #e6a23c; }
.status-danger { background-color: #fef0f0; color: #f56c6c; }
.status-info { background-color: #f4f4f5; color: #909399; }
.status-default { background-color: #f4f4f5; color: #606266; }

.info-section {
  margin-bottom: 30px;
}

.info-section h3 {
  font-size: 1.2em;
  margin-top: 0;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}

.user-status {
  color: #606266;
}

.amount {
  font-weight: bold;
  color: #f56c6c;
}

.job-link {
  text-decoration: none;
  color: #409eff;
}

.job-link:hover {
  text-decoration: underline;
}

.mt-20 {
  margin-top: 20px;
}

@media screen and (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .order-action-buttons {
    width: 100%;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
  }
}
</style> 