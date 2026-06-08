/**
 * Mock 数据
 * 后端未开发完成时，前端使用 mock 数据独立运行
 * 当 API 请求失败时自动 fallback 到 mock 数据
 */
import type { Project } from './projects'
import type { Page, Capabilities } from './pages'
import type { AnnotationRevision } from './annotations'
import type { QcIssue } from './qc'
import type { User } from './auth'

// ── 认证 ──
export const mockUser: User = {
  id: 'mock-user-001',
  username: '张三',
  email: 'zhangsan@example.com',
  is_active: true,
}

// ── 项目 ──
export const mockProjects: Project[] = [
  {
    id: 'proj-001',
    name: '小学数学试卷项目',
    description: '2024年春季学期三年级数学期末考试试卷识别与结构化解析',
    status: 'active',
    created_at: '2024-05-01T08:00:00Z',
    updated_at: '2024-05-27T10:00:00Z',
  },
  {
    id: 'proj-002',
    name: '初中英语试卷项目',
    description: '初二英语月考试卷 OCR 识别与标注',
    status: 'active',
    created_at: '2024-05-10T08:00:00Z',
    updated_at: '2024-05-25T14:00:00Z',
  },
  {
    id: 'proj-003',
    name: '小学语文试卷项目',
    description: '一年级语文期末试卷结构化解析',
    status: 'active',
    created_at: '2024-05-15T08:00:00Z',
    updated_at: '2024-05-26T09:00:00Z',
  },
  {
    id: 'proj-004',
    name: '高中物理试卷项目',
    description: '高一期末物理试卷识别与标注',
    status: 'completed',
    created_at: '2024-04-01T08:00:00Z',
    updated_at: '2024-05-20T16:00:00Z',
  },
  {
    id: 'proj-005',
    name: '初中数学试卷项目',
    description: '初二数学期中考试试卷 OCR 标注',
    status: 'active',
    created_at: '2024-05-20T08:00:00Z',
    updated_at: '2024-05-27T08:00:00Z',
  },
]

// ── 页面 ──
export const mockPages: Page[] = [
  { page_id: 'page-001', project_id: 'proj-001', filename: '三年级数学期末试卷-第1页', status: 'annotated', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-002', project_id: 'proj-001', filename: '三年级数学期末试卷-第2页', status: 'annotated', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-003', project_id: 'proj-001', filename: '三年级数学期末试卷-第3页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-004', project_id: 'proj-001', filename: '三年级数学期末试卷-第4页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-005', project_id: 'proj-001', filename: '三年级数学期末试卷-第5页', status: 'annotated', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-006', project_id: 'proj-001', filename: '三年级数学期末试卷-第6页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-007', project_id: 'proj-001', filename: '三年级数学期末试卷-第7页', status: 'annotated', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-008', project_id: 'proj-001', filename: '三年级数学期末试卷-第8页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-009', project_id: 'proj-001', filename: '三年级数学期末试卷-第9页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-010', project_id: 'proj-001', filename: '三年级数学期末试卷-第10页', status: 'annotated', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-011', project_id: 'proj-001', filename: '三年级数学期末试卷-第11页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-012', project_id: 'proj-001', filename: '三年级数学期末试卷-第12页', status: 'annotated', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-013', project_id: 'proj-001', filename: '三年级数学期末试卷-第13页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-014', project_id: 'proj-001', filename: '三年级数学期末试卷-第14页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
  { page_id: 'page-015', project_id: 'proj-001', filename: '三年级数学期末试卷-第15页', status: 'pending', width: 2480, height: 3508, created_at: '2024-05-27T10:00:00Z', updated_at: '2024-05-27T10:00:00Z' },
]

// ── 标注 Revision ──
export const mockRevision: AnnotationRevision = {
  id: 'rev-012',
  page_id: 'page-012',
  revision_no: 12,
  base_revision_id: 'rev-011',
  created_at: '2024-05-27T10:15:00Z',
  created_by: 'mock-user-001',
  data: {
    annotations: [
      { id: 'ann-001', type: 'bbox', label: '题目', x: 120, y: 180, w: 460, h: 60, text: '计算 24 × 3 = ____。' },
      { id: 'ann-002', type: 'bbox', label: '答案区域', x: 100, y: 300, w: 500, h: 50, text: '一个长方形的长是 8 厘米，宽是 6 厘米，它的面积是（  ）平方厘米。' },
      { id: 'ann-003', type: 'bbox', label: '选项区域', x: 100, y: 520, w: 420, h: 80, text: 'A. 398   B. 421   C. 305' },
    ],
  },
}

// ── QC 问题 ──
export const mockQcIssues: QcIssue[] = [
  {
    id: 'qc-001',
    page_id: 'page-012',
    annotation_id: 'ann-001',
    severity: 'error',
    code: 'OVERLAP_DETECTED',
    message: '标注对象 ann-001 与 ann-002 存在重叠',
    created_at: '2024-05-27T10:20:00Z',
  },
  {
    id: 'qc-002',
    page_id: 'page-012',
    annotation_id: 'ann-003',
    severity: 'warning',
    code: 'LOW_CONFIDENCE',
    message: 'OCR 置信度低于阈值 (0.75)',
    created_at: '2024-05-27T10:20:00Z',
  },
  {
    id: 'qc-003',
    page_id: 'page-012',
    severity: 'info',
    code: 'MISSING_LABEL',
    message: '页面存在未标注的文本区域',
    created_at: '2024-05-27T10:20:00Z',
  },
]

// ── Capabilities ──
export const mockCapabilities: Capabilities = {
  can_edit: true,
  can_review: true,
  can_export: true,
  can_manage: true,
}

// ── Mock 延迟工具 ──
const MOCK_DELAY = 300

export function mockDelay<T>(data: T): Promise<T> {
  return new Promise(resolve => setTimeout(() => resolve(structuredClone(data)), MOCK_DELAY))
}
