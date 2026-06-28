import { createRouter, createWebHashHistory } from 'vue-router'

// hash 路由：静态托管(GitHub Pages)下刷新不 404，无需服务端 rewrite。
const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/settings', component: () => import('../views/Settings.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '统计分析' } },
      { path: 'faults', component: () => import('../views/FaultList.vue'), meta: { title: '故障记录' } },
      { path: 'faults/new', component: () => import('../views/FaultForm.vue'), meta: { title: '新增故障' } },
      { path: 'faults/:id/edit', component: () => import('../views/FaultForm.vue'), meta: { title: '编辑故障' } },
      { path: 'forklifts', component: () => import('../views/ForkliftList.vue'), meta: { title: '叉车档案' } },
      { path: 'dicts', component: () => import('../views/DictManage.vue'), meta: { title: '字典管理' } },
      { path: 'users', component: () => import('../views/UserManage.vue'), meta: { title: '用户管理' } },
    ],
  },
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to) => {
  // 使用动态 import 避免循环依赖
  const auth = JSON.parse(localStorage.getItem('ff_user') || 'null')
  const token = localStorage.getItem('ff_token')
  const backend = localStorage.getItem('ff_backend_url')
  // 生产环境(GitHub Pages 等)必须先设置后端地址；
  // 开发环境(baseURL 为空时走 vite 代理)放行。
  if (!import.meta.env.DEV && !backend && to.path !== '/settings') return '/settings'
  if (to.meta.public) return true
  if (!token || !auth) return '/login'
  return true
})

export default router
