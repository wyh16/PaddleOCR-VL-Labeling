<script setup lang="ts">
/**
 * 标注工作台页面
 * 通过 AnnotationWorkspaceLayout 提供布局
 * 负责加载 page 元数据、图片访问入口、latest revision、label registry、QC 列表和 capabilities
 *
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 14 章
 */
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { pagesApi, type Page, type Capabilities } from '@/api/pages'
import { annotationsApi, type AnnotationRevision } from '@/api/annotations'
import { qcApi, type QcIssue } from '@/api/qc'
import { ApiClientError } from '@/api/client'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseTabs from '@/components/base/BaseTabs.vue'
import {
  MousePointer2,
  SquareDashedMousePointer,
  BookOpen,
  Hand,
  ZoomIn,
  ZoomOut,
  Maximize,
  Expand,
  Undo2,
  Redo2,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Eye,
  Fullscreen,
} from 'lucide-vue-next'

const { t } = useI18n()
const route = useRoute()

const pageId = computed(() => route.params.page_id as string)
const revisionId = computed(() => route.query.revision_id as string | undefined)

// ── 状态 ──
const loading = ref(true)
const error = ref('')
const errorCode = ref<number | undefined>()

// ── 数据 ──
const page = ref<Page | null>(null)
const capabilities = ref<Capabilities | null>(null)
const revision = ref<AnnotationRevision | null>(null)
const qcIssues = ref<QcIssue[]>([])

const isReadonly = computed(() => {
  if (revisionId.value) return true
  if (capabilities.value && !capabilities.value.can_edit) return true
  return false
})

const updateSaveStatus = inject<((status: 'saved' | 'dirty' | 'readonly') => void) | undefined>('updateSaveStatus')
const updatePageTitle = inject<((title: string) => void) | undefined>('updatePageTitle')

function syncWorkspaceMeta() {
  updateSaveStatus?.(isReadonly.value ? 'readonly' : 'saved')
  if (page.value) {
    updatePageTitle?.(page.value.filename)
  } else {
    updatePageTitle?.(t('routes.pages.workspace'))
  }
}

// ── 工具栏状态 ──
const activeTool = ref('select')
const zoomLevel = ref(100)

const tools = [
  { key: 'select', icon: MousePointer2, label: 'annotation.tools.select', shortcut: 'R' },
  { key: 'rectangle', icon: SquareDashedMousePointer, label: 'annotation.tools.rectangle', shortcut: 'W' },
  { key: 'readingOrder', icon: BookOpen, label: 'annotation.tools.readingOrder', shortcut: 'R' },
  { key: 'pan', icon: Hand, label: 'annotation.tools.pan', shortcut: 'Space' },
]

// ── 右侧面板 ──
const rightPanelTab = ref('labels')
const rightPanelTabs = computed(() => [
  { key: 'labels', label: t('annotation.labels.title') },
  { key: 'objects', label: t('annotation.objects.title'), count: 12 },
  { key: 'qc', label: t('annotation.qc.title'), count: 3 },
])

// ── 标签数据（mock） ──
const labels = [
  { name: '题目', color: '#5e6ad2', count: 124, visible: true },
  { name: '答案区域', color: '#24a148', count: 356, visible: true },
  { name: '选项区域', color: '#0f62fe', count: 89, visible: true },
  { name: '图像区域', color: '#da1e28', count: 45, visible: true },
  { name: '公式', color: '#dd5b00', count: 23, visible: true },
  { name: '表格', color: '#0f62fe', count: 12, visible: true },
  { name: '其他', color: '#8c8c8c', count: 8, visible: true },
]

// ── 页面缩略图（mock） ──
const currentPageIndex = ref(11)
const totalPages = 15
const pageThumbnails = Array.from({ length: totalPages }, (_, i) => ({
  index: i,
  number: i + 1,
  hasAnnotation: [3, 7, 11].includes(i),
}))

