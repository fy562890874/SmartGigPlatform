<template>
  <el-card class="job-card" shadow="hover" @click="$emit('click')">
    <div class="job-card-header">
      <h3>{{ job.title }}</h3>
      <span class="job-salary">{{ job.salary_range_display }}</span>
    </div>
    <div class="job-card-body">
      <p>{{ job.company_name_display }}</p>
      <p>{{ job.location_city }} {{ job.location_district }}</p>
    </div>
    <div class="job-card-footer">
      <el-tag v-for="tag in job.job_tags" :key="tag" type="info" effect="dark">{{ tag }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

defineProps({
  job: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped>
.job-card {
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.job-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.job-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.job-card-header h3 {
  font-size: 1.2em;
  font-weight: bold;
  margin: 0;
}

.job-card-header .job-salary {
  font-size: 1em;
  color: #67C23A;
}

.job-card-body p {
  margin: 0;
  color: #606266;
  font-size: 0.9em;
}

.job-card-footer {
  margin-top: 10px;
}

.job-card-footer .el-tag {
  margin-right: 5px;
}
</style>
