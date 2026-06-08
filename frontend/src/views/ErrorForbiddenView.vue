<script setup lang="ts">
/**
 * 403 权限不足页面
 * 不暴露敏感资源细节
 */
import { useI18n } from 'vue-i18n'
import BaseButton from '@/components/base/BaseButton.vue'
import { ShieldAlert } from 'lucide-vue-next'

const { t } = useI18n()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-bg-app">
    <div class="text-center">
      <ShieldAlert class="w-16 h-16 text-text-muted mx-auto mb-4" />
      <h1 class="text-display text-text mb-2">403</h1>
      <p class="text-body text-text-secondary mb-6">{{ t('errors.forbidden') }}</p>
      <router-link :to="{ name: 'projects.index' }">
        <BaseButton variant="primary">{{ t('common.back') }}</BaseButton>
      </router-link>
    </div>
  </div>
</template>
