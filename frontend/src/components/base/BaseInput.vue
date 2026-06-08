<script setup lang="ts">
/**
 * 基础输入框组件
 * 支持 label、description、error、readonly、disabled
 * 规范：frontend_component_library_spec.md §5.3
 */

interface Props {
  modelValue: string
  label?: string
  description?: string
  placeholder?: string
  type?: string
  error?: string
  disabled?: boolean
  readonly?: boolean
  size?: 'sm' | 'md' | 'lg'
}

withDefaults(defineProps<Props>(), {
  size: 'md',
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const sizeClasses: Record<string, string> = {
  sm: 'h-7 px-2 text-caption',
  md: 'h-9 px-3 text-body',
  lg: 'h-11 px-3 text-body',
}
</script>

<template>
  <div>
    <label v-if="label" class="block text-body-medium text-text mb-1">
      {{ label }}
      <span v-if="$attrs.required" class="text-danger ml-0.5">*</span>
    </label>
    <p v-if="description" class="text-caption text-text-tertiary mb-1">{{ description }}</p>
    <input
      :value="modelValue"
      :type="type || 'text'"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :class="[
        'w-full border rounded-md bg-surface text-text',
        'transition-colors duration-fast ease-standard',
        'placeholder:text-text-muted',
        'focus:outline-none focus:ring-2 focus:ring-focus focus:border-primary',
        error ? 'border-danger' : 'border-border-strong',
        disabled ? 'opacity-50 cursor-not-allowed bg-surface-alt' : '',
        readonly ? 'bg-surface-muted cursor-default' : '',
        sizeClasses[size],
      ]"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" class="mt-1 text-caption text-danger" role="alert">{{ error }}</p>
  </div>
</template>
