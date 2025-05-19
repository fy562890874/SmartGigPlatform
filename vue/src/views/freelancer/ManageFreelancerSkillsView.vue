<template>
  <div class="manage-freelancer-skills page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>管理我的技能</span>
          <el-button type="primary" :icon="Plus" @click="openAddSkillDialog">添加新技能</el-button>
        </div>
      </template>

      <div v-if="loadingSkills" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      <el-empty description="您还没有添加任何技能。" v-else-if="!freelancerSkills.length && !loadingSkills" />
      <el-table :data="freelancerSkills" v-else style="width: 100%">
        <el-table-column prop="skill.name" label="技能名称" width="180">
            <template #default="{ row }">
                {{ row.skill?.name || '未知技能' }}
            </template>
        </el-table-column>
        <el-table-column prop="skill.category" label="技能分类" width="150">
             <template #default="{ row }">
                {{ row.skill?.category || '-' }}
            </template>
        </el-table-column>
        <el-table-column prop="proficiency_level" label="熟练度" width="120" />
        <el-table-column prop="years_of_experience" label="经验年限" width="100" />
        <el-table-column label="证书" width="120">
          <template #default="{ row }">
            <el-link v-if="row.certificate_url" :href="row.certificate_url" type="primary" target="_blank">查看</el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="certificate_verified" label="证书已验证" width="120">
            <template #default="{ row }">
                <el-tag :type="row.certificate_verified ? 'success' : 'info'">{{ row.certificate_verified ? '是' : '否' }}</el-tag>
            </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" :icon="Edit" @click="openEditSkillDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="confirmRemoveSkill(row.skill_id)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑技能对话框 -->
    <el-dialog 
      :title="isEditingSkill ? '编辑技能' : '添加技能'" 
      v-model="skillDialogVisible"
      width="600px"
      @closed="resetSkillForm"
    >
      <el-form :model="skillForm" :rules="skillFormRules" ref="skillFormRef" label-width="100px">
        <el-form-item label="选择技能" prop="skill_id" v-if="!isEditingSkill">
          <el-select 
            v-model="skillForm.skill_id" 
            placeholder="请选择一项技能" 
            filterable
            remote
            :remote-method="searchPublicSkills"
            :loading="loadingPublicSkills"
            style="width: 100%;"
            value-key="id"
          >
            <el-option 
                v-for="skill in publicSkills" 
                :key="skill.id" 
                :label="`${skill.name} (${skill.category})`" 
                :value="skill.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="技能名称" v-if="isEditingSkill">
            <el-input :value="skillForm.skill_name" disabled />
        </el-form-item>
        <el-form-item label="熟练度" prop="proficiency_level">
          <el-select v-model="skillForm.proficiency_level" placeholder="请选择熟练度">
            <el-option label="初学者 (Beginner)" value="beginner"></el-option>
            <el-option label="中级 (Intermediate)" value="intermediate"></el-option>
            <el-option label="高级 (Advanced)" value="advanced"></el-option>
            <el-option label="专家 (Expert)" value="expert"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="经验年限" prop="years_of_experience">
          <el-input-number v-model="skillForm.years_of_experience" :min="0" :max="50" />
        </el-form-item>
        <el-form-item label="证书链接" prop="certificate_url">
          <el-input v-model="skillForm.certificate_url" placeholder="例如：http://example.com/cert.pdf"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="skillDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSkillForm" :loading="submittingSkill">确认</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import { Plus, Edit, Delete } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';

const router = useRouter();
const authStore = useAuthStore();

// 状态变量
const freelancerSkills = ref<any[]>([]);
const publicSkills = ref<any[]>([]);
const loadingSkills = ref(true);
const loadingPublicSkills = ref(false);

// 技能对话框状态
const skillDialogVisible = ref(false);
const isEditingSkill = ref(false);
const submittingSkill = ref(false);
const skillFormRef = ref<FormInstance>();

// 技能表单数据
const skillForm = reactive({
  skill_id: null as number | null,
  skill_name: '',
  proficiency_level: '',
  years_of_experience: 0,
  certificate_url: ''
});

// 表单验证规则
const skillFormRules = {
  skill_id: [
    { required: true, message: '请选择一项技能', trigger: 'change' }
  ],
  proficiency_level: [
    { required: true, message: '请选择熟练度', trigger: 'change' }
  ],
  years_of_experience: [
    { required: true, message: '请输入经验年限', trigger: 'blur' }
  ]
};

