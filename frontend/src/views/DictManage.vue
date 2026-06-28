<template>
  <div>
    <el-tabs v-model="activeType" @tab-change="load">
      <el-tab-pane v-for="t in TYPES" :key="t.key" :label="t.label" :name="t.key" />
    </el-tabs>

    <el-card>
      <div style="margin-bottom: 12px">
        <el-input v-model="q" placeholder="按名称搜索" clearable style="width: 220px" @keyup.enter="load" />
        <el-button @click="load" style="margin-left: 8px">搜索</el-button>
        <el-button type="success" @click="openCreate">＋ 新增{{ currentLabel }}</el-button>
      </div>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column v-if="activeType === 'models'" label="品牌" width="120">
          <template #default="{ row }">{{ row.brand_name || '-' }}</template>
        </el-table-column>
        <el-table-column v-if="activeType === 'models'" prop="specs" label="规格" min-width="120" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="toggle(row)">
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="del(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dlg" :title="(form.id ? '编辑' : '新增') + currentLabel" :fullscreen="isMobile" width="440px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item v-if="activeType === 'models'" label="品牌" required>
          <el-select v-model="form.brand_id" filterable placeholder="选择品牌" style="width: 100%">
            <el-option v-for="b in brands" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="activeType === 'models'" label="规格">
          <el-input v-model="form.specs" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" controls-position="right" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 相似项提示 -->
    <el-dialog v-model="similarDlg" title="检测到相似项" :fullscreen="isMobile" width="420px">
      <p style="margin-top: 0">已存在与「<b>{{ form.name }}</b>」相似的项目：</p>
      <el-table :data="similar" size="small" :show-header="false" border>
        <el-table-column prop="name" />
        <el-table-column width="100" align="right">
          <template #default="{ row }"><el-tag size="small" type="warning">{{ row.score }}% 相似</el-tag></template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="similarDlg = false">返回修改</el-button>
        <el-button type="warning" @click="forceCreate">仍要新建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api'
import { useBreakpoint } from '../composables/useBreakpoint'
import { useDictStore } from '../stores/dicts'

const { isMobile } = useBreakpoint()
const dictStore = useDictStore()

const TYPES = [
  { key: 'brands', label: '品牌' },
  { key: 'models', label: '型号' },
  { key: 'sites', label: '地点' },
  { key: 'systems', label: '故障系统' },
  { key: 'symptoms', label: '故障现象' },
  { key: 'causes', label: '故障原因' },
  { key: 'repairs', label: '维修方式' },
]
const activeType = ref('systems')
const currentLabel = computed(() => TYPES.find((t) => t.key === activeType.value)?.label || '')

const rows = ref([])
const brands = ref([])
const q = ref('')
const loading = ref(false)
const dlg = ref(false)
const saving = ref(false)
const similarDlg = ref(false)
const similar = ref([])
const form = reactive({ id: null, name: '', brand_id: null, specs: '', sort_order: 0 })

async function load() {
  loading.value = true
  dictStore.invalidate(activeType.value)
  try {
    const { data } = await http.get(`/api/dicts/${activeType.value}`, {
      // 不传 active 参数，后端返回"启用+停用"全集
      params: { q: q.value || undefined },
    })
    rows.value = data
    if (activeType.value === 'models') {
      const { data: b } = await http.get('/api/dicts/brands')
      brands.value = b
    }
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, { id: null, name: '', brand_id: null, specs: '', sort_order: 0 })
  dlg.value = true
}
function openEdit(row) {
  Object.assign(form, { id: row.id, name: row.name, brand_id: row.brand_id, specs: row.specs || '', sort_order: row.sort_order })
  dlg.value = true
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  if (activeType.value === 'models' && !form.brand_id) {
    ElMessage.warning('请选择品牌')
    return
  }
  saving.value = true
  try {
    const payload = { name: form.name.trim(), sort_order: form.sort_order, is_active: true }
    if (activeType.value === 'models') {
      payload.brand_id = form.brand_id
      payload.specs = form.specs
    }
    if (form.id) {
      await http.put(`/api/dicts/${activeType.value}/${form.id}`, payload)
      ElMessage.success('已更新')
      dlg.value = false
      load()
    } else {
      // 新增前查重
      const { data } = await http.get(`/api/dicts/${activeType.value}/similar`, {
        params: { q: form.name.trim() },
      })
      if (data && data.length) {
        similar.value = data
        similarDlg.value = true
      } else {
        await doCreate(payload)
      }
    }
  } finally {
    saving.value = false
  }
}

async function forceCreate() {
  const payload = { name: form.name.trim(), sort_order: form.sort_order, is_active: true }
  if (activeType.value === 'models') {
    payload.brand_id = form.brand_id
    payload.specs = form.specs
  }
  similarDlg.value = false
  await doCreate(payload)
}

async function doCreate(payload) {
  await http.post(`/api/dicts/${activeType.value}`, payload)
  ElMessage.success('已新建')
  dlg.value = false
  load()
}

async function toggle(row) {
  await http.put(`/api/dicts/${activeType.value}/${row.id}`, { is_active: !row.is_active })
  load()
}

async function del(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.name}」？若已被引用将改为提示。`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await http.delete(`/api/dicts/${activeType.value}/${row.id}`)
    ElMessage.success('已删除')
    load()
  } catch {
    /* 被引用时 409 由全局拦截器提示 */
  }
}

onMounted(load)
</script>
