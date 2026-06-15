import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { defineComponent } from 'vue'

import BaseButton from '../BaseButton.vue'
import BaseEmptyState from '../BaseEmptyState.vue'
import BaseErrorState from '../BaseErrorState.vue'
import BaseInput from '../BaseInput.vue'

const TestIcon = defineComponent({
  template: '<svg data-testid="icon" />',
})

describe('BaseButton', () => {
  it('renders a typed button with slot text and icon', () => {
    const wrapper = mount(BaseButton, {
      props: {
        type: 'submit',
        variant: 'secondary',
        size: 'lg',
        leftIcon: TestIcon,
      },
      slots: {
        default: 'Save',
      },
    })

    const button = wrapper.get('button')
    expect(button.attributes('type')).toBe('submit')
    expect(button.text()).toContain('Save')
    expect(wrapper.find('[data-testid="icon"]').exists()).toBe(true)
    expect(button.classes()).toContain('h-10')
    expect(button.classes()).toContain('border')
  })

  it('disables interaction while loading and shows the loading icon', () => {
    const wrapper = mount(BaseButton, {
      props: {
        loading: true,
        leftIcon: TestIcon,
      },
      slots: {
        default: 'Saving',
      },
    })

    const button = wrapper.get('button')
    expect(button.attributes('disabled')).toBeDefined()
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
    expect(wrapper.find('[data-testid="icon"]').exists()).toBe(false)
    expect(button.text()).toContain('Saving')
  })
})

describe('BaseInput', () => {
  it('emits model and raw input events when edited', async () => {
    const wrapper = mount(BaseInput, {
      props: {
        modelValue: 'old',
        placeholder: 'Name',
      },
    })

    const input = wrapper.get('input')
    await input.setValue('new')

    expect(input.attributes('placeholder')).toBe('Name')
    expect(wrapper.emitted('update:modelValue')).toEqual([['new']])
    expect(wrapper.emitted('input')).toHaveLength(1)
  })

  it('passes numeric constraints and invalid state to the native input', async () => {
    const wrapper = mount(BaseInput, {
      props: {
        type: 'number',
        modelValue: 3,
        min: 0,
        max: 9,
        step: 1,
        invalid: true,
        size: 'sm',
      },
    })

    const input = wrapper.get('input')
    expect(input.attributes('type')).toBe('number')
    expect(input.attributes('min')).toBe('0')
    expect(input.attributes('max')).toBe('9')
    expect(input.attributes('step')).toBe('1')
    expect(input.classes()).toContain('border-danger')
    expect(input.classes()).toContain('h-7')

    await input.trigger('change')
    expect(wrapper.emitted('change')).toHaveLength(1)
  })
})

describe('BaseEmptyState', () => {
  it('renders title, description, icon and action slot', () => {
    const wrapper = mount(BaseEmptyState, {
      props: {
        title: 'No data',
        description: 'Upload files first',
        icon: TestIcon,
      },
      slots: {
        default: '<button>Upload</button>',
      },
    })

    expect(wrapper.text()).toContain('No data')
    expect(wrapper.text()).toContain('Upload files first')
    expect(wrapper.find('[data-testid="icon"]').exists()).toBe(true)
    expect(wrapper.get('button').text()).toBe('Upload')
  })
})

describe('BaseErrorState', () => {
  it('shows details and emits retry when retry is enabled', async () => {
    const wrapper = mount(BaseErrorState, {
      props: {
        title: 'Load failed',
        detail: 'request_id=req_1',
        retryLabel: 'Retry',
        canRetry: true,
      },
    })

    expect(wrapper.text()).toContain('Load failed')
    expect(wrapper.text()).toContain('request_id=req_1')

    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('hides retry action when retry is not available', () => {
    const wrapper = mount(BaseErrorState, {
      props: {
        title: 'Forbidden',
        canRetry: false,
      },
    })

    expect(wrapper.find('button').exists()).toBe(false)
  })
})
