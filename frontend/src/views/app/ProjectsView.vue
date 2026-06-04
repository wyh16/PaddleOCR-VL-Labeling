<script setup lang="ts">
/**
 * 项目列表页
 * 接入项目列表 API，支持 loading / error / empty 状态
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { projectsApi, type Project } from '@/api/projects'
import { ApiClientError } from '@/api/client'
import BaseButton from '@/components/base/BaseButton.vue'

const { t } = useI18n()
const router = useRouter()

const projects = ref<Project[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const response = await projectsApi.list()
    projects.value = response.items
  } catch (e) {
    if (e instanceof ApiClientError) {
      if (e.status === 0) {
        error.value = t('errors.network')
      } else {
        error.value = t('errors.server')
      }
    } else {
      error.value = t('errors.unknown')
    }
  } finally {
    loading.value = false
  }
})

function goToProject(projectId: string) {
  router.push({
    name: 'projects.detail',
    params: { project_id: projectId },
  })
}
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-text">{{ t('routes.projects.index') }}</h2>
      <BaseButton variant="primary">
        {{ t('project.create') }}
      </BaseButton>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-muted">
      {{ t('common.loading') }}
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-danger mb-4">{{ error }}</p>
      <BaseButton variant="secondary" size="sm" @click="() => { loading = true; error = ''; }">
        {{ t('common.retry') }}
      </BaseButton>
    </div>

    <!-- Empty -->
    <div v-else-if="projects.length === 0" class="text-center py-12 text-muted">
      {{ t('common.noData') }}
    </div>

    <!-- List -->
    <div v-else class="grid gap-4">
      <div
        v-for="project in projects"
        :key="project.id"
        class="p-4 bg-surface rounded-lg border border-border hover:border-accent cursor-pointer transition-colors"
        @click="goToProject(project.id)"
      >
        <h3 class="font-medium text-text">{{ project.name }}</h3>
        <p v-if="project.description" class="text-sm text-muted mt-1">
          {{ project.description }}
        </p>
      </div>
    </div>
  </div>
</template>
