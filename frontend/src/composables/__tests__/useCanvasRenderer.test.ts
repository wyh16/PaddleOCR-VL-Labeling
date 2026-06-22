import { describe, expect, it } from 'vitest'

import { useCanvasRenderer } from '../useCanvasRenderer'

describe('useCanvasRenderer', () => {
  it('大图平移时会限制在视口边界内', () => {
    const renderer = useCanvasRenderer()
    renderer.imageSize.value = { x: 1600, y: 1200 }
    renderer.scale.value = 1
    renderer.offset.value = { x: 0, y: 0 }

    renderer.pan(300, 200)
    expect(renderer.offset.value).toEqual({ x: 0, y: 0 })

    renderer.pan(-1200, -900)
    expect(renderer.offset.value).toEqual({ x: -800, y: -600 })
  })

  it('小图平移时对应轴保持自动居中', () => {
    const renderer = useCanvasRenderer()
    renderer.imageSize.value = { x: 400, y: 200 }
    renderer.scale.value = 1
    renderer.offset.value = { x: 0, y: 0 }

    renderer.pan(120, -80)
    expect(renderer.offset.value).toEqual({ x: 200, y: 200 })
  })

  it('缩小时遵守基于 fitScale 的动态最小缩放并自动居中', () => {
    const renderer = useCanvasRenderer()
    renderer.imageSize.value = { x: 1000, y: 500 }

    renderer.fitToContainer()
    expect(renderer.fitScale.value).toBeCloseTo(0.76)
    expect(renderer.minScale.value).toBeCloseTo(0.38)

    renderer.zoomAt(-0.9, 400, 300)
    expect(renderer.scale.value).toBeCloseTo(0.38)
    expect(renderer.offset.value.x).toBeCloseTo(210)
    expect(renderer.offset.value.y).toBeCloseTo(205)
  })

  it('手动设置视图后也能重新约束回可见范围', () => {
    const renderer = useCanvasRenderer()
    renderer.imageSize.value = { x: 400, y: 200 }
    renderer.scale.value = 0.5
    renderer.offset.value = { x: -100, y: 20 }

    renderer.constrainViewport()
    expect(renderer.offset.value).toEqual({ x: 300, y: 250 })
  })
})
