<template>
  <div class="doc-upload">
    <div class="tabs">
      <button
        class="tab-btn"
        :class="{ active: mode === 'file' }"
        @click="mode = 'file'"
        type="button"
      >📎 文件</button>
      <button
        class="tab-btn"
        :class="{ active: mode === 'url' }"
        @click="mode = 'url'"
        type="button"
      >🔗 URL</button>
    </div>

    <div
      v-if="mode === 'file'"
      class="upload-area"
      :class="{ dragover }"
      @click="$refs.fileInput.click()"
      @dragover.prevent="dragover = true"
      @dragleave="dragover = false"
      @drop.prevent="handleDrop"
    >
      <input ref="fileInput" type="file" accept=".pdf,.txt,.docx" @change="handleSelect" />
      <div v-if="uploading" class="flex items-center justify-between gap-8" style="justify-content:center">
        <span class="loading-spinner"></span> 上传中...
      </div>
      <div v-else>
        <div style="font-size:28px;margin-bottom:4px">📎</div>
        <div>点击或拖拽文件到此处上传</div>
        <div class="text-sm text-secondary mt-12">支持 PDF、TXT、DOCX</div>
      </div>
    </div>

    <div v-else class="upload-area url-area">
      <div style="font-size:28px;margin-bottom:4px">🔗</div>
      <div class="mb-8">粘贴网页链接，系统会抓取正文并入库</div>
      <form class="url-form" @submit.prevent="doUploadUrl">
        <input
          v-model="url"
          type="url"
          placeholder="https://example.com/article"
          :disabled="uploading"
          required
        />
        <button type="submit" :disabled="uploading || !url.trim()">
          <span v-if="uploading" class="loading-spinner"></span>
          <span v-else>添加</span>
        </button>
      </form>
      <div class="text-sm text-secondary mt-8">
        仅支持 http(s)、静态 HTML；JS 渲染页面可能抓取不全
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { uploadDoc, uploadUrlDoc } from '../api/document.js'

const props = defineProps({ kbId: String })
const emit = defineEmits(['uploaded'])
const showToast = inject('showToast')

const mode = ref('file')
const uploading = ref(false)
const dragover = ref(false)
const url = ref('')

async function doUpload(file) {
  if (!file) return
  uploading.value = true
  try {
    await uploadDoc(props.kbId, file)
    showToast(`「${file.name}」上传成功，正在处理...`)
    emit('uploaded')
  } catch (e) {
    showToast('上传失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}

async function doUploadUrl() {
  const target = url.value.trim()
  if (!target) return
  uploading.value = true
  try {
    await uploadUrlDoc(props.kbId, target)
    showToast(`「${target}」抓取成功，正在处理...`)
    url.value = ''
    emit('uploaded')
  } catch (e) {
    showToast('抓取失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}

function handleSelect(e) {
  doUpload(e.target.files?.[0])
  e.target.value = ''
}

function handleDrop(e) {
  dragover.value = false
  doUpload(e.dataTransfer.files?.[0])
}
</script>

<style scoped>
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}
.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border, #ddd);
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.tab-btn.active {
  background: var(--primary, #3b82f6);
  color: #fff;
  border-color: var(--primary, #3b82f6);
}
.url-area {
  cursor: default;
}
.url-form {
  display: flex;
  gap: 8px;
  width: 100%;
  margin-top: 8px;
}
.url-form input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--border, #ddd);
  border-radius: 6px;
  font-size: 14px;
}
.url-form button {
  padding: 8px 16px;
  background: var(--primary, #3b82f6);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  min-width: 64px;
}
.url-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
