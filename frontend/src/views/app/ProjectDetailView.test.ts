import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const {
  push,
  replace,
  listMock,
} = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn(),
  listMock: vi.fn(),
}))

import ProjectDetailView from './ProjectDetailView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { project_id: '10' },
    query: {},
  }),
  useRouter: () => ({
    push,
    replace,
  }),
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('@/api/pages', () => ({
  pagesApi: {
    list: listMock,
  },
}))

vi.mock('@/api/assets', () => ({
  assetsApi: {
    uploadWithProgress: vi.fn(),
  },
}))

vi.mock('./projectDetailErrors', () => ({
  formatProjectDetailError: vi.fn(() => 'error'),
}))

function createWrapper() {
  return mount(ProjectDetailView, {
    global: {
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>',
        },
      },
    },
  })
}

describe('ProjectDetailView', () => {
  beforeEach(() => {
    push.mockReset()
    replace.mockReset()
    listMock.mockReset()

    listMock.mockResolvedValue({
      items: [
        {
          page_id: 'page_1',
          project_id: 10,
          filename: 'page.png',
          status: 'imported',
          width: 100,
          height: 200,
        },
      ],
      total: 1,
    })
  })

  it('项目页面列表加载成功时显示页面项', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('page.png')
    expect(wrapper.text()).toContain('common.edit')
  })

  it('项目页面列表加载失败时显示错误态而不是空列表', async () => {
    listMock.mockRejectedValueOnce(new Error('boom'))

    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('error')
    expect(wrapper.text()).toContain('common.retry')
    expect(wrapper.text()).not.toContain('common.noData')
  })
})
