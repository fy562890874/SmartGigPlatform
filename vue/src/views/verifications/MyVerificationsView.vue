<template>
  <div class="my-verifications page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>我的认证记录</h1>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="认证类型">
          <el-select v-model="filterParams.profile_type" placeholder="全部类型" clearable @change="fetchVerifications">
            <el-option label="零工认证" value="freelancer"></el-option>
            <el-option label="雇主个人认证" value="employer_individual"></el-option>
            <el-option label="雇主企业认证" value="employer_company"></el-option>
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 加载中状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 空状态 -->
      <div v-else-if="verifications.length === 0" class="empty-state">
        <el-empty description="暂无认证记录">
          <el-button type="primary" @click="goToSubmit">立即认证</el-button>
        </el-empty>
      </div>

      <!-- 认证记录列表 -->
      <div v-else class="verification-list">
        <el-table :data="verifications" style="width: 100%" border>
          <el-table-column prop="id" label="记录ID" width="80" />
          <el-table-column label="认证类型" width="150">
            <template #default="scope">
              {{ formatProfileType(scope.row.profile_type) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ formatStatus(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="提交时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="审核时间" width="180">
            <template #default="scope">
              {{ scope.row.reviewed_at ? formatDate(scope.row.reviewed_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="拒绝原因">
            <template #default="scope">
              {{ scope.row.rejection_reason || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-button 
                v-if="scope.row.status === 'rejected'" 
                type="primary" 
                size="small" 
                @click="reapply(scope.row)"
              >
                重新提交
              </el-button>
              <el-button
                size="small"
                @click="viewDetails(scope.row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

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

    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailsVisible" 
      title="认证详情" 
      width="70%"
    >
      <div v-if="currentRecord" class="verification-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="认证类型">{{ formatProfileType(currentRecord.profile_type) }}</el-descriptions-item>
          <el-descriptions-item label="认证状态">
            <el-tag :type="getStatusType(currentRecord.status)">{{ formatStatus(currentRecord.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(currentRecord.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ currentRecord.reviewed_at ? formatDate(currentRecord.reviewed_at) : '-' }}</el-descriptions-item>
          
          <el-descriptions-item v-if="currentRecord.status === 'rejected'" label="拒绝原因" :span="2">
            {{ currentRecord.rejection_reason }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="submitted-data">
          <h3>认证资料</h3>
          
          <!-- 个人认证资料 -->
          <template v-if="currentRecord.profile_type === 'freelancer' || currentRecord.profile_type === 'employer_individual'">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="真实姓名">{{ currentRecord.submitted_data?.real_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="身份证号">{{ maskIdCard(currentRecord.submitted_data?.id_card_number) }}</el-descriptions-item>
            </el-descriptions>
            
            <div class="id-card-photos">
              <div class="photo-item" v-if="currentRecord.submitted_data?.id_card_photo_front_url">
                <p>身份证正面照</p>
                <el-image 
                  :src="currentRecord.submitted_data.id_card_photo_front_url" 
                  :preview-src-list="[currentRecord.submitted_data.id_card_photo_front_url]"
                  fit="contain"
                />
              </div>
              <div class="photo-item" v-if="currentRecord.submitted_data?.id_card_photo_back_url">
                <p>身份证背面照</p>
                <el-image 
                  :src="currentRecord.submitted_data.id_card_photo_back_url" 
                  :preview-src-list="[currentRecord.submitted_data.id_card_photo_back_url]"
                  fit="contain"
                />
              </div>
            </div>
          </template>
          
          <!-- 企业认证资料 -->
          <template v-if="currentRecord.profile_type === 'employer_company'">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="企业名称">{{ currentRecord.submitted_data?.company_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="统一社会信用代码">{{ currentRecord.submitted_data?.business_license_number || '-' }}</el-descriptions-item>
              <el-descriptions-item label="法人代表">{{ currentRecord.submitted_data?.legal_representative || '-' }}</el-descriptions-item>
            </el-descriptions>
            
            <div class="license-photo" v-if="currentRecord.submitted_data?.business_license_photo_url">
              <p>营业执照照片</p>
              <el-image 
                :src="currentRecord.submitted_data.business_license_photo_url" 
                :preview-src-list="[currentRecord.submitted_data.business_license_photo_url]"
                fit="contain"
              />
            </div>
          </template>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailsVisible = false">关闭</el-button>
          <el-button 
            v-if="currentRecord && currentRecord.status === 'rejected'" 
            type="primary" 
            @click="reapplyFromDetails"
          >
            重新提交认证
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';
import apiClient from '@/utils/apiClient';

// 路由和认证
const router = useRouter();
const authStore = useAuthStore();

// 页面状态
const loading = ref(false);
const verifications = ref<any[]>([]);
const totalItems = ref(0);
const totalPages = ref(1);
const detailsVisible = ref(false);
const currentRecord = ref<any>(null);

// 筛选参数
const filterParams = reactive({
  profile_type: '', // 默认全部类型
  page: 1,
  per_page: 10
});

// 获取用户认证记录
const fetchVerifications = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get('verifications/me', { params: filterParams });
    
    // apiClient已处理成功响应
    const data = response.data;
    verifications.value = data.items;
    totalItems.value = data.pagination.total_items;
    totalPages.value = data.pagination.total_pages;
  } catch (error: any) {
    console.error('获取认证记录失败:', error);
    // apiClient已处理错误消息
  } finally {
    loading.value = false;
  }
};

// 格式化显示函数
const formatProfileType = (type: string) => {
  const types: Record<string, string> = {
    'freelancer': '零工认证',
    'employer_individual': '雇主个人认证',
    'employer_company': '雇主企业认证'
  };
  return types[type] || type;
};

const formatStatus = (status: string) => {
  const statuses: Record<string, string> = {
    'pending': '审核中',
    'approved': '已通过',
    'rejected': '已拒绝'
  };
  return statuses[status] || status;
};

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  };
  return types[status] || 'info';
};

// 脱敏身份证号
const maskIdCard = (idCard?: string) => {
  if (!idCard) return '-';
  if (idCard.length >= 18) {
    return idCard.substring(0, 6) + '********' + idCard.substring(14);
  } else if (idCard.length >= 15) {
    return idCard.substring(0, 6) + '*****' + idCard.substring(11);
  }
  return idCard;
};

// 格式化日期
const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString();
};

// 页码变化处理
const handlePageChange = (page: number) => {
  filterParams.page = page;
  fetchVerifications();
};

// 查看详情
const viewDetails = (record: any) => {
  currentRecord.value = record;
  detailsVisible.value = true;
};

// 重新申请认证
const reapply = (record: any) => {
  router.push({
    path: '/verifications/submit',
    query: { type: record.profile_type, recordId: record.id }
  });
};

// 从详情对话框重新申请
const reapplyFromDetails = () => {
  if (currentRecord.value) {
    detailsVisible.value = false;
    reapply(currentRecord.value);
  }
};

// 前往提交认证页面
const goToSubmit = () => {
  router.push('/verifications/submit');
};

// 页面加载时获取数据
onMounted(() => {
  fetchVerifications();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1200px;
  margin: 20px auto;
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
  background-color: #f9f9f9;
  border-radius: 4px;
}

.loading-state, 
.empty-state {
  padding: 40px 0;
  text-align: center;
}

.verification-list {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.verification-details {
  padding: 10px;
}

.submitted-data {
  margin-top: 30px;
}

.submitted-data h3 {
  margin-bottom: 15px;
  font-weight: bold;
  color: #303133;
}

.id-card-photos {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.photo-item, 
.license-photo {
  width: 300px;
}

.photo-item p,
.license-photo p {
  margin-bottom: 10px;
  color: #606266;
}

.el-image {
  width: 100%;
  height: 180px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

:deep(.el-tag) {
  min-width: 60px;
  text-align: center;
}
</style>
