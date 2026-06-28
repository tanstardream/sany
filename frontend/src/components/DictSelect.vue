<!--
  字典选择组件：核心 UX。
  - 可搜索下拉，优先复用已有项；
  - 下拉底部"新建"按钮 → 输入名称 → 先查相似项 → 命中则提示"使用已有 / 仍要新建"；
  - 支持额外字段(如型号的品牌)。
-->
<template>
  <el-select
    :model-value="modelValue"
    filterable
    clearable
    :placeholder="placeholder"
    :loading="loading"
    style="width: 100%"
    @change="onChange"
  >
    <el-option v-for="it in options" :key="it.id" :label="it.name" :value="it.id">
      <span>{{ it.name }}</span>
      <span v-if="!it.is_active" style="color: #bbb; font-size: 12px"> (停用)</span>
    </el-option>
    <template v-if="allowCreate" #footer>
      <el-button text type="primary" :icon="Plus" @click="openCreate">＋ 新建{{ label }}</el-button>
    </template>
  </el-select>

  <!-- 新建对话框 -->
  <el-dialog v-model="createVisible" :title="'新建' + label" :width="isMobile ? '92%' : '420px'" append-to-body>
    <el-form label-width="80px">
      <el-form-item :label="label" required>
        <el-input v-model="form.name" placeholder="请输入名称" @keyup.enter="submit" />
      </el-form-item>
      <el-form-item v-for="f in extraFields" :key="f.key" :label="f.label">
        <el-select
          v-if="f.type === 'select'"
          v-model="form[f.key]"
          clearable
          filterable
          placeholder="请选择"
          style="width: 100%"
        >
          <el-option v-for="o in f.options" :key="o.id" :label="o.name" :value="o.id" />
        </el-select>
        <el-input v-else v-model="form[f.key]" :placeholder="f.placeholder || ''" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="createVisible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
    </template>
  </el-dialog>

  <!-- 相似项提示 -->
  <el-dialog v-model="similarVisible" title="检测到相似项" :width="isMobile ? '92%' : '440px'" append-to-body>
    <p style="margin-top: 0">已存在与「<b>{{ form.name }}</b>」相似的项目，建议优先复用：</p>
    <el-table :data="similar" size="small" :show-header="false" border>
      <el-table-column prop="name" />
      <el-table-column width="100" align="right">
        <template #default="{ row }">
          <el-tag size="small" type="warning">{{ row.score }}% 相似</el-tag>
        </template>
      </el-table-column>
    </el-table>
    <p style="margin-bottom: 0; color: #888; font-size: 13px">
      复用已有项可避免字典重复；如确为不同项目，可仍要新建。
    </p>
    <template #footer>
      <el-button @click="similarVisible = false; createVisible = true">返回修改</el-button>
      <el-button
        v-for="s in similar.slice(0, 3)"
        :key="s.id"
        type="primary"
        plain
        @click="chooseExisting(s)"
      >使用「{{ s.name }}」</el-button>
      <el-button type="warning" @click="forceCreate">仍要新建</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import http from '../api'
import { useBreakpoint } from '../composables/useBreakpoint'

const { isMobile } = useBreakpoint()

const props = defineProps({
  modelValue: { type: [Number, String, null], default: null },
  dtype: { type: String, required: true },
  label: { type: String, default: '项目' },
  placeholder: { type: String, default: '请选择' },
  extraFields: { type: Array, default: () => [] },
  includeInactive: { type: Boolean, default: false },
  allowCreate: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'created'])

const options = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const params = props.includeInactive ? {} : { active: true }
    const { data } = await http.get(`/api/dicts/${props.dtype}`, { params })
    options.value = data
  } finally {
    loading.value = false
  }
}
onMounted(load)
defineExpose({ refresh: load })

function onChange(v) {
  emit('update:modelValue', v)
}

// ---- 新建 + 防重复 ----
const createVisible = ref(false)
const similarVisible = ref(false)
const submitting = ref(false)
const form = ref({ name: '' })
const similar = ref([])

function openCreate() {
  form.value = { name: '' }
  for (const f of props.extraFields) form.value[f.key] = null
  createVisible.value = true
}

async function submit() {
  if (!form.value.name || !form.value.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  try {
    const { data } = await http.get(`/api/dicts/${props.dtype}/similar`, {
      params: { q: form.value.name.trim() },
    })
    if (data && data.length) {
      similar.value = data
      createVisible.value = false
      similarVisible.value = true
      return
    }
  } catch {
    /* 查重失败则直接创建 */
  }
  doCreate()
}

function chooseExisting(s) {
  emit('update:modelValue', s.id)
  similarVisible.value = false
  createVisible.value = false
  ElMessage.success('已选用：' + s.name)
}

function forceCreate() {
  similarVisible.value = false
  doCreate()
}

async function doCreate() {
  submitting.value = true
  try {
    const payload = { name: form.value.name.trim(), is_active: true }
    for (const f of props.extraFields) payload[f.key] = form.value[f.key]
    const { data } = await http.post(`/api/dicts/${props.dtype}`, payload)
    await load()
    emit('update:modelValue', data.id)
    emit('created', data)
    createVisible.value = false
    ElMessage.success('已新建：' + data.name)
  } finally {
    submitting.value = false
  }
}
</script>
