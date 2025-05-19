<!--
  @file JobsView.vue
  @description 零工工作广场页面，展示可筛选和搜索的工作列表。
  @author Fy
  @date 2025-05-18
  @routePath '/jobs'
  @relatedRoutes '/job/:id' (工作详情), '/' (首页)
-->
<template>
  <div class="jobs-view">
    <!-- Header Section with Dynamic Navigation - Based on HomeView -->
    <el-header class="home-header" height="60px">
      <div class="logo-container" @click="navigateTo('home')">
        <!-- <img src="@/assets/logo.png" alt="Platform Logo" class="logo-img" /> -->
        <span class="platform-name">智慧零工平台</span>
      </div>
      <el-menu mode="horizontal" :ellipsis="false" class="header-menu" :default-active="'jobs'">
        <el-menu-item index="jobs" @click="navigateTo('jobs')">浏览工作</el-menu-item>
        <el-menu-item index="skills" @click="navigateTo('skills')">技能广场</el-menu-item>
        <el-menu-item index="about" @click="navigateTo('about')">关于我们</el-menu-item>
        <el-menu-item index="help" @click="navigateTo('help')">帮助中心</el-menu-item>
      </el-menu>
      <div class="auth-actions">
        <template v-if="!authStore.isLoggedIn">
          <el-button type="primary" plain @click="navigateTo('login')">登录</el-button>
          <el-button type="danger" @click="navigateTo('register')">免费注册</el-button>
        </template>
        <template v-else>
          <el-dropdown @command="handleUserCommand">
            <span class="el-dropdown-link">
              <el-avatar :size="30" :src="userAvatar" :icon="UserFilled" style="margin-right: 8px;"></el-avatar>
              {{ authStore.user?.nickname || authStore.user?.phone_number }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="dashboard">
                  <el-icon><House /></el-icon>我的工作台
                </el-dropdown-item>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人资料
                </el-dropdown-item>
                <el-dropdown-item command="orders" v-if="authStore.isLoggedIn">
                  <el-icon><List /></el-icon>我的订单
                </el-dropdown-item>
                <el-dropdown-item command="verification" v-if="authStore.isLoggedIn">
                  <el-icon><CircleCheck /></el-icon>我的认证
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>账号设置
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </div>
    </el-header>

    <!-- Hero Section for Jobs - Modified from HomeView -->
    <section class="hero-section">
      <div class="hero-banner-item" style="background-image: url('https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1600&q=80')">
        <div class="hero-content">
          <h2>寻找您理想的工作机会</h2>
          <p>智慧零工平台精准匹配您的技能与需求</p>
        </div>
      </div>
      <!-- 搜索与筛选区 - Moved inside hero banner -->
      <div class="hero-search-bar">
        <el-form :model="filters" @submit.prevent="applyFilters" class="search-filter-form">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索职位名称、公司..."
            size="large"
            class="search-input"
            clearable
          >
            <template #prepend>
              <el-select v-model="filters.category" placeholder="职位类别" style="width: 150px;" filterable>
                <el-option label="全部类别" value=""></el-option>
                <el-option v-for="cat in categories" :key="cat.value" :label="cat.label" :value="cat.value"></el-option>
              </el-select>
            </template>
            <template #append>
              <el-button type="primary" :icon="SearchIcon" @click="applyFilters" :loading="loading">搜索</el-button>
            </template>
          </el-input>
        </el-form>
      </div>
    </section>

    <div class="page-container">
      <!-- Advanced Filters Section -->
      <el-card class="search-filter-bar section-card" shadow="never">
        <el-form :model="filters" inline @submit.prevent="applyFilters">
          <el-row :gutter="16" style="width: 100%">
            <el-col :xs="24" :sm="12" :md="8">
              <el-form-item label="状态">
                <el-select v-model="filters.status" placeholder="所有状态" clearable>
                  <el-option v-for="stat in statuses" :key="stat.value" :label="stat.label" :value="stat.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="8">
              <el-form-item label="紧急">
                <el-checkbox v-model="filters.is_urgent" label="仅看紧急" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="8">
              <el-form-item label="排序">
                <el-select v-model="filters.sortOption" placeholder="排序方式" @change="applyFilters" style="width: 100%;">
                  <el-option label="最新发布" value="created_at_desc" />
                  <el-option label="最早发布" value="created_at_asc" />
                  <el-option label="薪资 (高-低)" value="salary_max_desc" />
                  <el-option label="薪资 (低-高)" value="salary_min_asc" />
                </el-select>
              </el-form-item>
            </el-col>      </el-row>
        </el-form>
      </el-card>

    <!-- 工作列表标题 -->
    <h2 class="section-title">可用工作机会</h2>

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
    <div v-if="!loading && jobs.length > 0 && pagination.total_pages > 1" class="pagination-container">      <el-pagination
        background
        layout="prev, pager, next, jumper, ->, total"
        :total="pagination.total_items"
        :page-size="pagination.per_page"
        :current-page="pagination.page"
        @current-change="handlePageChange"
      />
    </div>  </div>
  
  <el-footer class="home-footer">
    <p>&copy; {{ new Date().getFullYear() }} 智慧零工平台. All rights reserved.</p>
    <p>
      <el-link @click="navigateTo('about')">关于我们</el-link> |
      <el-link @click="navigateTo('help')">帮助中心</el-link> |
      <el-link @click="navigateToPrivacyPolicy">隐私政策</el-link> |
      <el-link @click="navigateToTerms">服务条款</el-link>
    </p>
  </el-footer>
</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElCard, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElCheckbox, ElButton, ElRow, ElCol, ElTag, ElPagination, ElSkeleton, ElAlert, ElEmpty, ElIcon, ElMessage, ElMessageBox } from 'element-plus';
import { Search as SearchIcon, Location, Money, OfficeBuilding, Briefcase, CollectionTag, User, Setting, SwitchButton, List, CircleCheck, House, ArrowDown, UserFilled } from '@element-plus/icons-vue';
import apiClient from '@/utils/apiClient';
import { getPaginatedData } from '@/utils/http';
import { useAuthStore } from '@/stores/auth';

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
  page: number; // Added page here
  per_page: number;
  total_items: number;
  total_pages: number;
}

