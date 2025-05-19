import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth' // 假设 authStore 在此路径
// import { useUserStore } from '@/stores/user' // 如果需要根据用户角色等预加载信息

// 视图组件 - 假设这些文件都将创建在 views 目录下或其子目录
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/auth/Login.vue'
import RegisterView from '../views/auth/Register.vue'
import ForgotPasswordView from '../views/auth/ForgotPassword.vue' // 假设创建
import JobsView from '../views/JobsView.vue'
import JobDetailView from '../views/JobDetailView.vue' // 需创建
import AboutView from '../views/AboutView.vue'
import HelpCenterView from '../views/HelpCenterView.vue'
import SettingsView from '../views/SettingsView.vue'
import NotFoundView from '../views/NotFoundView.vue'

// 零工相关视图
import FreelancerDashboardView from '../views/freelancer/FreelancerDashboardView.vue' // 需创建
import EditFreelancerProfileView from '../views/freelancer/EditFreelancerProfileView.vue' // 需创建
import ManageFreelancerSkillsView from '../views/freelancer/ManageFreelancerSkillsView.vue' // 需创建
import MyApplicationsView from '../views/freelancer/MyApplicationsView.vue' // 需创建

// 雇主相关视图
import EmployerDashboardView from '../views/employer/EmployerDashboardView.vue' // 需创建
import EditEmployerProfileView from '../views/employer/EditEmployerProfileView.vue' // 需创建
import PostJobView from '../views/employer/PostJobView.vue' // 需创建
import MyPostedJobsView from '../views/employer/MyPostedJobsView.vue' // 需创建
import JobApplicantsView from '../views/employer/JobApplicantsView.vue' // 需创建

// 通用个人中心相关视图 (认证)
import MyVerificationsView from '../views/verifications/MyVerificationsView.vue'
import SubmitVerificationView from '../views/verifications/SubmitVerificationView.vue'


