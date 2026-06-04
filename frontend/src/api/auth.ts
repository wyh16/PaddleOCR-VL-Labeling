/**
 * 认证相关 API
 */
import { api } from './client'

export interface User {
  id: string
  username: string
  email: string
  is_active: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  user: User
}

export const authApi = {
  /** 获取当前用户信息 */
  me: () => api.get<User>('/auth/me'),

  /** 登录 */
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/auth/login', data),

  /** 登出 */
  logout: () => api.post<void>('/auth/logout'),
}
