<template>
  <div class="post-job-view page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEditing ? '编辑工作' : '发布新工作' }}</span>
          <el-button @click="goBack">返回</el-button>
        </div>
      </template>

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>

      <el-form 
        v-else
        :model="jobForm" 
        :rules="jobRules" 
        ref="jobFormRef" 
        label-width="120px" 
        label-position="right"
        class="job-form"
      >
        <!-- 基本信息 -->
        <h3 class="form-section-title">基本信息</h3>

        <el-form-item label="工作标题" prop="title">
          <el-input v-model="jobForm.title" placeholder="请输入工作标题"></el-input>
        </el-form-item>

        <el-form-item label="工作类别" prop="job_category">
          <el-select v-model="jobForm.job_category" placeholder="请选择工作类别" style="width: 100%;">
            <!-- 预设的工作类别选项 -->
            <el-option label="软件开发" value="software_development"></el-option>
            <el-option label="设计" value="design"></el-option>
            <el-option label="市场营销" value="marketing"></el-option>
            <el-option label="客户服务" value="customer_service"></el-option>
            <el-option label="行政助理" value="administrative"></el-option>
            <el-option label="餐饮服务" value="food_service"></el-option>
            <el-option label="家政服务" value="housekeeping"></el-option>
            <el-option label="物流运输" value="logistics"></el-option>
            <el-option label="零售" value="retail"></el-option>
            <el-option label="其他" value="others"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="工作描述" prop="description">
          <el-input 
            type="textarea" 
            v-model="jobForm.description" 
            :rows="5"
            placeholder="请详细描述工作内容、要求等..."
          ></el-input>
        </el-form-item>

        <!-- 工作标签 -->
        <el-form-item label="工作标签" prop="job_tags_string">
          <el-tag
            v-for="tag in jobTags"
            :key="tag"
            closable
            @close="removeTag(tag)"
            class="job-tag"
          >
            {{ tag }}
          </el-tag>
          <el-input
            v-if="tagInputVisible"
            ref="tagInputRef"
            v-model="tagInputValue"
            class="tag-input"
            size="small"
            @blur="handleTagInputConfirm"
            @keyup.enter="handleTagInputConfirm"
          />
          <el-button v-else class="button-new-tag" size="small" @click="showTagInput">
            + 添加标签
          </el-button>
        </el-form-item>

        <!-- 工作时间 -->
        <h3 class="form-section-title">工作时间</h3>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker
                v-model="jobForm.start_time"
                type="datetime"
                placeholder="选择开始时间"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                :disabled-date="disablePastDates"
                style="width: 100%;"
              ></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker
                v-model="jobForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                :disabled-date="disablePastDates"
                style="width: 100%;"
              ></el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="报名截止时间" prop="application_deadline">
          <el-date-picker
            v-model="jobForm.application_deadline"
            type="datetime"
            placeholder="选择报名截止时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            :disabled-date="disablePastDates"
            style="width: 100%;"
          ></el-date-picker>
        </el-form-item>

        <!-- 薪资信息 -->
        <h3 class="form-section-title">薪资信息</h3>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="薪资金额" prop="salary_amount">
              <el-input-number
                v-model="jobForm.salary_amount"
                :min="0"
                :precision="2"
                :step="100"
                style="width: 100%;"
              ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计薪方式" prop="salary_type">
              <el-select v-model="jobForm.salary_type" placeholder="请选择计薪方式" style="width: 100%;">
                <el-option label="时薪" value="hourly"></el-option>
                <el-option label="日薪" value="daily"></el-option>
                <el-option label="周薪" value="weekly"></el-option>
                <el-option label="月薪" value="monthly"></el-option>
                <el-option label="固定金额" value="fixed"></el-option>
                <el-option label="面议" value="negotiable"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="薪资可议价" prop="salary_negotiable">
          <el-switch
            v-model="jobForm.salary_negotiable"
            :active-text="jobForm.salary_negotiable ? '是' : '否'"
          ></el-switch>
        </el-form-item>

        <!-- 工作地点 -->
        <h3 class="form-section-title">工作地点</h3>

        <el-form-item label="详细地址" prop="location_address">
          <el-input v-model="jobForm.location_address" placeholder="请输入详细地址"></el-input>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="省份" prop="location_province">
              <el-input v-model="jobForm.location_province" placeholder="省份"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="城市" prop="location_city">
              <el-input v-model="jobForm.location_city" placeholder="城市"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="区县" prop="location_district">
              <el-input v-model="jobForm.location_district" placeholder="区县"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 其他信息 -->
        <h3 class="form-section-title">其他信息</h3>

        <el-form-item label="需求人数" prop="required_people">
          <el-input-number
            v-model="jobForm.required_people"
            :min="1"
            :step="1"
            style="width: 100%;"
          ></el-input-number>
        </el-form-item>

        <el-form-item label="技能要求" prop="skill_requirements">
          <el-input
            type="textarea"
            v-model="jobForm.skill_requirements"
            :rows="3"
            placeholder="请描述所需技能要求"
          ></el-input>
        </el-form-item>

        <el-form-item label="紧急招聘" prop="is_urgent">
          <el-switch
            v-model="jobForm.is_urgent"
            :active-text="jobForm.is_urgent ? '是' : '否'"
          ></el-switch>
        </el-form-item>

        <!-- 表单操作 -->
        <el-form-item>
          <el-button
            type="primary" 
            @click="submitJobForm" 
            :loading="submitting"
          >
            {{ isEditing ? '保存修改' : '发布工作' }}
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import { ElMessage, FormInstance, FormRules } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// Form refs
const jobFormRef = ref<FormInstance>();
const tagInputRef = ref();

