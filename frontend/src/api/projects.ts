/**
 * 项目相关 API
 */
import { api } from './client'

export interface Project {
  id: string
  name: string
  description: string
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: Project[]
  total: number
}

export const projectsApi = {
  /** 获取项目列表 */
  list: (params?: { page?: number; size?: number }) => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.size) query.set('size', String(params.size))
    const qs = query.toString()
    return api.get<ProjectListResponse>(`/projects${qs ? `?${qs}` : ''}`)
  },

  /** 获取项目详情 */
  get: (projectId: string) =>
    api.get<Project>(`/projects/${projectId}`),

  /** 创建项目 */
  create: (data: { name: string; description?: string }) =>
    api.post<Project>('/projects', data),

  /** 更新项目 */
  update: (projectId: string, data: Partial<Project>) =>
    api.patch<Project>(`/projects/${projectId}`, data),

  /** 删除项目 */
  delete: (projectId: string) =>
    api.delete<void>(`/projects/${projectId}`),
}
