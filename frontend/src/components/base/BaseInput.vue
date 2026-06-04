<script setup lang="ts">
/**
 * 基础输入框组件
 * 支持 label、description、error、readonly、disabled
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
}

defineProps<Props>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div>
    <label v-if="label" class="block text-sm font-medium text-text mb-1">
      {{ label }}
    </label>
    <p v-if="description" class="text-xs text-muted mb-1">{{ description }}</p>
    <input
      :value="modelValue"
      :type="type || 'text'"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-accent transition-colors"
      :class="[
        error ? 'border-danger' : 'border-border',
        disabled ? 'opacity-50 cursor-not-allowed bg-surface' : '',
        readonly ? 'bg-surface cursor-default' : '',
      ]"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" class="mt-1 text-sm text-danger">{{ error }}</p>
  </div>
</template>
