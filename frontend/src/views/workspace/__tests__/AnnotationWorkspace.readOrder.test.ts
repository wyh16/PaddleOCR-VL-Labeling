import { flushPromises, mount } from '@vue/test-utils'
import { computed, defineComponent, nextTick, ref } from 'vue'
import { createI18n } from 'vue-i18n'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SAVE_STATUS_KEY, UPDATE_SAVE_STATUS_KEY, type SaveStatus } from '../workspaceGuards'

const pushMock = vi.fn()
const listByProjectMock = vi.fn()
const listQcMock = vi.fn()
const getPageMock = vi.fn()
const getCapabilitiesMock = vi.fn()
const listPagesMock = vi.fn()
const fetchImageBlobMock = vi.fn()
const getLatestMock = vi.fn()
const saveMock = vi.fn()

const storeObjects = ref([
  {
    id: 'obj-1',
    type: 'question_block',
    label_namespace: 'k12',
    geometry: { bbox_xyxy: [10, 10, 60, 60] as [number, number, number, number] },
    read_order: 2,
    attributes: {},
    source_refs: [],
    status: 'active' as const,
    color: '#5e6ad2',
  },
  {
    id: 'obj-2',
    type: 'answer_area',
    label_namespace: 'k12',
    geometry: { bbox_xyxy: [80, 10, 140, 60] as [number, number, number, number] },
    read_order: 1,
    attributes: {},
    source_refs: [],
    status: 'active' as const,
    color: '#24a148',
  },
])

const selectedId = ref<string | null>('obj-1')
const selectedObject = computed(() => storeObjects.value.find(obj => obj.id === selectedId.value) || null)
const saveStatusCalls: SaveStatus[] = []
let startReadOrderSessionMock = vi.fn()
let setReadOrderMock = vi.fn()
let clearReadOrderMock = vi.fn()

function resetStoreMocks() {
  storeObjects.value = [
    {
      id: 'obj-1',
      type: 'question_block',
      label_namespace: 'k12',
      geometry: { bbox_xyxy: [10, 10, 60, 60] as [number, number, number, number] },
      read_order: 2,
      attributes: {},
      source_refs: [],
      status: 'active',
      color: '#5e6ad2',
    },
    {
      id: 'obj-2',
      type: 'answer_area',
      label_namespace: 'k12',
      geometry: { bbox_xyxy: [80, 10, 140, 60] as [number, number, number, number] },
      read_order: 1,
      attributes: {},
      source_refs: [],
      status: 'active',
      color: '#24a148',
    },
  ]
  selectedId.value = 'obj-1'
  startReadOrderSessionMock = vi.fn(() => false)
  setReadOrderMock = vi.fn((id: string, order: number) => {
    const target = storeObjects.value.find(obj => obj.id === id)
    if (target) target.read_order = order
  })
  clearReadOrderMock = vi.fn(() => true)
  saveStatusCalls.length = 0
}

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { page_id: 'page-1' },
    query: {},
  }),
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('@/api/pages', () => ({
  pagesApi: {
    get: (...args: unknown[]) => getPageMock(...args),
    getCapabilities: (...args: unknown[]) => getCapabilitiesMock(...args),
    list: (...args: unknown[]) => listPagesMock(...args),
    fetchImageBlob: (...args: unknown[]) => fetchImageBlobMock(...args),
  },
}))

vi.mock('@/api/annotations', () => ({
  annotationsApi: {
    getLatest: (...args: unknown[]) => getLatestMock(...args),
    getRevision: vi.fn(),
    save: (...args: unknown[]) => saveMock(...args),
  },
}))

vi.mock('@/api/labels', () => ({
  labelsApi: {
    listByProject: (...args: unknown[]) => listByProjectMock(...args),
  },
}))

vi.mock('@/api/qc', () => ({
  qcApi: {
    listByPage: (...args: unknown[]) => listQcMock(...args),
  },
}))

