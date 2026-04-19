<template>
  <div class="page">
    <div class="flex justify-between items-center mb-12">
      <h1 class="page-title">任务监控</h1>
      <div class="flex gap-8 items-center">
        <select class="input" style="width:auto" v-model="statusFilter" @change="load">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="processing">处理中</option>
          <option value="success">成功</option>
          <option value="failed">失败</option>
        </select>
        <button class="btn btn-outline btn-sm" @click="load">🔄 刷新</button>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="empty-state"><span class="loading-spinner"></span></div>

      <div v-else-if="tasks.length === 0" class="empty-state">
        <div class="icon">📋</div>
        <p>暂无任务记录</p>
      </div>

      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>任务 ID</th>
              <th>类型</th>
              <th>状态</th>
              <th>错误信息</th>
              <th>创建时间</th>
              <th>完成时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tasks" :key="t.id">
              <td class="text-sm" style="font-family:monospace">{{ t.id.slice(0, 8) }}…</td>
              <td>{{ t.task_type }}</td>
              <td><StatusBadge :status="t.status" /></td>
              <td class="text-sm text-secondary">{{ t.error_message || '—' }}</td>
              <td class="text-sm">{{ formatTime(t.created_at) }}</td>
              <td class="text-sm">{{ t.completed_at ? formatTime(t.completed_at) : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="total > tasks.length" class="mt-12" style="text-align:center">
        <button class="btn btn-outline btn-sm" @click="loadMore">加载更多</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { listTasks } from '../api/task.js'
import StatusBadge from '../components/StatusBadge.vue'

const tasks = ref([])
const total = ref(0)
const loading = ref(true)
const statusFilter = ref('')
let offset = 0
let pollTimer = null

async function load() {
  loading.value = true
  offset = 0
  try {
    const params = { limit: 20, offset: 0 }
    if (statusFilter.value) params.status = statusFilter.value
    const data = await listTasks(params)
    tasks.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  offset += 20
  const params = { limit: 20, offset }
  if (statusFilter.value) params.status = statusFilter.value
  const data = await listTasks(params)
  tasks.value.push(...data.items)
}

function formatTime(s) {
  return new Date(s).toLocaleString('zh-CN')
}

onMounted(() => {
  load()
  pollTimer = setInterval(load, 5000)
})

onUnmounted(() => clearInterval(pollTimer))
</script>
