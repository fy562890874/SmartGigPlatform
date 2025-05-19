<template>
  <div class="home-view">
    <!-- Header Section with Dynamic Navigation -->
    <el-header class="home-header" height="60px">
      <div class="logo-container" @click="navigateTo('home')">
        <!-- <img src="@/assets/logo.png" alt="Platform Logo" class="logo-img" /> -->
        <span class="platform-name">智慧零工平台</span>
      </div>
      <el-menu mode="horizontal" :ellipsis="false" class="header-menu">
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

    <!-- Hero Section -->
    <section class="hero-section">
      <el-carousel height="350px" :interval="5000" arrow="always">
        <el-carousel-item v-for="item in heroBanners" :key="item.id">
          <div class="hero-banner-item" :style="`background-image: url(${item.imageUrl})`">
            <div class="hero-content">
              <h2>{{ item.title }}</h2>
              <p>{{ item.subtitle }}</p>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
      <div class="hero-search-bar">
        <el-input
          v-model="searchQuery.keyword"
          placeholder="搜索职位、技能、或服务..."
          size="large"
          class="search-input"
          clearable
        >
          <template #prepend>
            <el-select v-model="searchQuery.category" placeholder="职位类别" style="width: 150px;" filterable>
              <el-option label="全部类别" value=""></el-option>
              <el-option v-for="cat in jobCategoriesForSearch" :key="cat.value" :label="cat.label" :value="cat.value"></el-option>
            </el-select>
          </template>
          <template #append>
            <el-button type="primary" :icon="Search" @click="performSearch" :loading="searching">搜索</el-button>
          </template>
        </el-input>
      </div>
    </section>

    <!-- Quick Entries / Main Actions Section -->
    <section class="main-actions-section page-container">
      <el-row :gutter="20" justify="center">
        <template v-if="!authStore.isLoggedIn">
          <el-col :xs="24" :sm="12" :md="8">
            <el-card shadow="hover" class="action-card" @click="navigateTo('jobs')">
              <el-icon :size="40" color="#409EFF"><Briefcase /></el-icon>
              <h3>寻找工作机会</h3>
              <p>浏览最新的零工、兼职和项目机会。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-card shadow="hover" class="action-card" @click="navigateTo('register')">
               <el-icon :size="40" color="#67C23A"><User /></el-icon>
              <h3>成为零工达人</h3>
              <p>注册您的技能，开始承接项目。</p>
            </el-card>
          </el-col>
           <el-col :xs="24" :sm="12" :md="8">
            <el-card shadow="hover" class="action-card" @click="navigateTo('register')">
               <el-icon :size="40" color="#E6A23C"><OfficeBuilding /></el-icon>
              <h3>发布用工需求</h3>
              <p>快速找到合适的专业人才完成您的工作。</p>
            </el-card>
          </el-col>
        </template>
        <template v-else-if="authStore.user?.current_role === 'freelancer'">
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateTo('jobs')">
              <el-icon :size="40"><Briefcase /></el-icon>
              <h3>发现新工作</h3>
              <p>根据您的技能和偏好寻找项目。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateTo('my-applications')">
              <el-icon :size="40"><Document /></el-icon>
              <h3>我的申请</h3>
              <p>跟踪您的工作申请状态。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateTo('edit-freelancer-profile')">
              <el-icon :size="40"><Setting /></el-icon>
              <h3>完善我的档案</h3>
              <p>更新信息，吸引更多雇主。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateTo('manage-freelancer-skills')">
              <el-icon :size="40"><Star /></el-icon>
              <h3>管理我的技能</h3>
              <p>展示您的专业技能和经验。</p>
            </el-card>
          </el-col>
        </template>
        <template v-else-if="authStore.user?.current_role === 'employer'">
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateTo('post-job')">
              <el-icon :size="40"><Plus /></el-icon>
              <h3>发布新工作</h3>
              <p>快速发布您的用工需求。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateTo('my-posted-jobs')">
              <el-icon :size="40"><List /></el-icon>
              <h3>管理已发布</h3>
              <p>查看和管理您的招聘信息。</p>
            </el-card>
          </el-col>
           <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateTo('edit-employer-profile')">
              <el-icon :size="40"><OfficeBuilding /></el-icon>
              <h3>完善企业信息</h3>
              <p>提升信誉，吸引优秀人才。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="action-card" @click="navigateToJobApplicantsDefault()">
              <el-icon :size="40"><Comment /></el-icon>
              <h3>查看应聘者</h3>
              <p>管理您收到的工作申请。</p>
            </el-card>
          </el-col>
        </template>
      </el-row>
    </section>

    <!-- Featured Jobs Section -->
    <section class="featured-jobs-section page-container">
      <h2 class="section-title">热门职位推荐</h2>
      <div v-if="loadingFeaturedJobs" class="loading-placeholder">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="featuredJobs.length === 0 && !loadingFeaturedJobs" class="empty-state">
        <el-empty description="暂无推荐职位" />
      </div>
      <el-row v-else :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" v-for="job in featuredJobs" :key="job.id">
          <JobCard :job="job" @click="viewJobDetail(String(job.id))" />
        </el-col>
      </el-row>
      <div class="view-all-jobs" v-if="featuredJobs.length > 0">
        <el-button type="primary" plain @click="navigateTo('jobs')">查看所有职位 <el-icon class="el-icon--right"><Right /></el-icon></el-button>
      </div>
    </section>

    <!-- Platform Advantages Section -->
    <section class="platform-advantages-section">
      <div class="page-container">
        <h2 class="section-title">平台核心优势</h2>
        <el-row :gutter="30" justify="center">
          <el-col :xs="24" :sm="12" :md="6" v-for="advantage in platformAdvantages" :key="advantage.title">
            <div class="advantage-item">
              <el-icon :size="50" :color="advantage.color || '#409EFF'"><component :is="advantage.icon" /></el-icon>
              <h3>{{ advantage.title }}</h3>
              <p>{{ advantage.description }}</p>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- Popular Categories Section -->
    <section class="popular-categories-section page-container">
      <h2 class="section-title">热门技能与行业</h2>
      <div class="categories-tags">
        <el-tag
          v-for="category in popularJobCategories"
          :key="category.name"
          effect="plain"
          size="large"
          class="category-tag"
          @click="searchByCategory(category.value)"
          round
        >
          {{ category.name }}
        </el-tag>
      </div>
    </section>

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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/apiClient'
import { getPaginatedData } from '@/utils/http'
import JobCard from '@/components/JobCard.vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import {
  Search, Briefcase, User, Plus, Document, Promotion, Platform, Setting, TrendCharts, MessageBox, DataAnalysis,
  OfficeBuilding, ArrowDown, House, Star, SwitchButton, List, CircleCheck, Comment, Right, UserFilled, Medal,
  CollectionTag, Pointer, Service
} from '@element-plus/icons-vue'