vi.mock('@/components/annotation/AnnotationCanvas.vue', () => ({
  default: defineComponent({
    name: 'AnnotationCanvasStub',
    template: '<div class="annotation-canvas-stub"></div>',
    setup(_props, { expose }) {
      const store = {
        objects: storeObjects,
        selectedObject,
        selectedId,
        baseRevisionId: ref<string | undefined>(undefined),
        revisionNo: ref(0),
        canUndo: computed(() => false),
        canRedo: computed(() => false),
        setImageBounds: vi.fn(),
        loadFromRevision: vi.fn(),
        select: (id: string | null) => { selectedId.value = id },
        updateObject: vi.fn(),
        deleteObject: vi.fn(),
        deleteSelected: vi.fn(),
        undo: vi.fn(),
        redo: vi.fn(),
        clearReadOrder: (...args: unknown[]) => clearReadOrderMock(...args),
        startReadOrderSession: (...args: unknown[]) => startReadOrderSessionMock(...args),
        endReadOrderSession: vi.fn(),
        setReadOrder: (...args: unknown[]) => setReadOrderMock(...args),
        toDraft: vi.fn(() => ({ page_id: 'page-1', base_revision_id: null, data: { k12_annotations: [] } })),
      }
      const renderer = {
        zoomIn: vi.fn(),
        zoomOut: vi.fn(),
        fitToWidth: vi.fn(),
        fitToContainer: vi.fn(),
        zoomPercent: computed(() => 100),
        scale: ref(1),
        offset: ref({ x: 0, y: 0 }),
        viewport: computed(() => ({ w: 800, h: 600 })),
      }
      expose({
        store,
        renderer,
        redraw: vi.fn(),
      })
      return {}
    },
  }),
}))

import AnnotationWorkspace from '../AnnotationWorkspace.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {
      common: {
        loading: '加载中',
        retry: '重试',
        save: '保存',
        noData: '暂无数据',
        fullscreen: '全屏',
      },
      errors: {
        notFound: '未找到',
        forbidden: '无权限',
        server: '服务器错误',
        conflict: '冲突',
      },
      workspace: {
        prevPage: '上一张',
        nextPage: '下一张',
        pageN: '第 {current}/{total} 页',
        pageList: '页面列表',
        conflictSaveAsNew: '另存为新版本',
        conflictRebase: '重置基线',
        conflictExport: '导出草稿',
        conflictDiscard: '放弃修改',
        conflictRebaseConfirm: '确认',
        conflictDiscardConfirm: '确认',
      },
      annotation: {
        tools: {
          select: '选择',
          bbox: '矩形框',
          read_order: '阅读顺序',
          pan: '平移',
          zoomOut: '缩放-',
          zoomIn: '缩放+',
          fitWidth: '适应宽度',
          fitPage: '适应页面',
          undo: '撤销',
          redo: '重做',
          delete: '删除',
        },
        labels: { title: '标签管理' },
        objects: { count: '对象列表 {count}' },
        qc: {
          count: 'QC问题 {count}',
          empty: '暂无 QC 问题',
          targetObject: '对象 {id}',
          pageLevel: '页面级问题',
          suggestion: '建议',
          severity: { passed: '通过', warning: '警告', failed: '失败' },
        },
        properties: {
          title: '属性编辑',
          label: '标签',
          readOrder: '阅读顺序',
          clearReadOrder: '清空排序',
          coordinates: '坐标',
          id: 'ID',
          readOrderPositiveInteger: '阅读顺序必须是正整数',
          readOrderDuplicate: '阅读顺序不能重复',
        },
        shortcuts: {
          title: '快捷键帮助',
          bboxTool: '矩形框',
          selectTool: '选择',
          readOrderTool: '阅读顺序',
          panCanvas: '平移',
          undo: '撤销',
          redo: '重做',
          deleteSelected: '删除',
          save: '保存',
        },
      },
    },
  },
})

const WrapperHost = defineComponent({
  components: { AnnotationWorkspace },
  setup() {
    const saveStatus = ref<SaveStatus>('saved')
    return {
      saveStatus,
      updateSaveStatus: (status: SaveStatus) => {
        saveStatus.value = status
        saveStatusCalls.push(status)
      },
    }
  },
  provide() {
    return {
      [SAVE_STATUS_KEY]: (this as unknown as { saveStatus: { value: SaveStatus } }).saveStatus,
      [UPDATE_SAVE_STATUS_KEY]: (this as unknown as { updateSaveStatus: (status: SaveStatus) => void }).updateSaveStatus,
    }
  },
  template: '<AnnotationWorkspace />',
})

