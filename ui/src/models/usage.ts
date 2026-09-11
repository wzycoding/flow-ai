import {
  type BasePaginatorRequest,
  type BasePaginatorResponse,
} from '@/models/base'

// 获取用量列表请求
export type GetUsagesWithPageRequest = BasePaginatorRequest & {
  source?: string
}

// 获取用量列表响应数据
export type GetUsagesWithPageResponse = BasePaginatorResponse<{
  id: string
  source: string
  app_name: string
  provider_name: string
  model_name: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  created_at: number
}>
