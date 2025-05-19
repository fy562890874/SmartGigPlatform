<!--
  @file SkillsView.vue
  @description 技能广场页面，展示平台所有技能标签和分类
  @author Fy
  @date 2023-05-20
-->
<template>
  <div class="skills-view page-container">
    <el-card shadow="never" class="skills-card">
      <template #header>
        <div class="card-header">
          <h1>技能广场</h1>
          <p class="subtitle">浏览平台所有技能分类和标签</p>
        </div>
      </template>
      
      <!-- 筛选和搜索区 -->
      <div class="filter-section">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="8">
            <el-input 
              v-model="filters.keyword" 
              placeholder="搜索技能" 
              prefix-icon="Search"
              clearable
              @keyup.enter="fetchSkills"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-select 
              v-model="filters.category" 
              placeholder="选择分类" 
              clearable
              style="width: 100%"
              @change="fetchSkills"
            >
              <el-option 
                v-for="category in categories" 
                :key="category" 
                :label="category" 
                :value="category"
              />
            </el-select>
          </el-col>
          <el-col :xs="24" :sm="24" :md="8">
            <el-checkbox v-model="filters.isHot" @change="fetchSkills">
              只显示热门技能
            </el-checkbox>
          </el-col>
        </el-row>
      </div>
      
      <!-- 技能分类标签组 -->
      <div class="categories-section" v-if="categories.length > 0">
        <h2>技能分类</h2>
        <div class="categories-tags">
          <el-tag
            v-for="category in categories"
            :key="category"
            effect="plain"
            @click="selectCategory(category)"
            :class="{ 'active-tag': filters.category === category }"
          >
            {{ category }}
          </el-tag>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      
      <!-- 技能列表 -->
      <div v-else class="skills-list">
        <el-empty v-if="skills.length === 0" description="未找到相关技能" />
        
        <el-table v-else :data="skills" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="技能名称" />
          <el-table-column prop="category" label="分类" width="180" />
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column label="热门" width="80">
            <template #default="scope">
              <el-tag type="danger" v-if="scope.row.is_hot">热门</el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-container" v-if="pagination.total_items > 0">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="pagination.total_items"
            :page-size="pagination.per_page"
            :current-page="pagination.page"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { Search } from '@element-plus/icons-vue';
import apiClient from '@/utils/apiClient';
import { getPaginatedData } from '@/utils/http';

// 数据结构定义
interface Skill {
  id: number;
  name: string;
  category: string;
  description: string;
  is_hot: boolean;
  created_at: string;
  updated_at: string;
}

interface Pagination {
  page: number;
  per_page: number;
  total_pages: number;
  total_items: number;
}

// 状态定义
const loading = ref(false);
const skills = ref<Skill[]>([]);
const categories = ref<string[]>([]);
const filters = reactive({
  keyword: '',
  category: '',
  isHot: false
});
const pagination = reactive<Pagination>({
  page: 1,
  per_page: 20,
  total_pages: 0,
  total_items: 0
});

// 获取所有技能分类
const fetchCategories = async () => {
  try {
    const result = await apiClient.get('skills/categories');
    categories.value = result?.categories || [];
  } catch (error) {
    console.error('获取技能分类失败:', error);
    categories.value = [];
  }
};

// 获取技能列表
const fetchSkills = async () => {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      per_page: pagination.per_page
    };
    
    if (filters.keyword) params.q = filters.keyword;
    if (filters.category) params.category = filters.category;
    if (filters.isHot) params.is_hot = true;
    
    const response = await apiClient.get('skills', { params });
    
    const { items = [], pagination: paginationData = {} as Pagination } = getPaginatedData<Skill>(response);
    
    skills.value = items;
    pagination.page = paginationData.page || 1;
    pagination.per_page = paginationData.per_page || 20;
    pagination.total_pages = paginationData.total_pages || 1;
    pagination.total_items = paginationData.total_items || 0;
  } catch (error) {
    console.error('获取技能列表失败:', error);
    skills.value = [];
  } finally {
    loading.value = false;
  }
};

// 选择分类
const selectCategory = (category: string) => {
  if (filters.category === category) {
    // 如果点击的是已选中的分类，则取消选中
    filters.category = '';
  } else {
    filters.category = category;
  }
  pagination.page = 1; // 重置页码
  fetchSkills();
};

// 页码变化处理
const handlePageChange = (page: number) => {
  pagination.page = page;
  fetchSkills();
};

// 页面加载
onMounted(() => {
  fetchCategories();
  fetchSkills();
});
</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 15px;
}

.skills-card {
  margin-bottom: 20px;
}

.card-header {
  text-align: center;
  margin-bottom: 20px;
}

.card-header h1 {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 8px;
}

.subtitle {
  color: #606266;
  font-size: 14px;
}

.filter-section {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.filter-section .el-col {
  margin-bottom: 15px;
}

.categories-section {
  margin-bottom: 30px;
}

.categories-section h2 {
  font-size: 1.2em;
  margin-bottom: 15px;
  color: #303133;
}

.categories-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.categories-tags .el-tag {
  cursor: pointer;
  transition: all 0.2s;
  padding: 8px 15px;
}

.categories-tags .el-tag:hover {
  transform: translateY(-2px);
}

.categories-tags .active-tag {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-7);
}

.loading-state {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.skills-list {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .categories-tags {
    gap: 8px;
  }
  
  .categories-tags .el-tag {
    padding: 6px 10px;
    font-size: 12px;
  }
}
</style>