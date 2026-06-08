<script setup lang="ts">
/**
 * Toast 通知组件
 * 全局 Toast 容器，配合 useToast composable 使用
 * 规范：frontend_component_library_spec.md §5.8
 */
import { CircleCheck, CircleAlert, Info, X } from 'lucide-vue-next'
import { useToast, type Toast } from '@/composables/useToast'

const { toasts, removeToast } = useToast()

const iconMap: Record<Toast['type'], typeof CircleCheck> = {
  success: CircleCheck,
  error: CircleAlert,
  warning: CircleAlert,
  info: Info,
}

const variantClasses: Record<Toast['type'], string> = {
  success: 'border-success/30 bg-success-bg text-success',
  error: 'border-danger/30 bg-danger-bg text-danger',
  warning: 'border-warning/30 bg-warning-bg text-warning',
  info: 'border-info/30 bg-info-bg text-info',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-toast flex flex-col gap-2 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
            'pointer-events-auto flex items-center gap-2 px-3 py-2 rounded-lg border shadow-popover text-body max-w-sm animate-fade-in',
            variantClasses[toast.type],
          ]"
          role="alert"
        >
          <component :is="iconMap[toast.type]" class="w-4 h-4 shrink-0" />
          <span class="flex-1">{{ toast.message }}</span>
          <button
            class="shrink-0 p-0.5 rounded hover:bg-black/10 transition-colors"
            aria-label="Close"
            @click="removeToast(toast.id)"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 160ms cubic-bezier(0.2, 0, 0, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(24px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(24px);
}
</style>
