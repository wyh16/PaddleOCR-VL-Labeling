<script setup lang="ts">
/**
 * 应用主布局
 * 负责工作台通用框架，包括侧边栏、顶部状态区、主内容区
 */
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import BaseButton from '@/components/base/BaseButton.vue'

const { t } = useI18n()
const router = useRouter()
const { user, logout } = useAuth()

async function handleLogout() {
  await logout()
  router.replace({ name: 'auth.login' })
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- 侧边栏 -->
    <aside class="w-64 bg-surface border-r border-border flex flex-col">
      <div class="p-4 border-b border-border">
        <h1 class="text-lg font-bold text-text">{{ t('routes.app.home') }}</h1>
      </div>

      <nav class="flex-1 p-4 space-y-2">
        <router-link
          :to="{ name: 'projects.index' }"
          class="block px-3 py-2 rounded-md text-text hover:bg-background"
          active-class="bg-background"
        >
          {{ t('routes.projects.index') }}
        </router-link>

        <router-link
          :to="{ name: 'settings.index' }"
          class="block px-3 py-2 rounded-md text-text hover:bg-background"
          active-class="bg-background"
        >
          {{ t('routes.settings.index') }}
        </router-link>
      </nav>

      <div class="p-4 border-t border-border">
        <div v-if="user" class="text-sm text-muted mb-2">
          {{ user.username }}
        </div>
        <BaseButton
          variant="secondary"
          size="sm"
          class="w-full"
          @click="handleLogout"
        >
          {{ t('auth.logout') }}
        </BaseButton>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>
</template>
