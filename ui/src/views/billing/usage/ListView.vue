<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGetUsagesWithPage } from '@/hooks/use-usage'
import moment from 'moment'

// 1.定义页面所需基础数据
const route = useRoute()
const router = useRouter()
const {
  loading: getUsagesWithPageLoading,
  paginator,
  usages,
  loadUsages,
} = useGetUsagesWithPage()
const req = computed(() => {
  return {
    current_page: Number(route.query?.current_page ?? 1),
    page_size: Number(route.query?.page_size ?? 20),
  }
})

// 2.定义来源枚举到中文文案的映射
const sourceTextMap: Record<string, string> = {
  app: '应用对话',
  assistant: '辅助Agent',
  workflow: '工作流',
  summary: '后台任务',
}

// 3.页面加载完毕后获取用量列表数据
onMounted(async () => {
  await loadUsages(true, req.value)
})

// 4.监听路由query变化，重新加载数据
watch(
  () => route.query,
  async (newQuery, oldQuery) => {
    if (newQuery.current_page != oldQuery.current_page) {
      await loadUsages(false, req.value)
    }
  },
)
</script>

<template>
  <div class="px-6 flex flex-col overflow-hidden h-full">
    <div class="pt-6 sticky top-0 z-20 bg-gray-50">
      <!-- 顶层标题 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
          <a-avatar :size="32" class="bg-blue-700">
            <icon-safe :size="18" />
          </a-avatar>
          <div
            class="flex items-center gap-2 text-lg font-medium text-gray-900"
          >
            用量信息
            <div class="text-xs text-gray-500">
              当前账号下每次大模型调用的真实 token 消耗记录
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="h-[calc(100vh-224px)] overflow-scroll scrollbar-w-none">
      <a-table
        hoverable
        :pagination="{
          total: paginator.total_record,
          current: paginator.current_page,
          defaultCurrent: 1,
          pageSize: paginator.page_size,
          defaultPageSize: 20,
          showTotal: true,
        }"
        :loading="getUsagesWithPageLoading"
        :bordered="{ wrapper: false }"
        :data="usages"
        @page-change="
          (page: number) => {
            router.push({
              path: route.path,
              query: { current_page: page },
            })
          }
        "
      >
        <template #columns>
          <a-table-column
            title="来源"
            data-index="source"
            :width="120"
            header-cell-class="rounded-tl-lg !bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          >
            <template #cell="{ record }">
              {{ sourceTextMap[record.source] ?? record.source }}
            </template>
          </a-table-column>
          <a-table-column
            title="关联应用"
            data-index="app_name"
            :width="180"
            header-cell-class="!bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          >
            <template #cell="{ record }">
              <div class="line-clamp-1">
                {{ record.app_name || '-' }}
              </div>
            </template>
          </a-table-column>
          <a-table-column
            title="服务商"
            data-index="provider_name"
            :width="140"
            header-cell-class="!bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          />
          <a-table-column
            title="模型"
            data-index="model_name"
            :width="220"
            header-cell-class="!bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          >
            <template #cell="{ record }">
              <div class="line-clamp-1">{{ record.model_name }}</div>
            </template>
          </a-table-column>
          <a-table-column
            title="输入Token"
            data-index="prompt_tokens"
            :width="110"
            header-cell-class="!bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          />
          <a-table-column
            title="输出Token"
            data-index="completion_tokens"
            :width="110"
            header-cell-class="!bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          />
          <a-table-column
            title="总Token"
            data-index="total_tokens"
            :width="110"
            header-cell-class="!bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          />
          <a-table-column
            title="调用时间"
            data-index="created_at"
            header-cell-class="rounded-tr-lg !bg-gray-200 text-gray-700"
            cell-class="bg-transparent text-gray-700"
          >
            <template #cell="{ record }">
              {{
                moment(record.created_at * 1000).format('YYYY-MM-DD hh:mm:ss')
              }}
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>
  </div>
</template>

<style scoped></style>