// Interface for Job (ensure it matches your API response for jobs)
interface Job {
  id: number | string;
  title: string;
  description: string;
  job_category: string;
  job_tags?: string[];
  location_address: string;
  location_province?: string;
  location_city?: string;
  location_district?: string;
  salary_amount: number;
  salary_type: 'hourly' | 'daily' | 'weekly' | 'monthly' | 'fixed' | 'negotiable';
  salary_negotiable?: boolean;
  required_people: number;
  skill_requirements?: string;
  is_urgent?: boolean;
  application_deadline?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
  employer_info?: { name: string; avatar_url?: string };
  company_name_display?: string;
  salary_range_display?: string;
  [key: string]: any;
}

const router = useRouter()
const authStore = useAuthStore()

const searchQuery = ref({
  keyword: '',
  category: '',
})
const searching = ref(false)

const heroBanners = ref([
  { id: 1, title: '政府主导，精准匹配', subtitle: '打造您理想的灵活就业平台', imageUrl: 'https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1600&q=80' },
  { id: 2, title: '海量职位，等你发现', subtitle: '快速找到心仪的零工与项目', imageUrl: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1600&q=80' },
  { id: 3, title: '专业技能，大展宏图', subtitle: '让您的才华在这里发光发热', imageUrl: 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1600&q=80' },
])

// Simplified job categories for search dropdown, align with backend if possible
const jobCategoriesForSearch = ref([
  { label: '软件开发', value: 'software_development' },
  { label: '设计创意', value: 'design' },
  { label: '市场营销', value: 'marketing' },
  { label: '写作翻译', value: 'writing' },
  { label: '行政客服', value: 'customer_service' },
  { label: '家政服务', value: 'domestic_services' },
  { label: '餐饮服务', value: 'food_service' },
  { label: '物流配送', value: 'logistics' },
  { label: '零售百货', value: 'retail' },
  { label: '教育培训', value: 'education' },
  { label: '其他类别', value: 'others' },
])

const performSearch = () => {
  searching.value = true
  router.push({
    name: 'jobs', // Assuming 'jobs' is the route name for your job listing page
    query: {
      q: searchQuery.value.keyword,
      job_category: searchQuery.value.category,
    }
  }).finally(() => {
    searching.value = false
  })
}

const userAvatar = computed(() => {
  // 增加更多防御性检查，处理多种可能的用户数据结构
  if (!authStore.user) return '';
  
  // 使用类型断言来处理可能的不同用户对象结构
  const user = authStore.user as any;
  
  // 尝试从多种可能的路径获取头像URL
  const avatarUrl = user.avatar_url || 
                   (user.profile && user.profile.avatar_url) || 
                   '';
  
  console.log('用户头像URL:', avatarUrl);
  return avatarUrl;
})

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
      router.push({ name: 'my-verifications' }); // Or 'submit-verification' if preferred
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

const featuredJobs = ref<Job[]>([])
const loadingFeaturedJobs = ref(false)

const fetchFeaturedJobs = async () => {
  loadingFeaturedJobs.value = true;
  try {
    // 使用后端真正支持的查询参数
    const response = await apiClient.get('/jobs', { 
      params: { 
        per_page: 6,
        page: 1,
        sort_by: 'created_at_desc', // 按创建时间倒序排列
        status: 'open', // 只获取开放状态的工作
        is_urgent: true // 可以优先显示紧急工作
      } 
    });
    const { items = [] } = getPaginatedData(response);
    featuredJobs.value = items as Job[];
  } catch (error) {
    console.error('获取热门工作失败:', error);
    featuredJobs.value = []; // 确保出错时设置为空数组
  } finally {
    loadingFeaturedJobs.value = false;
  }
}

const platformAdvantages = ref([
  { title: '政府指导 安心保障', description: '官方平台，信息权威，交易安全，权益有保障。', icon: Pointer, color: '#67C23A' },
  { title: '精准匹配 高效对接', description: '智能算法，快速匹配最合适的职位与人才。', icon: Pointer, color: '#409EFF' },
  { title: '灵活就业 多元选择', description: '海量短期、兼职、项目制工作，满足多样化需求。', icon: CollectionTag, color: '#E6A23C' },
  { title: '专业服务 全程支持', description: '提供职业指导、技能培训、纠纷协调等一站式服务。', icon: Service, color: '#F56C6C' },
])

// Use jobCategoriesForSearch or a more specific list for display
const popularJobCategories = ref([
  { name: '软件开发', value: 'software_development' },
  { name: 'UI/UX设计', value: 'design_creative' },
  { name: '内容营销', value: 'digital_marketing' },
  { name: '专业翻译', value: 'writing_translation' },
  { name: '在线客服', value: 'customer_service' },
  { name: '技能培训', value: 'education_training' },
  { name: '居家保洁', value: 'life_services' },
  { name: '健康顾问', value: 'health_care' },
])

const navigateTo = (routeName: string, params?: any) => {
  if (routeName) {
    router.push({ name: routeName, params: params })
  }
}

const viewJobDetail = (jobId: string) => {
  router.push({ name: 'job-detail', params: { id: jobId } })
}

const searchByCategory = (categoryValue: string) => {
  router.push({ name: 'jobs', query: { job_category: categoryValue } })
}

const navigateToPrivacyPolicy = () => {
  // router.push({ name: 'privacy-policy' }); // If you have this route
  ElMessage.info('隐私政策页面待实现');
}
const navigateToTerms = () => {
  // router.push({ name: 'terms-of-service' }); // If you have this route
  ElMessage.info('服务条款页面待实现');
}

const navigateToJobApplicantsDefault = () => {
  // This should ideally navigate to a page listing jobs,
  // from where the employer can select a job to view its applicants.
  // Or, if there's a default/most recent job, navigate to its applicants.
  // For now, redirecting to "My Posted Jobs" as a placeholder.
  router.push({ name: 'my-posted-jobs' });
  ElMessage.info('请先选择一个职位以查看应聘者');
};


onMounted(() => {
  fetchFeaturedJobs()
  // Ensure authStore is initialized, especially if user info is fetched asynchronously
  if (authStore.token && !authStore.user) {
    authStore.getCurrentUser();
  }
})
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  background-color: #f4f6f8; /* Light background for the whole page */
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

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


/* Hero Section */
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


/* Main Actions Section */
.main-actions-section {
  padding-top: 40px; /* Adjusted due to hero search bar overlap */
  padding-bottom: 40px;
  text-align: center;
}

.action-card {
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 25px;
  height: 100%; /* Make cards in a row same height */
}

.action-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.15);
}

.action-card .el-icon {
  margin-bottom: 15px;
}

.action-card h3 {
  margin: 10px 0 8px;
  font-size: 1.3em;
  font-weight: 500;
  color: #303133;
}

.action-card p {
  font-size: 0.95em;
  color: #606266;
  line-height: 1.5;
}

/* Common Section Title */
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


/* Featured Jobs Section */
.featured-jobs-section {
  padding: 40px 0;
}
.view-all-jobs {
  margin-top: 30px;
  text-align: center;
}

/* Platform Advantages Section */
.platform-advantages-section {
  background-color: #ffffff; /* White background for contrast */
  padding: 60px 0;
}
.advantage-item {
  text-align: center;
  padding: 25px;
}
.advantage-item h3 {
  margin: 18px 0 10px;
  font-size: 1.4em;
  font-weight: 500;
}
.advantage-item p {
  font-size: 1em;
  color: #555;
  line-height: 1.6;
}

/* Popular Categories Section */
.popular-categories-section {
  padding: 40px 0 60px;
}
.categories-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 15px;
}
.category-tag {
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 18px 25px; /* Larger tags */
  font-size: 1.05em;
}
.category-tag:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

/* Footer */
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

.loading-placeholder, .empty-state {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
