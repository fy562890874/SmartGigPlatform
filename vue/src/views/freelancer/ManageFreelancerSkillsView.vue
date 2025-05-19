<!--
  @file ManageFreelancerSkillsView.vue
  @description 零工用户管理个人技能页面，可以添加、编辑和删除技能
  @author Fy
  @date 2023-05-21
-->
<template>
  <div class="manage-skills page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>管理我的技能</h1>
          <el-button type="primary" @click="showAddSkillDialog">添加新技能</el-button>
        </div>
      </template>
      
      <!-- 加载状态 -->
      <div v-if="loading.skills" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      
      <!-- 无技能状态 -->
      <el-empty 
        v-else-if="freelancerSkills.length === 0" 
        description="您还未添加任何技能，请添加技能以提高被雇主发现的机会"
      >
        <el-button type="primary" @click="showAddSkillDialog">添加技能</el-button>
      </el-empty>
      
      <!-- 技能列表 -->
      <div v-else class="skills-container">
        <el-table :data="freelancerSkills" style="width: 100%">
          <el-table-column prop="skill_name" label="技能名称" min-width="150" />
          <el-table-column prop="category" label="分类" width="150" />
          <el-table-column prop="experience_level" label="熟练度" width="120">
            <template #default="scope">
              <el-tag :type="getExperienceLevelType(scope.row.experience_level)">
                {{ formatExperienceLevel(scope.row.experience_level) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="详细描述" show-overflow-tooltip />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="scope">
              <el-button 
                size="small" 
                type="primary" 
                @click="editSkill(scope.row)"
                plain
              >
                编辑
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="confirmDeleteSkill(scope.row)"
                plain
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    
    <!-- 添加/编辑技能对话框 -->
    <el-dialog 
      v-model="skillDialogVisible" 
      :title="isEditing ? '编辑技能' : '添加新技能'"
      width="500px"
    >
      <el-form 
        ref="skillFormRef" 
        :model="skillForm" 
        :rules="skillRules" 
        label-width="100px"
      >
        <el-form-item label="技能分类" prop="category">
          <el-select 
            v-model="skillForm.category" 
            placeholder="选择技能分类" 
            filterable
            style="width: 100%"
            @change="handleCategoryChange"
          >
            <el-option 
              v-for="cat in skillCategories" 
              :key="cat" 
              :label="cat" 
              :value="cat"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="技能名称" prop="skill_id">
          <el-select 
            v-model="skillForm.skill_id" 
            placeholder="选择或搜索技能" 
            filterable
            style="width: 100%"
            :loading="loading.availableSkills"
          >
            <el-option 
              v-for="skill in availableSkills" 
              :key="skill.id" 
              :label="skill.name" 
              :value="skill.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="熟练程度" prop="experience_level">
          <el-select 
            v-model="skillForm.experience_level" 
            placeholder="选择熟练程度" 
            style="width: 100%"
          >
            <el-option label="入门" value="beginner" />
            <el-option label="中级" value="intermediate" />
            <el-option label="高级" value="advanced" />
            <el-option label="专家" value="expert" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="详细描述" prop="description">
          <el-input 
            v-model="skillForm.description" 
            type="textarea" 
            :rows="4" 
            placeholder="描述您的技能经验、项目案例等"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="skillDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="submitSkill"
            :loading="loading.submit"
          >
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/utils/apiClient';

// 路由和状态管理
const router = useRouter();
const authStore = useAuthStore();

// 表单引用
const skillFormRef = ref<FormInstance>();

// 加载状态
const loading = reactive({
  skills: false,
  availableSkills: false,
  categories: false,
  submit: false
});

// 数据
const freelancerSkills = ref<any[]>([]);
const availableSkills = ref<any[]>([]);
const skillCategories = ref<string[]>([]);
const skillDialogVisible = ref(false);
const isEditing = ref(false);
const currentSkillId = ref<number | null>(null);

// 技能表单
const skillForm = reactive({
  skill_id: '',
  category: '',
  experience_level: '',
  description: ''
});

// 表单验证规则
const skillRules = {
  category: [
    { required: true, message: '请选择技能分类', trigger: 'change' }
  ],
  skill_id: [
    { required: true, message: '请选择技能', trigger: 'change' }
  ],
  experience_level: [
    { required: true, message: '请选择熟练程度', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请填写技能描述', trigger: 'blur' },
    { min: 10, max: 500, message: '描述长度应在10-500个字符之间', trigger: 'blur' }
  ]
};

// 获取零工技能
const fetchFreelancerSkills = async () => {
  loading.skills = true;
  try {
    const response = await apiClient.get('profiles/freelancer/me/skills');
    freelancerSkills.value = response.data.items || [];
  } catch (error) {
    console.error('获取零工技能失败:', error);
  } finally {
    loading.skills = false;
  }
};

// 获取技能分类
const fetchSkillCategories = async () => {
  loading.categories = true;
  try {
    const response = await apiClient.get('skills/categories');
    skillCategories.value = response.data.categories || [];
  } catch (error) {
    console.error('获取技能分类失败:', error);
  } finally {
    loading.categories = false;
  }
};

// 获取特定分类的可用技能
const fetchAvailableSkills = async (category: string) => {
  if (!category) return;
  
  loading.availableSkills = true;
  try {
    const response = await apiClient.get('skills', { 
      params: { category, per_page: 100 }
    });
    availableSkills.value = response.data.items || [];
  } catch (error) {
    console.error('获取可用技能失败:', error);
  } finally {
    loading.availableSkills = false;
  }
};

// 显示添加技能对话框
const showAddSkillDialog = () => {
  isEditing.value = false;
  currentSkillId.value = null;
  resetSkillForm();
  skillDialogVisible.value = true;
};

// 编辑技能
const editSkill = (skill: any) => {
  isEditing.value = true;
  currentSkillId.value = skill.id;
  
  // 填充表单数据
  skillForm.category = skill.category;
  fetchAvailableSkills(skill.category).then(() => {
    skillForm.skill_id = skill.skill_id;
    skillForm.experience_level = skill.experience_level;
    skillForm.description = skill.description;
    
    skillDialogVisible.value = true;
  });
};

// 分类变更处理
const handleCategoryChange = (category: string) => {
  skillForm.skill_id = ''; // 清空之前选择的技能
  fetchAvailableSkills(category);
};

// 提交技能表单
const submitSkill = async () => {
  if (!skillFormRef.value) return;
  
  await skillFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.submit = true;
      try {
        // 准备提交数据
        const submitData = {
          skill_id: skillForm.skill_id,
          experience_level: skillForm.experience_level,
          description: skillForm.description
        };
        
        if (isEditing.value && currentSkillId.value) {
          // 更新已有技能
          await apiClient.put(`profiles/freelancer/me/skills/${currentSkillId.value}`, submitData);
          ElMessage.success('技能已成功更新');
        } else {
          // 添加新技能
          await apiClient.post('profiles/freelancer/me/skills', submitData);
          ElMessage.success('技能已成功添加');
        }
        
        // 关闭对话框并刷新列表
        skillDialogVisible.value = false;
        fetchFreelancerSkills();
      } catch (error) {
        console.error('保存技能失败:', error);
      } finally {
        loading.submit = false;
      }
    }
  });
};

