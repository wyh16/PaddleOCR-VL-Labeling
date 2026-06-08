<script setup lang="ts">
/**
 * Tabs 组件
 * 用于同页面内平级视图切换
 * 规范：frontend_component_library_spec.md §5.5
 */

interface Tab {
  key: string
  label: string
  count?: number
}

interface Props {
  tabs: Tab[]
  activeKey: string
}

defineProps<Props>()

const emit = defineEmits<{
  'update:activeKey': [key: string]
}>()
</script>

<template>
  <nav class="flex border-b border-border" role="tablist">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      role="tab"
      :aria-selected="activeKey === tab.key"
      :class="[
        'flex items-center gap-1.5 px-3 py-2 text-body-medium border-b-2 transition-colors whitespace-nowrap',
        activeKey === tab.key
          ? 'border-primary text-primary'
          : 'border-transparent text-text-secondary hover:text-text hover:border-border-strong',
      ]"
      @click="emit('update:activeKey', tab.key)"
    >
      <span class="truncate">{{ tab.label }}</span>
      <span
        v-if="tab.count !== undefined"
        :class="[
          'text-micro px-1 py-0 rounded-sm',
          activeKey === tab.key ? 'bg-primary/10 text-primary' : 'bg-surface-alt text-text-muted',
        ]"
      >
        {{ tab.count }}
      </span>
    </button>
  </nav>
</template>
