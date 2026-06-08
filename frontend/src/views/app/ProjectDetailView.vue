<script setup lang="ts">
/**
 * 项目详情页
 * tab 通过 URL Query 驱动，支持刷新保持
 * 参考：doc/开发文档/前端/frontend_routing_spec.md 第 9 章
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import BaseTabs from '@/components/base/BaseTabs.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

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
        <div v-if="activeTab === 'pages'">
          <div class="text-center py-12">
            <p class="text-body text-text-muted">{{ t('common.noData') }}</p>
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
