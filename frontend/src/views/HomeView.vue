<template>
  <div class="page">
    <div class="flex justify-between items-center mb-12">
      <h1 class="page-title">知识库</h1>
      <button class="btn btn-primary" @click="showCreate = true">+ 创建知识库</button>
    </div>

    <div v-if="loading" class="empty-state"><span class="loading-spinner"></span></div>

    <div v-else-if="kbs.length === 0" class="empty-state">
      <div class="icon">📭</div>
      <p>还没有知识库，创建一个开始吧</p>
    </div>

    <div v-else class="grid grid-3">
      <div v-for="kb in kbs" :key="kb.id" class="card" style="cursor:pointer" @click="$router.push(`/kb/${kb.id}`)">
        <div class="flex justify-between items-center">
          <h3>{{ kb.name }}</h3>
          <button class="btn btn-danger btn-sm" @click.stop="handleDelete(kb)">删除</button>
        </div>
        <p class="text-secondary text-sm mt-12">{{ kb.description || '暂无描述' }}</p>
        <div class="flex gap-12 mt-12 text-sm text-secondary">
          <span>📄 {{ kb.document_count }} 篇文档</span>
          <span>🕐 {{ formatDate(kb.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Create dialog -->
    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate = false">
      <div class="modal">
        <h3>创建知识库</h3>
        <div class="form-group">
          <label>名称 *</label>
          <input class="input" v-model="form.name" placeholder="例如：技术文档库" @keyup.enter="handleCreate" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea class="input" v-model="form.description" placeholder="可选描述"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" :disabled="!form.name.trim() || creating" @click="handleCreate">
            <span v-if="creating" class="loading-spinner"></span>
            创建
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { listKBs, createKB, deleteKB } from '../api/knowledgeBase.js'

const showToast = inject('showToast')
const kbs = ref([])
const loading = ref(true)
const showCreate = ref(false)
const creating = ref(false)
const form = ref({ name: '', description: '' })

async function load() {
  loading.value = true
  try {
    const data = await listKBs({ limit: 100 })
    kbs.value = data.items
  } catch (e) {
    showToast('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!form.value.name.trim()) return
  creating.value = true
  try {
    await createKB({ name: form.value.name.trim(), description: form.value.description.trim() || null })
    showToast('知识库已创建')
    showCreate.value = false
    form.value = { name: '', description: '' }
    await load()
  } catch (e) {
    showToast('创建失败: ' + e.message)
  } finally {
    creating.value = false
  }
}

async function handleDelete(kb) {
  if (!confirm(`确定删除知识库「${kb.name}」及其所有文档？`)) return
  try {
    await deleteKB(kb.id)
    showToast('已删除')
    await load()
  } catch (e) {
    showToast('删除失败: ' + e.message)
  }
}

function formatDate(s) {
  return new Date(s).toLocaleDateString('zh-CN')
}

onMounted(load)
</script>
