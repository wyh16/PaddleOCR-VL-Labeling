<script setup lang="ts">
/**
 * 项目列表页
 * 接入项目列表 API，支持 loading / error / empty 状态
 * 规范：frontend_component_library_spec.md §9
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { projectsApi, type Project } from '@/api/projects'
import { ApiClientError } from '@/api/client'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import { FolderKanban, Plus } from 'lucide-vue-next'

const { t } = useI18n()
const router = useRouter()

const projects = ref<Project[]>([])
const loading = ref(true)
const error = ref('')

async function loadProjects() {
  loading.value = true
  error.value = ''
  try {
    const response = await projectsApi.list()
    projects.value = response.items
  } catch (e) {
    if (e instanceof ApiClientError) {
      error.value = e.status === 0 ? t('errors.network') : t('errors.server')
    } else {
      error.value = t('errors.unknown')
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadProjects() })

function goToProject(projectId: string) {
  router.push({ name: 'projects.detail', params: { project_id: projectId } })
}
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-5xl mx-auto p-6">
      <!-- 页面头部 -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-title text-text">{{ t('routes.projects.index') }}</h1>
        <BaseButton variant="primary" :left-icon="Plus">
          {{ t('project.create') }}
        </BaseButton>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="h-24 bg-surface-alt rounded-lg animate-pulse"></div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-16">
        <p class="text-body text-danger mb-4">{{ error }}</p>
        <BaseButton variant="secondary" size="sm" @click="loadProjects">
          {{ t('common.retry') }}
        </BaseButton>
      </div>

      <!-- Empty -->
      <BaseEmptyState
        v-else-if="projects.length === 0"
        :icon="FolderKanban"
        :title="t('common.noData')"
        :description="t('project.create')"
      >
        <template #action>
          <BaseButton variant="primary" :left-icon="Plus">
            {{ t('project.create') }}
          </BaseButton>
        </template>
      </BaseEmptyState>

      <!-- 项目列表 -->
      <div v-else class="space-y-2">
        <div
          v-for="project in projects"
          :key="project.id"
          class="group flex items-center gap-4 p-4 bg-surface rounded-lg border border-border hover:border-primary/40 cursor-pointer transition-all duration-fast"
          @click="goToProject(project.id)"
        >
          <div class="w-10 h-10 rounded-lg bg-primary/8 flex items-center justify-center shrink-0">
            <FolderKanban class="w-5 h-5 text-primary" />
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-body-medium text-text group-hover:text-primary transition-colors truncate">
              {{ project.name }}
            </h3>
            <p v-if="project.description" class="text-caption text-text-secondary mt-0.5 truncate">
              {{ project.description }}
            </p>
          </div>
          <div class="text-caption text-text-muted shrink-0">
            <!-- Mock status badge -->
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-success-bg text-success text-micro font-medium">
              <span class="w-1.5 h-1.5 rounded-full bg-success"></span>
              进行中
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
