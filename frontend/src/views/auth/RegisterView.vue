<script setup lang="ts">
/**
 * 注册页
 * 使用基础组件，统一表单样式
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
const error = ref('')

async function handleRegister() {
  if (!username.value || !email.value || !password.value) return

  loading.value = true
  error.value = ''

  try {
    // TODO: 接入注册 API
    // await authApi.register({ username: username.value, email: email.value, password: password.value })
    // router.replace({ name: 'auth.login' })
  } catch (e) {
    error.value = t('errors.unknown')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-background rounded-lg shadow-lg p-8">
    <h1 class="text-2xl font-bold text-center mb-6">{{ t('auth.register') }}</h1>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <div v-if="error" class="p-3 bg-danger/10 text-danger text-sm rounded-md">
        {{ error }}
      </div>

      <BaseInput
        v-model="username"
        :label="t('auth.username')"
        :placeholder="t('auth.username')"
        :disabled="loading"
      />

      <BaseInput
        v-model="email"
        type="email"
        :label="t('auth.email')"
        :placeholder="t('auth.email')"
        :disabled="loading"
      />

      <BaseInput
        v-model="password"
        type="password"
        :label="t('auth.password')"
        :placeholder="t('auth.password')"
        :disabled="loading"
      />

      <BaseButton
        type="submit"
        variant="primary"
        :loading="loading"
        :disabled="!username || !email || !password"
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
