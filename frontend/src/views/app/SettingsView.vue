<script setup lang="ts">
/**
 * 系统设置页
 * 使用基础组件，统一表单样式
 * 规范：frontend_component_library_spec.md §5.3
 */
import { useI18n } from 'vue-i18n'
import BaseInput from '@/components/base/BaseInput.vue'
import { Globe, User, Bell, Shield } from 'lucide-vue-next'

const { t, locale } = useI18n()

function changeLocale(lang: string) {
  locale.value = lang
  localStorage.setItem('k12.locale', lang)
}
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="max-w-3xl mx-auto p-6">
      <!-- 页面头部 -->
      <div class="mb-6">
        <h1 class="text-title text-text mb-1">{{ t('routes.settings.index') }}</h1>
        <p class="text-body text-text-secondary">{{ t('routes.settings.index') }}</p>
      </div>

      <!-- 设置分组 -->
      <div class="space-y-6">
        <!-- 语言设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Globe class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.language') }}</h2>
          </div>
          <div class="max-w-xs">
            <label class="block text-body-medium text-text mb-1.5">
              {{ t('settings.language') }}
            </label>
            <select
              :value="locale"
              @change="changeLocale(($event.target as HTMLSelectElement).value)"
              class="w-full h-9 px-3 text-body bg-surface border border-border-strong rounded-md text-text focus:outline-none focus:ring-2 focus:ring-focus focus:border-primary transition-colors"
            >
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>
        </section>

        <!-- 个人信息 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <User class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">个人信息</h2>
          </div>
          <div class="max-w-md space-y-4">
            <BaseInput :label="t('auth.username')" model-value="" :placeholder="t('auth.username')" readonly />
            <BaseInput :label="t('auth.email')" model-value="" :placeholder="t('auth.email')" readonly />
          </div>
        </section>

        <!-- 通知设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Bell class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">通知设置</h2>
          </div>
          <p class="text-caption text-text-muted">暂无可配置项</p>
        </section>

        <!-- 安全设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Shield class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">安全设置</h2>
          </div>
          <p class="text-caption text-text-muted">暂无可配置项</p>
        </section>
      </div>
    </div>
  </div>
</template>
