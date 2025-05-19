<template>
  <el-header class="default-header">
    <div class="header-content">
      <div class="logo" @click="goHome">
        <!-- <img src="@/assets/logo.png" alt="Logo" class="logo-img"> -->
        <span class="logo-text">智慧零工平台</span>
      </div>
      <el-menu
        mode="horizontal"
        :default-active="activeMenu"
        class="header-menu"
        background-color="transparent"
        text-color="#FFFFFF"
        active-text-color="var(--accent-gold)"
        @select="handleMenuSelect"
        :ellipsis="false"
      >
        <el-menu-item index="home">首页</el-menu-item>
        <el-menu-item index="jobs">找工作</el-menu-item>
        <el-menu-item index="about">关于我们</el-menu-item>
        <el-menu-item index="help">帮助中心</el-menu-item>
      </el-menu>
      <div class="header-right">
        <template v-if="isLoggedIn">
          <el-button text @click="navigate('/messages')" class="header-button">
            <el-badge :value="unreadCount" :hidden="!unreadCount">
              <el-icon><Bell /></el-icon>
            </el-badge>
          </el-button>
          <el-dropdown @command="handleUserCommand" trigger="click">
            <span class="user-avatar-container">
              <el-avatar :size="32" :src="userAvatar" icon="UserFilled" />
              <span class="user-nickname">{{ userNickname }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="settings">账号设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
           <el-button text @click="navigate('/auth/login')" class="header-button">登录</el-button>
           <el-button type="primary" @click="navigate('/auth/register')" size="small" class="register-btn">注册</el-button>
        </template>
      </div>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElHeader, ElMenu, ElMenuItem, ElButton, ElDropdown, ElDropdownMenu, ElDropdownItem, ElIcon, ElBadge, ElAvatar } from 'element-plus'
import { Bell, UserFilled, ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// --- Reactive State ---
const isLoggedIn = computed(() => authStore.isLoggedIn)
const userNickname = computed(() => authStore.user?.nickname || '用户')
const userAvatar = computed(() => authStore.user?.avatarUrl || '') // Default avatar or UserFilled icon will show
const unreadCount = computed(() => 0) // Placeholder for message count

// --- Computed Properties ---
const activeMenu = computed(() => {
  const path = route.path
  if (path === '/' || path.startsWith('/home')) return 'home'
  if (path.startsWith('/job')) return 'jobs'
  if (path.startsWith('/about')) return 'about'
  if (path.startsWith('/help')) return 'help'
  return ''
})

// --- Methods ---
function navigate(path: string) {
  router.push(path)
}

function goHome() {
  navigate('/')
}

function handleMenuSelect(index: string) {
  const paths: Record<string, string> = {
    home: '/',
    jobs: '/jobs', // Navigate to jobs page
    about: '/about',
    help: '/help'
  }
  if (paths[index]) {
    navigate(paths[index])
  }
}

function handleUserCommand(command: string) {
  switch (command) {
    case 'profile':
      navigate('/profile/overview') // Navigate to profile overview
      break
    case 'settings':
      navigate('/settings')
      break
    case 'logout':
      authStore.logout()
      ElMessage.success('已退出登录')
      navigate('/')
      break
  }
}
</script>

<style scoped>
.default-header {
  background-color: var(--primary-red);
  color: #ffffff;
  height: 60px;
  padding: 0 24px;
  border-bottom: 1px solid var(--primary-red-hover);
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.logo {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-right: 40px;
}

.logo-img {
  height: 30px;
  margin-right: 10px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: #ffffff;
}

.header-menu {
  flex-grow: 1;
  border-bottom: none; /* Remove default border */
  height: 100%;
  display: flex;
  align-items: center; /* Center menu items vertically */
}

.header-menu .el-menu-item {
  height: 100%;
  display: flex;
  align-items: center;
  border-bottom: none !important; /* Override potential specificity issues */
  font-size: 15px;
}
.header-menu .el-menu-item:hover {
  background-color: var(--primary-red-hover) !important;
}
.header-menu .el-menu-item.is-active {
   border-bottom: 2px solid var(--accent-gold) !important; /* Use accent for active */
   color: var(--accent-gold) !important;
   background-color: transparent !important; /* Ensure active bg is transparent */
}


.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-button {
  color: #ffffff;
}
.header-button:hover {
  color: var(--accent-gold);
}

.user-avatar-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #ffffff;
  outline: none; /* Remove focus outline */
}
.user-avatar-container:hover .user-nickname,
.user-avatar-container:hover .el-icon {
    color: var(--accent-gold);
}

.user-nickname {
  margin-left: 8px;
  margin-right: 4px;
  font-size: 14px;
}

.register-btn {
    background-color: var(--accent-gold);
    border-color: var(--accent-gold);
    color: var(--text-color);
}
.register-btn:hover {
    background-color: #e0bb4f; /* Slightly darker gold */
    border-color: #e0bb4f;
}

/* Ensure dropdown icon color */
.el-icon--right {
    color: inherit;
}
</style>
