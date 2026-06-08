<script setup lang="ts">
/**
 * Badge 组件
 * 用于状态标识、计数、紧凑标签
 * 规范：frontend_component_library_spec.md §5.4
 */

interface Props {
  variant?: 'neutral' | 'primary' | 'success' | 'warning' | 'danger' | 'info'
  size?: 'sm' | 'md'
}

withDefaults(defineProps<Props>(), {
  variant: 'neutral',
  size: 'sm',
})

const variantClasses: Record<string, string> = {
  neutral: 'bg-surface-alt text-text-secondary',
  primary: 'bg-primary/10 text-primary',
  success: 'bg-success-bg text-success',
  warning: 'bg-warning-bg text-warning',
  danger: 'bg-danger-bg text-danger',
  info: 'bg-info-bg text-info',
}

const sizeClasses: Record<string, string> = {
  sm: 'px-1.5 py-0.5 text-micro',
  md: 'px-2 py-0.5 text-caption',
}
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-medium rounded-sm whitespace-nowrap',
      variantClasses[variant],
      sizeClasses[size],
    ]"
  >
    <slot />
  </span>
</template>
