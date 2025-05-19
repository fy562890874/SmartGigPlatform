<!--
  @file JobsView.vue
  @description 零工工作广场页面，展示可筛选和搜索的工作列表。
  @author Fy
  @date 2025-05-18
  @routePath '/jobs'
  @relatedRoutes '/job/:id' (工作详情), '/' (首页)
-->
<template>
  <DefaultHeader />
  <div class="jobs-view page-container">
    <!-- 搜索与筛选区 -->
    <el-card class="search-filter-bar section-card" shadow="never">
      <el-form :model="filters" inline @submit.prevent="applyFilters">
        <el-row :gutter="16" style="width: 100%">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="关键词">
              <el-input v-model="filters.keyword" placeholder="职位名称, 公司..." clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="5">
            <el-form-item label="分类">
              <el-select v-model="filters.category" placeholder="所有分类" clearable>
                <el-option v-for="cat in categories" :key="cat.value" :label="cat.label" :value="cat.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="5">
            <el-form-item label="状态">
              <el-select v-model="filters.status" placeholder="所有状态" clearable>
                <el-option v-for="stat in statuses" :key="stat.value" :label="stat.label" :value="stat.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4">
            <el-form-item label="紧急">
              <el-checkbox v-model="filters.is_urgent" label="仅看紧急" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="4">
            <el-form-item>
              <el-button type="primary" @click="applyFilters" :icon="SearchIcon">搜索</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 排序与视图切换 -->
    <div class="list-controls">
      <el-select v-model="filters.sortOption" placeholder="排序方式" @change="applyFilters" style="width: 200px;">
        <el-option label="最新发布" value="created_at_desc" />
        <el-option label="最早发布" value="created_at_asc" />
        <el-option label="薪资 (高-低)" value="salary_max_desc" />
        <el-option label="薪资 (低-高)" value="salary_min_asc" />
      </el-select>
      <!-- Placeholder for view toggle if needed -->
    </div>

    <!-- 工作列表 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>
    <div v-else-if="error" class="error-container">
      <el-alert :title="error || '加载失败'" type="error" show-icon :closable="false" />
    </div>
    <div v-else-if="jobs.length === 0" class="empty-container">
      <el-empty description="未找到相关零工信息" />
    </div>
    <el-row :gutter="16" v-else>
      <el-col :xs="24" :sm="12" :md="8" v-for="job in jobs" :key="job.id">
        <el-card class="job-card" shadow="hover" @click="navigateToJobDetail(job.id)">
          <template #header>
            <div class="job-card-header">
              <span class="job-title">{{ job.title }}</span>
              <el-tag v-if="job.is_urgent" type="danger" size="small">紧急</el-tag>
            </div>
          </template>
          <div class="job-card-body">
            <p v-if="job.employer_info?.name" class="job-company">
              <el-icon><OfficeBuilding /></el-icon> {{ job.employer_info.name }}
            </p>
            <p v-if="job.location_address" class="job-location">
              <el-icon><Location /></el-icon> {{ job.location_address }}
            </p>
            <p v-if="job.salary_min && job.salary_max" class="job-salary">
              <el-icon><Money /></el-icon> ¥{{ job.salary_min }} - ¥{{ job.salary_max }} {{ job.salary_type ? '(' + job.salary_type + ')' : '' }}
            </p>
            <p v-else-if="job.salary_min" class="job-salary">
              <el-icon><Money /></el-icon> ¥{{ job.salary_min }} {{ job.salary_type ? '(' + job.salary_type + ')' : '' }}
            </p>
             <p v-if="job.work_type" class="job-attribute">
              <el-icon><Briefcase /></el-icon> {{ job.work_type }}
            </p>
            <p v-if="job.category_details?.name" class="job-attribute">
              {/* This class is intentionally kept for styling consistency, even if empty at times */}
              <el-icon><CollectionTag /></el-icon> {{ job.category_details.name }}
            </p>
            <el-tag v-if="job.status" :type="jobStatusTagType(job.status)" size="small" effect="light" class="job-status-tag">
              {{ job.status }}
            </el-tag>
          </div>
          <template #footer>
            <div class="job-card-footer">
              <span class="job-date">发布于: {{ formatDate(job.created_at) }}</span>
              <el-button type="primary" plain size="small" @click.stop="navigateToJobDetail(job.id)">查看详情</el-button>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页 -->
    <div v-if="!loading && jobs.length > 0 && pagination.total_pages > 1" class="pagination-container">
      <el-pagination
        background
        layout="prev, pager, next, jumper, ->, total"
        :total="pagination.total_items"
        :page-size="pagination.per_page"
        :current-page="pagination.page"
        @current-change="handlePageChange"
      />
    </div>
  </div>
  <DefaultFooter />
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '@/utils/apiClient';
import { ElMessage, ElCard, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElCheckbox, ElButton, ElRow, ElCol, ElTag, ElPagination, ElSkeleton, ElAlert, ElEmpty, ElIcon } from 'element-plus';
import { Search as SearchIcon, Location, Money, OfficeBuilding, Briefcase, CollectionTag } from '@element-plus/icons-vue';
import DefaultHeader from '@/components/common/DefaultHeader.vue';
import DefaultFooter from '@/components/common/DefaultFooter.vue';

