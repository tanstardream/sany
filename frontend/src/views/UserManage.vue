<template>
  <el-card>
    <div style="margin-bottom: 12px">
      <el-button type="success" @click="openCreate">＋ 新增用户</el-button>
    </div>
    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="账号" width="150" />
      <el-table-column prop="display_name" label="姓名" width="150" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑/改密</el-button>
          <el-button link type="danger" :disabled="row.id === me?.id" @click="del(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="form.id ? '编辑用户' : '新增用户'" :fullscreen="isMobile" width="440px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="账号" required>
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item :label="form.id ? '新密码' : '密码'" :required="!form.id">
          <el-input v-model="form.password" type="password" show-password :placeholder="form.id ? '留空则不修改' : ''" />
        </el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.display_name" /></el-form-item>
        <el-form-item v-if="form.id" label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api'
import { useAuthStore } from '../stores/auth'
import { useBreakpoint } from '../composables/useBreakpoint'

const { isMobile } = useBreakpoint()

const auth = useAuthStore()
const me = computed(() => auth.user)
const rows = ref([])
const loading = ref(false)
const dlg = ref(false)
const saving = ref(false)
const form = reactive({ id: null, username: '', password: '', display_name: '', is_active: true })

function fmt(s) {
  return s ? new Date(s).toLocaleString('zh-CN') : ''
}

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/api/users')
    rows.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, { id: null, username: '', password: '', display_name: '', is_active: true })
  dlg.value = true
}
function openEdit(row) {
  Object.assign(form, { id: row.id, username: row.username, password: '', display_name: row.display_name, is_active: row.is_active })
  dlg.value = true
}

async function save() {
  if (!form.username) {
    ElMessage.warning('请输入账号')
    return
  }
  if (!form.id && !form.password) {
    ElMessage.warning('请输入密码')
    return
  }
  saving.value = true
  try {
    if (form.id) {
      const payload = { display_name: form.display_name, is_active: form.is_active }
      if (form.password) payload.password = form.password
      await http.put('/api/users/' + form.id, payload)
    } else {
      await http.post('/api/users', {
        username: form.username,
        password: form.password,
        display_name: form.display_name,
      })
    }
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function del(row) {
  await ElMessageBox.confirm(`确认删除用户「${row.username}」？`, '提示', { type: 'warning' })
  await http.delete('/api/users/' + row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