// ── 加载数据 ──
async function loadWorkspace() {
  loading.value = true
  error.value = ''
  errorCode.value = undefined

  try {
    if (!pageId.value) {
      error.value = t('errors.notFound')
      errorCode.value = 404
      syncWorkspaceMeta()
      return
    }

    try {
      page.value = await pagesApi.get(pageId.value)
    } catch (e) {
      if (e instanceof ApiClientError) {
        errorCode.value = e.status
        if (e.status === 404) error.value = t('errors.notFound')
        else if (e.status === 403) error.value = t('errors.forbidden')
        else error.value = t('errors.server')
      }
      syncWorkspaceMeta()
      return
    }

    try {
      capabilities.value = await pagesApi.getCapabilities(page.value.project_id)
    } catch {
      capabilities.value = { can_edit: false, can_review: false, can_export: false, can_manage: false }
    }

    try {
      if (revisionId.value) {
        const revisions = await annotationsApi.listRevisions(pageId.value)
        revision.value = revisions.find(r => r.id === revisionId.value) || null
      } else {
        revision.value = await annotationsApi.getLatest(pageId.value)
      }
    } catch (e) {
      if (e instanceof ApiClientError && e.status === 404) revision.value = null
    }

    try {
      const qcResponse = await qcApi.listByPage(pageId.value)
      qcIssues.value = qcResponse.items
    } catch { /* QC 加载失败不阻止页面显示 */ }

    syncWorkspaceMeta()
  } finally {
    loading.value = false
  }
}

