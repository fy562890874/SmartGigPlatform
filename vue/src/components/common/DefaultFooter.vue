<template>
  <el-footer class="default-footer">
    <div class="footer-content">
      <div class="footer-links">
        <el-link @click="navigate('/about')">关于我们</el-link>
        <el-divider direction="vertical" />
        <el-link @click="navigate('/help')">帮助中心</el-link>
        <el-divider direction="vertical" />
        <el-link href="#">服务协议</el-link>
        <el-divider direction="vertical" />
        <el-link href="#">隐私政策</el-link>
      </div>
      <div class="copyright">
        © 2025 智慧零工平台 All Rights Reserved. 技术支持：[Your Company/Department]
      </div>
    </div>
  </el-footer>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElFooter, ElLink, ElDivider } from 'element-plus'

const router = useRouter()

function navigate(path: string) {
  router.push(path)
}
</script>

<style scoped>
.default-footer {
  height: auto; /* Adjust height automatically */
  background-color: #f0f2f5; /* Lighter gray background */
  color: var(--muted-text-color);
  padding: 20px 24px;
  border-top: 1px solid var(--border-color-light);
  margin-top: 30px; /* Add some space above footer */
}

.footer-content {
  max-width: 1200px; /* Limit content width */
  margin: 0 auto;
  text-align: center;
}

.footer-links {
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap; /* Allow links to wrap on smaller screens */
  gap: 5px 10px; /* Vertical and horizontal gap */
}

.footer-links .el-link {
  color: var(--muted-text-color);
  font-size: 13px;
}
.footer-links .el-link:hover {
  color: var(--primary-red);
}
.footer-links .el-divider--vertical {
    height: 1em; /* Match link height */
    background-color: var(--border-color);
}

.copyright {
  font-size: 12px;
}
</style>
