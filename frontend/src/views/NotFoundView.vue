<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-text mb-4">404</h1>
      <p class="text-lg text-muted mb-6">页面不存在</p>
      <router-link
        to="/app/projects"
        class="px-4 py-2 bg-accent text-white rounded-md hover:bg-accent/90"
      >
        {{ t('common.back') }}
      </router-link>
    </div>
  </div>
</template>
