<script setup lang="ts">
/**
 * 基础 Modal 组件
 * 支持 Esc 关闭、可访问标题、焦点管理
 */
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

interface Props {
  open: boolean
  title?: string
  maxWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: 'max-w-md',
})

const emit = defineEmits<{
  close: []
}>()

const modalRef = ref<HTMLElement | null>(null)
const titleId = ref(`modal-title-${Math.random().toString(36).slice(2, 9)}`)

/** Esc 关闭 */
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) {
    emit('close')
  }
}

/** 焦点锁定到 modal 内 */
function trapFocus(event: KeyboardEvent) {
  if (!modalRef.value || event.key !== 'Tab') return

  const focusableElements = modalRef.value.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const firstElement = focusableElements[0] as HTMLElement
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

  if (event.shiftKey) {
    if (document.activeElement === firstElement) {
      lastElement.focus()
      event.preventDefault()
    }
  } else {
    if (document.activeElement === lastElement) {
      firstElement.focus()
      event.preventDefault()
    }
  }
}

/** 打开时聚焦 modal */
watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    modalRef.value?.focus()
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center">
        <!-- 背景遮罩 -->
        <div
          class="absolute inset-0 bg-black/50"
          @click="$emit('close')"
        />

        <!-- Modal 内容 -->
        <div
          ref="modalRef"
          :class="['relative bg-background rounded-lg shadow-xl w-full mx-4 p-6', maxWidth]"
          role="dialog"
          :aria-modal="open"
          :aria-labelledby="title ? titleId : undefined"
          tabindex="-1"
          @keydown="trapFocus"
        >
          <div v-if="title" :id="titleId" class="mb-4">
            <h3 class="text-lg font-medium text-text">{{ title }}</h3>
          </div>

          <slot />

          <div class="mt-6 flex justify-end space-x-3">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
