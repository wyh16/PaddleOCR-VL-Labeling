<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Project {
  id: string
  name: string
  description: string
  status: string
  created_at: string
}

const projects = ref<Project[]>([])
const loading = ref(true)

onMounted(async () => {
  // TODO: 调用 API 获取项目列表
  loading.value = false
})
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-text">{{ t('project.title') }}</h2>
      <button class="px-4 py-2 bg-accent text-white rounded-md hover:bg-accent/90">
        {{ t('project.create') }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-muted">
      {{ t('common.loading') }}
    </div>

    <div v-else-if="projects.length === 0" class="text-center py-12 text-muted">
      {{ t('common.noData') }}
    </div>

    <div v-else class="grid gap-4">
      <div
        v-for="project in projects"
        :key="project.id"
        class="p-4 bg-surface rounded-lg border border-border hover:border-accent cursor-pointer"
      >
        <h3 class="font-medium text-text">{{ project.name }}</h3>
        <p class="text-sm text-muted mt-1">{{ project.description }}</p>
      </div>
    </div>
  </div>
</template>
