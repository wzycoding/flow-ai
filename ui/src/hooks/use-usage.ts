import { ref } from 'vue'
import {
  type GetUsagesWithPageRequest,
  type GetUsagesWithPageResponse,
} from '@/models/usage'
import { getUsagesWithPage } from '@/services/usage'

export const useGetUsagesWithPage = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)
  const usages = ref<GetUsagesWithPageResponse['data']['list']>([])
  const defaultPaginator = {
    current_page: 1,
    page_size: 20,
    total_page: 0,
    total_record: 0,
  }
  const paginator = ref({ ...defaultPaginator })

  // 2.定义加载数据函数
  const loadUsages = async (
    init: boolean = false,
    req: GetUsagesWithPageRequest = {
      current_page: 1,
      page_size: 20,
    },
  ) => {
    // 2.1 判断是否超过总页数，如果是则返回
    if (!init && paginator.value.current_page > paginator.value.total_page) {
      return
    }

    // 2.2 加载更多数据
    try {
      loading.value = true
      const resp = await getUsagesWithPage(req)
      const data = resp.data

      // 2.3 更新分页器
      paginator.value = data.paginator

      // 2.4 表格式+分页器实现的分页，直接填充数据进行替换
      usages.value = data.list
    } finally {
      loading.value = false
    }
  }

  return { loading, usages, paginator, loadUsages }
}
