<template>
  <el-container style="height: 100vh">
    <el-aside v-if="!isMobile" width="210px" class="aside">
      <div class="logo">🚜 叉车故障系统</div>
      <el-menu :default-active="active" router>
        <el-menu-item v-for="m in menus" :key="m.index" :index="m.index">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="left">
          <el-button v-if="isMobile" text size="large" :icon="Menu" @click="drawer = true" />
          <span class="title">{{ route.meta.title || '叉车故障记录系统' }}</span>
        </div>
        <div class="right">
          <el-button v-if="isMobile" type="primary" :icon="Plus" circle @click="router.push('/faults/new')" />
          <span v-if="!isMobile" class="user">{{ auth.user?.display_name || auth.user?.username }}</span>
          <el-button text @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <el-drawer v-model="drawer" direction="ltr" size="68%" :with-header="false">
    <div class="logo drawer-logo">🚜 叉车故障系统</div>
    <el-menu :default-active="active" router @select="drawer = false">
      <el-menu-item v-for="m in menus" :key="m.index" :index="m.index">
        <el-icon><component :is="m.icon" /></el-icon>
        <span>{{ m.label }}</span>
      </el-menu-item>
    </el-menu>
  </el-drawer>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu, Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useBreakpoint } from '../composables/useBreakpoint'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { isMobile } = useBreakpoint()
const drawer = ref(false)

const menus = [
  { index: '/dashboard', icon: 'DataLine', label: '统计分析' },
  { index: '/faults', icon: 'Document', label: '故障记录' },
  { index: '/forklifts', icon: 'Tools', label: '叉车档案' },
  { index: '/dicts', icon: 'Collection', label: '字典管理' },
  { index: '/users', icon: 'User', label: '用户管理' },
  { index: '/settings', icon: 'Setting', label: '后端设置' },
]

const active = computed(() => (route.path.startsWith('/faults') ? '/faults' : route.path))

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.aside { background: #001529; }
.logo { height: 56px; line-height: 56px; text-align: center; color: #fff; font-size: 16px; font-weight: 600; }
.drawer-logo { background: #001529; }
.aside :deep(.el-menu) { background: #001529; border-right: none; }
.aside :deep(.el-menu-item) { color: #c9d1d9; }
.aside :deep(.el-menu-item.is-active) { background: #409eff; color: #fff; }
.aside :deep(.el-menu-item:hover) { background: #00203a; }
.header { background: #fff; border-bottom: 1px solid #ebeef5; display: flex; align-items: center; justify-content: space-between; }
.header .left { display: flex; align-items: center; gap: 4px; }
.header .title { font-size: 16px; font-weight: 600; }
.header .right { display: flex; align-items: center; gap: 8px; }
.header .user { color: #606266; }
</style>
