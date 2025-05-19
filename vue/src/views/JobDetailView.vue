<template>
  <DefaultHeader />
  <div class="job-detail-view page-container">
    <el-button @click="goBack" :icon="ArrowLeft" class="back-button">返回列表</el-button>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="8" animated />
    </div>

    <el-empty v-else-if="!job && !loading" description="工作详情未找到或加载失败" />

    <el-row :gutter="20" v-else-if="job">
      <el-col :md="16" :sm="24">
        <el-card class="job-main-info section-card" shadow="never">
          <template #header>
            <div class="job-title-header">
              <h1>{{ job.title }}</h1>
              <el-tag v-if="job.is_urgent" type="danger" effect="light" size="small">急聘</el-tag>
              <el-tag :type="statusTagType(job.status)" effect="light" size="small">{{ job.status }}</el-tag>
            </div>
          </template>

          <el-descriptions :column="2" border class="job-attributes">
            <el-descriptions-item label="薪资待遇">
              <span class="salary-amount">{{ job.salary_amount }}</span> {{ job.salary_type }}
              <el-tag v-if="job.salary_negotiable" size="small" type="info" style="margin-left: 8px;">可议</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="工作类别">{{ job.job_category }}</el-descriptions-item>
            <el-descriptions-item label="招聘人数">{{ job.required_people }}人</el-descriptions-item>
            <el-descriptions-item label="已接受">{{ job.accepted_people || 0 }}人</el-descriptions-item>
            <el-descriptions-item label="工作地点" :span="2">
              <el-icon><Location /></el-icon> {{ job.location_address }}
              <span v-if="job.location_province || job.location_city || job.location_district">
                ({{ job.location_province }} {{ job.location_city }} {{ job.location_district }})
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">
              <el-icon><Calendar /></el-icon> {{ formatDate(job.start_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="结束时间">
              <el-icon><Clock /></el-icon> {{ formatDate(job.end_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="报名截止" v-if="job.application_deadline">
              <el-icon><Pointer /></el-icon> {{ formatDate(job.application_deadline) }}
            </el-descriptions-item>
            <el-descriptions-item label="发布时间">
                {{ timeAgo(job.created_at) }}
            </el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">工作详情</el-divider>
          <div class="job-description" v-html="job.description"></div>

          <div v-if="job.skill_requirements" class="skill-requirements">
            <el-divider content-position="left">技能要求</el-divider>
            <p>{{ job.skill_requirements }}</p>
          </div>

          <div v-if="job.job_tags && job.job_tags.length > 0" class="job-tags-section">
            <el-divider content-position="left">工作标签</el-divider>
            <el-tag v-for="tag in job.job_tags" :key="tag" class="job-tag" type="info">{{ tag }}</el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :md="8" :sm="24">
        <el-card class="actions-card section-card" shadow="never">
          <template #header>
            <span>操作</span>
          </template>
          <div v-if="canApply">
            <el-button 
              type="primary" 
              @click="handleApplyJob" 
              :loading="applying || submittingApplication" 
              :disabled="hasApplied || !isJobOpenForApplication(job)"
              class="apply-button"
              size="large"
            >
              {{ hasApplied ? '已申请' : '立即申请' }}
            </el-button>
          </div>
          <div v-else-if="!authStore.isLoggedIn">
            <p>请<el-link type="primary" @click="redirectToLogin">登录</el-link>后申请。</p>
          </div>
           <div v-else-if="authStore.user?.current_role !== 'freelancer'">
            <p>仅零工角色可以申请工作。</p>
          </div>
          <div v-else-if="job && !isJobOpenForApplication(job)">
            <p>该工作已{{ job.status }}，无法申请。</p>
          </div>
          <el-button :icon="Share" @click="shareJob" class="share-button">分享工作</el-button>
          <!-- Add more actions like favorite, report etc. -->
        </el-card>

        <!-- Employer Info Card (Placeholder) -->
        <el-card class="employer-info-card section-card" shadow="never" v-if="job.employer_user_id">
            <template #header>
                <span>发布方信息</span>
            </template>
            <p>雇主ID: {{ job.employer_user_id }}</p>
            <!-- Fetch and display employer details here -->
            <el-button type="text">查看雇主主页</el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- Application Modal -->
    <el-dialog v-model="applyModalVisible" title="提交工作申请" width="500px" :before-close="() => applyModalVisible = false">
      <el-form :model="applicationForm" ref="applicationFormRef" label-position="top">
        <el-form-item label="申请留言 (可选)" prop="application_message">
          <el-input v-model="applicationForm.application_message" type="textarea" :rows="4" placeholder="可以向雇主简单介绍自己或表达申请意愿" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyModalVisible = false">取消</el-button>
        <el-button type="primary" @click="submitApplication" :loading="submittingApplication">确认提交</el-button>
      </template>
    </el-dialog>

  </div>
  <DefaultFooter />
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import { ElMessage, ElSkeleton, ElEmpty, ElCard, ElRow, ElCol, ElDescriptions, ElDescriptionsItem, ElTag, ElButton, ElIcon, ElDivider, ElDialog, ElForm, ElFormItem, ElInput, ElLink } from 'element-plus';
import { Location, Calendar, Clock, Pointer, Share, ArrowLeft } from '@element-plus/icons-vue';
import DefaultHeader from '@/components/common/DefaultHeader.vue';
import DefaultFooter from '@/components/common/DefaultFooter.vue';
import apiConfig from '@/utils/apiConfig';

// Inline Type Definitions based on backend API (job_api.py, job_application_api.py)
interface GeoPoint {
  type: string;
  coordinates: [number, number]; // [longitude, latitude]
}

interface Job {
  id: number;
  employer_user_id: number;
  title: string;
  description: string;
  job_category: string;
  job_tags?: string[];
  location_address: string;
  location_province?: string;
  location_city?: string;
  location_district?: string;
  location_point?: GeoPoint;
  start_time: string; // ISO 8601 datetime string
  end_time: string;   // ISO 8601 datetime string
  salary_amount: number;
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
}

interface JobApplicationCreationInput {
  application_message?: string;
}

interface JobApplicationOutput {
  id: number;
  job_id: number;
  freelancer_user_id: number;
  employer_user_id: number;
  application_message?: string;
  status: string;
  rejection_reason?: string;
  created_at: string;
  processed_at?: string;
}

interface CheckApplicationStatusResponse {
  has_applied: boolean;
  application_id?: number;
  application_status?: string;
}

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const job = ref<Job | null>(null);
const loading = ref(true);
const applying = ref(false); 
const hasApplied = ref(false); 

const applyModalVisible = ref(false);
const submittingApplication = ref(false);
const applicationForm = reactive<JobApplicationCreationInput>({
  application_message: '',
});
const applicationFormRef = ref<InstanceType<typeof ElForm>>();

const jobId = computed(() => {
  return Number(route.params.id);
});

const fetchJobDetails = async () => {
  if (!jobId.value || isNaN(jobId.value)) {
    ElMessage.error('无效的工作ID');
    loading.value = false;
    return;
  }
  loading.value = true;
  try {    // 使用 apiConfig.getApiUrl 构造 API 路径
    const response = await axios.get(apiConfig.getApiUrl(`/jobs/${jobId.value}`));
    if (response.data && response.data.code === 0) {
      job.value = response.data.data;
      job.value = response.data;
      // If employer_info or category_details are expected but not directly on Job from backend,
      // they would need to be handled here or the Job interface adjusted if API sends them.
      // For now, assuming job_output_model is directly used.
      if (authStore.isLoggedIn) {
        await checkApplicationStatus();
      }
    } else {
      job.value = null;
      ElMessage.error('未找到工作详情或API响应格式不正确。');
    }
  } catch (error: any) {
    console.error('获取工作详情失败:', error);
    job.value = null;
    // Error already handled by apiClient interceptor, but can add specific logic
    // ElMessage.error(error.message || '获取工作详情失败，请稍后再试。');
  } finally {
    loading.value = false;
  }
};

const checkApplicationStatus = async () => {
  if (!authStore.isLoggedIn || !job.value) return;
  applying.value = true; // This seems to be for UI state, not directly "applying"
  try {    // 使用 apiConfig.getApiUrl 构造 API 路径
    const token = authStore.token;
    const response = await axios.get(
      apiConfig.getApiUrl(`/job-applications/check`), 
      {
        headers: { Authorization: `Bearer ${token}` },
        params: { job_id: job.value.id }
      }
    );
    if (response.data && response.data.code === 0) {
      hasApplied.value = response.data.data.has_applied;
    }
  } catch (error) {
    console.error('检查申请状态失败:', error);
    // ElMessage.error('检查申请状态失败。'); // Error handled by interceptor
  } finally {
    applying.value = false;
  }
};

const isJobOpenForApplication = (currentJob: Job | null): boolean => {
  if (!currentJob) return false;
  const jobStatus = currentJob.status?.toLowerCase();
  return jobStatus !== 'closed' && jobStatus !== 'filled' && jobStatus !== 'cancelled';
};

const canApply = computed(() => {
  return authStore.isLoggedIn && 
         authStore.user?.current_role === 'freelancer' && 
         job.value && 
         isJobOpenForApplication(job.value);
});

const handleApplyJob = () => {
  if (!canApply.value) {
    if (!authStore.isLoggedIn) ElMessage.warning('请先登录');
    else if (authStore.user?.current_role !== 'freelancer') ElMessage.warning('仅零工用户可以申请');
    else if (job.value && !isJobOpenForApplication(job.value)) ElMessage.warning('该工作当前状态无法申请');
    else ElMessage.warning('无法申请该工作');
    return;
  }
  if (hasApplied.value) {
    ElMessage.info('您已经申请过该职位了');
    return;
  }
  applicationForm.application_message = ''; // Clear previous message
  applyModalVisible.value = true;
};

const submitApplication = async () => {
  if (!applicationFormRef.value) return;
  await applicationFormRef.value.validate(async (valid) => {
    if (valid && job.value) {
      submittingApplication.value = true;
      try {        // 使用 apiConfig.getApiUrl 构造 API 路径
        const token = authStore.token;
        const response = await axios.post(
          apiConfig.getApiUrl(`/job-applications/jobs/${job.value.id}/apply`), 
          applicationForm,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (response.data && response.data.code === 0) {
          ElMessage.success('申请已成功提交！');
          hasApplied.value = true; // Update status after successful application
          applyModalVisible.value = false;
        }
      } catch (error) {
        console.error('提交申请失败:', error);
        // ElMessage.error('提交申请失败，请重试。'); // Error handled by interceptor
      } finally {
        submittingApplication.value = false;
      }
    } else {
      ElMessage.warning('请填写必要的申请信息。');
    }
  });
};

const goBack = () => {
  router.push({ name: 'JobsView' }); 
};

const redirectToLogin = () => {
  router.push({ name: 'Login', query: { redirect: route.fullPath } });
};

const shareJob = () => {
  if (navigator.share && job.value) {
    navigator.share({
      title: job.value.title,
      text: `来看看这个工作：${job.value.title}`,
      url: window.location.href,
    })
    .then(() => console.log('Successful share'))
    .catch((error) => console.log('Error sharing', error));
  } else {
    navigator.clipboard.writeText(window.location.href)
      .then(() => ElMessage.success('链接已复制到剪贴板'))
      .catch(() => ElMessage.error('复制链接失败'));
  }
};

const statusTagType = (status?: string): 'success' | 'info' | 'warning' | 'danger' | 'primary' => {
  const s = status?.toLowerCase();
  if (s === 'open') return 'success';
  if (s === 'filled' || s === 'closed') return 'info';
  if (s === 'cancelled') return 'warning';
  return 'primary'; // Default for other statuses
};

const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '日期无效'; // Check for invalid date
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' , hour:'2-digit', minute: '2-digit'});
  } catch (e) {
    return '日期格式错误';
  }
};

const timeAgo = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '日期无效'; // Check for invalid date
    const now = new Date();
    const seconds = Math.round((now.getTime() - date.getTime()) / 1000);
    
    if (seconds < 0) return formatDate(dateString); // Future date, show formatted
    if (seconds < 60) return `${seconds} 秒前`;
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes} 分钟前`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.round(hours / 24);
    if (days < 30) return `${days} 天前`;
    return formatDate(dateString); 
  } catch (e) {
    return '日期格式错误';
  }
};

onMounted(() => {
  fetchJobDetails();
});

</script>

<style scoped lang="scss">
.job-detail-view {
  padding-top: 20px;
  padding-bottom: 40px;
  background-color: #f4f6f8;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.back-button {
  margin-bottom: 20px;
}

.section-card {
  margin-bottom: 20px;
  border: none;
  border-radius: 8px;
  background-color: #fff;
}

.job-main-info {
  .job-title-header {
    display: flex;
    align-items: center;
    h1 {
      margin-right: 10px;
      font-size: 1.8em;
      font-weight: 600;
      color: #303133;
      margin-bottom: 0; // Override default h1 margin
    }
  }
  .job-attributes {
    margin-top: 20px;
    .salary-amount {
      font-size: 1.2em;
      font-weight: bold;
      color: #E6A23C;
    }
    .el-descriptions__label {
      font-weight: bold;
    }
  }
  .job-description {
    margin-top: 15px;
    line-height: 1.8;
    color: #606266;
    white-space: pre-wrap; /* Respect newlines and spaces in description */
  }
  .skill-requirements,
  .job-tags-section {
    margin-top: 15px;
    p, .el-tag {
      color: #606266;
    }
    .job-tag {
      margin-right: 8px;
      margin-bottom: 8px;
    }
  }
}

.actions-card {
  .apply-button {
    width: 100%;
    margin-bottom: 10px;
  }
  .share-button {
    width: 100%;
  }
  p {
    font-size: 0.9em;
    color: #606266;
    text-align: center;
    margin-bottom: 10px;
  }
}

.employer-info-card {
  // Styles for employer info card
  p {
     font-size: 0.9em;
  }
}

.loading-state,
.empty-state {
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #fff;
  border-radius: 8px;
  margin-bottom: 20px;
}

.el-divider {
  margin: 25px 0;
}

</style>
