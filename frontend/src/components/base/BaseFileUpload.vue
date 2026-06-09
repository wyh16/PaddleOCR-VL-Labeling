/**
 * 文件上传组件
 * 支持拖拽和点击选择，显示上传进度和结果
 */
<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload, X, FileCheck, AlertCircle, Loader2 } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  accept?: string
  multiple?: boolean
  maxSizeMB?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  accept: 'image/*',
  multiple: true,
  maxSizeMB: 50,
  disabled: false,
})

const emit = defineEmits<{
  select: [files: File[]]
}>()

export interface UploadFile {
  file: File
  status: 'pending' | 'uploading' | 'done' | 'error'
  progress: number
  result?: unknown
  error?: string
}

const dragover = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadFiles = ref<UploadFile[]>([])

const hasFiles = computed(() => uploadFiles.value.length > 0)

function triggerSelect() {
  fileInputRef.value?.click()
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) addFiles(Array.from(input.files))
  input.value = ''
}

function handleDrop(e: DragEvent) {
  dragover.value = false
  if (props.disabled) return
  if (e.dataTransfer?.files) addFiles(Array.from(e.dataTransfer.files))
}

function addFiles(files: File[]) {
  const maxSize = props.maxSizeMB * 1024 * 1024
  const valid = files.filter(f => f.size <= maxSize)
  const newItems: UploadFile[] = valid.map(f => ({
    file: f,
    status: 'pending',
    progress: 0,
  }))
  uploadFiles.value.push(...newItems)
  emit('select', valid)
}

function removeFile(index: number) {
  uploadFiles.value.splice(index, 1)
}

function clearAll() {
  uploadFiles.value = []
}

defineExpose({ uploadFiles, clearAll })
</script>

<template>
  <div
    :class="[
      'relative border-2 border-dashed rounded-lg transition-colors',
      dragover ? 'border-primary bg-primary/5' : 'border-border hover:border-border-strong',
      disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
    ]"
    @click="triggerSelect"
    @dragover.prevent="dragover = true"
    @dragleave="dragover = false"
    @drop.prevent="handleDrop"
  >
    <input
      ref="fileInputRef"
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="hidden"
      @change="handleFileInput"
    />

    <!-- 上传区域 -->
    <div class="flex flex-col items-center justify-center py-8 px-4">
      <Upload class="w-8 h-8 text-text-muted mb-2" />
      <p class="text-body text-text-secondary mb-1">{{ t('upload.dragOrClick') }}</p>
      <p class="text-caption text-text-muted">{{ t('upload.acceptHint', { accept, maxSize: maxSizeMB }) }}</p>
    </div>

    <!-- 文件列表 -->
    <div v-if="hasFiles" class="border-t border-border px-4 py-3 space-y-2">
      <div
        v-for="(item, index) in uploadFiles"
        :key="index"
        class="flex items-center gap-2 text-caption"
      >
        <Loader2 v-if="item.status === 'uploading'" class="w-3.5 h-3.5 text-primary animate-spin shrink-0" />
        <FileCheck v-else-if="item.status === 'done'" class="w-3.5 h-3.5 text-success shrink-0" />
        <AlertCircle v-else-if="item.status === 'error'" class="w-3.5 h-3.5 text-danger shrink-0" />
        <span class="flex-1 truncate text-text">{{ item.file.name }}</span>
        <span class="text-text-muted">{{ (item.file.size / 1024 / 1024).toFixed(1) }}MB</span>
        <button
          class="p-0.5 rounded hover:bg-surface-muted text-text-muted hover:text-text transition-colors"
          :aria-label="t('common.remove')"
          @click.stop="removeFile(index)"
        >
          <X class="w-3 h-3" />
        </button>
      </div>
    </div>
  </div>
</template>
