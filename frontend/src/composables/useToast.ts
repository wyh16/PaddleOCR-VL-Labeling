/**
 * Toast 通知 composable
 */
import { ref, readonly } from 'vue'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

const toasts = ref<Toast[]>([])

export function useToast() {
  function addToast(toast: Omit<Toast, 'id'>) {
    const id = Date.now().toString()
    const newToast: Toast = { ...toast, id }
    toasts.value.push(newToast)

    // 自动移除
    const duration = toast.duration || 3000
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function removeToast(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function success(message: string) {
    addToast({ type: 'success', message })
  }

  function error(message: string) {
    addToast({ type: 'error', message, duration: 5000 })
  }

  function warning(message: string) {
    addToast({ type: 'warning', message })
  }

  function info(message: string) {
    addToast({ type: 'info', message })
  }

  return {
    toasts: readonly(toasts),
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
  }
}
