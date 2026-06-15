<script setup lang="ts">
/**
 * 通用按钮组件
 * 用于替代页面内重复的 primary / secondary / ghost / danger 按钮样式。
 */
import { Loader2 } from 'lucide-vue-next'
import type { Component } from 'vue'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg'

interface Props {
  type?: 'button' | 'submit' | 'reset'
  variant?: ButtonVariant
  size?: ButtonSize
  disabled?: boolean
  loading?: boolean
  block?: boolean
  leftIcon?: Component | null
  rightIcon?: Component | null
}

const props = withDefaults(defineProps<Props>(), {
  type: 'button',
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  block: false,
  leftIcon: null,
  rightIcon: null,
})

const variantClassMap: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-primary-hover',
  secondary: 'border border-border bg-surface text-text hover:bg-surface-muted',
  ghost: 'text-text-secondary hover:bg-surface-muted hover:text-text',
  danger: 'bg-danger text-white hover:opacity-90',
}

const sizeClassMap: Record<ButtonSize, string> = {
  xs: 'h-6 px-2 text-micro',
  sm: 'h-7 px-2.5 text-caption',
  md: 'h-8 px-3 text-caption',
  lg: 'h-10 px-4 text-body',
}
</script>

<template>
  <button
    :type="props.type"
    :disabled="props.disabled || props.loading"
    :class="[
      'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors',
      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus',
      'disabled:cursor-not-allowed disabled:opacity-50',
      variantClassMap[props.variant],
      sizeClassMap[props.size],
      props.block ? 'w-full' : '',
    ]"
  >
    <Loader2 v-if="props.loading" class="h-4 w-4 animate-spin shrink-0" />
    <component :is="props.leftIcon" v-else-if="props.leftIcon" class="h-4 w-4 shrink-0" />
    <slot />
    <component :is="props.rightIcon" v-if="props.rightIcon && !props.loading" class="h-4 w-4 shrink-0" />
  </button>
</template>
