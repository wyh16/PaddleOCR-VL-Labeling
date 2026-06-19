import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import BBoxOverlay from '../BBoxOverlay.vue'

const baseProps = {
  obj: {
    id: 'obj_1',
    type: 'question_block',
    label_namespace: 'k12',
    viewportBbox: [10, 20, 110, 120] as [number, number, number, number],
    color: '#5e6ad2',
    status: 'draft',
  },
  selected: true,
  labelName: 'question_block',
  activeTool: 'select' as const,
  panActive: false,
}

describe('BBoxOverlay', () => {
  it('仅在 select 模式下渲染 8 个 resize handles', () => {
    const wrapper = mount(BBoxOverlay, {
      props: baseProps,
    })

    expect(wrapper.findAll('rect')).toHaveLength(10)
  })

  it('非 select 模式下不暴露 resize handles', () => {
    const wrapper = mount(BBoxOverlay, {
      props: {
        ...baseProps,
        activeTool: 'read_order',
      },
    })

    expect(wrapper.findAll('rect')).toHaveLength(2)
  })

  it('临时平移激活时不触发选择和拖拽事件', async () => {
    const wrapper = mount(BBoxOverlay, {
      props: {
        ...baseProps,
        panActive: true,
      },
    })

    const rects = wrapper.findAll('rect')
    await rects[0].trigger('mousedown', { button: 0 })
    await rects[2].trigger('mousedown', { button: 0 })

    expect(wrapper.emitted('select')).toBeUndefined()
    expect(wrapper.emitted('dragStart')).toBeUndefined()
    expect(wrapper.emitted('handleDragStart')).toBeUndefined()
  })
})
