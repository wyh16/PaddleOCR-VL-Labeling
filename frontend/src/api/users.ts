/**
 * 系统用户管理 API
 * 后端：/api/v1/users
 */
import { api } from './client'

export interface SystemUser {
  id: string
  username: string
  display_name: string
  email: string | null
  status: 'active' | 'disabled' | 'pending'
  is_system_admin: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

interface RawSystemUser {
  id: number
  username: string
  display_name: string
  email: string | null
  status: 'active' | 'disabled' | 'pending'
  is_system_admin: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface SystemUserListResponse {
  items: SystemUser[]
  total: number
}

export interface CreateSystemUserRequest {
  username: string
  display_name: string
  password: string
  email?: string | null
  project_id?: number | null
  project_role_codes?: string[]
  is_system_admin: boolean
}

export interface UpdateSystemUserRequest {
  display_name?: string
  password?: string
  email?: string | null
  project_id?: number | null
  project_role_codes?: string[]
  is_system_admin?: boolean
}

function adaptUser(raw: RawSystemUser): SystemUser {
  return {
    ...raw,
    id: String(raw.id),
  }
}

export const usersApi = {
  list: async (keyword?: string): Promise<SystemUserListResponse> => {
    const query = keyword?.trim() ? `?q=${encodeURIComponent(keyword.trim())}` : ''
    const res = await api.get<{ items: RawSystemUser[]; total: number }>(`/users${query}`)
    return {
      items: res.items.map(adaptUser),
      total: res.total,
    }
  },

  create: async (payload: CreateSystemUserRequest): Promise<SystemUser> => {
    const raw = await api.post<RawSystemUser>('/users', payload)
    return adaptUser(raw)
  },

  update: async (userId: string, payload: UpdateSystemUserRequest): Promise<SystemUser> => {
    const raw = await api.patch<RawSystemUser>(`/users/${userId}`, payload)
    return adaptUser(raw)
  },

  disable: async (userId: string): Promise<SystemUser> => {
    const raw = await api.post<RawSystemUser>(`/users/${userId}/disable`)
    return adaptUser(raw)
  },

  enable: async (userId: string): Promise<SystemUser> => {
    const raw = await api.post<RawSystemUser>(`/users/${userId}/enable`)
    return adaptUser(raw)
  },
}