// Inline Type Definitions based on backend API (job_api.py)
interface GeoPoint {
  type: string;
  coordinates: [number, number]; // [longitude, latitude]
}

interface EmployerInfo { // Assuming this might be part of Job or fetched separately
  name: string;
  // Add other employer-related fields if available/needed
}

interface CategoryInfo { // For job category details
  id: number;
  name: string;
  // Add other category-related fields if available/needed
}

interface Job {
  id: number;
  employer_user_id: number;
  title: string;
  description: string;
  job_category: string; // This might be a slug or ID, map to CategoryInfo if needed
  job_tags?: string[];
  location_address: string;
  location_province?: string;
  location_city?: string;
  location_district?: string;
  location_point?: GeoPoint;
  start_time: string; // ISO 8601 datetime string
  end_time: string;   // ISO 8601 datetime string
  salary_amount: number; // Assuming this is the primary salary figure
  salary_min?: number; // For ranges, if applicable
  salary_max?: number; // For ranges, if applicable
  salary_type: 'hourly' | 'daily' | 'weekly' | 'monthly' | 'fixed' | 'negotiable';
  salary_negotiable?: boolean;
  required_people: number;
  accepted_people?: number;
  skill_requirements?: string;
  is_urgent?: boolean;
  status?: string; 
  cancellation_reason?: string;
  view_count?: number;
  application_deadline?: string; // ISO 8601 datetime string
  created_at: string;  // ISO 8601 datetime string
  updated_at: string;  // ISO 8601 datetime string
  employer_info?: EmployerInfo; // Optional: if backend includes this in job list
  category_details?: CategoryInfo; // Optional: if backend includes this
  work_type?: string; // Example: 'remote', 'on-site'
}

interface Pagination {
  page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
}

interface PaginatedJobsResponse {
  items: Job[];
  pagination: Pagination;
  // Potentially other metadata like applied_filters, etc.
}

const router = useRouter();

const jobs = ref<Job[]>([]);
const pagination = ref<Pagination>({
  page: 1,
  per_page: 9,
  total_items: 0,
  total_pages: 0,
});

const filters = reactive({
  keyword: '',
  category: '' as string | number, // Allow number if category IDs are numeric
  status: 'open',
  is_urgent: false as boolean, // Initialize as boolean, not null
  sortOption: 'created_at_desc',
});

const loading = ref(true);
const error = ref<string | null>(null);

const categories = ref<{label: string, value: string | number}[]>([
  { label: '技术', value: 'tech' }, // Assuming backend uses string slugs or IDs
  { label: '设计', value: 'design' },
  { label: '写作', value: 'writing' },
  { label: '市场', value: 'marketing' },
  { label: '客服', value: 'customer_service' },
  // If backend sends categories, populate this dynamically
]);
const statuses = ref([
  { label: '开放中', value: 'open' },
  { label: '已关闭', value: 'closed' },
  { label: '已招满', value: 'filled' },
  { label: '审核中', value: 'pending_approval' },
]);

