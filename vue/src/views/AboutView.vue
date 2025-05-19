<template>
  <div class="about-container page-container">
    <el-card class="about-card" shadow="never">
      <template #header>
        <div class="about-title">关于智慧零工平台</div>
      </template>
      <div class="about-content">
        <p>智慧零工平台是由政府主导的数字化公共就业服务平台，致力于通过现代信息技术重塑传统零工市场，构建连接供需双方的智能化服务生态系统。平台融合大数据、人工智能等先进技术，提供精准匹配、在线交易、技能提升、权益保障和数据分析等全方位服务。</p>
        <el-divider />
        <h3>联系方式</h3>
        <ul>
          <li>客服电话：<el-link type="primary" href="tel:400-123-4567">400-123-4567</el-link></li>
          <li>邮箱：<el-link type="primary" href="mailto:service@smartgig.com">service@smartgig.com</el-link></li>
          <li>地址：厦门市</li>
        </ul>
        <el-divider />
        <h3>项目团队</h3>
        <p>本平台由厦门理工学院软件项目管理团队开发，团队成员包括杜家麟、汪守振、陈芯茹、周锦鸿，指导老师：XXX。</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.about-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 60vh;
}
.about-card {
  max-width: 700px;
  width: 100%;
  margin: 40px auto;
  border-radius: 8px;
}
.about-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--primary-red);
  text-align: center;
}
.about-content {
  font-size: 16px;
  color: var(--text-color);
  line-height: 1.8;
}
.about-content h3 {
  margin-top: 24px;
  color: var(--secondary-blue);
}
.about-content ul {
  padding-left: 20px;
  margin-bottom: 0;
}
</style>