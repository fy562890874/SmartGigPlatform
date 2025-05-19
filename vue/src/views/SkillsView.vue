<template>
  <div class="skills-view page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>平台技能库</h1>
        </div>
      </template>

      <!-- Filters -->
      <el-form :model="filterParams" inline class="filter-form">
        <el-form-item label="技能名称">
          <el-input v-model="filterParams.q" placeholder="搜索技能名称" clearable @clear="applyFilters" />
        </el-form-item>
        <el-form-item label="技能分类">
          <el-input v-model="filterParams.category" placeholder="按分类筛选" clearable @clear="applyFilters" />
        </el-form-item>
        <el-form-item label=" ">
          <el-checkbox v-model="filterParams.is_hot" label="仅看热门" @change="applyFilters" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilters">搜索</el-button>
        </el-form-item>
      </el-form>

      <!-- Skills List -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="10" animated />
      </div>
      <div v-else-if="skills.length === 0" class="empty-state">
        <el-empty description="未找到符合条件的技能。" />
      </div>
      <div v-else class="skills-list">
        <el-table :data="skills" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="技能名称" sortable />
          <el-table-column prop="category" label="分类" width="180" sortable />
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column prop="is_hot" label="热门" width="100" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.is_hot ? 'success' : 'info'">
                {{ scope.row.is_hot ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" sortable>
            <template #default="scope">{{ formatDate(scope.row.created_at) }}</template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-container" v-if="pagination.totalItems > 0">
          <el-pagination
            background
            layout="total, prev, pager, next, jumper"
            :total="pagination.totalItems"
            :page-size="pagination.perPage"
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
import axios from 'axios';
import apiConfig from '@/utils/apiConfig';
import { ElMessage, ElSkeleton, ElEmpty, ElTable, ElTableColumn, ElTag, ElPagination, ElForm, ElFormItem, ElInput, ElCheckbox, ElButton } from 'element-plus';

const API_BASE_URL = apiConfig.getApiUrl(''); // 替换硬编码的 API_BASE_URL

// 筛选参数
const filterParams = reactive({
  q: '',
  category: '',
  is_hot: undefined, // undefined 表示不筛选热门
  page: 1,
  per_page: 10,
});

// 技能数据和加载状态
const skills = ref([]);
const pagination = reactive({
  totalItems: 0,
  totalPages: 0,
  page: 1,
  perPage: 10,
});
const loading = ref(false);

// 格式化日期
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

// 获取技能列表
const fetchSkills = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`${API_BASE_URL}/skills`, {
      params: {
        q: filterParams.q,
        category: filterParams.category,
        is_hot: filterParams.is_hot,
        page: filterParams.page,
        per_page: filterParams.per_page,
      },
    });

    if (response.status === 200 && response.data.code === 0) {
      skills.value = response.data.data.items;
      pagination.totalItems = response.data.data.pagination.total_items;
      pagination.totalPages = response.data.data.pagination.total_pages;
      pagination.page = response.data.data.pagination.page;
      pagination.perPage = response.data.data.pagination.per_page;
    } else {
      ElMessage.error(response.data.message || '获取技能列表失败');
    }
  } catch (error: any) {
    console.error('获取技能列表失败:', error);
    ElMessage.error(error.response?.data?.message || '获取技能列表失败，请稍后重试。');
  } finally {
    loading.value = false;
  }
};

// 应用筛选条件
const applyFilters = () => {
  filterParams.page = 1; // 重置到第一页
  fetchSkills();
};

// 分页切换
const handlePageChange = (newPage: number): void => {
  filterParams.page = newPage;
  fetchSkills();
};

// 组件挂载时加载数据
onMounted(() => {
  fetchSkills();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1200px;
  margin: 20px auto;
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
.loading-state, .empty-state {
  padding: 40px 0;
  text-align: center;
}
.skills-list {
  margin-top: 20px;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>