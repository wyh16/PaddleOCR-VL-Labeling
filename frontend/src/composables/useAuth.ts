/**
 * 认证状态 composable
 */
import { ref, readonly } from 'vue'
import { authApi, type User } from '@/api/auth'

const user = ref<User | null>(null)
const loading = ref(false)

export function useAuth() {
  async function fetchUser() {
    loading.value = true
    try {
      user.value = await authApi.me()
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const response = await authApi.login({ username, password })
      user.value = response.user
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      user.value = null
    }
  }

  return {
    user: readonly(user),
    loading: readonly(loading),
    fetchUser,
    login,
    logout,
  }
}
