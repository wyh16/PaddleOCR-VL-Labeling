<script setup lang="ts">
/**
 * Tooltip 组件
 * 短文本提示，不放可交互内容
 * 规范：frontend_component_library_spec.md §5.6
 */

interface Props {
  content: string
  position?: 'top' | 'bottom' | 'left' | 'right'
  shortcut?: string
}

withDefaults(defineProps<Props>(), {
  position: 'top',
})

const positionClasses: Record<string, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
}
</script>

<template>
  <div class="relative inline-flex group/tooltip">
    <slot />
    <div
      v-if="content"
      :class="[
        'absolute pointer-events-none opacity-0 group-hover/tooltip:opacity-100 transition-opacity duration-base z-toast',
        'px-2 py-1 text-micro font-medium text-white bg-text rounded-sm shadow-popover whitespace-nowrap',
        positionClasses[position],
      ]"
      role="tooltip"
    >
      {{ content }}
      <span v-if="shortcut" class="ml-1.5 opacity-60">{{ shortcut }}</span>
    </div>
  </div>
</template>
