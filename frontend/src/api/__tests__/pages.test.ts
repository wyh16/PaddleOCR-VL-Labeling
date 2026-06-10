import { describe, it, expect, vi, beforeEach } from 'vitest'
import { pagesApi } from '../pages'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('pagesApi', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('getCapabilities 透传规范字段布尔映射', async () => {
    const data = {
      can_view_project: true,
      can_create_annotation_revision: false,
      can_submit_revision: false,
      can_review_revision: false,
      can_create_export_job: false,
      can_download_export: false,
      can_manage_project_members: false,
      can_manage_labels: false,
      can_manage_relations: false,
      can_lock_revision: false,
      can_unlock_revision: false,
      can_rollback_revision: false,
      can_upload_assets: false,
      can_import_pages: false,
      can_view_audit_log: false,
      can_manage_system_users: false,
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
    })

    const result = await pagesApi.getCapabilities('123')
    expect(result).toEqual(data)
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/projects/123/me/capabilities', expect.any(Object))
  })
})

