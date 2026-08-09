<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import LogoImage from '@/assets/images/logo.png'
import KnowledgeAssistantImage from '@/assets/images/scenarios/knowledge-assistant.jpg'
import WorkflowAutomationImage from '@/assets/images/scenarios/workflow-automation.jpg'
import GenerativeAiImage from '@/assets/images/scenarios/generative-ai.jpg'

const capabilities = [
  {
    icon: 'robot',
    title: '快速创建Agent应用',
    description: '通过可视化界面，快速创建零代码AI 应用。',
  },
  {
    icon: 'branch',
    title: '可编排工作流',
    description: '支持拖拽自由编排工作流，包括LLM、Python代码、意图识别等10种工作流节点。',
  },
  {
    icon: 'storage',
    title: 'RAG 知识库',
    description: '统一管理您的文档与知识库数据，为Agent应用提供可靠的信息来源',
  },
  {
    icon: 'tool',
    title: '丰富工具生态',
    description: '多种内置工具直接使用，支持接入自定义开放API工具、MCP工具',
  },
  {
    icon: 'code',
    title: '开放 API',
    description: '支持以流式和非流式API形式对接您的Agent应用。',
  },
  {
    icon: 'bar-chart',
    title: 'Agent状态监控',
    description: '随时查看Agent应用运行数据、用户访问数据与token消耗',
  },
]

const applicationScenes = [
  {
    title: '智能助手',
    description: '连接个人知识库，提供准确、且可持续更新的智能问答助手。',
    image: KnowledgeAssistantImage,
    imageAlt: '抽象人工智能网络',
  },
  {
    title: 'AI 智能客服',
    description: '结合店铺信息与文档，为客户提供全天候、准确、优质的服务体验。',
    image: WorkflowAutomationImage,
    imageAlt: '数据分析与业务监控面板',
  },
  {
    title: 'AI 自媒体助手',
    description: '构建一整套从辅助选题策划、内容创作与素材整理完整工作流程，让自媒体运营更加高效。',
    image: GenerativeAiImage,
    imageAlt: '人工智能计算芯片',
  },
]

onMounted(() => document.documentElement.classList.add('marketing-home'))
onUnmounted(() => document.documentElement.classList.remove('marketing-home'))
</script>

