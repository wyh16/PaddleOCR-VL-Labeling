import { describe, expect, it } from 'vitest'

import { useAnnotationStore } from '../useAnnotationStore'

describe('useAnnotationStore', () => {
  it('从后端 k12_annotations 加载 canonical revision', () => {
    const store = useAnnotationStore()

    store.loadFromRevision({
      id: 'rev_public_001',
      page_id: 'page_public_001',
      revision_no: 3,
      status: 'draft',
      qc_status: 'pending',
      data: {
        schema_version: 'k12_annotation_v0.1',
        page_id: 'page_public_001',
        k12_annotations: [
          {
            id: 'ann_question_001',
            label_name: 'question_block',
            label_namespace: 'k12',
            geometry: {
              bbox_xyxy: [10, 20, 110, 120],
              quad: [[10, 20], [110, 20], [110, 120], [10, 120]],
              polygon: [[10, 20], [110, 20], [110, 120], [10, 120]],
              geometry_source: 'manual',
            },
            read_order: 0,
            attributes: { question_number: '1' },
            source_refs: [{ type: 'human' }],
            status: 'draft',
          },
        ],
        relations: [],
        history: [{ revision_id: 'rev_public_001', revision_no: 3 }],
      },
    })

    expect(store.baseRevisionId.value).toBe('rev_public_001')
    expect(store.revisionNo.value).toBe(3)
    expect(store.objects.value).toEqual([
      {
        id: 'ann_question_001',
        type: 'question_block',
        label_namespace: 'k12',
        geometry: {
          bbox_xyxy: [10, 20, 110, 120],
          quad: [[10, 20], [110, 20], [110, 120], [10, 120]],
          polygon: [[10, 20], [110, 20], [110, 120], [10, 120]],
          geometry_source: 'manual',
        },
        read_order: 1,
        attributes: { question_number: '1' },
        source_refs: [{ type: 'human' }],
        status: 'draft',
        color: '#5e6ad2',
      },
    ])
  })

  it('保存时输出 canonical annotation_json，而不是私有 objects', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 300)

    const created = store.addObject([-10, 20, 210, 120], {
      name: 'question_block',
      namespace: 'k12',
    })
    const draft = store.toDraft('page_public_001')
    const annotationJson = draft.data as {
      page_id: string
      schema_version: string
      k12_annotations: Array<Record<string, unknown>>
      relations: unknown[]
    }

    expect(draft.base_revision_id).toBeNull()
    expect(annotationJson.schema_version).toBe('k12_annotation_v0.1')
    expect(annotationJson.page_id).toBe('page_public_001')
    expect(annotationJson.relations).toEqual([])
    expect(annotationJson.k12_annotations).toEqual([
      {
        id: created.id,
        type: 'question_block',
        label_namespace: 'k12',
        geometry: {
          bbox_xyxy: [0, 20, 200, 120],
          quad: [[0, 20], [200, 20], [200, 120], [0, 120]],
          polygon: [[0, 20], [200, 20], [200, 120], [0, 120]],
          geometry_source: 'manual',
        },
        read_order: undefined,
        attributes: {},
        source_refs: [],
        status: 'draft',
      },
    ])
    expect('objects' in annotationJson).toBe(false)
  })

  it('moveObject 和 resizeObject 会 clamp 到图片边界', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 120)

    const created = store.addObject([10, 20, 60, 80], {
      name: 'question_block',
      namespace: 'k12',
    })

    store.moveObject(created.id, 500, 500)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([150, 60, 200, 120])

    store.resizeObject(created.id, 3, 280, 180)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([150, 60, 200, 120])

    store.resizeObject(created.id, 7, -40, -10)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([0, 0, 200, 120])
  })

  it('read_order 完整 round trip：加载（后端 0→前端 1）、点击排序、保存（前端 1→后端 0）', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 200)

    const first = store.addObject([10, 10, 100, 100], { name: 'question_block', namespace: 'k12' })
    const second = store.addObject([110, 110, 200, 200], { name: 'question_block', namespace: 'k12' })

    // 模拟从后端加载已有 read_order 的 revision
    store.loadFromRevision({
      id: 'rev_load_001',
      page_id: 'page_roundtrip',
      revision_no: 1,
      status: 'draft',
      qc_status: 'pending',
      data: {
        schema_version: 'k12_annotation_v0.1',
        page_id: 'page_roundtrip',
        k12_annotations: [
          { ...first, read_order: 0 },
          { ...second, read_order: 1 },
        ],
        relations: [],
      },
    })

    expect(store.baseRevisionId.value).toBe('rev_load_001')
    expect(store.objects.value[0].read_order).toBe(1)
    expect(store.objects.value[1].read_order).toBe(2)

    // 模拟 read_order 模式点击排序
    store.startReadOrderSession()
    const assigned1 = store.assignNextReadOrder(first.id)
    expect(assigned1).toBe(1)
    const assigned2 = store.assignNextReadOrder(second.id)
    expect(assigned2).toBe(2)

    // 模拟再次点击第一个取消排序
    const removed1 = store.assignNextReadOrder(first.id)
    expect(removed1).toBe(1)
    expect(store.objects.value[0].read_order).toBeUndefined()
    expect(store.objects.value[1].read_order).toBe(1)

    // 再次点击第一个重新排序
    const reassigned1 = store.assignNextReadOrder(first.id)
    expect(reassigned1).toBe(2)
    expect(store.objects.value[0].read_order).toBe(2)
    expect(store.objects.value[1].read_order).toBe(1)

    // 模拟保存，输出应为后端 0-based
    const draft = store.toDraft('page_roundtrip')
    const anns = (draft.data as any).k12_annotations as any[]
    expect(draft.base_revision_id).toBe('rev_load_001')

    const firstInDraft = anns.find(a => a.id === first.id)
    const secondInDraft = anns.find(a => a.id === second.id)
    expect(firstInDraft?.read_order).toBe(1) // 前端 2 -> 后端 1
    expect(secondInDraft?.read_order).toBe(0) // 前端 1 -> 后端 0
  })

  it('resizeObject 在右下边界退化时向内收缩，避免生成越界坐标', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 120)

    const created = store.addObject([10, 20, 60, 80], {
      name: 'question_block',
      namespace: 'k12',
    })

    store.resizeObject(created.id, 3, 280, 80)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([10, 20, 200, 80])

    store.resizeObject(created.id, 6, 250, 20)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([199, 20, 200, 80])

    store.resizeObject(created.id, 3, 200, 180)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([199, 20, 200, 120])

    store.resizeObject(created.id, 7, 199, 150)
    expect(store.objects.value[0].geometry.bbox_xyxy).toEqual([199, 119, 200, 120])
  })

  it('read_order session 会清空旧排序并按点击顺序写入 1..N', () => {
    const store = useAnnotationStore()
    store.setImageBounds(300, 200)

    const first = store.addObject([10, 10, 60, 60], {
      name: 'question_block',
      namespace: 'k12',
    })
    const second = store.addObject([80, 10, 140, 60], {
      name: 'answer_area',
      namespace: 'k12',
    })
    const third = store.addObject([160, 10, 220, 60], {
      name: 'formula',
      namespace: 'k12',
    })

    store.setReadOrder(first.id, 9)
    store.setReadOrder(second.id, 7)

    store.startReadOrderSession()
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([undefined, undefined, undefined])

    expect(store.assignNextReadOrder(second.id)).toBe(1)
    expect(store.assignNextReadOrder(first.id)).toBe(2)
    expect(store.assignNextReadOrder(third.id)).toBe(3)
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([2, 1, 3])

    store.clearReadOrder()
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([undefined, undefined, undefined])

    store.endReadOrderSession()
    expect(store.readOrderSession.value).toEqual({ active: false, counter: 0 })
  })

  it('read_order 模式下再次点击已排序对象会取消并顺延后续序号', () => {
    const store = useAnnotationStore()
    store.setImageBounds(300, 200)

    const first = store.addObject([10, 10, 60, 60], {
      name: 'question_block',
      namespace: 'k12',
    })
    const second = store.addObject([80, 10, 140, 60], {
      name: 'answer_area',
      namespace: 'k12',
    })
    const third = store.addObject([160, 10, 220, 60], {
      name: 'formula',
      namespace: 'k12',
    })

    store.startReadOrderSession()
    store.assignNextReadOrder(first.id)
    store.assignNextReadOrder(second.id)
    store.assignNextReadOrder(third.id)
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([1, 2, 3])

    expect(store.assignNextReadOrder(second.id)).toBe(2)
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([1, undefined, 2])
    expect(store.readOrderSession.value).toEqual({ active: true, counter: 2 })

    expect(store.assignNextReadOrder(second.id)).toBe(3)
    expect(store.objects.value.map(obj => obj.read_order)).toEqual([1, 3, 2])
    expect(store.readOrderSession.value).toEqual({ active: true, counter: 3 })
  })

  it('startReadOrderSession 返回是否清空了旧排序', () => {
    const store = useAnnotationStore()
    store.setImageBounds(300, 200)

    const first = store.addObject([10, 10, 60, 60], {
      name: 'question_block',
      namespace: 'k12',
    })

    expect(store.startReadOrderSession()).toBe(false)
    store.endReadOrderSession()

    store.setReadOrder(first.id, 3)
    expect(store.startReadOrderSession()).toBe(true)
    expect(store.objects.value[0].read_order).toBeUndefined()
  })

  it('保存和加载时会在前端 1-based 与后端 0-based 之间转换', () => {
    const store = useAnnotationStore()
    store.loadFromRevision({
      id: 'rev_public_002',
      page_id: 'page_public_001',
      revision_no: 4,
      status: 'draft',
      qc_status: 'pending',
      data: {
        schema_version: 'k12_annotation_v0.1',
        page_id: 'page_public_001',
        k12_annotations: [
          {
            id: 'ann_answer_001',
            type: 'answer_area',
            label_namespace: 'k12',
            geometry: {
              bbox_xyxy: [20, 30, 60, 80],
            },
            read_order: 1,
            attributes: {},
            source_refs: [],
            status: 'draft',
          },
        ],
        relations: [],
      },
    })

    expect(store.objects.value[0].read_order).toBe(2)

    const draft = store.toDraft('page_public_001')
    const annotationJson = draft.data as {
      k12_annotations: Array<{ read_order?: number }>
    }
    expect(annotationJson.k12_annotations[0].read_order).toBe(1)
  })

  it('updateObject 支持同步更新 label_namespace', () => {
    const store = useAnnotationStore()
    store.setImageBounds(200, 120)
    const created = store.addObject([10, 20, 60, 80], {
      name: 'question_block',
      namespace: 'k12',
    })

    store.updateObject(created.id, {
      type: 'figure',
      label_namespace: 'layout',
      color: '#101010',
    })

    expect(store.objects.value[0].type).toBe('figure')
    expect(store.objects.value[0].label_namespace).toBe('layout')
    expect(store.objects.value[0].color).toBe('#101010')
  })
})
