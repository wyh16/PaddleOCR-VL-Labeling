/**
 * Mock 数据
 * 后端未开发完成时，前端使用 mock 数据独立运行
 * 当 API 请求失败时自动 fallback 到 mock 数据
 */
import type { Page, Capabilities } from './pages'
import type { AnnotationRevision } from './annotations'
import type { QcIssue } from './qc'
import type { User } from './auth'

// ── 认证 ──
export const mockUser: User = {
  id: 'mock-user-001',
  username: 'admin',
  display_name: 'Admin',
  is_system_admin: true,
}

// ── 页面 ──
export const mockPages: Page[] = Array.from({ length: 15 }, (_, i) => ({
  page_id: `page-${String(i + 1).padStart(3, '0')}`,
  project_id: 'proj-001',
  filename: `三年级数学期末试卷-第${i + 1}页.png`,
  status: i < 10 ? 'annotated' as const : 'pending' as const,
  width: 2480,
  height: 3508,
  created_at: new Date(2024, 2, 1 + i).toISOString(),
  updated_at: new Date(2024, 4, 1 + i).toISOString(),
}))

// ── 标注 Revision ──
export const mockRevision: AnnotationRevision = {
  id: 'rev-012',
  page_id: 'page-012',
  revision_no: 12,
  base_revision_id: 'rev-011',
  created_at: '2024-05-27T10:23:45Z',
  created_by: 'mock-user-001',
  data: {
    objects: [
      {
        id: 'obj-001',
        label: 'question_block',
        geometry: { bbox_xyxy: [120, 180, 580, 320] },
        read_order: 1,
        attributes: {},
      },
      {
        id: 'obj-002',
        label: 'answer_area',
        geometry: { bbox_xyxy: [120, 340, 580, 420] },
        read_order: 2,
        attributes: {},
      },
      {
        id: 'obj-003',
        label: 'option_block',
        geometry: { bbox_xyxy: [120, 440, 520, 560] },
        read_order: 3,
        attributes: {},
      },
    ],
  },
}

// ── QC 问题 ──
export const mockQcIssues: QcIssue[] = [
  {
    id: 'qc-001',
    page_id: 'page-012',
    annotation_id: 'obj-001',
    severity: 'error',
    code: 'OVERLAP',
    message: '标注框与其他对象重叠',
    created_at: '2024-05-27T10:24:00Z',
  },
  {
    id: 'qc-002',
    page_id: 'page-012',
    annotation_id: 'obj-002',
    severity: 'warning',
    code: 'LOW_CONFIDENCE',
    message: 'OCR 置信度低于阈值',
    created_at: '2024-05-27T10:24:01Z',
  },
  {
    id: 'qc-003',
    page_id: 'page-012',
    severity: 'info',
    code: 'MISSING_LABEL',
    message: '存在未标注区域',
    created_at: '2024-05-27T10:24:02Z',
  },
]

// ── Capabilities ──
export const mockCapabilities: Capabilities = {
  can_edit: true,
  can_review: true,
  can_export: true,
  can_manage: true,
}

// ── 延迟工具 ──
export function mockDelay<T>(data: T, ms = 300): Promise<T> {
  return new Promise(resolve => setTimeout(() => resolve(structuredClone(data)), ms))
}
