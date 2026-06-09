/**
 * 认证相关 API
 * 后端：POST /auth/login, GET /auth/me
 */
import { api, setToken, clearToken } from './client'

/** 后端 AuthenticatedUser */
export interface User {
  id: string
  username: string
  display_name: string
  is_system_admin: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

/** 后端 LoginResponse */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

function adaptUser(raw: { id: number | string; username: string; display_name: string; is_system_admin?: boolean }): User {
  return {
    id: String(raw.id),
    username: raw.username,
    display_name: raw.display_name,
    is_system_admin: raw.is_system_admin ?? false,
  }
}

export const authApi = {
  /** 获取当前用户信息 */
  me: async () => {
    const raw = await api.get<{ id: number; username: string; display_name: string; is_system_admin: boolean }>('/auth/me')
    return adaptUser(raw)
  },

  /** 登录，成功后自动存储 token */
  login: async (data: LoginRequest) => {
    const res = await api.post<LoginResponse>('/auth/login', data)
    setToken(res.access_token)
    return {
      access_token: res.access_token,
      token_type: res.token_type,
      expires_in: res.expires_in,
      user: adaptUser(res.user),
    }
  },

  /** 登出（清空本地 token） */
  logout: async () => {
    clearToken()
  },
}
