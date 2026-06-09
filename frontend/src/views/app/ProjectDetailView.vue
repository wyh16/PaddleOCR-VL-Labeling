<script setup lang="ts">
/**
 * 项目详情页
 * tab 通过 URL Query 驱动，支持刷新保持
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 9 章
 */
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { assetsApi, type AssetUploadResponse } from '@/api/assets'
import { pagesApi, type Page } from '@/api/pages'
import { ApiClientError } from '@/api/client'
import BaseTabs from '@/components/base/BaseTabs.vue'
import BaseFileUpload from '@/components/base/BaseFileUpload.vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEmptyState from '@/components/base/BaseEmptyState.vue'
import { FileCheck, AlertCircle, Loader2, FileImage, PenTool } from 'lucide-vue-next'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.project_id as string)

// ── 页面列表 ──
const pages = ref<Page[]>([])
const pagesLoading = ref(true)

async function loadPages() {
  pagesLoading.value = true
  try {
    const res = await pagesApi.list(projectId.value)
    pages.value = res.items
  } catch {
    pages.value = []
  } finally {
    pagesLoading.value = false
  }
}

function openWorkspace(pageId: string) {
  router.push({ name: 'pages.workspace', params: { page_id: pageId } })
}

onMounted(() => { loadPages() })

const VALID_TABS = ['pages', 'members', 'jobs', 'exports', 'settings'] as const
type Tab = typeof VALID_TABS[number]

const activeTab = computed<Tab>(() => {
  const tab = route.query.tab as string
  if (tab && VALID_TABS.includes(tab as Tab)) return tab as Tab
  return 'pages'
})

const tabs = computed(() => VALID_TABS.map(key => ({
  key,
  label: t(`routes.projects.tabs.${key}`),
})))

function switchTab(tab: string) {
  router.replace({ query: { ...route.query, tab } })
}

// ── 上传状态 ──
interface UploadItem {
  file: File
  status: 'pending' | 'uploading' | 'done' | 'error'
  result?: AssetUploadResponse['data']
  error?: string
}

const uploadItems = ref<UploadItem[]>([])

function handleFiles(files: File[]) {
  const newItems: UploadItem[] = files.map(f => ({ file: f, status: 'pending' }))
  uploadItems.value.push(...newItems)
}

async function startUpload() {
  const pending = uploadItems.value.filter(i => i.status === 'pending')
  for (const item of pending) {
    item.status = 'uploading'
    try {
      const res = await assetsApi.upload(projectId.value, item.file)
      item.status = 'done'
      item.result = res.data
    } catch (e) {
      item.status = 'error'
      item.error = e instanceof ApiClientError ? e.message : t('upload.failed')
    }
  }
}

function clearCompleted() {
  uploadItems.value = uploadItems.value.filter(i => i.status !== 'done')
}
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-5xl mx-auto p-6">
      <!-- 页面头部 -->
      <div class="mb-6">
        <nav class="flex items-center gap-1.5 text-caption text-text-secondary mb-3">
          <router-link :to="{ name: 'projects.index' }" class="hover:text-text transition-colors">
            {{ t('routes.projects.index') }}
          </router-link>
          <span class="text-text-muted">/</span>
          <span class="text-text">{{ t('routes.projects.detail') }}</span>
        </nav>
        <h1 class="text-title text-text">{{ t('routes.projects.detail') }}</h1>
      </div>

      <!-- Tab 导航 -->
      <BaseTabs
        :tabs="tabs"
        :active-key="activeTab"
        class="mb-6"
        @update:active-key="switchTab"
      />

      <!-- Tab 内容 -->
      <div class="py-4">
        <!-- 页面 tab：上传图片 + 页面列表 -->
        <div v-if="activeTab === 'pages'">
          <BaseFileUpload
            accept="image/*"
            :multiple="true"
            :max-size-m-b="50"
            @select="handleFiles"
          />

          <!-- 上传按钮和文件列表 -->
          <div v-if="uploadItems.length > 0" class="mt-4">
            <div class="flex items-center justify-between mb-3">
              <span class="text-caption text-text-secondary">
                {{ uploadItems.length }} {{ t('upload.selectFiles') }}
              </span>
              <div class="flex gap-2">
                <BaseButton variant="ghost" size="sm" @click="clearCompleted">
                  {{ t('common.close') }}
                </BaseButton>
                <BaseButton
                  variant="primary"
                  size="sm"
                  :disabled="!uploadItems.some(i => i.status === 'pending')"
                  @click="startUpload"
                >
                  {{ t('upload.startUpload') }}
                </BaseButton>
              </div>
            </div>

            <!-- 文件状态列表 -->
            <div class="space-y-2">
              <div
                v-for="(item, index) in uploadItems"
                :key="index"
                class="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border"
              >
                <Loader2 v-if="item.status === 'uploading'" class="w-4 h-4 text-primary animate-spin shrink-0" />
                <FileCheck v-else-if="item.status === 'done'" class="w-4 h-4 text-success shrink-0" />
                <AlertCircle v-else-if="item.status === 'error'" class="w-4 h-4 text-danger shrink-0" />
                <div class="flex-1 min-w-0">
                  <p class="text-body text-text truncate">{{ item.file.name }}</p>
                  <p v-if="item.result" class="text-caption text-text-muted">
                    {{ item.result.asset_id }} · {{ item.result.width }}×{{ item.result.height }}
                  </p>
                  <p v-if="item.error" class="text-caption text-danger">{{ item.error }}</p>
                </div>
                <span class="text-caption text-text-muted shrink-0">
                  {{ (item.file.size / 1024 / 1024).toFixed(1) }}MB
                </span>
              </div>
            </div>
          </div>

          <!-- 已有页面列表 -->
          <div class="mt-6">
            <h3 class="text-body-medium text-text mb-3">{{ t('routes.projects.tabs.pages') }}</h3>

            <div v-if="pagesLoading" class="space-y-2">
              <div v-for="i in 3" :key="i" class="h-16 bg-surface-alt rounded-lg animate-pulse"></div>
            </div>

            <BaseEmptyState
              v-else-if="pages.length === 0"
              :icon="FileImage"
              :title="t('common.noData')"
              :description="t('upload.selectFiles')"
            />

            <div v-else class="space-y-2">
              <div
                v-for="page in pages"
                :key="page.page_id"
                class="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border hover:border-primary/40 cursor-pointer transition-all duration-fast"
                @click="openWorkspace(page.page_id)"
              >
                <FileImage class="w-5 h-5 text-primary shrink-0" />
                <div class="flex-1 min-w-0">
                  <p class="text-body text-text truncate">{{ page.filename }}</p>
                  <p class="text-caption text-text-muted">{{ page.width }}×{{ page.height }} · {{ page.status }}</p>
                </div>
                <BaseButton variant="ghost" size="sm" :left-icon="PenTool">
                  {{ t('annotation.tools.select') }}
                </BaseButton>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'members'">
          <div class="text-center py-12">
            <p class="text-body text-text-muted">{{ t('common.noData') }}</p>
          </div>
        </div>
        <div v-else-if="activeTab === 'jobs'">
          <div class="text-center py-12">
            <p class="text-body text-text-muted">{{ t('common.noData') }}</p>
          </div>
        </div>
        <div v-else-if="activeTab === 'exports'">
          <div class="text-center py-12">
            <p class="text-body text-text-muted">{{ t('common.noData') }}</p>
          </div>
        </div>
        <div v-else-if="activeTab === 'settings'">
          <div class="text-center py-12">
            <p class="text-body text-text-muted">{{ t('common.noData') }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
