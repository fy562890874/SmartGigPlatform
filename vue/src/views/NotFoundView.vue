<template>
  <div class="not-found-container">
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for does not exist.</p>
    <router-link to="/">Go to Home</router-link>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
/* NotFoundView.css 样式合并自此处 */
body, .not-found-container {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.not-found-title {
  font-size: 32px;
  font-weight: bold;
  color: var(--primary-red);
  margin-bottom: 16px;
}
.not-found-desc {
  font-size: 18px;
  color: var(--muted-text-color);
  margin-bottom: 24px;
}
</style>