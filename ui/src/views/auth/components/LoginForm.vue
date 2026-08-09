<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCredentialStore } from '@/stores/credential'
import { Message, type ValidatedError } from '@arco-design/web-vue'
import { usePasswordLogin } from '@/hooks/use-auth'
import { useProvider } from '@/hooks/use-oauth'
import LogoImage from '@/assets/images/logo.png'

// 1.定义自定义组件所需数据
const errorMessage = ref('')
const loginForm = ref({ email: '', password: '' })
const credentialStore = useCredentialStore()
const router = useRouter()
const { loading: passwordLoginLoading, authorization, handlePasswordLogin } = usePasswordLogin()
const { loading: providerLoading, redirect_url, handleProvider } = useProvider()

// 2.定义忘记密码点击事件
const forgetPassword = () => Message.error('忘记密码请联系管理员')

// 3.定义github第三方授权认证登录
const githubLogin = async () => {
  // 3.1 调用处理器获取提供者重定向地址
  await handleProvider('github')

  // 3.2 跳转到重定向地址
  window.location.href = redirect_url.value
}

// 4.账号密码登录
const handleSubmit = async ({ errors }: { errors: Record<string, ValidatedError> | undefined }) => {
  // 4.1 判断表单是否校验成功
  if (errors) return

  // 4.2 如果没有出错则发起请求进行登录
  try {
    // 4.3 发起账号密码登录，并且将loading设置为true
    await handlePasswordLogin(loginForm.value.email, loginForm.value.password)
    Message.success('登录成功，正在跳转')
    credentialStore.update(authorization.value)
    await router.replace({ path: '/home' })
  } catch (error: any) {
    // 4.4 添加错误信息并清除密码
    errorMessage.value = error.message
    loginForm.value.password = ''
  }
}
</script>

<template>
  <div class="w-full">
    <header class="mb-7 text-center">
      <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50">
        <img :src="LogoImage" alt="Flow AI" class="h-10 w-10 object-contain" />
      </div>
      <h1 class="text-[26px] font-semibold leading-9 tracking-tight text-gray-900">登录 Flow AI</h1>
      <p class="mt-1.5 text-sm leading-6 text-gray-500">欢迎回来，请登录您的账号</p>
    </header>

    <div
      class="mb-1 min-h-6 text-sm leading-6 text-red-600"
      :class="{ invisible: !errorMessage }"
      role="alert"
    >
      {{ errorMessage || '登录失败' }}
    </div>

    <!-- 登录表单 -->
    <a-form
      :model="loginForm"
      @submit="handleSubmit"
      layout="vertical"
      size="large"
      class="login-form flex w-full flex-col"
    >
      <a-form-item
        field="email"
        :rules="[{ type: 'email', required: true, message: '登录账号必须是合法的邮箱' }]"
        :validate-trigger="['change', 'blur']"
        hide-label
      >
        <a-input v-model="loginForm.email" size="large" placeholder="请输入邮箱账号">
          <template #prefix>
            <icon-user />
          </template>
        </a-input>
      </a-form-item>
      <a-form-item
        field="password"
        :rules="[{ required: true, message: '账号密码不能为空' }]"
        :validate-trigger="['change', 'blur']"
        hide-label
      >
        <a-input-password v-model="loginForm.password" size="large" placeholder="请输入账号密码">
          <template #prefix>
            <icon-lock />
          </template>
        </a-input-password>
      </a-form-item>
      <a-space :size="16" direction="vertical">
        <div class="flex items-center justify-between text-sm">
          <a-checkbox>记住密码</a-checkbox>
          <a-link @click="forgetPassword">忘记密码？</a-link>
        </div>
        <a-button
          :loading="passwordLoginLoading"
          size="large"
          type="primary"
          html-type="submit"
          long
          class="login-button"
        >
          登录
        </a-button>
        <a-divider class="oauth-divider">或使用其他方式登录</a-divider>
        <a-button
          :loading="providerLoading"
          size="large"
          type="outline"
          long
          class="github-button"
          @click="githubLogin"
        >
          <template #icon>
            <icon-github />
          </template>
          Github
        </a-button>
      </a-space>
    </a-form>
  </div>
</template>

<style scoped>
.login-form :deep(.arco-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.arco-input-wrapper) {
  height: 46px;
  padding: 0 14px;
  border: 1px solid #e5e8ef;
  border-radius: 10px;
  background: #f7f8fa;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.login-form :deep(.arco-input-wrapper:hover) {
  border-color: #b8c4e8;
  background: #fff;
}

.login-form :deep(.arco-input-wrapper.arco-input-focus) {
  border-color: #4f7cff !important;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.12) !important;
}

.login-button,
.github-button {
  height: 46px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
}

.login-button {
  border: none;
  background: linear-gradient(135deg, #3b73f5, #6269ea);
  box-shadow: 0 8px 18px rgba(59, 115, 245, 0.2);
}

.login-button:hover {
  background: linear-gradient(135deg, #2f65e7, #555be0);
}

.github-button {
  border-color: #e1e5ee;
  color: #303849;
}

.github-button:hover {
  border-color: #bbc5d9;
  background: #f7f8fa;
  color: #1d2738;
}

.oauth-divider {
  margin: 4px 0 0;
  color: #a0a7b4;
  font-size: 12px;
}
</style>