<template>
  <div class="landing-page">
    <header class="site-header">
      <div class="page-container flex h-full items-center justify-between">
        <router-link to="/" class="brand-link" aria-label="Flow AI 首页">
          <span class="brand-mark">
            <img :src="LogoImage" alt="" class="brand-logo" />
          </span>
          <span>Flow AI</span>
        </router-link>

        <nav class="site-nav" aria-label="官网导航">
          <a href="#capabilities">产品能力</a>
          <a href="#scenarios">应用场景</a>
        </nav>

        <div class="flex items-center gap-2.5">
          <router-link to="/auth/login" class="header-login">登录</router-link>
          <router-link to="/auth/login" class="primary-button primary-button--small">
            立即使用
          </router-link>
        </div>
      </div>
    </header>

    <main>
      <section class="hero-section">
        <div class="hero-grid" aria-hidden="true"></div>
        <div class="hero-orb hero-orb--one" aria-hidden="true"></div>
        <div class="hero-orb hero-orb--two" aria-hidden="true"></div>

        <div class="page-container relative z-10 flex flex-col items-center text-center">
          <h1 class="hero-title">
            把每一个好想法
            <br />
            <span>快速构建成一个Agent应用</span>
          </h1>
          <p class="hero-description">
            仅需5分钟，你就可以得到一个支持工具调用、<br class="desktop-break" />
            工作流编排、RAG的智能Agent应用
          </p>
          <div class="hero-actions">
            <router-link to="/auth/login" class="primary-button primary-button--hero">
              立即使用
            </router-link>
            <a href="#capabilities" class="secondary-button">了解产品能力</a>
          </div>

          <div class="product-stage">
            <div class="product-window">
              <div class="window-bar">
                <div class="flex gap-1.5"><i></i><i></i><i></i></div>
                <div class="window-title">Flow AI · Workflow Studio</div>
                <div class="window-status"><span></span> 已保存</div>
              </div>
              <div class="window-body">
                <aside class="mock-sidebar">
                  <div class="mock-brand">
                    <span class="mini-logo">F</span>
                    <strong>Flow AI</strong>
                  </div>
                  <div class="mock-menu-title">工作空间</div>
                  <div class="mock-menu active"><icon-branch /> 工作流</div>
                  <div class="mock-menu"><icon-robot /> AI 应用</div>
                  <div class="mock-menu"><icon-storage /> 知识库</div>
                  <div class="mock-menu"><icon-tool /> 工具</div>
                  <div class="mock-sidebar-card">
                    <span>运行状态</span>
                    <strong><i></i> 服务正常</strong>
                  </div>
                </aside>

                <div class="workflow-canvas">
                  <div class="canvas-toolbar">
                    <div>
                      <strong>智能知识问答</strong>
                      <span>自动保存于 1 分钟前</span>
                    </div>
                    <button><icon-play-arrow /> 运行</button>
                  </div>

                  <svg class="workflow-lines" viewBox="0 0 820 410" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="flowLine" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0" stop-color="#8eb4ff" />
                        <stop offset="1" stop-color="#7569ee" />
                      </linearGradient>
                    </defs>
                    <path d="M192 200 C 250 200, 235 122, 302 122" />
                    <path d="M442 122 C 505 122, 482 200, 548 200" />
                    <path d="M192 200 C 255 200, 238 292, 302 292" />
                    <path d="M442 292 C 505 292, 482 200, 548 200" />
                    <path d="M688 200 C 724 200, 724 200, 760 200" />
                  </svg>

                  <div class="flow-node flow-node--start">
                    <div class="node-icon node-icon--blue">
                      <icon-play-arrow />
                    </div>
                    <div><small>输入</small><strong>用户问题</strong></div>
                    <span class="node-port"></span>
                  </div>
                  <div class="flow-node flow-node--knowledge">
                    <span class="node-port node-port--left"></span>
                    <div class="node-icon node-icon--cyan">
                      <icon-storage />
                    </div>
                    <div><small>检索</small><strong>企业知识库</strong></div>
                    <span class="node-port"></span>
                  </div>
                  <div class="flow-node flow-node--tool">
                    <span class="node-port node-port--left"></span>
                    <div class="node-icon node-icon--orange"><icon-tool /></div>
                    <div><small>工具</small><strong>业务数据查询</strong></div>
                    <span class="node-port"></span>
                  </div>
                  <div class="flow-node flow-node--llm">
                    <span class="node-port node-port--left"></span>
                    <div class="node-icon node-icon--purple">
                      <icon-robot />
                    </div>
                    <div><small>大语言模型</small><strong>智能回答生成</strong></div>
                    <span class="node-port"></span>
                  </div>
                  <div class="flow-result">
                    <span></span>
                    <div><small>输出</small><strong>回答用户</strong></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="floating-card floating-card--left">
              <span class="float-icon float-icon--blue"><icon-thunderbolt /></span>
              <div><small>工作流运行</small><strong>1.8s 完成</strong></div>
            </div>
            <div class="floating-card floating-card--right">
              <span class="float-icon float-icon--purple"><icon-check /></span>
              <div><small>知识检索</small><strong>已命中 6 个片段</strong></div>
            </div>
          </div>

          <div class="capability-strip" aria-label="平台核心特性">
            <span>可视化编排</span><i></i> <span>多模型接入</span><i></i> <span>RAG 知识库</span
            ><i></i>
            <span>一键发布</span>
          </div>
        </div>
      </section>

      <section id="capabilities" class="section capabilities-section">
        <div class="page-container">
          <div class="section-heading">
            <h2>产品能力</h2>
            <p>从模型与数据，到编排与发布，让团队用更清晰的方式完成 AI 应用全生命周期。</p>
          </div>

          <div class="capability-grid">
            <article v-for="item in capabilities" :key="item.title" class="capability-card">
              <div class="capability-icon">
                <icon-robot v-if="item.icon === 'robot'" />
                <icon-branch v-else-if="item.icon === 'branch'" />
                <icon-storage v-else-if="item.icon === 'storage'" />
                <icon-tool v-else-if="item.icon === 'tool'" />
                <icon-code v-else-if="item.icon === 'code'" />
                <icon-bar-chart v-else />
              </div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <section id="scenarios" class="section scenarios-section">
        <div class="page-container">
          <div class="section-heading">
            <h2>应用场景</h2>
            <p>面向不同团队与需求，快速搭建可用、可靠、可持续迭代的智能应用。</p>
          </div>
          <div class="scenario-grid">
            <article v-for="scene in applicationScenes" :key="scene.title" class="scenario-card">
              <div class="scenario-image">
                <img :src="scene.image" :alt="scene.imageAlt" loading="lazy" />
                <div class="scenario-image-overlay" aria-hidden="true"></div>
              </div>
              <div class="scenario-content">
                <h3>{{ scene.title }}</h3>
                <p>{{ scene.description }}</p>
              </div>
            </article>
          </div>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <div class="page-container footer-content">
        <p class="footer-description">一站式 AI 应用开发与 LLMOps 平台</p>
        <div class="footer-meta">
          <span>© 2026 版权所有</span>
          <i aria-hidden="true"></i>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">
            辽ICP备2026009890号
          </a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
