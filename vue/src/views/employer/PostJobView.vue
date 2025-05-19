<!--
  @file PostJobView.vue
  @description 雇主发布工作页面，提供工作信息填写和提交功能
  @author Fy
  @date 2023-05-22
-->
<template>
  <div class="post-job page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>发布工作</h1>
          <!-- 添加调试信息 -->
          <div class="debug-info" v-if="isDebugMode">
            <p>已加载 {{ jobCategories.length }} 个工作类别</p>
            <p>已加载 {{ recommendedTags.length }} 个推荐标签</p>
          </div>
        </div>
      </template>
      
      <div v-if="loading.categories || loading.skills" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>
      
      <el-form
        v-else
        ref="jobFormRef"
        :model="jobForm"
        :rules="jobRules"
        label-width="120px"
        class="job-form"
      >
        <!-- 基本信息 -->
        <h2 class="form-section-title">基本信息</h2>
        
        <el-form-item label="工作标题" prop="title">
          <el-input v-model="jobForm.title" placeholder="请输入工作标题" />
        </el-form-item>
        
        <el-form-item label="工作类别" prop="job_category">
          <el-select v-model="jobForm.job_category" placeholder="请选择工作类别" style="width: 100%">
            <el-option
              v-for="category in jobCategories"
              :key="category.value"
              :label="category.label"
              :value="category.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="工作标签" prop="job_tags">
          <el-select
            v-model="jobForm.job_tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请选择或创建标签（最多5个）"
            style="width: 100%"
            :max="5"
          >
            <el-option
              v-for="tag in recommendedTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="工作详情" prop="description">
          <el-input
            v-model="jobForm.description"
            type="textarea"
            :rows="6"
            placeholder="请详细描述工作内容、职责、要求等"
          />
        </el-form-item>
        
        <!-- 技能要求 -->
        <h2 class="form-section-title">技能要求</h2>
        
        <el-form-item label="所需技能" prop="skill_requirements">
          <el-input
            v-model="jobForm.skill_requirements"
            type="textarea"
            :rows="4"
            placeholder="请描述所需技能要求"
          />
        </el-form-item>
        
        <!-- 工作地点 -->
        <h2 class="form-section-title">工作地点</h2>
        
        <el-form-item label="工作地址" prop="location_address">
          <el-input v-model="jobForm.location_address" placeholder="请输入详细地址" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="省份" prop="location_province">
              <el-input v-model="jobForm.location_province" placeholder="例如：浙江省" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="城市" prop="location_city">
              <el-input v-model="jobForm.location_city" placeholder="例如：杭州市" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="区县" prop="location_district">
              <el-input v-model="jobForm.location_district" placeholder="例如：西湖区" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 薪资信息 -->
        <h2 class="form-section-title">薪资信息</h2>
        
        <el-form-item label="薪资类型" prop="salary_type">
          <el-select v-model="jobForm.salary_type" placeholder="请选择薪资类型" style="width: 100%">
            <el-option label="固定价格" value="fixed" />
            <el-option label="时薪" value="hourly" />
            <el-option label="日薪" value="daily" />
            <el-option label="周薪" value="weekly" />
            <el-option label="月薪" value="monthly" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="薪资金额" prop="salary_amount">
          <el-input-number
            v-model="jobForm.salary_amount"
            :min="0"
            :precision="2"
            :step="100"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="jobForm.salary_negotiable">薪资可协商</el-checkbox>
        </el-form-item>
        
        <!-- 时间信息 -->
        <h2 class="form-section-title">时间信息</h2>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_time">
              <el-date-picker
                v-model="jobForm.start_time"
                type="datetime"
                placeholder="选择开始日期时间"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                :disabled-date="disablePastDates"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="end_time">
              <el-date-picker
                v-model="jobForm.end_time"
                type="datetime"
                placeholder="选择结束日期时间"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                :disabled-date="disablePastDates"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="报名截止" prop="application_deadline">
          <el-date-picker
            v-model="jobForm.application_deadline"
            type="datetime"
            placeholder="选择报名截止日期时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            :disabled-date="disablePastDates"
            style="width: 100%"
          />
        </el-form-item>
        
        <!-- 其他信息 -->
        <h2 class="form-section-title">其他信息</h2>
        
        <el-form-item label="招聘人数" prop="required_people">
          <el-input-number
            v-model="jobForm.required_people"
            :min="1"
            :max="100"
            :step="1"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="jobForm.is_urgent">紧急招聘</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitJobForm" :loading="loading.submit">发布工作</el-button>
          <el-button @click="resetForm">重置表单</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, FormInstance } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';

// 路由与状态管理
const router = useRouter();
const authStore = useAuthStore();
const jobFormRef = ref<FormInstance>();

// 加载状态
const loading = reactive({
  categories: false,
  skills: false,
  submit: false
});

// 工作类别与推荐标签
const jobCategories = ref<{ label: string; value: string }[]>([]);
const recommendedTags = ref<string[]>([]);

// 工作表单数据
const jobForm = reactive({
  title: '',
  job_category: '',
  job_tags: [] as string[],
  description: '',
  skill_requirements: '',
  location_address: '',
  location_province: '',
  location_city: '',
  location_district: '',
  salary_type: 'fixed',
  salary_amount: 0,
  salary_negotiable: false,
  start_time: '',
  end_time: '',
  application_deadline: '',
  required_people: 1,
  is_urgent: false
});