// Removed unused interface PaginatedJobsResponse

const router = useRouter();
const authStore = useAuthStore();

const jobs = ref<Job[]>([]);
const pagination = ref<Pagination>({
  page: 1, // Initialize page
  per_page: 9,
  total_items: 0,
  total_pages: 0,
});

// 用户头像计算属性 - 从HomeView.vue中引入
const userAvatar = computed(() => {
  // 增加更多防御性检查，处理多种可能的用户数据结构
  if (!authStore.user) return '';
  
  // 使用类型断言来处理可能的不同用户对象结构
  const user = authStore.user as any;
  
  // 尝试从多种可能的路径获取头像URL
  const avatarUrl = user.avatar_url || 
                   (user.profile && user.profile.avatar_url) || 
                   '';
  
  return avatarUrl;
});

const filters = reactive<{
  keyword: string;
  category: string | number;
  status: string;
  is_urgent: boolean;
  sortOption: string;
  page: number;
  per_page: number;
  [key: string]: string | number | boolean; 
}>({
  keyword: '',
  category: '',
  status: '', // 默认值为空，避免限制查询
  is_urgent: false, // 默认值为 false
  sortOption: '', // 默认值为空，避免限制查询
  page: 1,
  per_page: 9,
});

const loading = ref(true);
const error = ref<string | null>(null); // Declare error ref

const categories = ref<{label: string, value: string | number}[]>([
  { label: '技术', value: 'tech' }, // Assuming backend uses string slugs or IDs
  { label: '设计', value: 'design' },
  { label: '写作', value: 'writing' },
  { label: '市场', value: 'marketing' },
  { label: '客服', value: 'customer_service' },
  // If backend sends categories, populate this dynamically
]);
const statuses = ref<{
  label: string,
  value: string | number
}[]>([
  { label: '开放中', value: 'active' }, // 修改: 'open' -> 'active'
  { label: '已关闭', value: 'closed' },
  { label: '已招满', value: 'filled' },
  { label: '审核中', value: 'pending_approval' }
]);

