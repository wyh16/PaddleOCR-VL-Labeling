/**
 * 文件资产相关 API
 * 后端：POST /projects/{project_id}/assets/upload
 */
import { api } from './client'

export interface Asset {
  id: string
  filename: string
  mime_type: string
  size: number
  hash: string
  created_at: string
}

/** 后端 AssetUploadData */
export interface AssetUploadData {
  asset_id: string
  document_id: string
  page_id: string
  sha256: string
  size_bytes: number
  mime_type: string
  width: number
  height: number
  asset_reused: boolean
}

/** 后端 AssetUploadResponse: { data, request_id } */
export interface AssetUploadResponse {
  data: AssetUploadData
  request_id: string
}

export const assetsApi = {
  /** 获取资产详情 */
  get: (assetId: string) =>
    api.get<Asset>(`/assets/${assetId}`),

  /** 获取资产下载 URL */
  getDownloadUrl: (assetId: string) =>
    api.get<{ url: string; expires_at: string }>(`/assets/${assetId}/download`),

  /** 上传资产到指定项目 */
  upload: (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.upload<AssetUploadResponse>(
      `/projects/${projectId}/assets/upload`,
      formData,
    )
  },
}
