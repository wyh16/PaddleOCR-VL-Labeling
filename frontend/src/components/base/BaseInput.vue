<script setup lang="ts">
/**
 * 通用输入框组件
 * 保持基础输入样式一致，业务校验和提示交由上层页面处理。
 */
type InputSize = 'sm' | 'md' | 'lg'

interface Props {
  modelValue?: string | number
  type?: string
  placeholder?: string
  disabled?: boolean
  invalid?: boolean
  size?: InputSize
  min?: number | string
  max?: number | string
  step?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  disabled: false,
  invalid: false,
  size: 'md',
  min: undefined,
  max: undefined,
  step: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [event: Event]
  input: [event: Event]
}>()

const sizeClassMap: Record<InputSize, string> = {
  sm: 'h-7 px-2 text-caption',
  md: 'h-9 px-3 text-caption',
  lg: 'h-11 px-3 text-body',
}

function handleInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
  emit('input', event)
}

function handleChange(event: Event) {
  emit('change', event)
}
</script>

<template>
  <input
    :value="props.modelValue"
    :type="props.type"
    :placeholder="props.placeholder"
    :disabled="props.disabled"
    :min="props.min"
    :max="props.max"
    :step="props.step"
    :class="[
      'w-full rounded-md border bg-surface text-text transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-focus disabled:cursor-not-allowed disabled:opacity-50',
      props.invalid ? 'border-danger text-danger' : 'border-border',
      sizeClassMap[props.size],
    ]"
    @input="handleInput"
    @change="handleChange"
  />
</template>