const fetchJobs = async () => {
  loading.value = true;
  error.value = null;
  try {
    const [sortBy, sortOrder] = filters.sortOption.split('_');

    const params: Record<string, any> = {
      page: pagination.value.page,
      per_page: pagination.value.per_page,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
    if (filters.keyword) params.q = filters.keyword; // Map 'keyword' to 'q'
    if (filters.category) params.job_category = filters.category; // Map 'category' to 'job_category'
    if (filters.status) params.status = filters.status;
    if (filters.is_urgent === true) params.is_urgent = true;

    const response = await apiClient.get<PaginatedJobsResponse>('/jobs/', { params });
    jobs.value = response.data.items;
    if (response.data.pagination) {
      pagination.value = {
        ...response.data.pagination,
        per_page: response.data.pagination.per_page || pagination.value.per_page,
      };
    } else {
      pagination.value.total_items = response.data.items.length;
      pagination.value.total_pages = Math.ceil(pagination.value.total_items / pagination.value.per_page);
    }
  } catch (err: any) {
    console.error('Failed to fetch jobs:', err);
    const errorMessage = err.response?.data?.message || err.message || '获取工作列表失败，请稍后再试。';
    error.value = errorMessage;
    if (errorMessage) ElMessage.error(errorMessage);
    jobs.value = [];
    pagination.value = { page: 1, per_page: 9, total_items: 0, total_pages: 0 };
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (newPage: number) => {
  pagination.value.page = newPage;
  fetchJobs();
};

const applyFilters = () => {
  pagination.value.page = 1;
  fetchJobs();
};

const navigateToJobDetail = (jobId: number) => {
  router.push({ name: 'JobDetail', params: { id: jobId } });
};

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString();
};

const jobStatusTagType = (status: string): 'success' | 'warning' | 'info' | 'primary' | 'danger' => {
  switch (status?.toLowerCase()) {
    case 'open': return 'success';
    case 'closed': return 'info';
    case 'filled': return 'warning';
    case 'pending_approval': return 'primary';
    default: return 'info'; 
  }
};

onMounted(() => {
  fetchJobs();
});

</script>

<style scoped lang="scss">
.jobs-view {
  padding-top: 20px;
  padding-bottom: 40px;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding-left: 15px;
  padding-right: 15px;
}

.section-card {
  margin-bottom: 20px;
  border: none; 
  border-radius: 8px;
}

.search-filter-bar .el-form-item {
  margin-bottom: 0; 
}

.list-controls {
  display: flex;
  justify-content: flex-end; 
  align-items: center;
  margin-bottom: 20px;
}

.job-card {
  margin-bottom: 16px;
  border-radius: 8px;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  cursor: pointer;
}

.job-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.job-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.job-title {
  font-size: 1.1rem;
  font-weight: bold;
  color: #303133;
}

.job-card-body p {
  margin: 8px 0;
  font-size: 0.9rem;
  color: #606266;
  display: flex;
  align-items: center;
}

.job-card-body .el-icon {
  margin-right: 6px;
  color: #909399;
}

.job-company {
  font-weight: 500;
}

.job-salary {
  color: #E6A23C; 
  font-weight: 500;
}

.job-attribute {
  /* This class is used for job attributes like work_type and category. */
  /* It might appear empty in some cases if data is not present, but the class is kept for styling consistency. */
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  font-size: 0.9rem;
  margin-bottom: 6px;
}

.job-status-tag {
  margin-top: 8px;
}

.job-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: #909399;
}

.loading-container, .error-container, .empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px; 
  padding: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .search-filter-bar .el-form-item {
    width: 100%;
    margin-bottom: 10px; 
  }
  .search-filter-bar .el-col {
    margin-bottom: 0; 
  }
  .list-controls {
    flex-direction: column;
    align-items: stretch;
  }
  .list-controls .el-select {
    width: 100% !important;
    margin-bottom: 10px;
  }
}
</style>
