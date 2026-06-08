<script setup lang="ts">
/**
 * 基础按钮组件
 * 支持 xs/sm/md/lg 尺寸，primary/secondary/ghost/link/danger 变体
 * 规范：frontend_component_library_spec.md §5.1
 */
import { Loader2 } from 'lucide-vue-next'
import type { Component } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'link' | 'danger'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  leftIcon?: Component
  rightIcon?: Component
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
})

const variantClasses: Record<string, string> = {
  primary: 'bg-primary text-white hover:bg-primary-hover active:bg-primary-active',
  secondary: 'bg-surface text-text border border-border hover:bg-surface-muted active:bg-surface-alt',
  ghost: 'bg-transparent text-text hover:bg-surface-muted active:bg-surface-alt',
  link: 'bg-transparent text-primary hover:text-primary-hover active:text-primary-active underline-offset-2 hover:underline',
  danger: 'bg-danger text-white hover:bg-danger/90 active:bg-danger/80',
}

const sizeClasses: Record<string, string> = {
  xs: 'h-6 px-2 py-0.5 text-caption',
  sm: 'h-7 px-2.5 py-1 text-caption',
  md: 'h-8 px-3 py-1.5 text-body',
  lg: 'h-10 px-4 py-2 text-body',
}
</script>

<template>
  <button
    :disabled="disabled || loading"
    :class="[
      'rounded-md font-medium inline-flex items-center justify-center gap-1.5',
      'transition-all duration-fast ease-standard',
      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variantClasses[variant],
      sizeClasses[size],
    ]"
  >
    <Loader2 v-if="loading" class="w-4 h-4 animate-spin shrink-0" />
    <component :is="leftIcon" v-else-if="leftIcon" class="w-4 h-4 shrink-0" />
    <slot />
    <component :is="rightIcon" v-if="rightIcon" class="w-4 h-4 shrink-0" />
  </button>
</template>
