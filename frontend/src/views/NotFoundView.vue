<script setup lang="ts">
/**
 * 404 页面不存在
 */
import { useI18n } from 'vue-i18n'
import { FileQuestion } from 'lucide-vue-next'
import { BaseButton, BaseEmptyState } from '@/components/base'

const { t } = useI18n()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-bg-app">
    <div class="w-full max-w-md px-4">
      <BaseEmptyState title="404" :description="t('errors.notFound')" :icon="FileQuestion">
        <router-link v-slot="{ navigate }" :to="{ name: 'projects.index' }" custom>
          <BaseButton variant="primary" size="lg" @click="navigate">
            {{ t('common.back') }}
          </BaseButton>
        </router-link>
      </BaseEmptyState>
    </div>
  </div>
</template>
