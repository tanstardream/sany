<template>
  <div v-loading="loading">
    <el-row :gutter="12">
      <el-col :xs="12" :sm="8" :md="4" v-for="c in cards" :key="c.label">
        <el-card shadow="hover">
          <div class="kpi">
            <div class="kpi-v">{{ c.value }}</div>
            <div class="kpi-l">{{ c.label }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8" :md="4">
        <el-card shadow="hover">
          <div class="kpi">
            <el-button type="primary" text bg @click="$router.push('/faults/new')">＋ 录入新故障</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top: 12px">
      <el-col :xs="24" :md="12">
        <el-card header="按故障系统分布">
          <div ref="pieRef" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card header="故障原因 TOP8">
          <div ref="barRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top: 12px">
      <el-col :span="24">
        <el-card header="故障数量趋势（按月）">
          <div ref="lineRef" class="chart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import http from '../api'

const loading = ref(false)
const cards = ref([])
const pieRef = ref()
const barRef = ref()
const lineRef = ref()
let pieChart, barChart, lineChart

async function load() {
  loading.value = true
  try {
    const [ov, sys, cause, trend] = await Promise.all([
      http.get('/api/stats/overview').then((r) => r.data),
      http.get('/api/stats/by-dim?dim=system').then((r) => r.data),
      http.get('/api/stats/by-dim?dim=cause&top=8').then((r) => r.data),
      http.get('/api/stats/trend').then((r) => r.data),
    ])
    cards.value = [
      { label: '故障总数', value: ov.total_faults },
      { label: '叉车总数', value: ov.total_forklifts },
      { label: '本月故障', value: ov.this_month_faults },
      { label: '累计停机(h)', value: ov.total_downtime_hours },
      { label: '累计费用(元)', value: ov.total_repair_cost },
    ]
    await nextTick()
    pieChart = pieChart || echarts.init(pieRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, type: 'scroll' },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          label: { formatter: '{b}: {c}' },
          data: sys.map((d) => ({ name: d.label || '未分类', value: d.value })),
        },
      ],
    })
    const causeRev = [...cause].reverse()
    barChart = barChart || echarts.init(barRef.value)
    barChart.setOption({
      tooltip: {},
      grid: { left: 90, right: 24 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: causeRev.map((d) => d.label || '未分类') },
      series: [{ type: 'bar', data: causeRev.map((d) => d.value), itemStyle: { color: '#409eff' } }],
    })
    lineChart = lineChart || echarts.init(lineRef.value)
    lineChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 24, top: 24 },
      xAxis: { type: 'category', data: trend.map((d) => d.period) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          type: 'line',
          smooth: true,
          data: trend.map((d) => d.count),
          areaStyle: {},
          itemStyle: { color: '#67c23a' },
        },
      ],
    })
  } finally {
    loading.value = false
  }
}

function resize() {
  pieChart?.resize()
  barChart?.resize()
  lineChart?.resize()
}
onMounted(() => {
  load()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
})
</script>

<style scoped>
.chart { height: 320px; }
@media (max-width: 768px) { .chart { height: 260px; } }
.kpi { text-align: center; }
.kpi-v { font-size: 26px; font-weight: 600; color: #409eff; }
.kpi-l { color: #888; font-size: 13px; margin-top: 4px; }
</style>
