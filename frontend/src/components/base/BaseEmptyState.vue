<script setup lang="ts">
/**
 * 空态组件
 * 说明当前为空的原因和可执行动作
 * 规范：frontend_component_library_spec.md §5.8
 */
import type { Component } from 'vue'

interface Props {
  icon?: Component
  title: string
  description?: string
}

defineProps<Props>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-12 px-6 text-center">
    <component
      :is="icon"
      v-if="icon"
      class="w-10 h-10 text-text-muted mb-3"
    />
    <h3 class="text-subheading text-text mb-1">{{ title }}</h3>
    <p v-if="description" class="text-caption text-text-secondary max-w-sm">
      {{ description }}
    </p>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>
