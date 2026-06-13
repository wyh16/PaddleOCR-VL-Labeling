import { flushPromises, mount } from '@vue/test-utils'
import { computed, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const {
  clearImageMock,
  loadImageMock,
  renderMock,
  initCanvasMock,
  fitToContainerMock,
} = vi.hoisted(() => ({
  clearImageMock: vi.fn(),
  loadImageMock: vi.fn(),
  renderMock: vi.fn(),
  initCanvasMock: vi.fn(),
  fitToContainerMock: vi.fn(),
}))

vi.mock('@/composables/useAnnotationStore', () => ({
  useAnnotationStore: () => ({
    objects: ref([]),
    selectedId: ref(null),
    select: vi.fn(),
    assignNextReadOrder: vi.fn(),
    deleteSelected: vi.fn(),
    undo: vi.fn(),
    redo: vi.fn(),
    moveObject: vi.fn(),
    resizeObject: vi.fn(),
    savePreDragSnapshot: vi.fn(),
  }),
}))

vi.mock('@/composables/useCanvasRenderer', () => ({
  useCanvasRenderer: () => ({
    clearImage: clearImageMock,
    loadImage: loadImageMock,
    render: renderMock,
    initCanvas: initCanvasMock,
    fitToContainer: fitToContainerMock,
    viewport: computed(() => ({ w: 800, h: 600 })),
    imageToViewport: (x: number, y: number) => ({ x, y }),
    screenToImage: vi.fn(() => ({ x: 0, y: 0 })),
    scale: ref(1),
    offset: ref({ x: 0, y: 0 }),
    imageSize: ref({ x: 0, y: 0 }),
    zoomPercent: computed(() => 100),
    zoomAt: vi.fn(),
    pan: vi.fn(),
    fitToWidth: vi.fn(),
    zoomIn: vi.fn(),
    zoomOut: vi.fn(),
  }),
}))

import AnnotationCanvas from '../AnnotationCanvas.vue'

function createWrapper(imageUrl: string | null) {
  return mount(AnnotationCanvas, {
    props: {
      imageUrl,
      activeTool: 'select',
      activeLabel: null,
      qcOverlays: [],
      activeQcIssueId: null,
      readonly: false,
    },
    global: {
      stubs: {
        BBoxOverlay: true,
      },
    },
  })
}

describe('AnnotationCanvas', () => {
  beforeEach(() => {
    clearImageMock.mockReset()
    loadImageMock.mockReset()
    renderMock.mockReset()
    initCanvasMock.mockReset()
    fitToContainerMock.mockReset()
  })

  it('图片 URL 变为 null 时清空旧图并显示错误占位', async () => {
    loadImageMock.mockResolvedValue({})

    const wrapper = createWrapper('blob:first')
    await flushPromises()

    await wrapper.setProps({ imageUrl: null })
    await flushPromises()

    expect(clearImageMock).toHaveBeenCalled()
    expect(wrapper.text()).toContain('图片加载失败')
  })

  it('图片加载异常时不再保持永久加载态', async () => {
    loadImageMock.mockRejectedValue(new Error('load failed'))

    const wrapper = createWrapper('blob:broken')
    await flushPromises()

    expect(clearImageMock).toHaveBeenCalled()
    expect(wrapper.text()).toContain('图片加载失败')
  })
})
