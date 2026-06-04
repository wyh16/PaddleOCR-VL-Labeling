<script setup lang="ts">
/**
 * 基础 Modal 组件
 */

interface Props {
  open: boolean
  title?: string
}

defineProps<Props>()

defineEmits<{
  close: []
}>()
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
        <div class="relative bg-background rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
          <div v-if="title" class="mb-4">
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