// 表单验证规则
const jobRules = {
  title: [
    { required: true, message: '请输入工作标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度应在5到100个字符之间', trigger: 'blur' }
  ],
  job_category: [
    { required: true, message: '请选择工作类别', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请填写工作详情', trigger: 'blur' },
    { min: 20, max: 2000, message: '详情描述应在20到2000个字符之间', trigger: 'blur' }
  ],
  location_address: [
    { required: true, message: '请输入工作地址', trigger: 'blur' }
  ],
  location_province: [
    { required: true, message: '请输入省份', trigger: 'blur' }
  ],
  location_city: [
    { required: true, message: '请输入城市', trigger: 'blur' }
  ],
  salary_type: [
    { required: true, message: '请选择薪资类型', trigger: 'change' }
  ],
  salary_amount: [
    { required: true, message: '请输入薪资金额', trigger: 'blur' },
    { type: 'number', min: 0, message: '薪资金额必须大于等于0', trigger: 'blur' }
  ],
  start_time: [
    { required: true, message: '请选择开始日期时间', trigger: 'change' }
  ],
  end_time: [
    { required: true, message: '请选择结束日期时间', trigger: 'change' }
  ],
  required_people: [
    { required: true, message: '请输入招聘人数', trigger: 'blur' },
    { type: 'number', min: 1, message: '招聘人数必须至少为1', trigger: 'blur' }
  ]
};

// 获取工作类别
const fetchJobCategories = async () => {
  loading.categories = true;
  try {
    const response = await apiClient.get('jobs/categories');
    
    // 调试输出响应结构
    console.log('类别响应:', response);
    
    // 检查各种可能的响应格式
    let categoriesData = [];
    if (response && Array.isArray(response)) {
      // 如果直接返回数组
      categoriesData = response;
    } else if (response && typeof response === 'object') {
      // 检查不同的数据结构路径
      if (response.categories && Array.isArray(response.categories)) {
        categoriesData = response.categories;
      } else if (response.data && Array.isArray(response.data.categories)) {
        categoriesData = response.data.categories;
      } else if (response.items && Array.isArray(response.items)) {
        categoriesData = response.items;
      }
    }
    
    // 转换为需要的格式
    if (categoriesData.length > 0) {
      jobCategories.value = categoriesData.map((category: string) => ({
        label: category, 
        value: category
      }));
    }
    
    console.log('处理后的类别数据:', jobCategories.value);
  } catch (error) {
    console.error('获取工作类别失败:', error);
    ElMessage.error('获取工作类别失败，请刷新重试');
  } finally {
    loading.categories = false;
  }
};

// 获取推荐标签
const fetchRecommendedTags = async () => {
  loading.skills = true;
  try {
    const response = await apiClient.get('jobs/tags');
    
    // 调试输出响应结构
    console.log('标签响应:', response);
    
    // 检查各种可能的响应格式
    let tagsData = [];
    if (response && Array.isArray(response)) {
      tagsData = response;
    } else if (response && typeof response === 'object') {
      if (response.tags && Array.isArray(response.tags)) {
        tagsData = response.tags;
      } else if (response.data && Array.isArray(response.data.tags)) {
        tagsData = response.data.tags;
      } else if (response.items && Array.isArray(response.items)) {
        tagsData = response.items;
      }
    }
    
    recommendedTags.value = tagsData;
    console.log('处理后的标签数据:', recommendedTags.value);
  } catch (error) {
    console.error('获取推荐标签失败:', error);
  } finally {
    loading.skills = false;
  }
};

// 禁用过去的日期
const disablePastDates = (time: Date) => {
  return time.getTime() < Date.now() - 24 * 60 * 60 * 1000; // 允许今天
};

// 提交工作表单
const submitJobForm = async () => {
  if (!jobFormRef.value) return;
  
  await jobFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.submit = true;
      try {
        const response = await apiClient.post('jobs', jobForm);
        
        ElMessage.success('工作发布成功，待管理员审核');
        router.push({
          name: 'my-posted-jobs',
          query: { refresh: 'true' }
        });
      } catch (error) {
        console.error('发布工作失败:', error);
      } finally {
        loading.submit = false;
      }
    } else {
      ElMessage.error('请完成必填项并修正表单错误');
    }
  });
};

// 重置表单
const resetForm = () => {
  if (jobFormRef.value) {
    jobFormRef.value.resetFields();
  }
};

// 组件挂载
onMounted(() => {
  // 检查用户角色是否为雇主
  if (!authStore.isLoggedIn || authStore.user?.current_role !== 'employer') {
    ElMessage.warning('请先以雇主身份登录');
    router.push('/login');
    return;
  }
  
  // 获取分类和标签
  fetchJobCategories();
  fetchRecommendedTags();
});
</script>

<style scoped>
.page-container {
  max-width: 1000px;
  margin: 20px auto;
  padding: 0 15px;
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

.loading-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.job-form {
  margin-top: 20px;
}

.form-section-title {
  font-size: 1.2em;
  font-weight: bold;
  margin: 25px 0 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  color: #409EFF;
}

.el-form-item {
  margin-bottom: 22px;
}

.el-select,
.el-date-picker,
.el-input-number {
  width: 100%;
}

.debug-info {
  margin-top: 10px;
  padding: 10px;
  background-color: #f0f9eb;
  border: 1px dashed #67c23a;
  font-size: 12px;
}
</style>