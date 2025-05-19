<template>
  <div class="order-list-view page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>我的订单</span>
          <el-radio-group v-model="statusFilter" size="small" @change="filterOrders">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="pending_payment">待付款</el-radio-button>
            <el-radio-button label="pending_start">待开工</el-radio-button>
            <el-radio-button label="in_progress">进行中</el-radio-button>
            <el-radio-button label="pending_confirmation">待确认</el-radio-button>
            <el-radio-button label="completed">已完成</el-radio-button>
            <el-radio-button label="cancelled">已取消</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>

      <el-empty v-else-if="!orders.length" description="暂无订单记录" />

      <template v-else>
        <div class="order-list">
          <div v-for="order in orders" :key="order.id" class="order-item" @click="goToOrderDetail(order.id)">
            <div class="order-header">
              <div class="job-title">{{ order.job?.title || '未知工作' }}</div>
              <div class="order-status" :class="getStatusClass(order.status)">{{ formatStatus(order.status) }}</div>
            </div>
            <div class="order-body">
              <div class="order-info">
                <p>
                  <span class="label">订单号:</span>
                  <span>#{{ order.id }}</span>
                </p>
                <p>
                  <span class="label">{{ isEmployer ? '零工' : '雇主' }}:</span>
                  <span>{{ isEmployer ? (order.freelancer?.nickname || '未知用户') : (order.employer?.nickname || '未知用户') }}</span>
                </p>
                <p>
                  <span class="label">订单金额:</span>
                  <span class="amount">¥{{ order.order_amount?.toFixed(2) || '0.00' }}</span>
                </p>
                <p>
                  <span class="label">计划时间:</span>
                  <span>{{ formatDate(order.start_time_scheduled) }} - {{ formatDate(order.end_time_scheduled) }}</span>
                </p>
                <p v-if="order.start_time_actual && order.end_time_actual">
                  <span class="label">实际时间:</span>
                  <span>{{ formatDate(order.start_time_actual) }} - {{ formatDate(order.end_time_actual) }}</span>
                </p>
              </div>
              <div class="order-actions">
                <el-button type="primary" size="small" @click.stop="goToOrderDetail(order.id)">查看详情</el-button>
                <!-- 常用操作按钮可直接放在列表中 -->
                <template v-if="order.status === 'pending_start' && !isEmployer">
                  <el-button type="success" size="small" @click.stop="startWork(order.id)">开始工作</el-button>
                </template>
                <template v-if="order.status === 'in_progress' && !isEmployer">
                  <el-button type="success" size="small" @click.stop="completeWork(order.id)">完成工作</el-button>
                </template>
                <template v-if="order.status === 'pending_confirmation' && isEmployer">
                  <el-button type="success" size="small" @click.stop="confirmCompletion(order.id)">确认完成</el-button>
                </template>
              </div>
            </div>
            <div class="order-footer">
              <span>创建时间: {{ formatDateTime(order.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="totalItems"
            layout="total, prev, pager, next, jumper"
            @current-change="handlePageChange"
          />
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import dayjs from 'dayjs';

const router = useRouter();
const authStore = useAuthStore();

// 状态和数据
const orders = ref<any[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const statusFilter = ref('');
const currentUserRole = ref('');

// 计算属性
const isEmployer = computed(() => {
  return currentUserRole.value === 'employer';
});

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      return;
    }

    // 确定当前用户角色
    if (!currentUserRole.value) {
      if (authStore.user?.current_role) {
        currentUserRole.value = authStore.user.current_role;
      } else {
        // 尝试从 available_roles 中确定，优先使用 employer
        const availableRoles = authStore.user?.available_roles || [];
        if (availableRoles.includes('employer')) {
          currentUserRole.value = 'employer';
        } else if (availableRoles.includes('freelancer')) {
          currentUserRole.value = 'freelancer';
        } else {
          ElMessage.error('无法确定您的角色，请先设置角色');
          router.push('/settings');
          return;
        }
      }
    }

    // 构建请求参数
    const params: any = {
      page: currentPage.value,
      per_page: pageSize.value,
      role: currentUserRole.value,
    };

    // 如果有状态筛选
    if (statusFilter.value) {
      params.status = statusFilter.value;
    }

    // 发送请求
    const response = await axios.get('http://127.0.0.1:5000/api/v1/orders', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      params
    });

    // 处理响应
    if (response.data && response.data.code === 0) {
      const data = response.data.data;
      orders.value = data.items || [];
      totalItems.value = data.total_items || 0;
    } else {
      ElMessage.error(response.data?.message || '获取订单列表失败');
    }
  } catch (error: any) {
    console.error('获取订单列表失败:', error);
    ElMessage.error(error.response?.data?.message || '获取订单列表失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 页码变更处理
const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchOrders();
};

// 状态筛选
const filterOrders = () => {
  currentPage.value = 1; // 重置页码
  fetchOrders();
};

// 导航到订单详情
const goToOrderDetail = (orderId: number) => {
  router.push(`/orders/${orderId}`);
};

// 格式化订单状态
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

// 获取状态对应的样式类
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

// 日期格式化 (仅日期)
const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return '未设置';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 日期时间格式化
const formatDateTime = (dateStr: string | null | undefined) => {
  if (!dateStr) return '未设置';
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm');
};

// 订单操作函数
const startWork = async (orderId: number) => {
  try {
    const confirmed = await ElMessageBox.confirm('确定要开始这项工作吗？', '开始工作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    });
    
    if (confirmed) {
      await performOrderAction(orderId, 'start_work');
    }
  } catch {
    // 用户取消操作
  }
};

const completeWork = (orderId: number) => {
  router.push({
    path: `/orders/${orderId}`,
    query: { action: 'complete_work' }
  });
};

const confirmCompletion = async (orderId: number) => {
  try {
    const confirmed = await ElMessageBox.confirm('确认工作已完成且符合要求吗？', '确认完成', {
      confirmButtonText: '确认完成',
      cancelButtonText: '取消',
      type: 'success'
    });
    
    if (confirmed) {
      await performOrderAction(orderId, 'confirm_completion');
    }
  } catch {
    // 用户取消操作
  }
};

// 执行订单操作的通用函数
const performOrderAction = async (orderId: number, action: string, additionalData = {}) => {
  try {
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

    const response = await axios.post(
      `http://127.0.0.1:5000/api/v1/orders/${orderId}/actions`,
      payload,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (response.data && response.data.code === 0) {
      ElMessage.success('操作成功');
      // 刷新订单列表
      fetchOrders();
    } else {
      ElMessage.error(response.data?.message || '操作失败');
    }
  } catch (error: any) {
    console.error('订单操作失败:', error);
    ElMessage.error(error.response?.data?.message || '操作失败，请稍后重试');
  }
};

// 组件挂载时加载数据
onMounted(() => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  fetchOrders();
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
  flex-wrap: wrap;
  gap: 10px;
}

.card-header span {
  font-size: 1.2em;
  font-weight: bold;
}

.loading-state {
  padding: 20px;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.order-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.order-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.job-title {
  font-weight: bold;
  font-size: 16px;
}

.order-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status-primary { background-color: #ecf5ff; color: #409eff; }
.status-success { background-color: #f0f9eb; color: #67c23a; }
.status-warning { background-color: #fdf6ec; color: #e6a23c; }
.status-danger { background-color: #fef0f0; color: #f56c6c; }
.status-info { background-color: #f4f4f5; color: #909399; }
.status-default { background-color: #f4f4f5; color: #606266; }

.order-body {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.order-info {
  flex: 1;
}

.order-info p {
  margin: 8px 0;
  color: #606266;
}

.label {
  color: #909399;
  margin-right: 8px;
  min-width: 70px;
  display: inline-block;
}

.amount {
  font-weight: bold;
  color: #f56c6c;
}

.order-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.order-footer {
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #ebeef5;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

@media screen and (max-width: 768px) {
  .order-body {
    flex-direction: column;
  }
  
  .order-actions {
    flex-direction: row;
    margin-top: 10px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .el-radio-group {
    margin-top: 10px;
  }
}
</style> 