watch([pageId, revisionId], () => { loadWorkspace() })
watch(isReadonly, () => { syncWorkspaceMeta() })
onMounted(() => { loadWorkspace() })
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-text-muted">
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        {{ t('common.loading') }}
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <p class="text-heading text-text mb-2">{{ error }}</p>
        <p v-if="errorCode" class="text-caption text-text-muted mb-4">Error {{ errorCode }}</p>
        <BaseButton variant="primary" @click="loadWorkspace">
          {{ t('common.retry') }}
        </BaseButton>
      </div>
    </div>

    <!-- Workspace -->
    <template v-else-if="page">
      <!-- ═══ 工具栏 ═══ -->
      <div class="h-12 bg-surface border-b border-border flex items-center px-3 shrink-0 gap-1 z-toolbar">
        <!-- 左侧工具组 -->
        <div class="flex items-center gap-1">
          <button
            v-for="tool in tools"
            :key="tool.key"
            :class="[
              'w-8 h-8 flex items-center justify-center rounded-md transition-all duration-fast',
              activeTool === tool.key
                ? 'bg-primary/10 text-primary border border-primary/30'
                : 'text-text-secondary hover:bg-surface-muted hover:text-text border border-transparent',
            ]"
            :aria-label="t(tool.label)"
            :title="`${t(tool.label)} (${tool.shortcut})`"
            @click="activeTool = tool.key"
          >
            <component :is="tool.icon" class="w-4 h-4" />
          </button>
        </div>

        <!-- 分隔线 -->
        <div class="w-px h-5 bg-border mx-1"></div>

        <!-- 缩放控件 -->
        <div class="flex items-center gap-1">
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.zoomOut')"
            @click="zoomLevel = Math.max(25, zoomLevel - 25)"
          >
            <ZoomOut class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.zoomIn')"
            @click="zoomLevel = Math.min(400, zoomLevel + 25)"
          >
            <ZoomIn class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.fitWidth')"
          >
            <Expand class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.fitPage')"
          >
            <Maximize class="w-4 h-4" />
          </button>
        </div>

        <!-- 分隔线 -->
        <div class="w-px h-5 bg-border mx-1"></div>

        <!-- 缩放百分比 -->
        <button class="h-7 px-2 text-caption font-mono text-text-secondary hover:bg-surface-muted rounded-md transition-colors">
          {{ zoomLevel }}%
        </button>

        <!-- 右侧操作 -->
        <div class="ml-auto flex items-center gap-1">
          <!-- 撤销/重做 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.undo')"
            :title="`${t('annotation.tools.undo')} (Ctrl+Z)`"
          >
            <Undo2 class="w-4 h-4" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            :aria-label="t('annotation.tools.redo')"
            :title="`${t('annotation.tools.redo')} (Ctrl+Y)`"
          >
            <Redo2 class="w-4 h-4" />
          </button>

          <!-- 分隔线 -->
          <div class="w-px h-5 bg-border mx-1"></div>

          <!-- 删除 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-danger-bg hover:text-danger transition-colors"
            :aria-label="t('annotation.tools.delete')"
            :title="`${t('annotation.tools.delete')} (Delete)`"
          >
            <Trash2 class="w-4 h-4" />
          </button>

          <!-- 分隔线 -->
          <div class="w-px h-5 bg-border mx-1"></div>

          <!-- 缩放选择 -->
          <select class="h-7 px-1.5 text-caption bg-surface border border-border rounded-md text-text-secondary focus:outline-none focus:ring-2 focus:ring-focus">
            <option value="100">100%</option>
            <option value="75">75%</option>
            <option value="50">50%</option>
            <option value="25">25%</option>
          </select>

          <!-- 全屏 -->
          <button
            class="w-8 h-8 flex items-center justify-center rounded-md text-text-secondary hover:bg-surface-muted hover:text-text transition-colors"
            aria-label="Fullscreen"
          >
            <Fullscreen class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- ═══ 左侧：页面缩略图列表 ═══ -->
      <div class="flex flex-1 overflow-hidden">
        <!-- 左侧面板：页面导航 -->
        <div class="w-32 bg-surface-muted border-r border-border-soft flex flex-col shrink-0">
          <!-- 页码导航 -->
          <div class="flex items-center justify-between px-2 py-1.5 border-b border-border-soft">
            <button class="w-6 h-6 flex items-center justify-center rounded text-text-muted hover:text-text hover:bg-surface transition-colors">
              <ChevronLeft class="w-3.5 h-3.5" />
            </button>
            <span class="text-caption text-text">
              <span class="font-medium">1</span>
              <span class="text-text-muted"> / </span>
              <span>4</span>
            </span>
            <button class="w-6 h-6 flex items-center justify-center rounded text-text-muted hover:text-text hover:bg-surface transition-colors">
              <ChevronRight class="w-3.5 h-3.5" />
            </button>
          </div>

          <!-- 缩略图列表 -->
          <div class="flex-1 overflow-y-auto p-1.5 space-y-1.5">
            <div
              v-for="thumb in pageThumbnails.slice(0, 4)"
              :key="thumb.index"
              :class="[
                'rounded-md overflow-hidden cursor-pointer border-2 transition-colors',
                currentPageIndex === thumb.index ? 'border-primary' : 'border-transparent hover:border-border-strong',
              ]"
            >
              <div class="aspect-[3/4] bg-bg-canvas flex items-center justify-center relative">
                <div class="w-full h-full bg-surface-muted flex items-center justify-center">
                  <div class="text-micro text-text-muted">{{ thumb.number }}</div>
                </div>
                <!-- 标注指示点 -->
                <div
                  v-if="thumb.hasAnnotation"
                  class="absolute bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-primary"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- ═══ 中间画布区 ═══ -->
        <div class="flex-1 bg-bg-canvas relative overflow-hidden flex items-center justify-center">
          <!-- 画布内容占位 -->
          <div class="text-center">
            <div class="w-96 bg-white border border-border-soft rounded-lg shadow-sm p-8 mx-auto">
              <div class="text-heading text-text-warm mb-4">小学数学三年级期末测试卷</div>
              <div class="space-y-3 text-body text-text-warm text-left">
                <div class="text-subheading">一、填空题（每题 2 分，共 20 分）</div>
                <div>1. 计算 24 × 3 = <span class="inline-block w-16 border-b border-border-strong mx-1"></span>。</div>
                <div>2. 一个长方形的长是 8 厘米，宽是 6 厘米，它的面积是（  ）平方厘米。</div>
                <div class="pl-4">3. 在括号里填上合适的单位。</div>
                <div class="pl-8">(1) 一支铅笔长约 18 <span class="inline-block w-12 border-b border-border-strong mx-1"></span>。</div>
                <div class="pl-8">(2) 一张课桌高约 7 <span class="inline-block w-12 border-b border-border-strong mx-1"></span>。</div>
                <div class="text-subheading mt-4">二、选择题（每题 2 分，共 10 分）</div>
                <div>1. 下面哪个数比 400 大？</div>
                <div class="pl-4 flex gap-4">
                  <span>A. 398</span>
                  <span>B. 421</span>
                  <span>C. 305</span>
                </div>
              </div>
            </div>

            <!-- Mock overlay boxes -->
            <div class="absolute top-1/4 left-1/3 w-48 border-2 border-overlay-manual rounded-sm pointer-events-none">
              <span class="absolute -top-5 left-0 text-micro bg-overlay-manual text-white px-1 py-0.5 rounded-sm">题目</span>
            </div>
            <div class="absolute top-[45%] left-1/4 w-64 border-2 border-overlay-manual rounded-sm pointer-events-none">
              <span class="absolute -top-5 left-0 text-micro bg-success text-white px-1 py-0.5 rounded-sm">答案区域</span>
            </div>
            <div class="absolute top-[65%] left-1/4 w-56 border-2 border-overlay-candidate rounded-sm pointer-events-none">
              <span class="absolute -top-5 left-0 text-micro bg-info text-white px-1 py-0.5 rounded-sm">选项区域</span>
            </div>
          </div>
        </div>

        <!-- ═══ 右侧：标签管理/对象列表/QC ═══ -->
        <div class="w-64 bg-surface border-l border-border flex flex-col shrink-0">
          <!-- Tab 切换 -->
          <BaseTabs
            :tabs="rightPanelTabs"
            :active-key="rightPanelTab"
            class="shrink-0"
            @update:active-key="rightPanelTab = $event"
          />

          <!-- 标签管理 -->
          <div v-if="rightPanelTab === 'labels'" class="flex-1 overflow-y-auto">
            <div class="p-3">
              <button class="w-full h-8 text-caption text-primary hover:bg-primary/5 rounded-md flex items-center justify-center gap-1 transition-colors mb-3">
                {{ t('annotation.labels.newLabel') }}
              </button>

              <div class="space-y-1">
                <div
                  v-for="label in labels"
                  :key="label.name"
                  class="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-surface-muted transition-colors cursor-pointer"
                >
                  <input type="checkbox" :checked="label.visible" class="w-3.5 h-3.5 rounded border-border-strong text-primary focus:ring-focus" />
                  <span class="w-3 h-3 rounded-sm shrink-0" :style="{ backgroundColor: label.color }"></span>
                  <span class="flex-1 text-body text-text truncate">{{ label.name }}</span>
                  <span class="text-caption text-text-muted">{{ label.count }}</span>
                  <button class="p-0.5 rounded text-text-muted hover:text-text transition-colors" aria-label="Show">
                    <Eye class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 对象列表 -->
          <div v-else-if="rightPanelTab === 'objects'" class="flex-1 overflow-y-auto">
            <div class="p-3 text-caption text-text-muted">
              {{ t('annotation.objects.count', { count: 12 }) }}
            </div>
          </div>

          <!-- QC 问题 -->
          <div v-else-if="rightPanelTab === 'qc'" class="flex-1 overflow-y-auto">
            <div class="p-3 text-caption text-text-muted">
              {{ t('annotation.qc.count', { count: 3 }) }}
            </div>
          </div>

          <!-- 属性编辑 -->
          <div class="border-t border-border p-3 shrink-0">
            <div class="text-body-medium text-text mb-3">{{ t('annotation.properties.title') }}</div>
            <div class="space-y-2">
              <div>
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.label') }}</label>
                <select class="w-full h-7 px-2 text-caption bg-surface border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-focus">
                  <option>题目</option>
                  <option>答案区域</option>
                  <option>选项区域</option>
                </select>
              </div>
              <div>
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.textContent') }}</label>
                <input
                  type="text"
                  value="计算 24 × 3 = ____。"
                  class="w-full h-7 px-2 text-caption bg-surface border border-border rounded-md text-text focus:outline-none focus:ring-2 focus:ring-focus"
                  readonly
                />
              </div>
              <div>
                <label class="text-micro text-text-tertiary block mb-1">{{ t('annotation.properties.coordinates') }}</label>
                <div class="grid grid-cols-4 gap-1">
                  <input type="text" value="120" class="h-7 px-1.5 text-caption font-mono bg-surface border border-border rounded-md text-text text-center focus:outline-none focus:ring-2 focus:ring-focus" readonly />
                  <input type="text" value="180" class="h-7 px-1.5 text-caption font-mono bg-surface border border-border rounded-md text-text text-center focus:outline-none focus:ring-2 focus:ring-focus" readonly />
                  <input type="text" value="580" class="h-7 px-1.5 text-caption font-mono bg-surface border border-border rounded-md text-text text-center focus:outline-none focus:ring-2 focus:ring-focus" readonly />
                  <input type="text" value="240" class="h-7 px-1.5 text-caption font-mono bg-surface border border-border rounded-md text-text text-center focus:outline-none focus:ring-2 focus:ring-focus" readonly />
                </div>
              </div>
              <div class="flex justify-between text-micro text-text-tertiary">
                <span>{{ t('annotation.properties.id') }}: <span class="font-mono">obj_00123</span></span>
              </div>
              <div class="text-micro text-text-tertiary">
                {{ t('annotation.properties.createdAt') }}: 2024-05-27 10:15:23
              </div>
            </div>
          </div>

          <!-- 快捷键帮助 -->
          <div class="border-t border-border p-3 shrink-0">
            <div class="text-body-medium text-text mb-2">{{ t('annotation.shortcuts.title') }}</div>
            <div class="grid grid-cols-2 gap-x-3 gap-y-1 text-micro">
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">W</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.rectangleTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl + Z</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.undo') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">R</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.selectTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl + Y</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.redo') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">R</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.readingOrderTool') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Delete</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.deleteSelected') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Space</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.panCanvas') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <kbd class="font-mono text-text-tertiary bg-surface-alt border border-border rounded px-1 py-0.5">Ctrl + S</kbd>
                <span class="text-text-secondary">{{ t('annotation.shortcuts.save') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 底部：页面缩略图条 ═══ -->
      <div class="h-24 bg-surface border-t border-border shrink-0 flex items-center px-3 gap-2 z-sticky">
        <button class="flex items-center gap-1 text-caption text-text-secondary hover:text-text px-2 py-1 rounded-md hover:bg-surface-muted transition-colors shrink-0">
          <ChevronLeft class="w-3.5 h-3.5" />
          {{ t('annotation.pages.prevPage') }}
        </button>

        <div class="flex-1 flex items-center gap-1.5 overflow-x-auto">
          <div
            v-for="thumb in pageThumbnails"
            :key="thumb.index"
            :class="[
              'shrink-0 w-14 rounded-md overflow-hidden cursor-pointer border-2 transition-colors',
              currentPageIndex === thumb.index ? 'border-primary' : 'border-transparent hover:border-border-strong',
            ]"
          >
            <div class="aspect-[3/4] bg-bg-canvas flex items-center justify-center relative">
              <div class="text-micro text-text-muted">{{ thumb.number }}</div>
              <div
                v-if="thumb.hasAnnotation"
                class="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-primary"
              ></div>
            </div>
          </div>
        </div>

        <button class="flex items-center gap-1 text-caption text-text-secondary hover:text-text px-2 py-1 rounded-md hover:bg-surface-muted transition-colors shrink-0">
          {{ t('annotation.pages.nextPage') }}
          <ChevronRight class="w-3.5 h-3.5" />
        </button>
      </div>
    </template>
  </div>
</template>
