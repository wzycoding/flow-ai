import { get } from '@/utils/request'
import {
  type GetUsagesWithPageRequest,
  type GetUsagesWithPageResponse,
} from '@/models/usage'

// 获取用量分页列表数据
export const getUsagesWithPage = (req: GetUsagesWithPageRequest) => {
  return get<GetUsagesWithPageResponse>(`/usages`, { params: req })
}
