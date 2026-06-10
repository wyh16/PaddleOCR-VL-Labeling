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
            read_order: 1,
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

    const created = store.addObject([-10, 20, 210, 120], 'question_block')
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
        read_order: 1,
        attributes: {},
        source_refs: [],
        status: 'draft',
      },
    ])
    expect('objects' in annotationJson).toBe(false)
  })
})
