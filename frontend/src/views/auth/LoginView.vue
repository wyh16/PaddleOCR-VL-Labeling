<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  // TODO: 实现登录逻辑
  loading.value = true
  try {
    // await api.login(username.value, password.value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-background rounded-lg shadow-lg p-8">
    <h1 class="text-2xl font-bold text-center mb-6">{{ t('auth.login') }}</h1>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-text mb-1">
          {{ t('auth.username') }}
        </label>
        <input
          v-model="username"
          type="text"
          class="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-accent"
          :placeholder="t('auth.username')"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-text mb-1">
          {{ t('auth.password') }}
        </label>
        <input
          v-model="password"
          type="password"
          class="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-accent"
          :placeholder="t('auth.password')"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-2 px-4 bg-accent text-white rounded-md hover:bg-accent/90 disabled:opacity-50"
      >
        {{ loading ? t('common.loading') : t('auth.login') }}
      </button>
    </form>

    <p class="mt-4 text-center text-sm text-muted">
      {{ t('auth.noAccount') }}
      <router-link to="/auth/register" class="text-accent hover:underline">
        {{ t('auth.register') }}
      </router-link>
    </p>
  </div>
</template>
