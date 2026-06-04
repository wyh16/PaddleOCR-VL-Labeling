<script setup lang="ts">
/**
 * 注册页
 * MVP 默认不开放注册，页面只展示说明和返回登录入口
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseInput from '@/components/base/BaseInput.vue'
import BaseButton from '@/components/base/BaseButton.vue'

const { t } = useI18n()

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const registrationEnabled = false

async function handleRegister() {
  if (!registrationEnabled) return
}
</script>

<template>
  <div class="bg-background rounded-lg shadow-lg p-8">
    <h1 class="text-2xl font-bold text-center mb-6">{{ t('auth.register') }}</h1>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <div
        v-if="!registrationEnabled"
        class="p-3 bg-warning/10 text-warning text-sm rounded-md"
      >
        <p class="font-medium">{{ t('auth.registerUnavailableTitle') }}</p>
        <p class="mt-1">{{ t('auth.registerUnavailableDescription') }}</p>
      </div>

      <BaseInput
        v-model="username"
        :label="t('auth.username')"
        :placeholder="t('auth.username')"
        :disabled="loading || !registrationEnabled"
      />

      <BaseInput
        v-model="email"
        type="email"
        :label="t('auth.email')"
        :placeholder="t('auth.email')"
        :disabled="loading || !registrationEnabled"
      />

      <BaseInput
        v-model="password"
        type="password"
        :label="t('auth.password')"
        :placeholder="t('auth.password')"
        :disabled="loading || !registrationEnabled"
      />

      <BaseButton
        type="submit"
        variant="primary"
        :loading="loading"
        :disabled="!registrationEnabled || !username || !email || !password"
        class="w-full"
      >
        {{ t('auth.register') }}
      </BaseButton>
    </form>

    <p class="mt-4 text-center text-sm text-muted">
      {{ t('auth.hasAccount') }}
      <router-link :to="{ name: 'auth.login' }" class="text-accent hover:underline">
        {{ t('auth.login') }}
      </router-link>
    </p>
  </div>
</template>
