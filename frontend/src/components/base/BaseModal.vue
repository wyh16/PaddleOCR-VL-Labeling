<script setup lang="ts">
/**
 * Modal 组件
 * 支持 Esc 关闭、焦点管理、Teleport
 * 规范：frontend_component_library_spec.md §5.7
 */
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { X } from 'lucide-vue-next'

interface Props {
  open: boolean
  title?: string
  maxWidth?: string
  closable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: 'max-w-md',
  closable: true,
})

const emit = defineEmits<{
  close: []
}>()

const modalRef = ref<HTMLElement | null>(null)
const titleId = ref(`modal-title-${Math.random().toString(36).slice(2, 9)}`)

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open && props.closable) {
    emit('close')
  }
}

function trapFocus(event: KeyboardEvent) {
  if (!modalRef.value || event.key !== 'Tab') return
  const focusable = modalRef.value.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const first = focusable[0] as HTMLElement
  const last = focusable[focusable.length - 1] as HTMLElement
  if (event.shiftKey) {
    if (document.activeElement === first) { last.focus(); event.preventDefault() }
  } else {
    if (document.activeElement === last) { first.focus(); event.preventDefault() }
  }
}

watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    modalRef.value?.focus()
  }
})

onMounted(() => { document.addEventListener('keydown', handleKeydown) })
onUnmounted(() => { document.removeEventListener('keydown', handleKeydown) })
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="fixed inset-0 z-modal flex items-center justify-center">
        <div class="absolute inset-0 bg-black/40" @click="closable && emit('close')" />
        <div
          ref="modalRef"
          :class="['relative bg-surface rounded-lg shadow-modal w-full mx-4 p-6', maxWidth]"
          role="dialog"
          :aria-modal="true"
          :aria-labelledby="title ? titleId : undefined"
          tabindex="-1"
          @keydown="trapFocus"
        >
          <div v-if="title || closable" class="flex items-center justify-between mb-4">
            <h3 v-if="title" :id="titleId" class="text-heading text-text">{{ title }}</h3>
            <button
              v-if="closable"
              class="p-1 rounded-md text-text-muted hover:text-text hover:bg-surface-muted transition-colors ml-auto"
              aria-label="Close"
              @click="emit('close')"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
          <slot />
          <div v-if="$slots.footer" class="mt-6 flex justify-end gap-2">
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
  transition: opacity 220ms cubic-bezier(0.2, 0, 0, 1);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
