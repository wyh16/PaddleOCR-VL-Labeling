<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

function changeLocale(lang: string) {
  locale.value = lang
  localStorage.setItem('k12.locale', lang)
}
</script>

<template>
  <div class="p-6">
    <h2 class="text-2xl font-bold text-text mb-6">设置</h2>

    <div class="max-w-md space-y-6">
      <!-- 语言设置 -->
      <div>
        <label class="block text-sm font-medium text-text mb-2">语言</label>
        <select
          :value="locale"
          @change="changeLocale(($event.target as HTMLSelectElement).value)"
          class="w-full px-3 py-2 border border-border rounded-md bg-background"
        >
          <option value="zh-CN">简体中文</option>
          <option value="en-US">English</option>
        </select>
      </div>

      <!-- TODO: 其他设置项 -->
    </div>
  </div>
</template>
