import { beforeEach, describe, expect, it, vi } from 'vitest'
import { assetsApi } from '../assets'
import { clearToken, setToken } from '../client'

class FakeXMLHttpRequest {
  static lastInstance: FakeXMLHttpRequest | null = null

  upload: { onprogress?: (event: { lengthComputable: boolean; loaded: number; total: number }) => void } = {}
  onload: (() => void) | null = null
  onerror: (() => void) | null = null
  status = 0
  responseText = ''
  method = ''
  url = ''
  headers: Record<string, string> = {}
  aborted = false

  constructor() {
    FakeXMLHttpRequest.lastInstance = this
  }

  open(method: string, url: string) {
    this.method = method
    this.url = url
  }

  setRequestHeader(key: string, value: string) {
    this.headers[key] = value
  }

  send(_body: FormData) {}

  abort() {
    this.aborted = true
  }
}

describe('assetsApi.uploadWithProgress', () => {
  beforeEach(() => {
    FakeXMLHttpRequest.lastInstance = null
    clearToken()
    vi.stubGlobal('XMLHttpRequest', FakeXMLHttpRequest as unknown as typeof XMLHttpRequest)
  })

  it('通过 XHR 上传并携带 Authorization header', async () => {
    setToken('token_123')
    const file = new File(['image'], 'page.png', { type: 'image/png' })
    const progress = vi.fn()

    const { promise } = assetsApi.uploadWithProgress('p1', file, progress)
    const xhr = FakeXMLHttpRequest.lastInstance!

    xhr.upload.onprogress?.({ lengthComputable: true, loaded: 50, total: 100 })
    xhr.status = 200
    xhr.responseText = JSON.stringify({
      data: {
        asset_id: 'asset_1',
        document_id: 'doc_1',
        page_id: 'page_1',
        sha256: 'a',
        size_bytes: 1,
        mime_type: 'image/png',
        width: 100,
        height: 200,
        asset_reused: false,
      },
      request_id: 'req_1',
    })
    xhr.onload?.()

    await expect(promise).resolves.toMatchObject({
      data: { asset_id: 'asset_1', page_id: 'page_1' },
      request_id: 'req_1',
    })
    expect(progress).toHaveBeenCalledWith(50)
    expect(xhr.method).toBe('POST')
    expect(xhr.url).toBe('/api/v1/projects/p1/assets/upload')
    expect(xhr.headers.Authorization).toBe('Bearer token_123')
  })

  it('失败时抛出统一 ApiClientError', async () => {
    const file = new File(['image'], 'page.png', { type: 'image/png' })

    const { promise } = assetsApi.uploadWithProgress('p1', file, vi.fn())
    const xhr = FakeXMLHttpRequest.lastInstance!

    xhr.status = 403
    xhr.responseText = JSON.stringify({
      error: {
        code: 'FORBIDDEN',
        message: 'Permission denied',
        details: { project_id: 'p1' },
      },
      request_id: 'req_403',
    })
    xhr.onload?.()

    await expect(promise).rejects.toMatchObject({
      status: 403,
      code: 'FORBIDDEN',
      requestId: 'req_403',
      details: { project_id: 'p1' },
    })
  })
})