const fetchJobs = async () => {
  loading.value = true;
  error.value = null;
  try {
    // 构造 API 参数，移除空值参数
    const apiParams = Object.fromEntries(
      Object.entries({
        page: filters.page,
        per_page: filters.per_page,
        q: filters.keyword || undefined, // 移除空值
        job_category: filters.category || undefined, // 移除空值
        status: filters.status || undefined, // 移除空值
        is_urgent: filters.is_urgent || undefined, // 移除空值
        sort_by: filters.sortOption || undefined // 移除空值
      }).filter(([_, value]) => value !== undefined)
    );

    const response = await apiClient.get('/jobs', { params: apiParams });
    const { items = [], pagination: paginationData = {} as Pagination } = getPaginatedData<Job>(response);

    jobs.value = items;
    pagination.value = {
      page: paginationData.page || 1,
      per_page: paginationData.per_page || 9,
      total_items: paginationData.total_items || 0,
      total_pages: paginationData.total_pages || 0
    };
  } catch (err: any) {
    console.error('获取工作列表失败:', err);
    error.value = '获取工作列表失败，请稍后再试';
    jobs.value = [];
    pagination.value = { page: 1, per_page: 9, total_items: 0, total_pages: 0 };
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (newPage: number) => {
  filters.page = newPage; // Update page in filters as well
  // pagination.value.page = newPage; // This will be set by filters.page in fetchJobs
  fetchJobs();
};

const applyFilters = () => {
  filters.page = 1; // Reset to first page on new filter application
  // pagination.value.page = 1; // This will be set by filters.page in fetchJobs
  fetchJobs();
};

const navigateToJobDetail = (jobId: number) => {
  router.push({ name: 'job-detail', params: { id: jobId } });
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

// 处理用户下拉菜单命令 - 从HomeView.vue中引入
const handleUserCommand = (command: string) => {
  switch (command) {
    case 'dashboard':
      if (authStore.user?.current_role === 'freelancer') {
        router.push({ name: 'freelancer-dashboard' })
      } else if (authStore.user?.current_role === 'employer') {
        router.push({ name: 'employer-dashboard' })
      } else {
        router.push('/') // Fallback
      }
      break
    case 'profile':
      if (authStore.user?.current_role === 'freelancer') {
        router.push({ name: 'edit-freelancer-profile' })
      } else if (authStore.user?.current_role === 'employer') {
        router.push({ name: 'edit-employer-profile' })
      }
      break
    case 'orders':
      router.push({ name: 'my-orders' });
      break;
    case 'verification':
      router.push({ name: 'my-verifications' });
      break;
    case 'settings':
      router.push({ name: 'settings' }) // General settings page
      break
    case 'logout':
      ElMessageBox.confirm('您确定要退出登录吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }).then(() => {
        authStore.logout()
        ElMessage.success('已成功退出登录')
        router.push('/') // Or to login page: router.push({ name: 'login' })
      }).catch(() => {
        // User cancelled
      })
      break
  }
}

// 通用导航函数 - 从HomeView.vue中引入
const navigateTo = (routeName: string, params?: any) => {
  if (routeName) {
    router.push({ name: routeName, params: params })
  }
}

// 页脚导航函数 - 从HomeView.vue中引入
const navigateToPrivacyPolicy = () => {
  // router.push({ name: 'privacy-policy' }); // If you have this route
  ElMessage.info('隐私政策页面待实现');
}

const navigateToTerms = () => {
  // router.push({ name: 'terms-of-service' }); // If you have this route
  ElMessage.info('服务条款页面待实现');
}

onMounted(() => {
  fetchJobs();
  // Ensure authStore is initialized, especially if user info is fetched asynchronously
  if (authStore.token && !authStore.user) {
    authStore.getCurrentUser();
  }
});

</script>

<style scoped>
.jobs-view {
  display: flex;
  flex-direction: column;
  background-color: #f4f6f8; /* Light background for the whole page */
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Header Styling from HomeView */
.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.logo-container {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.logo-img {
  height: 40px; /* Adjust as needed */
  margin-right: 10px;
}

.platform-name {
  font-size: 1.5em;
  font-weight: bold;
  color: var(--el-color-primary);
}

.header-menu {
  border-bottom: none; /* Remove default border from el-menu */
  flex-grow: 1;
  margin-left: 30px;
}

.header-menu .el-menu-item {
  font-size: 1em;
}

.header-menu .el-menu-item:hover {
  color: var(--el-color-primary-light-3);
}

.auth-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.el-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: var(--el-color-primary);
}

.el-dropdown-link:hover {
  color: var(--el-color-primary-light-3);
}

/* Hero Section from HomeView */
.hero-section {
  position: relative;
  width: 100%;
  margin-bottom: 60px; /* Space for overlapping search bar */
}

.hero-banner-item {
  width: 100%;
  height: 350px;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  text-align: center;
}

.hero-banner-item .hero-content {
  background-color: rgba(0, 0, 0, 0.55);
  padding: 25px 45px;
  border-radius: 10px;
  max-width: 80%;
}

.hero-banner-item h2 {
  font-size: 2.8em;
  margin-bottom: 15px;
  font-weight: 600;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
}

.hero-banner-item p {
  font-size: 1.3em;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
}

.hero-search-bar {
  position: absolute;
  bottom: -40px; /* Overlap amount */
  left: 50%;
  transform: translateX(-50%);
  width: 75%;
  max-width: 900px;
  background-color: #fff;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
  z-index: 10;
}

.search-input .el-input-group__prepend .el-select .el-input__wrapper {
  box-shadow: none !important;
}

.search-input .el-input-group__prepend {
  background-color: transparent;
  border-right: none;
}

.search-input .el-input__wrapper {
  border-left: none;
}

.search-input .el-input-group__append {
   background-color: transparent;
}

/* Job cards and filters */
.section-card {
  margin-bottom: 20px;
  border: none; 
  border-radius: 8px;
  margin-top: 20px;
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
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
  height: 100%;
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

/* Section Title - Same as in HomeView */
.section-title {
  text-align: center;
  font-size: 2.2em;
  font-weight: 600;
  color: #303133;
  margin-bottom: 40px;
  position: relative;
  padding-bottom: 10px;
}
.section-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background-color: var(--el-color-primary);
  border-radius: 2px;
}

/* Footer - Remove if using DefaultFooter */
.home-footer {
  text-align: center;
  padding: 30px 20px;
  background-color: #303133;
  color: #a9a9a9;
  font-size: 0.9em;
}
.home-footer .el-link {
  color: #c0c4cc;
  margin: 0 8px;
}
.home-footer .el-link:hover {
  color: #ffffff;
}
.home-footer p {
  margin-bottom: 8px;
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
  .hero-search-bar {
    width: 90%;
    padding: 15px;
  }
  .hero-banner-item h2 {
    font-size: 2em;
  }
  .hero-banner-item p {
    font-size: 1em;
  }
}
</style>
