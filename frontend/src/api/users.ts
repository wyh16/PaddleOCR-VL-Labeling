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
  created_at: string | null
  updated_at: string | null
}

interface RawSystemUser {
  id: number
  username: string
  display_name: string
  email: string | null
  status: 'active' | 'disabled' | 'pending'
  is_system_admin: boolean
  last_login_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface SystemUserListResponse {
  items: SystemUser[]
  total: number
}

export interface CreateSystemUserRequest {
  username: string
  display_name: string
  temporary_password: string
  email?: string | null
  is_system_admin: boolean
}

export interface UpdateSystemUserRequest {
  display_name?: string
  temporary_password?: string
  email?: string | null
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
    const res = await api.get<{ data: RawSystemUser[]; request_id: string }>(`/users${query}`)
    return {
      items: res.data.map(adaptUser),
      total: res.data.length,
    }
  },

  create: async (payload: CreateSystemUserRequest): Promise<SystemUser> => {
    const res = await api.post<{ data: RawSystemUser; request_id: string }>('/users', payload)
    return adaptUser(res.data)
  },

  update: async (userId: string, payload: UpdateSystemUserRequest): Promise<SystemUser> => {
    const res = await api.patch<{ data: RawSystemUser; request_id: string }>(`/users/${userId}`, payload)
    return adaptUser(res.data)
  },

  disable: async (userId: string): Promise<SystemUser> => {
    const res = await api.post<{ data: RawSystemUser; request_id: string }>(`/users/${userId}/disable`)
    return adaptUser(res.data)
  },

  enable: async (userId: string): Promise<SystemUser> => {
    const res = await api.post<{ data: RawSystemUser; request_id: string }>(`/users/${userId}/enable`)
    return adaptUser(res.data)
  },
}
