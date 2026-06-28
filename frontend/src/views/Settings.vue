<template>
  <div class="settings-wrap">
    <el-card class="card">
      <h3 style="margin-top: 0">后端服务器设置</h3>
      <p class="desc">
        前端可托管在任意位置（如 GitHub Pages）。请填写后端 API 地址，<br />
        例如服务器上的地址：<code>http://10.0.0.152:8000</code>
      </p>
      <el-input v-model="url" placeholder="https://api.asos233.com" clearable>
        <template #prepend>API 地址</template>
      </el-input>
      <div class="actions">
        <el-button type="primary" :loading="testing" @click="testAndSave">测试并保存</el-button>
        <el-button v-if="auth.token" @click="$router.push('/')">返回系统</el-button>
        <el-button v-else @click="goLogin">去登录</el-button>
      </div>
      <el-alert
        v-if="result === false"
        type="error"
        :closable="false"
        title="无法连接后端，请检查地址是否正确、后端是否已启动，以及是否跨域(CORS)被拦。"
        style="margin-top: 12px"
      />
      <el-alert
        v-if="result === true"
        type="success"
        :closable="false"
        title="连接成功，已保存。"
        style="margin-top: 12px"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { setBackend } from '../api'

const auth = useAuthStore()
const router = useRouter()
const url = ref(auth.backend || 'https://api.asos233.com')
const testing = ref(false)
const result = ref(null)

async function testAndSave() {
  testing.value = true
  result.value = null
  const u = (url.value || '').trim().replace(/\/$/, '')
  if (!u) {
    result.value = false
    testing.value = false
    return
  }
  try {
    // 用独立 axios 实例探测，避开全局拦截器与旧 baseURL
    await axios.get(u + '/api/health', { timeout: 6000 })
    setBackend(u)
    auth.backend = u
    result.value = true
  } catch {
    result.value = false
  } finally {
    testing.value = false
  }
}

function goLogin() {
  router.push('/login')
}
</script>

<style scoped>
.settings-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}
.card { width: 460px; }
.desc { color: #888; font-size: 13px; line-height: 1.6; }
.actions { margin-top: 14px; }
code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; }
</style>
