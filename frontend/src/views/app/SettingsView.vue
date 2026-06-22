<script setup lang="ts">
/**
 * 系统设置页
 */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Globe, User, Bell, Shield } from 'lucide-vue-next'
import { ApiClientError } from '@/api/client'
import { BaseButton, BaseInput } from '@/components/base'
import { useAuth } from '@/composables/useAuth'

const { t, locale } = useI18n()
const { user, changePassword } = useAuth()

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const savingPassword = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
]

const currentUserDisplayName = computed(() => user.value?.display_name || '')
const currentUsername = computed(() => user.value?.username || '')

function changeLocale(lang: string) {
  locale.value = lang
  localStorage.setItem('k12.locale', lang)
}

function formatPasswordError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (typeof error.message === 'string' && error.message.startsWith('errors.')) {
      return t(error.message)
    }
    if (error.status === 0) return t('errors.network')
    return error.message || t('errors.server')
  }
  return t('errors.unknown')
}

async function handlePasswordSubmit() {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (!currentPassword.value.trim() || !newPassword.value.trim() || !confirmPassword.value.trim()) {
    passwordError.value = t('settings.password.messages.required')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = t('settings.password.messages.mismatch')
    return
  }

  savingPassword.value = true
  try {
    await changePassword(currentPassword.value, newPassword.value)
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    passwordSuccess.value = t('settings.password.messages.success')
  } catch (error) {
    passwordError.value = formatPasswordError(error)
  } finally {
    savingPassword.value = false
  }
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
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('settings.language') }}</span>
              <select :value="locale"
                class="h-9 w-full rounded-md border border-border bg-surface px-3 text-body text-text outline-none transition-colors focus:border-primary"
                @change="changeLocale(($event.target as HTMLSelectElement).value)">
                <option v-for="option in languageOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>
        </section>

        <!-- 个人信息 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <User class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.personalInfo') }}</h2>
          </div>
          <div class="max-w-md space-y-4">
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('auth.username') }}</span>
              <BaseInput :model-value="currentUsername" :placeholder="t('auth.username')" readonly disabled />
            </label>
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('users.fields.displayName') }}</span>
              <BaseInput :model-value="currentUserDisplayName" :placeholder="t('users.fields.displayName')" readonly
                disabled />
            </label>
          </div>
        </section>

        <!-- 通知设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Bell class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.notifications') }}</h2>
          </div>
          <p class="text-caption text-text-muted">{{ t('settings.noConfigItems') }}</p>
        </section>

        <!-- 安全设置 -->
        <section class="bg-surface rounded-lg border border-border p-5">
          <div class="flex items-center gap-2.5 mb-4">
            <Shield class="w-4 h-4 text-primary" />
            <h2 class="text-subheading text-text">{{ t('settings.security') }}</h2>
          </div>
          <div class="max-w-md space-y-4">
            <div class="rounded-md border border-border bg-surface-muted px-3 py-2 text-caption text-text-secondary">
              {{ t('settings.password.description') }}
            </div>
            <div v-if="passwordError"
              class="rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-caption text-danger">
              {{ passwordError }}
            </div>
            <div v-if="passwordSuccess"
              class="rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-caption text-primary">
              {{ passwordSuccess }}
            </div>
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('settings.password.currentPassword')
                }}</span>
              <BaseInput v-model="currentPassword" type="password"
                :placeholder="t('settings.password.currentPasswordPlaceholder')" :disabled="savingPassword" />
            </label>
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('settings.password.newPassword') }}</span>
              <BaseInput v-model="newPassword" type="password"
                :placeholder="t('settings.password.newPasswordPlaceholder')" :disabled="savingPassword" />
            </label>
            <label class="block">
              <span class="mb-1 block text-caption text-text-secondary">{{ t('settings.password.confirmPassword')
                }}</span>
              <BaseInput v-model="confirmPassword" type="password"
                :placeholder="t('settings.password.confirmPasswordPlaceholder')" :disabled="savingPassword" />
            </label>
            <BaseButton type="button" block :loading="savingPassword" :disabled="savingPassword"
              @click="handlePasswordSubmit">
              {{ t('settings.password.submit') }}
            </BaseButton>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
