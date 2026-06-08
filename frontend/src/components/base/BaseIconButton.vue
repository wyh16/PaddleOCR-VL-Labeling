<script setup lang="ts">
/**
 * 图标按钮组件
 * 用于单个图标操作：关闭、刷新、更多、折叠
 * 规范：frontend_component_library_spec.md §5.2
 */
import { Loader2 } from 'lucide-vue-next'
import type { Component } from 'vue'

interface Props {
  icon: Component
  size?: 'xs' | 'sm' | 'md' | 'lg'
  variant?: 'ghost' | 'primary' | 'danger'
  disabled?: boolean
  loading?: boolean
  ariaLabel: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  variant: 'ghost',
  disabled: false,
  loading: false,
})

const sizeMap: Record<string, string> = {
  xs: 'w-6 h-6',
  sm: 'w-7 h-7',
  md: 'w-8 h-8',
  lg: 'w-10 h-10',
}

const iconSizeMap: Record<string, string> = {
  xs: 'w-3.5 h-3.5',
  sm: 'w-4 h-4',
  md: 'w-4 h-4',
  lg: 'w-[18px] h-[18px]',
}

const variantMap: Record<string, string> = {
  ghost: 'text-text-secondary hover:bg-surface-muted hover:text-text active:bg-surface-alt',
  primary: 'text-primary bg-primary/10 hover:bg-primary/20 active:bg-primary/30',
  danger: 'text-danger hover:bg-danger-bg active:bg-danger/20',
}
</script>

<template>
  <button
    :disabled="disabled || loading"
    :aria-label="ariaLabel"
    :title="ariaLabel"
    :class="[
      'inline-flex items-center justify-center rounded-md shrink-0',
      'transition-all duration-fast ease-standard',
      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      sizeMap[size],
      variantMap[variant],
    ]"
  >
    <Loader2 v-if="loading" :class="['animate-spin', iconSizeMap[size]]" />
    <component :is="icon" v-else :class="iconSizeMap[size]" />
  </button>
</template>