function mountWorkspace() {
  return mount(WrapperHost, {
    global: {
      plugins: [i18n],
      stubs: {
        BookOpen: true,
        MousePointer2: true,
        SquareDashedMousePointer: true,
        Hand: true,
        ZoomIn: true,
        ZoomOut: true,
        Maximize: true,
        Expand: true,
        Undo2: true,
        Redo2: true,
        Trash2: true,
        Fullscreen: true,
        Save: true,
        Loader2: true,
        ChevronLeft: true,
        ChevronRight: true,
      },
    },
  })
}

describe('AnnotationWorkspace read_order', () => {
  beforeEach(() => {
    resetStoreMocks()
    pushMock.mockReset()
    listByProjectMock.mockReset()
    listQcMock.mockReset()
    getPageMock.mockReset()
    getCapabilitiesMock.mockReset()
    listPagesMock.mockReset()
    fetchImageBlobMock.mockReset()
    getLatestMock.mockReset()
    saveMock.mockReset()

    getPageMock.mockResolvedValue({
      page_id: 'page-1',
      project_id: 1,
      width: 200,
      height: 120,
      filename: 'page-1.png',
    })
    getCapabilitiesMock.mockResolvedValue({
      can_view_project: true,
      can_create_annotation_revision: true,
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
    })
    listByProjectMock.mockResolvedValue({
      items: [
        {
          namespace: 'k12',
          name: 'question_block',
          display_name: '题目',
          display_name_i18n: { 'zh-CN': '题目' },
          default_color: '#5e6ad2',
        },
        {
          namespace: 'k12',
          name: 'answer_area',
          display_name: '答案区域',
          display_name_i18n: { 'zh-CN': '答案区域' },
          default_color: '#24a148',
        },
      ],
    })
    listQcMock.mockResolvedValue({ items: [] })
    listPagesMock.mockResolvedValue({ items: [] })
    fetchImageBlobMock.mockResolvedValue('blob:image')
    getLatestMock.mockResolvedValue({
      id: 'rev-1',
      revision_no: 1,
      page_id: 'page-1',
      data: { k12_annotations: [], relations: [] },
    })
  })

  it('进入 read_order 会保留旧排序且不额外标记 dirty', async () => {
    const wrapper = mountWorkspace()
    await flushPromises()

    const readOrderButton = wrapper.find('button[title="阅读顺序 (R)"]')
    await readOrderButton.trigger('click')
    await nextTick()

    expect(startReadOrderSessionMock).toHaveBeenCalled()
    expect(saveStatusCalls).not.toContain('dirty')
  })

  it('手动输入重复 read_order 时显示错误且不写入 store', async () => {
    const wrapper = mountWorkspace()
    await flushPromises()

    const objectItems = wrapper.findAll('.cursor-pointer')
    await objectItems[0].trigger('click')
    await nextTick()

    const readOrderButton = wrapper.find('button[title="阅读顺序 (R)"]')
    await readOrderButton.trigger('click')
    await nextTick()

    const input = wrapper.find('input[type="number"]')
      ; (input.element as HTMLInputElement).value = '1'
    await input.trigger('change')
    await nextTick()

    expect(setReadOrderMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('阅读顺序不能重复')
  })

  it('手动输入非正整数时显示错误', async () => {
    const wrapper = mountWorkspace()
    await flushPromises()

    const objectItems = wrapper.findAll('.cursor-pointer')
    await objectItems[0].trigger('click')
    await nextTick()

    const readOrderButton = wrapper.find('button[title="阅读顺序 (R)"]')
    await readOrderButton.trigger('click')
    await nextTick()

    const input = wrapper.find('input[type="number"]')
      ; (input.element as HTMLInputElement).value = '0'
    await input.trigger('change')
    await nextTick()

    expect(setReadOrderMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('阅读顺序必须是正整数')
  })
})