// 确认删除技能
const confirmDeleteSkill = (skill: any) => {
  ElMessageBox.confirm(
    `确定要删除技能"${skill.skill_name}"吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await apiClient.delete(`profiles/freelancer/me/skills/${skill.id}`);
      ElMessage.success('技能已成功删除');
      fetchFreelancerSkills();
    } catch (error) {
      console.error('删除技能失败:', error);
    }
  }).catch(() => {
    // 用户取消删除
  });
};

// 重置技能表单
const resetSkillForm = () => {
  skillForm.category = '';
  skillForm.skill_id = '';
  skillForm.experience_level = '';
  skillForm.description = '';
  availableSkills.value = [];
};

// 格式化经验水平
const formatExperienceLevel = (level: string): string => {
  const levelMap: Record<string, string> = {
    'beginner': '入门',
    'intermediate': '中级',
    'advanced': '高级',
    'expert': '专家'
  };
  return levelMap[level] || level;
};

// 获取经验水平对应的标签类型
const getExperienceLevelType = (level: string): string => {
  const typeMap: Record<string, string> = {
    'beginner': 'info',
    'intermediate': 'success',
    'advanced': 'warning',
    'expert': 'danger'
  };
  return typeMap[level] || 'info';
};

// 组件挂载
onMounted(() => {
  if (authStore.isLoggedIn && authStore.user?.current_role === 'freelancer') {
    fetchFreelancerSkills();
    fetchSkillCategories();
  } else {
    ElMessage.warning('请先以零工身份登录');
    router.push('/login');
  }
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

.skills-container {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>