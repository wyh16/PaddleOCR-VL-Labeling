<script setup lang="ts">
/**
 * 通用错误态组件
 * 统一加载失败、权限失败等阻断错误的展示和重试入口。
 */
import { AlertCircle } from 'lucide-vue-next'

import BaseButton from './BaseButton.vue'

interface Props {
  title: string
  detail?: string
  retryLabel?: string
  canRetry?: boolean
}

withDefaults(defineProps<Props>(), {
  detail: '',
  retryLabel: '',
  canRetry: false,
})

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="flex-1 flex items-center justify-center">
    <div class="text-center">
      <AlertCircle class="mx-auto mb-3 h-10 w-10 text-text-muted" />
      <p class="text-heading text-text mb-2">{{ title }}</p>
      <p v-if="detail" class="text-caption text-text-muted mb-4">{{ detail }}</p>
      <BaseButton v-if="canRetry" variant="primary" size="md" @click="emit('retry')">
        {{ retryLabel }}
      </BaseButton>
    </div>
  </div>
</template>
