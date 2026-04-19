<template>
  <div class="chat-panel">
    <div class="chat-messages" ref="messagesEl">
      <div v-if="messages.length === 0" class="empty-state" style="padding:48px 16px">
        <div class="icon">💬</div>
        <p>对这个知识库提问试试</p>
        <p class="text-sm text-secondary mt-12">例如：这些文档的主要内容是什么？</p>
      </div>

      <template v-for="(msg, i) in messages" :key="i">
        <div :class="['chat-msg', msg.role]">
          {{ msg.content }}
          <div v-if="msg.citations?.length" class="citations">
            <div class="citation-header">📎 引用来源</div>
            <div v-for="c in msg.citations" :key="c.index" class="citation">
              <strong>[{{ c.index }}]</strong> {{ c.filename }}
              <span v-if="c.page_number">· 第{{ c.page_number }}页</span>
              <span>· 相似度 {{ (c.score * 100).toFixed(0) }}%</span>
              <div style="margin-top:4px;color:#667085">{{ truncate(c.content, 120) }}</div>
            </div>
          </div>
        </div>
      </template>

      <div v-if="asking" class="chat-msg assistant">
        <span class="loading-spinner"></span> 思考中...
      </div>
    </div>

    <div class="chat-input-bar">
      <input
        class="input"
        v-model="question"
        placeholder="输入你的问题..."
        @keyup.enter="handleAsk"
        :disabled="asking"
      />
      <button class="btn btn-primary" @click="handleAsk" :disabled="asking || !question.trim()">
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, inject } from 'vue'
import { queryKB } from '../api/qa.js'

const props = defineProps({ kbId: String })
const showToast = inject('showToast')

const messages = ref([])
const question = ref('')
const asking = ref(false)
const messagesEl = ref(null)

function scrollBottom() {
  nextTick(() => {
    const el = messagesEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function handleAsk() {
  const q = question.value.trim()
  if (!q || asking.value) return

  messages.value.push({ role: 'user', content: q })
  question.value = ''
  asking.value = true
  scrollBottom()

  try {
    const res = await queryKB(props.kbId, q)
    messages.value.push({
      role: 'assistant',
      content: res.answer,
      citations: res.citations,
    })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '⚠️ 回答失败: ' + e.message })
    showToast('问答失败: ' + e.message)
  } finally {
    asking.value = false
    scrollBottom()
  }
}

function truncate(s, n) {
  return s.length > n ? s.slice(0, n) + '…' : s
}
</script>
