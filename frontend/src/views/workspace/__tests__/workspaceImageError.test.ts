import { describe, expect, it } from 'vitest'

import { ApiClientError } from '@/api/client'

import { formatWorkspaceImageError } from '../workspaceImageError'

const messages: Record<string, string> = {
  'errors.network': '网络错误',
  'errors.unauthorized': '未登录',
  'errors.forbidden': '权限不足',
  'errors.notFound': '资源不存在',
  'errors.conflict': '数据冲突',
  'errors.validation': '数据校验失败',
  'errors.server': '服务器错误',
  'errors.requestIdLabel': '请求 ID',
}

const t = (key: string) => messages[key] || key

describe('workspaceImageError', () => {
  it('格式化带 request_id 的图片错误', () => {
    const error = new ApiClientError({
      message: 'Page has no image asset',
      status: 404,
      code: 'IMAGE_NOT_FOUND',
      request_id: 'req_123',
    })

    expect(formatWorkspaceImageError(t, error)).toBe('资源不存在 (请求 ID: req_123)')
  })

  it('非 ApiClientError 回退为服务器错误', () => {
    expect(formatWorkspaceImageError(t, new Error('boom'))).toBe('服务器错误')
  })
})
