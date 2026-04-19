<template>
  <span :class="['badge', badgeClass]">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: String })

const MAP = {
  pending:    { class: 'badge-neutral',  label: '待处理' },
  parsing:    { class: 'badge-info',     label: '解析中' },
  chunking:   { class: 'badge-info',     label: '切块中' },
  embedding:  { class: 'badge-info',     label: '向量化' },
  processing: { class: 'badge-warning',  label: '处理中' },
  ready:      { class: 'badge-success',  label: '就绪' },
  success:    { class: 'badge-success',  label: '成功' },
  failed:     { class: 'badge-danger',   label: '失败' },
}

const entry = computed(() => MAP[props.status] || { class: 'badge-neutral', label: props.status })
const badgeClass = computed(() => entry.value.class)
const label = computed(() => entry.value.label)
</script>
