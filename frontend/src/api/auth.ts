/**
 * 认证相关 API
 */
import { api, mockFallback } from './client'
import { mockUser, mockDelay } from './mock'

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
  me: () => mockFallback(
    () => api.get<User>('/auth/me'),
    () => mockDelay(mockUser),
  ),

  /** 登录 */
  login: (data: LoginRequest) => mockFallback(
    () => api.post<LoginResponse>('/auth/login', data),
    () => mockDelay({ user: { ...mockUser, username: data.username || mockUser.username } }),
  ),

  /** 登出 */
  logout: () => mockFallback(
    () => api.post<void>('/auth/logout'),
    () => mockDelay(undefined as void),
  ),
}