:global(html.marketing-home),
:global(html.marketing-home body) {
  min-width: 320px;
  scroll-behavior: smooth;
}

.landing-page {
  min-height: 100vh;
  overflow: hidden;
  color: #182033;
  background: #fff;
  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    'PingFang SC',
    'Microsoft YaHei',
    sans-serif;
}

.page-container {
  width: min(1180px, calc(100% - 48px));
  margin: 0 auto;
}

.site-header {
  position: fixed;
  z-index: 50;
  top: 0;
  right: 0;
  left: 0;
  height: 72px;
  border-bottom: 1px solid rgba(223, 228, 240, 0.72);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
}

.brand-link {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #192237;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.brand-mark {
  display: flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid rgba(209, 222, 255, 0.8);
  border-radius: 12px;
  background: linear-gradient(145deg, #f4f8ff, #eef0ff);
}

.brand-logo {
  width: 56px;
  height: 56px;
  max-width: none;
  object-fit: contain;
}

.site-nav {
  display: flex;
  align-items: center;
  gap: 36px;
  color: #5a6478;
  font-size: 14px;
}

.site-nav a,
.header-login {
  transition: color 0.2s ease;
}

.site-nav a:hover,
.header-login:hover {
  color: #376df2;
}

.header-login {
  padding: 9px 12px;
  color: #4d586d;
  font-size: 14px;
  font-weight: 500;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 10px;
  font-weight: 600;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.primary-button {
  color: #fff;
  background: linear-gradient(135deg, #3975f5, #635fe8);
  box-shadow: 0 8px 18px rgba(67, 103, 236, 0.2);
}

.primary-button:hover {
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(67, 103, 236, 0.3);
}

.primary-button--small {
  min-width: 108px;
  height: 40px;
  padding: 0 18px;
  font-size: 14px;
}

.hero-section {
  position: relative;
  padding: 154px 0 94px;
  background: radial-gradient(circle at 50% 22%, rgba(225, 234, 255, 0.72), transparent 33%),
    linear-gradient(180deg, #fbfcff 0%, #f8faff 62%, #fff 100%);
}

.hero-grid {
  position: absolute;
  inset: 72px 0 auto;
  height: 650px;
  background-image: linear-gradient(rgba(91, 116, 177, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(91, 116, 177, 0.07) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: radial-gradient(ellipse at center, #000 15%, transparent 72%);
}

.hero-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(2px);
  pointer-events: none;
}

.hero-orb--one {
  top: 120px;
  left: -180px;
  width: 430px;
  height: 430px;
  background: rgba(97, 146, 255, 0.08);
}

.hero-orb--two {
  top: 330px;
  right: -190px;
  width: 390px;
  height: 390px;
  background: rgba(123, 89, 238, 0.08);
}

.hero-title {
  margin-top: 25px;
  color: #172034;
  font-size: clamp(46px, 5vw, 72px);
  font-weight: 700;
  line-height: 1.16;
  letter-spacing: -0.055em;
}

.hero-title span {
  color: transparent;
  background: linear-gradient(100deg, #3477f6 18%, #675ce8 78%);
  background-clip: text;
}

.hero-description {
  margin-top: 25px;
  color: #667085;
  font-size: 17px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  margin-top: 32px;
  align-items: center;
  gap: 12px;
}

.primary-button--hero,
.secondary-button {
  min-width: 146px;
  height: 50px;
  padding: 0 24px;
  font-size: 15px;
}

.secondary-button {
  border: 1px solid #dfe4ef;
  color: #3f4b61;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 5px 15px rgba(32, 48, 85, 0.05);
}

.secondary-button:hover {
  border-color: #bfcdf0;
  color: #376df2;
  background: #fff;
  transform: translateY(-2px);
}

.product-stage {
  position: relative;
  width: 100%;
  margin-top: 72px;
}

.product-window {
  overflow: hidden;
  width: min(100%, 1040px);
  margin: 0 auto;
  border: 1px solid rgba(213, 220, 235, 0.92);
  border-radius: 20px;
  background: #fff;
  box-shadow:
    0 34px 90px rgba(34, 54, 104, 0.14),
    0 8px 30px rgba(34, 54, 104, 0.06);
}

.window-bar {
  display: grid;
  height: 48px;
  padding: 0 18px;
  align-items: center;
  grid-template-columns: 1fr auto 1fr;
  border-bottom: 1px solid #e9edf4;
  color: #8992a3;
  background: #fbfcfe;
  font-size: 11px;
}

.window-bar i {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d7dce6;
}

.window-title {
  color: #8b94a5;
  font-weight: 500;
}

.window-status {
  display: flex;
  align-items: center;
  justify-self: end;
  gap: 6px;
}

.window-status span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #33bf83;
}

.window-body {
  display: flex;
  height: 480px;
}

.mock-sidebar {
  position: relative;
  width: 180px;
  padding: 18px 14px;
  border-right: 1px solid #e8ecf3;
  background: #fbfcfe;
  text-align: left;
}

.mock-brand {
  display: flex;
  margin-bottom: 28px;
  align-items: center;
  gap: 9px;
  color: #273147;
  font-size: 12px;
}

.mini-logo {
  display: flex;
  width: 27px;
  height: 27px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #fff;
  background: linear-gradient(135deg, #3e83f7, #6d59e9);
  font-size: 13px;
  font-weight: 700;
}

.mock-menu-title {
  margin: 0 9px 8px;
  color: #a2a9b7;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.12em;
}

.mock-menu {
  display: flex;
  height: 35px;
  margin-bottom: 3px;
  padding: 0 10px;
  align-items: center;
  gap: 9px;
  border-radius: 8px;
  color: #70798a;
  font-size: 11px;
}

.mock-menu.active {
  color: #376df2;
  background: #edf3ff;
  font-weight: 600;
}

.mock-sidebar-card {
  position: absolute;
  right: 14px;
  bottom: 16px;
  left: 14px;
  display: flex;
  padding: 11px;
  flex-direction: column;
  gap: 4px;
  border: 1px solid #e3e8f1;
  border-radius: 9px;
  color: #9aa2b1;
  background: #fff;
  font-size: 9px;
}

.mock-sidebar-card strong {
  color: #4b5568;
  font-size: 10px;
}

.mock-sidebar-card i {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 5px;
  border-radius: 50%;
  background: #2fc583;
}

.workflow-canvas {
  position: relative;
  flex: 1;
  overflow: hidden;
  background-color: #f8faff;
  background-image: radial-gradient(#ccd5e8 0.8px, transparent 0.8px);
  background-size: 18px 18px;
}

.canvas-toolbar {
  position: absolute;
  z-index: 3;
  top: 0;
  right: 0;
  left: 0;
  display: flex;
  height: 58px;
  padding: 0 20px;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(225, 230, 240, 0.9);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(10px);
}

.canvas-toolbar > div {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.canvas-toolbar strong {
  color: #30394b;
  font-size: 11px;
}

.canvas-toolbar span {
  margin-top: 2px;
  color: #a1a8b5;
  font-size: 8px;
}

.canvas-toolbar button {
  display: flex;
  height: 30px;
  padding: 0 12px;
  align-items: center;
  gap: 5px;
  border-radius: 7px;
  color: #fff;
  background: #4c72ec;
  font-size: 9px;
}

.workflow-lines {
  position: absolute;
  inset: 58px 0 0;
  width: 100%;
  height: calc(100% - 58px);
}

.workflow-lines path {
  fill: none;
  stroke: url(#flowLine);
  stroke-width: 2;
  stroke-linecap: round;
  opacity: 0.7;
}

.flow-node {
  position: absolute;
  z-index: 2;
  display: flex;
  width: 142px;
  height: 66px;
  padding: 12px;
  align-items: center;
  gap: 10px;
  border: 1px solid #dde4f1;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8px 22px rgba(47, 66, 109, 0.08);
  text-align: left;
}

.flow-node--start {
  top: 220px;
  left: 4%;
}

.flow-node--knowledge {
  top: 139px;
  left: 31%;
}

.flow-node--tool {
  top: 309px;
  left: 31%;
}

.flow-node--llm {
  top: 220px;
  left: 61%;
  border-color: #cdd5fb;
  box-shadow: 0 10px 26px rgba(93, 91, 218, 0.12);
}

.node-icon {
  display: flex;
  width: 30px;
  height: 30px;
  flex: none;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 14px;
}

.node-icon--blue {
  color: #3578ed;
  background: #eaf2ff;
}

.node-icon--cyan {
  color: #188a9f;
  background: #e7f8fa;
}

.node-icon--orange {
  color: #ce7928;
  background: #fff3e6;
}

.node-icon--purple {
  color: #6559dd;
  background: #efedff;
}

.flow-node small,
.flow-result small {
  display: block;
  margin-bottom: 3px;
  color: #9ba3b2;
  font-size: 8px;
}

.flow-node strong,
.flow-result strong {
  display: block;
  color: #424c60;
  font-size: 10px;
  white-space: nowrap;
}

.node-port {
  position: absolute;
  top: 29px;
  right: -5px;
  width: 9px;
  height: 9px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #6f86df;
  box-shadow: 0 0 0 1px #6f86df;
}

.node-port--left {
  right: auto;
  left: -5px;
}

.flow-result {
  position: absolute;
  z-index: 2;
  top: 226px;
  right: 2.5%;
  display: flex;
  width: 110px;
  height: 54px;
  padding: 10px;
  align-items: center;
  gap: 9px;
  border: 1px solid #dce4ef;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(47, 66, 109, 0.08);
  text-align: left;
}

.flow-result > span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #30bf80;
  box-shadow: 0 0 0 5px rgba(48, 191, 128, 0.12);
}

.floating-card {
  position: absolute;
  display: flex;
  min-width: 178px;
  padding: 13px 16px;
  align-items: center;
  gap: 11px;
  border: 1px solid rgba(222, 228, 240, 0.86);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 16px 40px rgba(43, 59, 98, 0.13);
  backdrop-filter: blur(12px);
  text-align: left;
}

.floating-card--left {
  bottom: 45px;
  left: -18px;
}

.floating-card--right {
  top: 92px;
  right: -16px;
}

.float-icon {
  display: flex;
  width: 35px;
  height: 35px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.float-icon--blue {
  color: #3d76ed;
  background: #eaf2ff;
}

.float-icon--purple {
  color: #6659de;
  background: #efedff;
}

.floating-card small {
  display: block;
  margin-bottom: 2px;
  color: #969ead;
  font-size: 9px;
}

.floating-card strong {
  color: #3b465a;
  font-size: 11px;
}

.capability-strip {
  display: flex;
  margin-top: 54px;
  align-items: center;
  justify-content: center;
  gap: 26px;
  color: #8a93a4;
  font-size: 13px;
  font-weight: 500;
}

.capability-strip i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #c7cfde;
}

.section {
  padding: 118px 0;
}

.capabilities-section {
  background: #fff;
}

.section-heading {
  max-width: 680px;
  margin: 0 auto 54px;
  text-align: center;
}

.section-heading h2 {
  margin-top: 14px;
  color: #182033;
  font-size: 40px;
  font-weight: 650;
  line-height: 1.3;
  letter-spacing: -0.035em;
}

.section-heading p {
  margin-top: 16px;
  color: #788295;
  font-size: 16px;
  line-height: 1.8;
}

.capability-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.capability-card {
  position: relative;
  min-height: 240px;
  padding: 28px;
  overflow: hidden;
  border: 1px solid #e8ebf2;
  border-radius: 18px;
  background: linear-gradient(145deg, #fff, #fbfcff);
  transition:
    transform 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.capability-card::after {
  position: absolute;
  right: -45px;
  bottom: -65px;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: rgba(74, 115, 238, 0.045);
  content: '';
}

.capability-card:hover {
  border-color: #d3dcf6;
  transform: translateY(-5px);
  box-shadow: 0 18px 45px rgba(40, 59, 104, 0.09);
}

.capability-icon {
  display: flex;
  width: 46px;
  height: 46px;
  align-items: center;
  justify-content: center;
  border: 1px solid #dfe7fb;
  border-radius: 13px;
  color: #4674eb;
  background: #f2f6ff;
  font-size: 20px;
}

.capability-card h3 {
  margin-top: 25px;
  color: #253047;
  font-size: 18px;
  font-weight: 600;
}

.capability-card p {
  margin-top: 11px;
  color: #798395;
  font-size: 14px;
  line-height: 1.75;
}

.scenarios-section {
  background: #fff;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.scenario-card {
  position: relative;
  overflow: hidden;
  border: 1px solid #e6eaf2;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 12px 34px rgba(38, 55, 93, 0.07);
  transition:
    transform 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.scenario-card:hover {
  border-color: #d4ddf3;
  box-shadow: 0 20px 46px rgba(38, 55, 93, 0.12);
  transform: translateY(-5px);
}

.scenario-image {
  position: relative;
  height: 190px;
  overflow: hidden;
  background: #eef3ff;
}

.scenario-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: saturate(0.72) contrast(0.9) brightness(1.06);
  transition: transform 0.45s ease;
}

.scenario-card:hover .scenario-image img {
  transform: scale(1.04);
}

.scenario-image-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(48, 82, 172, 0.03), rgba(34, 55, 118, 0.26)),
    linear-gradient(120deg, rgba(73, 132, 246, 0.12), rgba(111, 87, 232, 0.08));
}

.scenario-content {
  min-height: 150px;
  padding: 25px 28px 28px;
}

.scenario-card h3 {
  color: #283349;
  font-size: 21px;
  font-weight: 600;
}

.scenario-card p {
  max-width: 280px;
  margin-top: 11px;
  color: #7a8496;
  font-size: 14px;
  line-height: 1.75;
}

.site-footer {
  padding: 30px 0 28px;
  border-top: 1px solid #edf0f5;
  background: #fafbfc;
}

.footer-content {
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  gap: 9px;
  text-align: center;
}

.footer-description {
  color: #717b8e;
  font-size: 13px;
  line-height: 20px;
}

.footer-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #9aa2b0;
  font-size: 12px;
  line-height: 18px;
}

.footer-meta i {
  width: 1px;
  height: 11px;
  background: #d9dee7;
}

.footer-meta a:hover {
  color: #496fda;
}

@media (max-width: 1024px) {
  .site-nav {
    display: none;
  }

  .product-window {
    width: 94%;
  }

  .floating-card {
    display: none;
  }

  .capability-grid,
  .scenario-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-container {
    width: min(100% - 32px, 1180px);
  }

  .site-header {
    height: 64px;
  }

  .header-login {
    display: none;
  }

  .primary-button--small {
    min-width: 96px;
    height: 38px;
    padding: 0 14px;
  }

  .hero-section {
    padding-top: 126px;
  }

  .hero-title {
    font-size: 43px;
  }

  .desktop-break {
    display: none;
  }

  .product-stage {
    margin-top: 55px;
  }

  .product-window {
    width: 720px;
    transform: scale(0.7);
    transform-origin: top left;
  }

  .product-stage {
    width: 504px;
    height: 370px;
    max-width: 100%;
  }

  .capability-strip {
    flex-wrap: wrap;
    gap: 12px 18px;
  }

  .section {
    padding: 86px 0;
  }

  .section-heading h2 {
    font-size: 34px;
  }

  .capability-grid,
  .scenario-grid {
    grid-template-columns: 1fr;
  }

  .scenario-card {
    min-height: 0;
  }
}

@media (max-width: 520px) {
  .brand-link {
    font-size: 17px;
  }

  .brand-mark {
    width: 34px;
    height: 34px;
  }

  .hero-title {
    font-size: 37px;
  }

  .hero-description {
    font-size: 15px;
  }

  .hero-actions {
    width: 100%;
    flex-direction: column;
  }

  .primary-button--hero,
  .secondary-button {
    width: 100%;
  }

  .product-stage {
    display: none;
  }

  .capability-strip {
    margin-top: 58px;
  }

  .capability-grid {
    grid-template-columns: 1fr;
  }

  .capability-card {
    min-height: 220px;
  }

  .footer-meta {
    flex-direction: column;
    align-items: center;
    gap: 5px;
  }

  .footer-meta i {
    display: none;
  }
}
</style>
