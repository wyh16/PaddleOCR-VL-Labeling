<script setup lang="ts">
/**
 * 项目详情页
 * tab 通过 URL Query 驱动，支持刷新保持
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 9 章
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

/** tab 白名单 */
const VALID_TABS = ['pages', 'members', 'jobs', 'exports', 'settings'] as const
type Tab = typeof VALID_TABS[number]

/**
 * 当前 tab，从 Query 读取，非法值回退到 'pages'
 * 使用 computed 保证 URL 变化时自动更新
 */
const activeTab = computed<Tab>(() => {
  const tab = route.query.tab as string
  if (tab && VALID_TABS.includes(tab as Tab)) {
    return tab as Tab
  }
  return 'pages'
})

/** 切换 tab，更新 URL Query */
function switchTab(tab: Tab) {
  router.replace({
    query: { ...route.query, tab },
  })
}

// TODO: 加载项目详情
</script>

<template>
  <div class="p-6">
    <h2 class="text-2xl font-bold text-text mb-6">{{ t('routes.projects.detail') }}</h2>

    <!-- Tab 导航 -->
    <div class="border-b border-border mb-6">
      <nav class="flex space-x-8">
        <button
          v-for="tab in VALID_TABS"
          :key="tab"
          class="py-2 px-1 border-b-2 text-sm font-medium transition-colors"
          :class="activeTab === tab
            ? 'border-accent text-accent'
            : 'border-transparent text-muted hover:text-text'"
          @click="switchTab(tab)"
        >
          {{ t(`routes.projects.tabs.${tab}`) }}
        </button>
      </nav>
    </div>

    <!-- Tab 内容 -->
    <div>
      <div v-if="activeTab === 'pages'">
        <!-- TODO: 页面列表 -->
        <p class="text-muted">{{ t('common.loading') }}</p>
      </div>
      <div v-else-if="activeTab === 'members'">
        <!-- TODO: 成员列表 -->
        <p class="text-muted">{{ t('common.loading') }}</p>
      </div>
      <div v-else-if="activeTab === 'jobs'">
        <!-- TODO: 任务列表 -->
        <p class="text-muted">{{ t('common.loading') }}</p>
      </div>
      <div v-else-if="activeTab === 'exports'">
        <!-- TODO: 导出列表 -->
        <p class="text-muted">{{ t('common.loading') }}</p>
      </div>
      <div v-else-if="activeTab === 'settings'">
        <!-- TODO: 项目设置 -->
        <p class="text-muted">{{ t('common.loading') }}</p>
      </div>
    </div>
  </div>
</template>