// 获取用户的技能列表
const fetchFreelancerSkills = async () => {
  loadingSkills.value = true;
  try {
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      return;
    }

    // 使用axios直接请求API
    const response = await axios.get(apiConfig.getApiUrl('profiles/freelancer/me/skills'), {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    // 处理响应数据
    if (response.data && response.data.code === 0) {
      if (Array.isArray(response.data.data)) {
        freelancerSkills.value = response.data.data;
      } else if (response.data.data && Array.isArray(response.data.data.skills)) {
        freelancerSkills.value = response.data.data.skills;
      } else {
        freelancerSkills.value = [];
      }
    } else {
      freelancerSkills.value = [];
    }
  } catch (error: any) {
    console.error('获取零工技能失败:', error);
    ElMessage.error(error.response?.data?.message || '获取技能列表失败。');
    freelancerSkills.value = [];
  } finally {
    loadingSkills.value = false;
  }
};

// 搜索公开技能库
const searchPublicSkills = async (query: string) => {
  if (query.trim() === '') {
    publicSkills.value = [];
    return;
  }

  loadingPublicSkills.value = true;
  try {
    const token = authStore.token;
    if (!token) return;

    // 使用axios直接请求API
    const response = await axios.get('http://127.0.0.1:5000/api/v1/skills', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      params: {
        q: query,
        page: 1,
        per_page: 20
      }
    });

    // 处理响应数据
    if (response.data && response.data.code === 0) {
      if (response.data.data && Array.isArray(response.data.data.items)) {
        publicSkills.value = response.data.data.items;
      } else {
        publicSkills.value = [];
      }
    } else {
      publicSkills.value = [];
    }
  } catch (error: any) {
    console.error('搜索技能失败:', error);
    publicSkills.value = [];
  } finally {
    loadingPublicSkills.value = false;
  }
};

// 打开添加技能对话框
const openAddSkillDialog = () => {
  isEditingSkill.value = false;
  skillForm.skill_id = null;
  skillForm.skill_name = '';
  skillForm.proficiency_level = '';
  skillForm.years_of_experience = 0;
  skillForm.certificate_url = '';
  skillDialogVisible.value = true;
};

// 打开编辑技能对话框
const openEditSkillDialog = (skill: any) => {
  isEditingSkill.value = true;
  skillForm.skill_id = skill.skill_id;
  skillForm.skill_name = skill.skill?.name || '未知技能';
  skillForm.proficiency_level = skill.proficiency_level || '';
  skillForm.years_of_experience = skill.years_of_experience || 0;
  skillForm.certificate_url = skill.certificate_url || '';
  skillDialogVisible.value = true;
};

// 重置技能表单
const resetSkillForm = () => {
  if (skillFormRef.value) {
    skillFormRef.value.resetFields();
  }
};

// 提交技能表单（添加或编辑）
const submitSkillForm = async () => {
  if (!skillFormRef.value) return;

  await skillFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请完善表单信息');
      return;
    }

    submittingSkill.value = true;
    const token = authStore.token;
    if (!token) {
      ElMessage.error('您尚未登录或登录已过期');
      router.push('/login');
      submittingSkill.value = false;
      return;
    }

    try {
      if (isEditingSkill.value) {
        // 编辑现有技能
        const payload = {
          proficiency_level: skillForm.proficiency_level,
          years_of_experience: skillForm.years_of_experience,
          certificate_url: skillForm.certificate_url || null
        };

        await axios.put(
          `http://127.0.0.1:5000/api/v1/profiles/freelancer/me/skills/${skillForm.skill_id}`,
          payload,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        ElMessage.success('技能信息更新成功');
      } else {
        // 添加新技能
        const payload = {
          skill_id: skillForm.skill_id,
          proficiency_level: skillForm.proficiency_level,
          years_of_experience: skillForm.years_of_experience,
          certificate_url: skillForm.certificate_url || null
        };

        await axios.post(
          'http://127.0.0.1:5000/api/v1/profiles/freelancer/me/skills',
          payload,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        ElMessage.success('技能添加成功');
      }

      // 关闭对话框并刷新技能列表
      skillDialogVisible.value = false;
      fetchFreelancerSkills();
    } catch (error: any) {
      console.error('保存技能失败:', error);
      let errorMessage = '操作失败，请稍后重试';

      if (error.response && error.response.data) {
        if (error.response.data.message) {
          errorMessage = error.response.data.message;
        } else if (error.response.data.errors) {
          const errors = error.response.data.errors;
          errorMessage = Object.values(errors).flat().join('; ');
        }
      }

      ElMessage.error(errorMessage);
    } finally {
      submittingSkill.value = false;
    }
  });
};

// 确认删除技能
const confirmRemoveSkill = (skillId: number) => {
  ElMessageBox.confirm(
    '确定要移除这项技能吗？',
    '移除技能',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    removeSkill(skillId);
  }).catch(() => {
    // 用户取消删除操作
  });
};

// 执行删除技能请求
const removeSkill = async (skillId: number) => {
  const token = authStore.token;
  if (!token) {
    ElMessage.error('您尚未登录或登录已过期');
    router.push('/login');
    return;
  }

  try {
    await axios.delete(`http://127.0.0.1:5000/api/v1/profiles/freelancer/me/skills/${skillId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    ElMessage.success('技能已移除');
    // 重新获取技能列表
    fetchFreelancerSkills();
  } catch (error: any) {
    console.error('移除技能失败:', error);
    ElMessage.error(error.response?.data?.message || '移除技能失败，请稍后重试');
  }
};

// 组件挂载时执行
onMounted(() => {
  // 检查用户是否登录
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }

  // 获取用户技能列表
  fetchFreelancerSkills();
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

.el-table .el-button + .el-button {
    margin-left: 8px;
}

.el-dialog .el-select {
    width: 100%;
}
</style>