<script setup lang="ts">
/**
 * 项目列表页
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { projectsApi, type Project } from '@/api/projects'
import { NButton, NEmpty, NSpin, NModal, NInput, NFormItem, useMessage, useDialog } from 'naive-ui'
import { FolderKanban, Plus, Trash2 } from 'lucide-vue-next'

const { t } = useI18n()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()

const projects = ref<Project[]>([])
const loading = ref(true)

// ── 创建项目弹窗 ──
const showModal = ref(false)
const creating = ref(false)
const formName = ref('')
const formDesc = ref('')

async function loadProjects() {
  loading.value = true
  try {
    const response = await projectsApi.list()
    projects.value = response.items
  } catch {
    // 后端不可用或无数据时视为空列表，引导用户创建
    projects.value = []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!formName.value.trim()) return
  creating.value = true
  try {
    await projectsApi.create({
      name: formName.value.trim(),
      description: formDesc.value.trim() || undefined,
    })
    showModal.value = false
    formName.value = ''
    formDesc.value = ''
    message.success(t('common.success'))
    await loadProjects()
  } catch (e) {
    message.error(t('common.error'))
  } finally {
    creating.value = false
  }
}

function handleDelete(project: Project) {
  dialog.warning({
    title: t('common.confirm'),
    content: `${t('common.delete')} "${project.name}"?`,
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      try {
        await projectsApi.delete(project.id)
        message.success(t('common.success'))
        await loadProjects()
      } catch (e) {
        message.error(t('common.error'))
      }
    },
  })
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
        <NButton type="primary" @click="showModal = true">
          <template #icon><Plus /></template>
          {{ t('project.create') }}
        </NButton>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <NSpin size="large" />
      </div>

      <!-- Empty -->
      <NEmpty v-else-if="projects.length === 0" :description="t('common.noData')" class="py-16">
        <template #extra>
          <NButton type="primary" @click="showModal = true">
            <template #icon><Plus /></template>
            {{ t('project.create') }}
          </NButton>
        </template>
      </NEmpty>

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
          <div class="flex items-center gap-2 shrink-0">
            <span class="text-micro text-text-muted">{{ project.schema_version }}</span>
            <NButton
              size="small"
              quaternary
              type="error"
              @click.stop="handleDelete(project)"
            >
              <template #icon><Trash2 /></template>
            </NButton>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建项目弹窗 -->
    <NModal v-model:show="showModal" preset="card" :title="t('project.create')" style="max-width: 480px;">
      <NFormItem :label="t('project.name')">
        <NInput v-model:value="formName" :placeholder="t('project.name')" />
      </NFormItem>
      <NFormItem :label="t('project.description')">
        <NInput v-model:value="formDesc" type="textarea" :placeholder="t('project.description')" :rows="3" />
      </NFormItem>
      <template #footer>
        <div class="flex justify-end gap-2">
          <NButton @click="showModal = false">{{ t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="creating" :disabled="!formName.trim()" @click="handleCreate">
            {{ t('common.confirm') }}
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>
