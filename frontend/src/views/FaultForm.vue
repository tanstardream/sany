<template>
  <div>
    <el-page-header @back="$router.back()" style="margin-bottom: 16px">
      <template #content>{{ isEdit ? '编辑故障' : '新增故障' }}</template>
    </el-page-header>

    <el-card>
      <el-form :model="form" :label-position="isMobile ? 'top' : 'right'" label-width="100px" style="max-width: 780px">
        <el-divider content-position="left">基本信息</el-divider>
        <el-form-item label="叉车" required>
          <el-select
            v-model="form.forklift_id"
            filterable
            placeholder="选择叉车（按资产编号/型号筛选）"
            style="width: 100%"
          >
            <el-option
              v-for="f in forklifts"
              :key="f.id"
              :label="`${f.asset_no} | ${f.brand_name || ''} ${f.model_name || ''} | ${f.site_name || ''}`"
              :value="f.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="故障日期" required>
          <el-date-picker
            v-model="form.fault_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="处理人">
          <el-input v-model="form.handler" placeholder="处理人姓名" />
        </el-form-item>

        <el-divider content-position="left">故障分类（可下拉内新建）</el-divider>
        <el-form-item label="故障系统">
          <DictSelect dtype="systems" label="系统" v-model="form.system_id" placeholder="选择或新建系统" />
        </el-form-item>
        <el-form-item label="故障现象">
          <DictSelect dtype="symptoms" label="现象" v-model="form.symptom_id" placeholder="选择或新建现象" />
        </el-form-item>
        <el-form-item label="故障原因">
          <DictSelect dtype="causes" label="原因" v-model="form.cause_id" placeholder="选择或新建原因" />
        </el-form-item>
        <el-form-item label="维修方式">
          <DictSelect dtype="repairs" label="维修方式" v-model="form.repair_id" placeholder="选择或新建维修方式" />
        </el-form-item>

        <el-divider content-position="left">补充信息</el-divider>
        <el-form-item label="停机时长(h)">
          <el-input-number v-model="form.downtime_hours" :min="0" :precision="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="维修费用(元)">
          <el-input-number v-model="form.repair_cost" :min="0" :precision="2" controls-position="right" />
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="补充说明" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api'
import DictSelect from '../components/DictSelect.vue'
import { useBreakpoint } from '../composables/useBreakpoint'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const { isMobile } = useBreakpoint()

const forklifts = ref([])
const saving = ref(false)
const form = ref({
  forklift_id: null,
  fault_date: new Date().toISOString().slice(0, 10),
  system_id: null,
  symptom_id: null,
  cause_id: null,
  repair_id: null,
  handler: '',
  downtime_hours: null,
  repair_cost: null,
  description: '',
})

onMounted(async () => {
  const { data } = await http.get('/api/forklifts/all')
  forklifts.value = data
  if (isEdit.value) {
    const { data: f } = await http.get('/api/faults/' + route.params.id)
    form.value = {
      forklift_id: f.forklift_id,
      fault_date: f.fault_date,
      system_id: f.system_id,
      symptom_id: f.symptom_id,
      cause_id: f.cause_id,
      repair_id: f.repair_id,
      handler: f.handler || '',
      downtime_hours: f.downtime_hours,
      repair_cost: f.repair_cost,
      description: f.description || '',
    }
  }
})

async function save() {
  if (!form.value.forklift_id) {
    ElMessage.warning('请选择叉车')
    return
  }
  if (!form.value.fault_date) {
    ElMessage.warning('请选择故障日期')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await http.put('/api/faults/' + route.params.id, form.value)
    } else {
      await http.post('/api/faults', form.value)
    }
    ElMessage.success('保存成功')
    router.push('/faults')
  } finally {
    saving.value = false
  }
}
</script>
