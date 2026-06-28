<template>
  <div>
    <el-card style="margin-bottom: 12px">
      <el-form inline>
        <el-form-item label="资产/部门">
          <el-input v-model="q" placeholder="资产编号/部门" clearable style="width: 200px" @keyup.enter="load(1)" />
        </el-form-item>
        <el-form-item label="地点">
          <DictSelect dtype="sites" label="地点" v-model="siteId" placeholder="全部" style="width: 150px" @update:model-value="load(1)" />
        </el-form-item>
        <el-button type="primary" @click="load(1)">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button type="success" @click="openCreate">＋ 新建叉车</el-button>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="asset_no" label="资产编号" width="130" />
        <el-table-column label="型号" width="160">
          <template #default="{ row }">{{ row.brand_name }} {{ row.model_name }}</template>
        </el-table-column>
        <el-table-column prop="site_name" label="地点" width="100" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column prop="purchase_date" label="购入日期" width="120" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '在用' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="del(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        style="margin-top: 12px; display: flex; justify-content: flex-end"
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="load()"
      />
    </el-card>

    <el-dialog v-model="dlg" :title="form.id ? '编辑叉车' : '新建叉车'" :fullscreen="isMobile" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="资产编号" required>
          <el-input v-model="form.asset_no" />
        </el-form-item>
        <el-form-item label="品牌">
          <DictSelect dtype="brands" label="品牌" v-model="form.brand_temp" :allow-create="true" placeholder="选择品牌" />
        </el-form-item>
        <el-form-item label="型号">
          <DictSelect dtype="models" label="型号" v-model="form.model_id" :extra-fields="modelExtra" placeholder="选择或新建型号" />
        </el-form-item>
        <el-form-item label="地点">
          <DictSelect dtype="sites" label="地点" v-model="form.site_id" placeholder="选择或新建地点" />
        </el-form-item>
        <el-form-item label="部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="购入日期">
          <el-date-picker v-model="form.purchase_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="在用" value="在用" />
            <el-option label="停用" value="停用" />
            <el-option label="报废" value="报废" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api'
import DictSelect from '../components/DictSelect.vue'
import { useBreakpoint } from '../composables/useBreakpoint'

const { isMobile } = useBreakpoint()

const q = ref('')
const siteId = ref(null)
const rows = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)
const dlg = ref(false)
const saving = ref(false)

const brands = ref([])
const modelExtra = ref([])
const emptyForm = () => ({
  id: null, asset_no: '', model_id: null, brand_temp: null, site_id: null,
  department: '', purchase_date: null, status: '在用', remark: '',
})
const form = reactive(emptyForm())

async function loadBrands() {
  const { data } = await http.get('/api/dicts/brands')
  brands.value = data
  modelExtra.value = [{ key: 'brand_id', label: '品牌', type: 'select', options: data }]
}

async function load(p) {
  if (p) page.value = p
  loading.value = true
  try {
    const { data } = await http.get('/api/forklifts', {
      params: { q: q.value || undefined, site_id: siteId.value || undefined, page: page.value, size: size.value },
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function reset() {
  q.value = ''
  siteId.value = null
  load(1)
}

function openCreate() {
  Object.assign(form, emptyForm())
  dlg.value = true
}

function openEdit(row) {
  Object.assign(form, emptyForm(), {
    id: row.id, asset_no: row.asset_no, model_id: row.model_id, site_id: row.site_id,
    department: row.department, purchase_date: row.purchase_date, status: row.status, remark: row.remark,
  })
  dlg.value = true
}

async function save() {
  if (!form.asset_no) {
    ElMessage.warning('请填写资产编号')
    return
  }
  if (!form.model_id) {
    ElMessage.warning('请选择型号')
    return
  }
  saving.value = true
  try {
    const payload = {
      asset_no: form.asset_no, model_id: form.model_id, site_id: form.site_id,
      department: form.department, purchase_date: form.purchase_date, status: form.status, remark: form.remark,
    }
    if (form.id) await http.put('/api/forklifts/' + form.id, payload)
    else await http.post('/api/forklifts', payload)
    ElMessage.success('保存成功')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function del(row) {
  await ElMessageBox.confirm('确认删除叉车 ' + row.asset_no + ' ？', '提示', { type: 'warning' })
  await http.delete('/api/forklifts/' + row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  await loadBrands()
  load(1)
})
</script>
