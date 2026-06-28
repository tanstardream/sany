<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <h2 class="title">🚜 叉车故障记录系统</h2>
      <div class="backend-info">
        后端：<b>{{ auth.backend || '未设置' }}</b>
        <router-link to="/settings"> [修改]</router-link>
      </div>
      <el-form :model="form" label-position="top" @submit.prevent="doLogin" style="margin-top: 12px">
        <el-form-item label="账号">
          <el-input v-model="form.username" placeholder="账号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码"
            @keyup.enter="doLogin"
          />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" @click="doLogin">登 录</el-button>
      </el-form>
      <div class="hint">首次登录后，请在「用户管理」中修改密码</div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const form = reactive({ username: 'admin', password: '' })
const loading = ref(false)

async function doLogin() {
  if (!auth.hasBackend) {
    router.push('/settings')
    return
  }
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    router.push(route.query.redirect || '/')
  } catch {
    /* 错误提示由全局拦截器处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f2a44, #2d3a5a);
}
.login-card { width: min(380px, 92vw); padding: 12px 16px; }
.title { text-align: center; margin: 4px 0; }
.backend-info { text-align: center; color: #888; font-size: 13px; }
.hint { text-align: center; color: #aaa; font-size: 12px; margin-top: 8px; }
</style>
