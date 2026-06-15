<script setup lang="ts">
/**
 * 通用空态组件
 * 统一空列表、功能占位和无数据场景的展示样式。
 */
import type { Component } from 'vue'

interface Props {
  title?: string
  description?: string
  icon?: Component | null
}

withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  icon: null,
})
</script>

<template>
  <div class="rounded-lg border border-dashed border-border bg-surface px-6 py-12 text-center">
    <component :is="icon" v-if="icon" class="mx-auto mb-3 h-10 w-10 text-text-muted" />
    <p v-if="title" class="text-body text-text">{{ title }}</p>
    <p v-if="description" class="mt-2 text-caption text-text-muted">{{ description }}</p>
    <div v-if="$slots.default" class="mt-4 flex justify-center">
      <slot />
    </div>
  </div>
</template>
