<template>
  <div class="page">
    <!-- Header -->
    <div class="flex justify-between items-center mb-12">
      <div>
        <router-link to="/" class="text-secondary text-sm">← 返回</router-link>
        <h1 class="page-title" style="margin-top:4px">{{ kb?.name || '加载中...' }}</h1>
        <p v-if="kb?.description" class="text-secondary text-sm">{{ kb.description }}</p>
      </div>
    </div>

    <!-- Split: docs left, chat right -->
    <div class="split">
      <!-- Left: Documents -->
      <div>
        <DocUpload :kb-id="id" @uploaded="loadDocs" />

        <div class="card mt-12">
          <h3 class="mb-12">📄 文档 ({{ docs.length }})</h3>

          <div v-if="docs.length === 0" class="empty-state">
            <p>暂无文档，上传一个试试</p>
          </div>

          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>文件名</th>
                  <th>类型</th>
                  <th>状态</th>
                  <th>版本</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="doc in docs" :key="doc.id">
                  <td>{{ doc.filename }}</td>
                  <td><span class="badge badge-neutral">{{ doc.file_type }}</span></td>
                  <td><StatusBadge :status="doc.status" /></td>
                  <td>v{{ doc.current_version }}</td>
                  <td class="flex gap-8">
                    <label class="btn btn-outline btn-sm" style="cursor:pointer">
                      重传
                      <input type="file" style="display:none" accept=".pdf,.txt,.docx" @change="handleReupload(doc, $event)" />
                    </label>
                    <button class="btn btn-danger btn-sm" @click="handleDeleteDoc(doc)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Right: Chat -->
      <div class="card" style="padding:0;overflow:hidden">
        <ChatPanel :kb-id="id" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { getKB } from '../api/knowledgeBase.js'
import { listDocs, deleteDoc, reuploadDoc } from '../api/document.js'
import DocUpload from '../components/DocUpload.vue'
import ChatPanel from '../components/ChatPanel.vue'
import StatusBadge from '../components/StatusBadge.vue'

const props = defineProps({ id: String })
const showToast = inject('showToast')

const kb = ref(null)
const docs = ref([])

async function loadKB() {
  try {
    kb.value = await getKB(props.id)
  } catch (e) {
    showToast('加载知识库失败: ' + e.message)
  }
}

async function loadDocs() {
  try {
    const data = await listDocs(props.id, { limit: 100 })
    docs.value = data.items
  } catch (e) {
    showToast('加载文档列表失败: ' + e.message)
  }
}

async function handleDeleteDoc(doc) {
  if (!confirm(`确定删除「${doc.filename}」？`)) return
  try {
    await deleteDoc(doc.id)
    showToast('已删除')
    await loadDocs()
    await loadKB()
  } catch (e) {
    showToast('删除失败: ' + e.message)
  }
}

async function handleReupload(doc, event) {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    await reuploadDoc(doc.id, file)
    showToast(`已重新上传，新版本处理中`)
    await loadDocs()
  } catch (e) {
    showToast('重传失败: ' + e.message)
  }
  event.target.value = ''
}

onMounted(() => {
  loadKB()
  loadDocs()
})
</script>
