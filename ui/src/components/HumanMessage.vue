<script setup lang="ts">
// 1.定义自定义组件所需数据
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'

const props = defineProps({
  account: {
    type: Object,
    default: () => {
      return {}
    },
    required: true,
  },
  query: { type: String, default: '', required: true },
  image_urls: { type: Array, default: () => [] },
})

// 复制消息内容到剪贴板，成功后图标短暂切换为对钩
const copied = ref(false)
let copied_timer: ReturnType<typeof setTimeout> | null = null
const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(props.query)
    copied.value = true
    if (copied_timer) clearTimeout(copied_timer)
    copied_timer = setTimeout(() => { copied.value = false }, 2000)
  } catch (err) {
    Message.error(String(err))
  }
}
</script>

<template>
  <div class="flex gap-2 group">
    <!-- 左侧头像 -->
    <a-avatar :size="30" shape="circle" class="flex-shrink-0" :image-url="props.account?.avatar" />
    <!-- 右侧昵称与消息 -->
    <div class="flex flex-col items-start gap-2">
      <!-- 账号昵称 -->
      <div class="text-gray-700 font-bold">{{ props.account?.name }}</div>
      <!-- 人类消息 -->
      <div class="bg-blue-100 border border-blue-200 px-4 py-3 rounded-2xl break-all" style="color: #374151 !important;">
        <a-image v-for="(image_url, idx) in props.image_urls" :key="idx" :src="String(image_url)" />
        {{ props.query }}
      </div>
      <!-- 消息操作 -->
      <div class="w-full flex items-center">
        <a-tooltip :content="copied ? '已复制' : '复制'" position="bottom">
          <span class="flex items-center">
            <icon-check v-if="copied" class="text-gray-500" />
            <icon-copy
              v-else
              class="text-gray-400 cursor-pointer hover:text-gray-700"
              @click="handleCopy"
            />
          </span>
        </a-tooltip>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
