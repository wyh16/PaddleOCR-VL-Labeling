<script setup lang="ts">
/**
 * 403 权限不足页面
 */
import { useI18n } from 'vue-i18n'
import { ShieldAlert } from 'lucide-vue-next'
import { BaseButton, BaseEmptyState } from '@/components/base'

const { t } = useI18n()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-bg-app">
    <div class="w-full max-w-md px-4">
      <BaseEmptyState title="403" :description="t('errors.forbidden')" :icon="ShieldAlert">
        <router-link v-slot="{ navigate }" :to="{ name: 'projects.index' }" custom>
          <BaseButton variant="primary" size="lg" @click="navigate">
            {{ t('common.back') }}
          </BaseButton>
        </router-link>
      </BaseEmptyState>
    </div>
  </div>
</template>
