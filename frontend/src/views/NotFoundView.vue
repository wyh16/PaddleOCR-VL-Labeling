<script setup lang="ts">
/**
 * 404 页面不存在
 */
import { useI18n } from 'vue-i18n'
import BaseButton from '@/components/base/BaseButton.vue'
import { FileQuestion } from 'lucide-vue-next'

const { t } = useI18n()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-bg-app">
    <div class="text-center">
      <FileQuestion class="w-16 h-16 text-text-muted mx-auto mb-4" />
      <h1 class="text-display text-text mb-2">404</h1>
      <p class="text-body text-text-secondary mb-6">{{ t('errors.notFound') }}</p>
      <router-link :to="{ name: 'projects.index' }">
        <BaseButton variant="primary">{{ t('common.back') }}</BaseButton>
      </router-link>
    </div>
  </div>
</template>
