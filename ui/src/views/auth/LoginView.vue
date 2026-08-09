<script setup lang="ts">
import LoginForm from './components/LoginForm.vue'
</script>

<template>
  <div class="login-page">
    <div class="login-glow login-glow--top" aria-hidden="true"></div>
    <div class="login-glow login-glow--bottom" aria-hidden="true"></div>

    <main class="relative z-10 flex min-h-full items-center justify-center px-6 py-20">
      <section class="login-card" aria-label="账号登录">
        <login-form />
      </section>
    </main>

    <footer class="login-footer">
      <span>Flow AI</span>
      <span class="text-gray-300">|</span>
      <a
        href="https://beian.miit.gov.cn/"
        target="_blank"
        rel="noopener noreferrer"
        class="transition-colors hover:text-gray-700"
      >
        辽ICP备2026009890号
      </a>
    </footer>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 0%, rgba(82, 123, 255, 0.1), transparent 34%),
    linear-gradient(145deg, #f8faff 0%, #f5f7fb 48%, #f8f6ff 100%);
}

.login-page::before {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(64, 92, 190, 0.13) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: linear-gradient(to bottom, black, transparent 70%);
  content: '';
  opacity: 0.45;
}

.login-card {
  width: min(100%, 440px);
  padding: 42px 44px 40px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow:
    0 24px 70px rgba(31, 51, 101, 0.12),
    0 3px 12px rgba(31, 51, 101, 0.05);
  backdrop-filter: blur(18px);
  transform: translateY(16px);
}

.login-glow {
  position: absolute;
  width: 360px;
  height: 360px;
  border-radius: 9999px;
  filter: blur(4px);
  pointer-events: none;
}

.login-glow--top {
  top: -220px;
  right: 8%;
  background: rgba(64, 128, 255, 0.12);
}

.login-glow--bottom {
  bottom: -250px;
  left: 5%;
  background: rgba(126, 86, 255, 0.1);
}

.login-footer {
  position: absolute;
  z-index: 10;
  right: 0;
  bottom: 24px;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #86909c;
  font-size: 13px;
  line-height: 20px;
}

@media (max-height: 700px) {
  .login-card {
    padding-top: 30px;
    padding-bottom: 28px;
    transform: translateY(8px);
  }

  .login-footer {
    bottom: 12px;
  }
}

@media (max-width: 640px) {
  .login-card {
    padding: 36px 28px 32px;
    border-radius: 20px;
  }
}
</style>
