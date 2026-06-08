<script setup lang="ts">
/**
 * Tag 组件
 * 用于标签选择、可关闭标签
 * 规范：frontend_component_library_spec.md §5.4
 */
import { X } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  color?: string
  closable?: boolean
}

withDefaults(defineProps<Props>(), {
  closable: false,
})

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1 px-2 py-0.5 text-caption font-medium rounded-sm whitespace-nowrap bg-surface-alt text-text-secondary"
  >
    <span
      v-if="color"
      class="w-2 h-2 rounded-full shrink-0"
      :style="{ backgroundColor: color }"
    />
    <slot />
    <button
      v-if="closable"
      class="ml-0.5 rounded hover:bg-surface-strong p-0.5 transition-colors"
      :aria-label="t('common.remove')"
      @click.stop="emit('close')"
    >
      <X class="w-3 h-3" />
    </button>
  </span>
</template>
