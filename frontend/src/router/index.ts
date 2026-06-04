import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/app/projects',
    },
    {
      path: '/auth',
      component: () => import('@/views/auth/AuthLayout.vue'),
      children: [
        {
          path: 'login',
          name: 'login',
          component: () => import('@/views/auth/LoginView.vue'),
        },
        {
          path: 'register',
          name: 'register',
          component: () => import('@/views/auth/RegisterView.vue'),
        },
      ],
    },
    {
      path: '/app',
      component: () => import('@/views/app/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/views/app/ProjectsView.vue'),
        },
        {
          path: 'projects/:project_id',
          name: 'project-detail',
          component: () => import('@/views/app/ProjectDetailView.vue'),
        },
        {
          path: 'pages/:page_id',
          name: 'page-workspace',
          component: () => import('@/views/workspace/AnnotationWorkspace.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/app/SettingsView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

// 全局导航守卫
router.beforeEach((to, _from, next) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth) {
    // TODO: 检查登录状态
    // const isAuthenticated = checkAuth()
    // if (!isAuthenticated) {
    //   next({ name: 'login' })
    //   return
    // }
  }

  next()
})

export default router
