<template>
  <div class="help-container page-container">
    <el-card class="help-card" shadow="never">
      <template #header>
        <div class="help-title">帮助中心</div>
      </template>
      <el-collapse accordion>
        <el-collapse-item title="如何注册和登录？" name="1">
          <div>点击右上角“注册”，填写手机号、验证码、密码等信息即可注册。已有账号可直接登录。</div>
        </el-collapse-item>
        <el-collapse-item title="如何找工作？" name="2">
          <div>在首页或工作广场页面，使用搜索和筛选功能查找合适的岗位，点击岗位卡片可查看详情并报名。</div>
        </el-collapse-item>
        <el-collapse-item title="如何发布工作？" name="3">
          <div>登录后点击底部“发布”按钮，填写工作信息并提交即可发布。</div>
        </el-collapse-item>
        <el-collapse-item title="如何找回密码？" name="4">
          <div>在登录页面点击“忘记密码”，通过手机号和验证码重置新密码。</div>
        </el-collapse-item>
        <el-collapse-item title="如何联系客服？" name="5">
          <div>您可以拨打客服电话 <el-link type="primary" href="tel:400-123-4567">400-123-4567</el-link> 或发送邮件至 <el-link type="primary" href="mailto:service@smartgig.com">service@smartgig.com</el-link>。</div>
        </el-collapse-item>
      </el-collapse>
      <el-divider />
      <div class="help-contact">
        <span>如需进一步帮助，请联系客服：</span>
        <el-link type="primary" href="tel:400-123-4567">400-123-4567</el-link>
        <el-link type="primary" href="mailto:service@smartgig.com">service@smartgig.com</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.help-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 60vh;
}
.help-card {
  max-width: 700px;
  width: 100%;
  margin: 40px auto;
  border-radius: 8px;
}
.help-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--primary-red);
  text-align: center;
}
.help-contact {
  margin-top: 20px;
  text-align: center;
  font-size: 15px;
}
</style>