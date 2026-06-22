<script setup lang="ts">
/**
 * 系统用户管理页
 * 只面向系统管理员，负责创建、编辑、启用和禁用账号。
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ApiClientError } from '@/api/client'
import {
  usersApi,
  type CreateSystemUserRequest,
  type SystemUser,
  type UpdateSystemUserRequest,
} from '@/api'
import { useAuth } from '@/composables/useAuth'
import { BaseButton, BaseInput, BaseStatusBadge } from '@/components/base'
import { ShieldCheck, UserPlus, Search, RefreshCw } from 'lucide-vue-next'

const { t } = useI18n()
const { user: currentUser } = useAuth()

const loading = ref(false)
const submitting = ref(false)
const actionUserId = ref<string | null>(null)
const editingUserId = ref<string | null>(null)
const allUsers = ref<SystemUser[]>([])
const keyword = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const filteredUsers = computed(() => {
  const trimmedKeyword = keyword.value.trim().toLowerCase()
  if (!trimmedKeyword) return allUsers.value
  return allUsers.value.filter(user =>
    user.username.toLowerCase().includes(trimmedKeyword) ||
    user.display_name.toLowerCase().includes(trimmedKeyword) ||
    (user.email && user.email.toLowerCase().includes(trimmedKeyword))
  )
})

const form = ref({
  username: '',
  display_name: '',
  email: '',
  password: '',
  role: 'user',
})

const isEditMode = computed(() => editingUserId.value !== null)
const editingTargetUser = computed(
  () => allUsers.value.find(user => user.id === editingUserId.value) ?? null
)
const pageDescription = computed(() => t('users.description'))
const formTitle = computed(() => (isEditMode.value ? t('users.editTitle') : t('users.createTitle')))
const submitButtonText = computed(() =>
  isEditMode.value ? t('users.actions.updateUser') : t('users.actions.createUser')
)
const passwordHint = computed(() =>
  isEditMode.value ? t('users.passwordHintEdit') : t('users.passwordHintCreate')
)
const roleHint = computed(() => {
  if (editingTargetUser.value && isCurrentUser(editingTargetUser.value)) {
    return t('users.selfRoleHint')
  }
  if (editingTargetUser.value && isLastActiveSystemAdmin(editingTargetUser.value)) {
    return t('users.lastAdminHint')
  }
  return t('users.roleHint')
})

function isCurrentUser(targetUser: SystemUser) {
  return targetUser.id === currentUser.value?.id
}

const lastActiveAdminIds = computed(() => {
  const activeAdmins = allUsers.value.filter(u => u.is_system_admin && u.status === 'active')
  if (activeAdmins.length !== 1) return new Set<string>()
  return new Set<string>([activeAdmins[0].id])
})

function isLastActiveSystemAdmin(targetUser: SystemUser) {
  return lastActiveAdminIds.value.has(targetUser.id)
}

function getLocalizedError(error: unknown, fallbackKey: string): string {
  if (error instanceof ApiClientError) {
    const requestId = error.requestId ? ` ${t('errors.requestIdLabel')}: ${error.requestId}` : ''
    return `${t(error.message || fallbackKey)}${requestId}`
  }
  return t(fallbackKey)
}

async function loadUsers() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await usersApi.list()
    allUsers.value = response.items
  } catch (error) {
    allUsers.value = []
    errorMessage.value = getLocalizedError(error, 'users.messages.loadFailed')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  editingUserId.value = null
  form.value = {
    username: '',
    display_name: '',
    email: '',
    password: '',
    role: 'user',
  }
}

function startEdit(user: SystemUser) {
  editingUserId.value = user.id
  form.value = {
    username: user.username,
    display_name: user.display_name,
    email: user.email ?? '',
    password: '',
    role: user.is_system_admin ? 'system_admin' : 'user',
  }
  errorMessage.value = ''
  successMessage.value = ''
}

function getRoleText(user: SystemUser) {
  return user.is_system_admin ? t('users.roles.systemAdmin') : t('users.roles.user')
}

function getStatusText(status: SystemUser['status']) {
  const key = `users.status.${status}`
  const localized = t(key)
  return localized === key ? status : localized
}

function getStatusVariant(status: SystemUser['status']) {
  if (status === 'active') return 'saved'
  if (status === 'disabled') return 'failed'
  return 'info'
}

function formatDateTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value.replace('T', ' ').replace(/\.\d+$/, '')
  }
  const pad2 = (input: number) => String(input).padStart(2, '0')
  const year = date.getFullYear()
  const month = pad2(date.getMonth() + 1)
  const day = pad2(date.getDate())
  const hour = pad2(date.getHours())
  const minute = pad2(date.getMinutes())
  const second = pad2(date.getSeconds())
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

function formatLastLoginAt(value: SystemUser['last_login_at']) {
  if (!value) return t('users.neverLoggedIn')
  return formatDateTime(value)
}

async function submitForm() {
  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    if (isEditMode.value && editingUserId.value) {
      const targetUser = editingTargetUser.value
      const nextIsSystemAdmin = form.value.role === 'system_admin'
      if (targetUser && isCurrentUser(targetUser) && !nextIsSystemAdmin) {
        errorMessage.value = t('users.messages.selfDemotionForbidden')
        return
      }
      if (targetUser && isLastActiveSystemAdmin(targetUser) && !nextIsSystemAdmin) {
        errorMessage.value = t('users.messages.lastAdminProtected')
        return
      }

      const payload: UpdateSystemUserRequest = {
        display_name: form.value.display_name.trim(),
        email: form.value.email.trim() || null,
        is_system_admin: nextIsSystemAdmin,
      }
      if (form.value.password.trim()) {
        payload.temporary_password = form.value.password.trim()
      }
      await usersApi.update(editingUserId.value, payload)
      successMessage.value = t('users.messages.updateSuccess')
    } else {
      const payload: CreateSystemUserRequest = {
        username: form.value.username.trim(),
        display_name: form.value.display_name.trim(),
        email: form.value.email.trim() || null,
        temporary_password: form.value.password.trim(),
        is_system_admin: form.value.role === 'system_admin',
      }
      await usersApi.create(payload)
      successMessage.value = t('users.messages.createSuccess')
    }
    resetForm()
    await loadUsers()
  } catch (error) {
    errorMessage.value = getLocalizedError(
      error,
      isEditMode.value ? 'users.messages.updateFailed' : 'users.messages.createFailed'
    )
  } finally {
    submitting.value = false
  }
}

async function toggleUserStatus(user: SystemUser) {
  actionUserId.value = user.id
  errorMessage.value = ''
  successMessage.value = ''
  try {
    if (user.status === 'disabled') {
      await usersApi.enable(user.id)
      successMessage.value = t('users.messages.enableSuccess')
    } else {
      if (isCurrentUser(user)) {
        errorMessage.value = t('users.messages.selfDisableForbidden')
        return
      }
      if (isLastActiveSystemAdmin(user)) {
        errorMessage.value = t('users.messages.lastAdminProtected')
        return
      }
      await usersApi.disable(user.id)
      successMessage.value = t('users.messages.disableSuccess')
    }
    await loadUsers()
  } catch (error) {
    errorMessage.value = getLocalizedError(error, 'users.messages.actionFailed')
  } finally {
    actionUserId.value = null
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="flex-1 overflow-auto">
    <div class="mx-auto max-w-7xl p-6">
      <div class="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 class="text-title text-text">{{ t('nav.users') }}</h1>
          <p class="mt-2 text-body text-text-secondary">{{ pageDescription }}</p>
        </div>
        <div class="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-caption text-primary">
          <div class="flex items-center gap-2">
            <ShieldCheck class="h-4 w-4 shrink-0" />
            <span>{{ t('users.adminHint') }}</span>
          </div>
        </div>
      </div>

      <div class="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
        <section class="rounded-lg border border-border bg-surface p-5">
          <div class="mb-4 flex items-center gap-2">
            <UserPlus class="h-4 w-4 text-primary" />
            <h2 class="text-subheading text-text">
              {{ formTitle }}
            </h2>
          </div>

          <form class="space-y-4" @submit.prevent="submitForm">
            <div>
              <label class="mb-1 block text-caption font-medium text-text">{{ t('users.fields.username') }}</label>
              <BaseInput v-model="form.username" :placeholder="t('users.placeholders.username')"
                :disabled="isEditMode" />
            </div>

            <div>
              <label class="mb-1 block text-caption font-medium text-text">{{ t('users.fields.displayName') }}</label>
              <BaseInput v-model="form.display_name" :placeholder="t('users.placeholders.displayName')" />
            </div>

            <div>
              <label class="mb-1 block text-caption font-medium text-text">{{ t('users.fields.email') }}</label>
              <BaseInput v-model="form.email" type="email" :placeholder="t('users.placeholders.email')" />
            </div>

            <div>
              <label class="mb-1 block text-caption font-medium text-text">{{ t('users.fields.password') }}</label>
              <BaseInput v-model="form.password" type="password"
                :placeholder="isEditMode ? t('users.placeholders.passwordOptional') : t('users.placeholders.password')" />
              <p class="mt-1 text-micro text-text-muted">{{ passwordHint }}</p>
            </div>

            <div>
              <label class="mb-1 block text-caption font-medium text-text">{{ t('users.fields.role') }}</label>
              <select v-model="form.role"
                class="h-9 w-full rounded-md border border-border bg-surface px-3 text-caption text-text focus:outline-none focus:ring-2 focus:ring-focus">
                <option value="user">{{ t('users.roles.user') }}</option>
                <option value="system_admin">{{ t('users.roles.systemAdmin') }}</option>
              </select>
              <p class="mt-1 text-micro text-text-muted">{{ roleHint }}</p>
            </div>

            <div class="flex gap-3 pt-2">
              <BaseButton type="submit" :loading="submitting" :left-icon="UserPlus">
                {{ submitButtonText }}
              </BaseButton>
              <BaseButton type="button" variant="secondary" @click="resetForm">
                {{ t('users.actions.resetForm') }}
              </BaseButton>
            </div>
          </form>

          <div v-if="errorMessage"
            class="mt-4 rounded-lg border border-danger/20 bg-danger-bg px-4 py-3 text-caption text-danger">
            {{ errorMessage }}
          </div>
          <div v-if="successMessage"
            class="mt-4 rounded-lg border border-success/20 bg-success/10 px-4 py-3 text-caption text-success">
            {{ successMessage }}
          </div>
        </section>

        <section class="rounded-lg border border-border bg-surface p-5">
          <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="text-subheading text-text">{{ t('users.listTitle') }}</h2>
              <p class="mt-1 text-caption text-text-secondary">
                {{ t('users.listSummary', { total: allUsers.length }) }}
              </p>
            </div>
            <div class="flex w-full items-center gap-3 md:w-auto">
              <div class="relative min-w-0 flex-1 md:w-72">
                <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <BaseInput v-model="keyword" class="pl-9" :placeholder="t('users.searchPlaceholder')" />
              </div>
              <BaseButton type="button" variant="secondary" size="sm" :left-icon="RefreshCw" @click="loadUsers">
                {{ t('common.retry') }}
              </BaseButton>
            </div>
          </div>

          <div v-if="loading"
            class="rounded-lg border border-dashed border-border px-6 py-12 text-center text-text-muted">
            {{ t('common.loading') }}
          </div>

          <div v-else-if="filteredUsers.length === 0"
            class="rounded-lg border border-dashed border-border px-6 py-12 text-center text-text-muted">
            {{ t('users.empty') }}
          </div>

          <div v-else class="overflow-hidden rounded-lg border border-border">
            <div
              class="grid grid-cols-[1.2fr_1.2fr_0.9fr_0.9fr_220px] bg-surface-alt px-4 py-3 text-micro font-medium uppercase tracking-wide text-text-muted">
              <span>{{ t('users.fields.username') }}</span>
              <span>{{ t('users.fields.displayName') }}</span>
              <span>{{ t('users.fields.role') }}</span>
              <span>{{ t('users.fields.status') }}</span>
              <span>{{ t('users.fields.actions') }}</span>
            </div>

            <div v-for="user in filteredUsers" :key="user.id"
              class="grid grid-cols-[1.2fr_1.2fr_0.9fr_0.9fr_220px] items-center gap-3 border-t border-border px-4 py-4 text-caption">
              <div class="min-w-0">
                <div class="truncate font-medium text-text">{{ user.username }}</div>
                <div class="truncate text-text-muted">{{ user.email || t('users.noEmail') }}</div>
              </div>

              <div class="min-w-0">
                <div class="truncate text-text">{{ user.display_name }}</div>
                <div class="truncate text-text-muted">
                  {{ formatLastLoginAt(user.last_login_at) }}
                </div>
              </div>

              <div>
                <span class="inline-flex rounded-sm bg-primary/10 px-2 py-1 text-micro font-medium text-primary">
                  {{ getRoleText(user) }}
                </span>
              </div>

              <div>
                <BaseStatusBadge :status="getStatusVariant(user.status)" :label="getStatusText(user.status)" />
              </div>

              <div class="flex items-center gap-2">
                <BaseButton type="button" variant="secondary" size="sm" @click="startEdit(user)">
                  {{ t('users.actions.editUser') }}
                </BaseButton>
                <BaseButton v-if="user.status === 'disabled'" type="button" size="sm"
                  :loading="actionUserId === user.id" @click="toggleUserStatus(user)">
                  {{ t('users.actions.enableUser') }}
                </BaseButton>
                <BaseButton v-else type="button" variant="danger" size="sm" :loading="actionUserId === user.id"
                  :disabled="isCurrentUser(user) || isLastActiveSystemAdmin(user)" @click="toggleUserStatus(user)">
                  {{ t('users.actions.disableUser') }}
                </BaseButton>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
