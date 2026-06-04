<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="min-h-screen flex">
    <!-- 侧边栏 -->
    <aside class="w-64 bg-surface border-r border-border flex flex-col">
      <div class="p-4 border-b border-border">
        <h1 class="text-lg font-bold text-text">文档标注平台</h1>
      </div>

      <nav class="flex-1 p-4 space-y-2">
        <router-link
          to="/app/projects"
          class="block px-3 py-2 rounded-md text-text hover:bg-background"
          active-class="bg-background"
        >
          {{ t('project.title') }}
        </router-link>

        <router-link
          to="/app/settings"
          class="block px-3 py-2 rounded-md text-text hover:bg-background"
          active-class="bg-background"
        >
          设置
        </router-link>
      </nav>

      <div class="p-4 border-t border-border">
        <button class="w-full px-3 py-2 text-sm text-muted hover:text-text">
          {{ t('auth.logout') }}
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>
</template>
