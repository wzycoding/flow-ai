<script setup lang="ts">
import BannerImage from '@/assets/images/login-banner.png'

// 轮播图列表
const carousels = [
  {
    slogan: '个人效率工具平台',
    subSlogan: '集成多种实用工具，提升工作效率',
    image: BannerImage,
  },
  {
    slogan: '简洁易用的工作助手',
    subSlogan: '助力日常办公与项目管理',
    image: BannerImage,
  },
]
</script>

<template>
  <div
    class="w-[550px] flex items-center justify-center bg-gradient-to-tr from-[#1d2129] to-[#00308f]"
  >
    <div class="flex-1 h-full">
      <a-carousel animation-name="fade" class="h-full">
        <a-carousel-item v-for="carousel in carousels" :key="carousel.slogan">
          <div class="flex flex-col items-center justify-center h-full">
            <div class="text-2xl leading-7 font-bold text-gray-100">{{ carousel.slogan }}</div>
            <div class="mt-2 text-gray-400 leading-[22px]">{{ carousel.subSlogan }}</div>
            <img :src="carousel.image" alt="FlowAI" class="w-[320px] mt-[30px]" />
          </div>
        </a-carousel-item>
      </a-carousel>
    </div>
  </div>
</template>

<style scoped></style>
