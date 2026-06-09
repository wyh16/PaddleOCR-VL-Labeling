/**
 * 画布缩放/平移 + 坐标转换
 * 图片坐标系：原图像素，左上角为原点
 * 屏幕坐标系：容器内像素，左上角为原点
 */
import { ref, computed } from 'vue'

export interface Point {
  x: number
  y: number
}

export function useCanvasTransform() {
  const scale = ref(1)
  const offset = ref<Point>({ x: 0, y: 0 })
  const imageSize = ref<Point>({ x: 1, y: 1 })
  const containerSize = ref<Point>({ x: 1, y: 1 })

  const MIN_SCALE = 0.1
  const MAX_SCALE = 5

  /** 设置图片原始尺寸 */
  function setImageSize(w: number, h: number) {
    imageSize.value = { x: w, y: h }
  }

  /** 设置容器尺寸 */
  function setContainerSize(w: number, h: number) {
    containerSize.value = { x: w, y: h }
  }

  /** 适应容器宽度 */
  function fitToWidth() {
    const s = containerSize.value.x / imageSize.value.x
    scale.value = Math.max(MIN_SCALE, Math.min(MAX_SCALE, s))
    offset.value = {
      x: 0,
      y: (containerSize.value.y - imageSize.value.y * scale.value) / 2,
    }
  }

  /** 适应容器（宽度和高度都适应） */
  function fitToContainer() {
    const sx = containerSize.value.x / imageSize.value.x
    const sy = containerSize.value.y / imageSize.value.y
    const s = Math.min(sx, sy) * 0.95 // 留 5% padding
    scale.value = Math.max(MIN_SCALE, Math.min(MAX_SCALE, s))
    offset.value = {
      x: (containerSize.value.x - imageSize.value.x * scale.value) / 2,
      y: (containerSize.value.y - imageSize.value.y * scale.value) / 2,
    }
  }

  /** 缩放（以指定屏幕坐标为中心） */
  function zoom(delta: number, center?: Point) {
    const oldScale = scale.value
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, oldScale * (1 + delta)))

    if (center) {
      // 以 center 为中心缩放，保持 center 对应的图片点不变
      const imgX = (center.x - offset.value.x) / oldScale
      const imgY = (center.y - offset.value.y) / oldScale
      offset.value = {
        x: center.x - imgX * newScale,
        y: center.y - imgY * newScale,
      }
    }

    scale.value = newScale
  }

  /** 平移（屏幕像素增量） */
  function pan(dx: number, dy: number) {
    offset.value = {
      x: offset.value.x + dx,
      y: offset.value.y + dy,
    }
  }

  /** 屏幕坐标 → 图片坐标 */
  function screenToImage(sx: number, sy: number): Point {
    return {
      x: (sx - offset.value.x) / scale.value,
      y: (sy - offset.value.y) / scale.value,
    }
  }

  /** 图片坐标 → 屏幕坐标 */
  function imageToScreen(ix: number, iy: number): Point {
    return {
      x: ix * scale.value + offset.value.x,
      y: iy * scale.value + offset.value.y,
    }
  }

  /** CSS transform 字符串 */
  const transformStyle = computed(() =>
    `translate(${offset.value.x}px, ${offset.value.y}px) scale(${scale.value})`
  )

  /** 缩放百分比 */
  const zoomPercent = computed(() => Math.round(scale.value * 100))

  return {
    scale,
    offset,
    imageSize,
    containerSize,
    transformStyle,
    zoomPercent,
    setImageSize,
    setContainerSize,
    fitToWidth,
    fitToContainer,
    zoom,
    pan,
    screenToImage,
    imageToScreen,
  }
}