// State variables
const loading = ref(false);
const submitting = ref(false);
const tagInputVisible = ref(false);
const tagInputValue = ref('');
const jobTags = ref<string[]>([]);

// Job form data
const jobForm = reactive({
  title: '',
  job_category: '',
  description: '',
  job_tags_string: '',
  start_time: '',
  end_time: '',
  application_deadline: '',
  salary_amount: 0,
  salary_type: 'hourly',
  salary_negotiable: false,
  location_address: '',
  location_province: '',
  location_city: '',
  location_district: '',
  latitude: null as number | null,
  longitude: null as number | null,
  required_people: 1,
  skill_requirements: '',
  is_urgent: false
});

// Determine if editing existing job or creating new one
const isEditing = computed(() => {
  return route.params.id !== undefined || route.name === 'edit-job';
});

const jobId = computed(() => {
  return route.params.id ? Number(route.params.id) : null;
});

// Form validation rules
const jobRules = reactive<FormRules>({
  title: [
    { required: true, message: '请输入工作标题', trigger: 'blur' }
  ],
  job_category: [
    { required: true, message: '请选择工作类别', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入工作描述', trigger: 'blur' }
  ],
  start_time: [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' }
  ],
  salary_amount: [
    { required: true, message: '请输入薪资金额', trigger: 'blur' }
  ],
  salary_type: [
    { required: true, message: '请选择计薪方式', trigger: 'change' }
  ],
  location_address: [
    { required: true, message: '请输入工作地点', trigger: 'blur' }
  ],
  required_people: [
    { required: true, message: '请输入需求人数', trigger: 'blur' }
  ]
});

// Date validation
const disablePastDates = (date: Date) => {
  return date.getTime() < Date.now() - 8.64e7; // 禁用过去的日期（昨天及以前）
};

// Tag handling methods
const showTagInput = () => {
  tagInputVisible.value = true;
  nextTick(() => {
    tagInputRef.value?.focus();
  });
};

const handleTagInputConfirm = () => {
  const value = tagInputValue.value.trim();
  if (value && !jobTags.value.includes(value)) {
    jobTags.value.push(value);
    updateJobTagsString();
  }
  tagInputVisible.value = false;
  tagInputValue.value = '';
};

const removeTag = (tag: string) => {
  jobTags.value = jobTags.value.filter(t => t !== tag);
  updateJobTagsString();
};

const updateJobTagsString = () => {
  jobForm.job_tags_string = jobTags.value.join(',');
};

// Fetch existing job details if editing
const fetchJobDetails = async () => {
  if (!isEditing.value || !jobId.value) return;

  loading.value = true;
  try {
    const response = await axios.get(
      apiConfig.getApiUrl(`/jobs/${jobId.value}`),
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    );

    if (response.data && response.data.code === 0) {
      const jobData = response.data.data;
      
      // Populate the form
      jobForm.title = jobData.title || '';
      jobForm.job_category = jobData.job_category || '';
      jobForm.description = jobData.description || '';
      jobForm.start_time = jobData.start_time || '';
      jobForm.end_time = jobData.end_time || '';
      jobForm.application_deadline = jobData.application_deadline || '';
      jobForm.salary_amount = jobData.salary_amount || 0;
      jobForm.salary_type = jobData.salary_type || 'hourly';
      jobForm.salary_negotiable = jobData.salary_negotiable || false;
      jobForm.location_address = jobData.location_address || '';
      jobForm.location_province = jobData.location_province || '';
      jobForm.location_city = jobData.location_city || '';
      jobForm.location_district = jobData.location_district || '';
      jobForm.required_people = jobData.required_people || 1;
      jobForm.skill_requirements = jobData.skill_requirements || '';
      jobForm.is_urgent = jobData.is_urgent || false;
      
      // Handle job tags
      if (jobData.job_tags && Array.isArray(jobData.job_tags)) {
        jobTags.value = [...jobData.job_tags];
        updateJobTagsString();
      }
    } else {
      ElMessage.error(response.data?.message || '获取工作详情失败');
      goBack();
    }
  } catch (error: any) {
    console.error('获取工作详情失败:', error);
    ElMessage.error(error.response?.data?.message || '获取工作详情失败，请稍后重试');
    goBack();
  } finally {
    loading.value = false;
  }
};

// Form submission
const submitJobForm = async () => {
  if (!jobFormRef.value) return;

  await jobFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请正确填写所有必填项');
      return;
    }

    submitting.value = true;
    try {
      // Prepare payload - convert jobForm to a new object to avoid reactive issues
      const payload = {
        title: jobForm.title,
        job_category: jobForm.job_category,
        description: jobForm.description,
        job_tags: jobTags.value,
        start_time: jobForm.start_time,
        end_time: jobForm.end_time,
        application_deadline: jobForm.application_deadline || null,
        salary_amount: jobForm.salary_amount,
        salary_type: jobForm.salary_type,
        salary_negotiable: jobForm.salary_negotiable,
        location_address: jobForm.location_address,
        location_province: jobForm.location_province || null,
        location_city: jobForm.location_city || null,
        location_district: jobForm.location_district || null,
        latitude: jobForm.latitude || null,
        longitude: jobForm.longitude || null,
        required_people: jobForm.required_people,
        skill_requirements: jobForm.skill_requirements || null,
        is_urgent: jobForm.is_urgent
      };

      let response;
      
      if (isEditing.value && jobId.value) {
        // Update existing job
        response = await axios.put(
          apiConfig.getApiUrl(`/jobs/${jobId.value}`),
          payload,
          {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        if (response.data && response.data.code === 0) {
          ElMessage.success('工作更新成功');
          router.push('/jobs/posted');
        } else {
          ElMessage.error(response.data?.message || '更新工作失败');
        }
      } else {
        // Create new job
        response = await axios.post(
          apiConfig.getApiUrl('/jobs'),
          payload,
          {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        if (response.data && response.data.code === 0) {
          ElMessage.success('工作发布成功');
          router.push('/jobs/posted');
        } else {
          ElMessage.error(response.data?.message || '发布工作失败');
        }
      }
    } catch (error: any) {
      console.error('提交工作表单失败:', error);
      ElMessage.error(error.response?.data?.message || '操作失败，请稍后重试');
    } finally {
      submitting.value = false;
    }
  });
};

// Reset the form
const resetForm = () => {
  if (!jobFormRef.value) return;
  
  if (isEditing.value) {
    // If editing, reset to original values
    fetchJobDetails();
  } else {
    // If creating new, clear the form
    jobFormRef.value.resetFields();
    jobTags.value = [];
    updateJobTagsString();
  }
};

// Navigation
const goBack = () => {
  router.back();
};

// Component initialization
onMounted(async () => {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/auth/login');
    return;
  }
  
  if (authStore.user?.current_role !== 'employer') {
    ElMessage.warning('您没有权限访问此页面');
    router.push('/');
    return;
  }
  
  if (isEditing.value) {
    await fetchJobDetails();
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

.loading-state {
  padding: 20px;
}

.job-form {
  padding: 20px 0;
}

.form-section-title {
  font-size: 1.1em;
  margin: 15px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.job-tag {
  margin-right: 6px;
  margin-bottom: 6px;
}

.tag-input {
  width: 100px;
  display: inline-block;
  vertical-align: middle;
  margin-right: 8px;
}

.button-new-tag {
  margin-bottom: 6px;
}
</style> 