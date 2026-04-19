<template>
  <div
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
</template>

<script setup>
import { ref, inject } from 'vue'
import { uploadDoc } from '../api/document.js'

const props = defineProps({ kbId: String })
const emit = defineEmits(['uploaded'])
const showToast = inject('showToast')

const uploading = ref(false)
const dragover = ref(false)

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

function handleSelect(e) {
  doUpload(e.target.files?.[0])
  e.target.value = ''
}

function handleDrop(e) {
  dragover.value = false
  doUpload(e.dataTransfer.files?.[0])
}
</script>