const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/auth/login',
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true }, // 只允许未登录用户访问
  },
  {
    path: '/auth/register',
    name: 'register',
    component: RegisterView,
    meta: { guestOnly: true },
  },
  {
    path: '/auth/forgot-password',
    name: 'forgot-password',
    component: ForgotPasswordView, // 确保创建此组件
    meta: { guestOnly: true },
  },
  {
    path: '/jobs',
    name: 'jobs',
    component: JobsView,
  },
  {
    path: '/jobs/new',
    name: 'post-job',
    component: PostJobView,
    meta: { requiresAuth: true, roles: ['employer'] }, // 仅雇主可访问
  },
  {
    path: '/jobs/:id',
    name: 'job-detail',
    component: JobDetailView, // 确保创建此组件
    props: true, // 将 :id 作为 prop 传递给组件
  },
  {
    path: '/jobs/:jobId/applicants',
    name: 'job-applicants',
    component: JobApplicantsView,
    props: true,
    meta: { requiresAuth: true, roles: ['employer'] },
  },
  {
    path: '/jobs/edit/:id', // 编辑职位
    name: 'edit-job',
    component: PostJobView, // 可复用 PostJobView，通过 prop 区分是新建还是编辑
    props: true,
    meta: { requiresAuth: true, roles: ['employer'] },
  },
  {
    path: '/about',
    name: 'about',
    component: AboutView,
  },
  {
    path: '/help',
    name: 'help',
    component: HelpCenterView,
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { requiresAuth: true },
  },
  // 零工专属路由
  {
    path: '/dashboard/freelancer',
    name: 'freelancer-dashboard',
    component: FreelancerDashboardView,
    meta: { requiresAuth: true, roles: ['freelancer'] },
  },
  {
    path: '/profile/freelancer/edit',
    name: 'edit-freelancer-profile',
    component: EditFreelancerProfileView,
    meta: { requiresAuth: true, roles: ['freelancer'] },
  },
  {
    path: '/profile/freelancer/skills',
    name: 'manage-freelancer-skills',
    component: ManageFreelancerSkillsView,
    meta: { requiresAuth: true, roles: ['freelancer'] },
  },
  {
    path: '/applications/my',
    name: 'my-applications',
    component: MyApplicationsView,
    meta: { requiresAuth: true, roles: ['freelancer'] },
  },
  // 雇主专属路由
  {
    path: '/dashboard/employer',
    name: 'employer-dashboard',
    component: EmployerDashboardView,
    meta: { requiresAuth: true, roles: ['employer'] },
  },
  {
    path: '/profile/employer/edit',
    name: 'edit-employer-profile',
    component: EditEmployerProfileView,
    meta: { requiresAuth: true, roles: ['employer'] },
  },
  {
    path: '/jobs/posted', // 雇主查看自己发布的职位
    name: 'my-posted-jobs',
    component: MyPostedJobsView,
    meta: { requiresAuth: true, roles: ['employer'] },
  },
  // 通用个人中心 (需登录)
  {
    path: '/my-orders',
    name: 'my-orders',
    component: () => import('../views/orders/OrderListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders/:orderId',
    name: 'order-detail',
    component: () => import('../views/orders/OrderDetailView.vue'),
    props: true,
    meta: { requiresAuth: true }, // 需要进一步逻辑判断用户是否有权查看此订单
  },
  {
    path: '/profile/verification',
    name: 'verification',
    component: SubmitVerificationView,
    meta: { requiresAuth: true },
  },
  {
    path: '/verifications/submit',
    name: 'submit-verification',
    component: SubmitVerificationView,
    meta: { requiresAuth: true },
  },
  {
    path: '/verifications/records',
    name: 'my-verifications',
    component: MyVerificationsView,
    meta: { requiresAuth: true },
  },
  // New route for SkillsView
  {
    path: '/skills',
    name: 'skills',
    component: () => import('../views/SkillsView.vue'), // Lazy load for better performance
    meta: { requiresAuth: false } // Publicly accessible page
  },
  // 404 页面
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

// 导航守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  // 确保 Pinia store 初始化完成 (特别是 token 的加载)
  // Pinia store 通常在应用加载时通过插件或在 main.ts 中初始化
  // 此处我们假设 authStore 的状态 (isLoggedIn, user) 在此时已反映 localStorage 中的 token

  const requiresAuth = to.meta.requiresAuth
  const guestOnly = to.meta.guestOnly
  const requiredRoles = to.meta.roles as string[] | undefined

  if (guestOnly && authStore.isLoggedIn) {
    // 如果是只允许访客访问的页面但用户已登录，则重定向到首页
    next({ name: 'home' })
  } else if (requiresAuth && !authStore.isLoggedIn) {
    // 如果需要认证但用户未登录，重定向到登录页
    // 可以保存用户尝试访问的页面，以便登录后重定向回来
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (requiresAuth && authStore.isLoggedIn && requiredRoles) {
    // 如果需要特定角色
    // 确保用户信息（包括角色）已加载
    // 如果 authStore.user 是 null 或者 roles 不存在，可能需要先获取用户信息
    if (!authStore.user || !authStore.user.available_roles) { // 检查 available_roles
        // 可能需要一个 action 来获取当前用户信息，如果它不是在 init() 中处理的
        // await authStore.fetchCurrentUser(); // 示例, 确保 authStore 有此方法或 init() 已处理
        // 如果 init() 异步加载用户信息，这里可能不需要额外操作，或者需要等待 init 完成
    }
    // 从 authStore 获取用户角色。确保 authStore.user 和 authStore.user.available_roles 存在且正确
    const userRoles = authStore.user?.available_roles || [] // 主要使用 available_roles

    const hasRole = requiredRoles.some(role => userRoles.includes(role))
    if (hasRole) {
      next()
    } else {
      // 如果用户没有所需角色，可以重定向到无权限页面或首页
      // console.warn(\`Navigation blocked: User roles \${userRoles} do not include required roles \${requiredRoles} for path \${to.path}\`);
      next({ name: 'home' }) // 或者一个专门的 'unauthorized' 页面
    }
  } else {
    // 其他情况，直接允许导航
    next()
  }
})

export default router