<template>
  <div>
    <el-card style="margin-bottom: 12px">
      <el-form :inline="!isMobile">
        <el-form-item label="关键词">
          <el-input v-model="q" placeholder="描述/处理人/编号/资产号" clearable style="width: 200px" @keyup.enter="load(1)" />
        </el-form-item>
        <el-form-item label="系统">
          <DictSelect dtype="systems" label="系统" v-model="systemId" placeholder="全部" style="width: 160px" @update:model-value="load(1)" />
        </el-form-item>
        <el-form-item label="原因">
          <DictSelect dtype="causes" label="原因" v-model="causeId" placeholder="全部" style="width: 160px" @update:model-value="load(1)" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="range" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始" end-placeholder="结束" />
        </el-form-item>
        <el-button type="primary" @click="load(1)">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button type="success" @click="$router.push('/faults/new')">＋ 新增故障</el-button>
      </el-form>
    </el-card>

    <el-card>
      <el-table v-if="!isMobile" :data="rows" v-loading="loading" stripe>
        <el-table-column prop="fault_no" label="编号" width="95" />
        <el-table-column label="叉车" width="170">
          <template #default="{ row }">
            <div>{{ row.forklift_asset_no || '-' }}</div>
            <small style="color: #888">{{ row.brand_name }} {{ row.model_name }} · {{ row.site_name }}</small>
          </template>
        </el-table-column>
        <el-table-column prop="fault_date" label="日期" width="110" />
        <el-table-column prop="system_name" label="系统" width="100">
          <template #default="{ row }">{{ row.system_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="cause_name" label="原因" width="130">
          <template #default="{ row }">{{ row.cause_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="downtime_hours" label="停机h" width="80" align="right" />
        <el-table-column prop="handler" label="处理人" width="80" />
        <el-table-column prop="created_by_name" label="录入" width="80" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push('/faults/' + row.id + '/edit')">编辑</el-button>
            <el-button link type="danger" @click="del(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 移动端卡片列表 -->
      <div v-else v-loading="loading" class="m-list">
        <el-card v-for="r in rows" :key="r.id" class="m-card" shadow="hover">
          <div class="m-head">
            <b>{{ r.fault_no }}</b>
            <span class="m-date">{{ r.fault_date }}</span>
          </div>
          <div class="m-forklift">{{ r.forklift_asset_no || '-' }} · {{ r.brand_name }} {{ r.model_name }} · {{ r.site_name }}</div>
          <div class="m-tags">
            <el-tag size="small" v-if="r.system_name">{{ r.system_name }}</el-tag>
            <el-tag size="small" type="warning" v-if="r.cause_name">{{ r.cause_name }}</el-tag>
          </div>
          <div class="m-desc" v-if="r.description">{{ r.description }}</div>
          <div class="m-meta">
            <span v-if="r.downtime_hours != null">停机 {{ r.downtime_hours }}h</span>
            <span v-if="r.handler">处理 {{ r.handler }}</span>
            <span v-if="r.created_by_name">录入 {{ r.created_by_name }}</span>
          </div>
          <div class="m-actions">
            <el-button size="small" type="primary" @click="$router.push('/faults/' + r.id + '/edit')">编辑</el-button>
            <el-button size="small" type="danger" plain @click="del(r)">删除</el-button>
          </div>
        </el-card>
        <el-empty v-if="!rows.length && !loading" description="暂无数据" />
      </div>

      <el-pagination
        style="margin-top: 12px; display: flex; justify-content: flex-end"
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, prev, pager, next, sizes"
        @current-change="load()"
        @size-change="load(1)"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api'
import DictSelect from '../components/DictSelect.vue'
import { useBreakpoint } from '../composables/useBreakpoint'

const { isMobile } = useBreakpoint()

const q = ref('')
const systemId = ref(null)
const causeId = ref(null)
const range = ref([])
const rows = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)

async function load(p) {
  if (p) page.value = p
  loading.value = true
  try {
    const { data } = await http.get('/api/faults', {
      params: {
        q: q.value || undefined,
        system_id: systemId.value || undefined,
        cause_id: causeId.value || undefined,
        start_date: range.value?.[0],
        end_date: range.value?.[1],
        page: page.value,
        size: size.value,
      },
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function reset() {
  q.value = ''
  systemId.value = null
  causeId.value = null
  range.value = []
  load(1)
}

async function del(row) {
  await ElMessageBox.confirm('确认删除故障 ' + row.fault_no + ' ？', '提示', { type: 'warning' })
  await http.delete('/api/faults/' + row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => load(1))
</script>
