<template>
  <header class="app-header">
    <router-link to="/" class="logo">📚 知识库系统</router-link>
    <nav>
      <router-link to="/">知识库</router-link>
      <router-link to="/tasks">任务监控</router-link>
    </nav>
  </header>
  <router-view />
  <div v-if="toast" class="toast">{{ toast }}</div>
</template>

<script setup>
import { ref, provide } from 'vue'

const toast = ref('')
let timer = null

function showToast(msg, duration = 3500) {
  toast.value = msg
  clearTimeout(timer)
  timer = setTimeout(() => (toast.value = ''), duration)
}

provide('showToast', showToast)
</script>
