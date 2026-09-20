<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import {
  ArrowLeft, ArrowRight, BookOpen, CalendarDays, Camera, Check, ChevronDown,
  CircleUserRound, CloudSun, Compass, Feather, Footprints, Heart, ImagePlus,
  LayoutGrid, LocateFixed, Map, MapPin, Mic, Moon, MoreHorizontal, Music2,
  Navigation, Pause, PenLine, Play, Plus, Route, Search, Send, Settings,
  Share2, Sparkles, Sun, Upload, WandSparkles, X, ZoomIn, ZoomOut
} from 'lucide-vue-next'
import TravelMap from './components/TravelMap.vue'
import {
  analyzePhoto, generateJournal as generateJournalApi, generateMemory as generateMemoryApi,
  login as loginApi, logout as logoutApi, register as registerApi, saveJournal, uploadMedia,
} from './api'
import { locateTravelMoment } from './services/baiduMap'

const activePage = ref('home')
const isLoggedIn = ref(Boolean(localStorage.getItem('travel01_token')))
const isAiOpen = ref(false)
const isGenerating = ref(false)
const isPlaying = ref(false)
const liked = ref(false)
const mood = ref('松弛')
const toast = ref('')
const selectedTrip = ref(0)
const editorTitle = ref('在洱海边，等一场日落')
const editorText = ref('风从苍山越过来，把湖面吹成一匹闪着银光的绸缎。我们沿着环海西路慢慢骑行，没有赶时间，也没有特意寻找风景。\n\n傍晚六点，云层终于裂开一道金色的缝。那一刻，远处的渔船、岸边的芦苇和我们的影子，都被落日温柔地收进了今天。')
const loginAccount = ref('demo')
const loginPassword = ref('demo1234')
const loginError = ref('')
const authMode = ref('login')
const registerEmail = ref('')
const aiPrompt = ref('想写得松弛、自然一些，保留日落时的感动。')
const aiStyle = ref('散文随笔')
const photoInput = ref()
const editorTextarea = ref()
const uploadedPhotoUrl = ref('')
const isUploading = ref(false)
const isRecording = ref(false)
const recordingSeconds = ref(0)
const layoutStyle = ref('collage')
const editorLocation = ref('洱海生态廊道')
const editorLatitude = ref(25.743)
const editorLongitude = ref(100.177)
const routeInfo = ref(null)
const generatedMemory = ref(null)
let mediaRecorder
let recordingTimer
let audioChunks = []

const navItems = [
  { id: 'home', label: '今日', icon: LayoutGrid },
  { id: 'journal', label: '手账', icon: BookOpen },
  { id: 'map', label: '足迹', icon: Map },
  { id: 'memories', label: '回忆', icon: Sparkles },
]

const trips = [
  { city: '大理', province: '云南', date: '2026.08.16—08.21', days: '6天', color: '#d77b59', longitude: 100.177, latitude: 25.743, zoom: 12, places: ['喜洲古镇','洱海生态廊道','龙龛码头'], route: [[100.123,25.851],[100.177,25.743],[100.192,25.679]] },
  { city: '阿勒泰', province: '新疆', date: '2026.06.03—06.10', days: '8天', color: '#607a69', longitude: 88.1413, latitude: 47.8449, zoom: 10, places: ['阿勒泰市','将军山'], route: [[88.1413,47.8449],[88.109,47.826]] },
  { city: '泉州', province: '福建', date: '2026.03.12—03.15', days: '4天', color: '#d3a74f', longitude: 118.6757, latitude: 24.8741, zoom: 13, places: ['开元寺','西街'], route: [[118.5864,24.9188],[118.5852,24.9165]] },
  { city: '京都', province: '日本', date: '2025.11.02—11.07', days: '6天', color: '#9a6d70', longitude: 135.7681, latitude: 35.0116, zoom: 11, places: ['京都站'], route: [[135.7588,34.9858]] },
]

const currentTrip = computed(() => trips[selectedTrip.value])
const dateLine = computed(() => {
  const now = new Date()
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return `${weekdays[now.getDay()]} · ${now.getMonth() + 1}月${now.getDate()}日`
})
const pageTitle = computed(() => ({
  home: '今天，去哪里？', journal: '我的手账', map: '世界足迹', memories: '时光精选', profile: '个人空间'
}[activePage.value]))

let toastTimer
function notify(message) {
  toast.value = message
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 2600)
}

function navigate(page) {
  activePage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/** 切换旅行城市时同步清理上一段路线的摘要。 */
function selectTrip(index) {
  selectedTrip.value = index
  routeInfo.value = null
}

function openAi() {
  isAiOpen.value = true
  nextTick(() => document.querySelector('.ai-sheet textarea')?.focus())
}

async function generateJournal() {
  isGenerating.value = true
  try {
    const result = await generateJournalApi(aiPrompt.value, aiStyle.value)
    editorTitle.value = result.title
    editorText.value = result.content
    isGenerating.value = false
    isAiOpen.value = false
    navigate('journal')
    notify(result.provider === 'local-template' ? '已使用本地模板生成手账' : 'AI 已为你生成今日手账')
  } catch (error) {
    isGenerating.value = false
    notify(error.message)
  }
}

async function handleLogin() {
  loginError.value = ''
  try {
    await loginApi(loginAccount.value, loginPassword.value)
    isLoggedIn.value = true
    activePage.value = 'home'
  } catch (error) {
    loginError.value = error.message
  }
}

async function handleRegister() {
  loginError.value = ''
  if (!registerEmail.value.includes('@')) {
    loginError.value = '请输入有效的邮箱地址'
    return
  }
  try {
    await registerApi(loginAccount.value.trim(), registerEmail.value.trim(), loginPassword.value)
    isLoggedIn.value = true
    activePage.value = 'home'
  } catch (error) {
    loginError.value = error.message
  }
}

function toggleAuthMode() {
  authMode.value = authMode.value === 'login' ? 'register' : 'login'
  loginError.value = ''
  if (authMode.value === 'register' && loginAccount.value === 'demo') {
    loginAccount.value = ''
    loginPassword.value = ''
  }
}

async function handleSaveJournal() {
  try {
    await saveJournal({
      title: editorTitle.value, content: editorText.value, mood: mood.value,
      locationName: editorLocation.value, latitude: editorLatitude.value, longitude: editorLongitude.value,
    })
    notify('手账已保存到 SQLite')
  } catch (error) {
    notify(error.message)
  }
}

function handleLogout() {
  logoutApi()
  activePage.value = 'home'
  isLoggedIn.value = false
}

/** 打开系统文件选择器，选中后上传并自动进行图片理解。 */
function openPhotoPicker() {
  photoInput.value?.click()
}

async function handlePhotoSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  isUploading.value = true
  uploadedPhotoUrl.value = URL.createObjectURL(file)
  try {
    notify('照片上传中…')
    const media = await uploadMedia(file)
    notify('华为云正在理解照片…')
    const result = await analyzePhoto(media.id)
    if (result.suggested_caption && !editorText.value.includes(result.suggested_caption)) {
      editorText.value += `\n\n${result.suggested_caption}`
    }
    notify(`图片分析完成 · ${result.tags.slice(0, 3).join(' · ')}`)
  } catch (error) {
    notify(error.message)
  } finally {
    isUploading.value = false
    event.target.value = ''
  }
}

/** 第一次点击开始录音，第二次点击停止并上传。 */
async function toggleVoiceRecording() {
  if (isRecording.value) return mediaRecorder?.stop()
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    recordingSeconds.value = 0
    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = (event) => event.data.size && audioChunks.push(event.data)
    mediaRecorder.onstop = async () => {
      clearInterval(recordingTimer)
      stream.getTracks().forEach((track) => track.stop())
      isRecording.value = false
      const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' })
      const file = new File([blob], `voice-${Date.now()}.webm`, { type: blob.type })
      try {
        await uploadMedia(file, { durationSeconds: recordingSeconds.value })
        notify(`声音明信片已保存 · ${recordingSeconds.value}秒`)
      } catch (error) {
        notify(error.message)
      }
    }
    mediaRecorder.start()
    isRecording.value = true
    recordingTimer = setInterval(() => recordingSeconds.value += 1, 1000)
    notify('正在录音，再次点击即可结束')
  } catch (error) {
    notify(error.name === 'NotAllowedError' ? '需要允许麦克风权限才能录音' : '当前设备无法录音')
  }
}

/** 获取浏览器位置，并通过百度 JS API 写入手账地点。 */
async function recordCurrentLocation() {
  try {
    notify('正在获取当前位置…')
    const result = await locateTravelMoment()
    applyLocatedPosition(result)
    notify(`位置已记录：${result.name}`)
  } catch (error) {
    notify(error.message)
  }
}

function applyLocatedPosition(result) {
  editorLocation.value = result.name || result.address
  editorLatitude.value = result.latitude
  editorLongitude.value = result.longitude
}

/** 使用系统分享能力；桌面端不支持时复制手账文字。 */
async function shareJournal() {
  const shareData = { title: editorTitle.value, text: editorText.value }
  try {
    if (navigator.share) await navigator.share(shareData)
    else {
      await navigator.clipboard.writeText(`${editorTitle.value}\n\n${editorText.value}`)
      notify('手账内容已复制到剪贴板')
    }
  } catch (error) {
    if (error.name !== 'AbortError') notify('暂时无法分享，请稍后再试')
  }
}

function focusEditorText() {
  editorTextarea.value?.focus()
  notify('可以继续写下此刻的感受')
}

async function handleGenerateMemory() {
  try {
    notify('正在整理你的旅行片段…')
    generatedMemory.value = await generateMemoryApi()
    notify('九月旅行月刊已生成并保存')
  } catch (error) {
    notify(error.message)
  }
}

onBeforeUnmount(() => {
  clearInterval(recordingTimer)
  if (uploadedPhotoUrl.value) URL.revokeObjectURL(uploadedPhotoUrl.value)
})
</script>

<template>
  <div class="app-shell" :class="{ 'login-mode': !isLoggedIn }">
    <transition name="fade">
      <section v-if="!isLoggedIn" class="login-screen">
        <div class="login-visual">
          <div class="brand light"><span class="brand-mark"><Feather :size="19" /></span>旅页</div>
          <div class="login-quote">
            <span class="eyebrow">TRAVEL, WRITE, REMEMBER</span>
            <h1>把沿途的风，<br />写进时光里。</h1>
            <p>AI 陪你记录每一次出发，让散落的照片、声音与足迹，成为一本会呼吸的旅行手账。</p>
          </div>
          <div class="visual-caption"><MapPin :size="15" /> 38°12′N · 洱海西岸</div>
        </div>
        <div class="login-panel">
          <div class="login-card">
            <div class="mobile-brand brand"><span class="brand-mark"><Feather :size="19" /></span>旅页</div>
            <span class="section-kicker">{{ authMode === 'login' ? '欢迎回来' : '初次见面' }}</span>
            <h2>{{ authMode === 'login' ? '继续你的旅程' : '创建旅行档案' }}</h2>
            <p class="muted">{{ authMode === 'login' ? '登录后，所有珍贵回忆都会在这里重逢。' : '从今天起，把照片、声音与足迹收进同一本手账。' }}</p>
            <label>用户名 / 邮箱<input v-model="loginAccount" /></label>
            <label v-if="authMode === 'register'">邮箱<input v-model="registerEmail" type="email" /></label>
            <label>密码<div class="password"><input v-model="loginPassword" type="password" @keyup.enter="authMode === 'login' ? handleLogin() : handleRegister()" /><button v-if="authMode === 'login'" type="button" @click="loginError = '演示环境暂未接入邮件服务，可使用 demo / demo1234 登录'">忘记密码？</button></div></label>
            <p v-if="loginError" class="login-error">{{ loginError }}</p>
            <button class="primary full" @click="authMode === 'login' ? handleLogin() : handleRegister()">{{ authMode === 'login' ? '登录旅页' : '创建并开始记录' }} <ArrowRight :size="17" /></button>
            <div class="login-or"><span></span>或<span></span></div>
            <button class="wechat full" @click="loginError = '微信登录将在接入开放平台后启用'"><span>微</span> 微信快捷登录</button>
            <p class="signup">{{ authMode === 'login' ? '还没有账号？' : '已经有账号？' }}<button @click="toggleAuthMode">{{ authMode === 'login' ? '创建新账户' : '返回登录' }}</button></p>
          </div>
        </div>
      </section>
    </transition>

    <template v-if="isLoggedIn">
      <aside class="sidebar">
        <button class="brand" @click="navigate('home')"><span class="brand-mark"><Feather :size="19" /></span>旅页</button>
        <nav>
          <button v-for="item in navItems" :key="item.id" :class="{ active: activePage === item.id }" @click="navigate(item.id)">
            <component :is="item.icon" :size="19" stroke-width="1.8" />
            <span>{{ item.label }}</span>
          </button>
        </nav>
        <div class="sidebar-bottom">
          <button :class="{ active: activePage === 'profile' }" @click="navigate('profile')"><CircleUserRound :size="19" /><span>我的</span></button>
          <div class="profile-mini" @click="navigate('profile')">
            <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=96&auto=format&fit=crop" alt="林屿头像" />
            <div><strong>林屿</strong><small>世界漫游者 · Lv.8</small></div>
            <MoreHorizontal :size="17" />
          </div>
        </div>
      </aside>

      <main class="main">
        <input ref="photoInput" class="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp,image/gif" @change="handlePhotoSelected" />
        <header class="topbar">
          <div>
            <span class="date-line">{{ dateLine }}</span>
            <h1>{{ pageTitle }}</h1>
          </div>
          <div class="top-actions">
            <button class="icon-button" aria-label="搜索地点" @click="navigate('map')"><Search :size="20" /></button>
            <button class="weather" @click="notify('杭州 · 24°C · 多云转晴')"><CloudSun :size="19" /><span>24°</span><small>杭州</small></button>
            <button class="avatar" @click="navigate('profile')"><img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=96&auto=format&fit=crop" alt="用户头像" /></button>
          </div>
        </header>

        <transition name="page" mode="out-in">
          <div :key="activePage" class="page-content">
            <section v-if="activePage === 'home'" class="home-page">
              <article class="hero-card">
                <div class="hero-image"></div>
                <div class="hero-overlay"></div>
                <div class="hero-copy">
                  <span class="glass-tag"><Sun :size="14" /> 旅行中的第 4 天</span>
                  <h2>大理的风，<br />吹慢了时间。</h2>
                  <p><MapPin :size="15" /> 云南 · 大理白族自治州</p>
                </div>
                <button class="hero-cta" @click="navigate('journal')"><PenLine :size="18" /> 续写今日手账</button>
                <div class="hero-index">04 <span>/ 06</span></div>
              </article>

              <div class="quick-grid">
                <button class="quick-card photo" :disabled="isUploading" @click="openPhotoPicker">
                  <span class="quick-icon"><Camera :size="22" /></span>
                  <span><strong>{{ isUploading ? '照片处理中…' : '照片打卡' }}</strong><small>上传后由 AI 理解画面</small></span>
                  <ArrowRight :size="18" />
                </button>
                <button class="quick-card voice" :class="{ recording: isRecording }" @click="toggleVoiceRecording">
                  <span class="quick-icon"><Mic :size="22" /></span>
                  <span><strong>{{ isRecording ? `录音中 ${recordingSeconds}s` : '声音明信片' }}</strong><small>{{ isRecording ? '再次点击结束并保存' : '收藏旅途的声音' }}</small></span>
                  <ArrowRight :size="18" />
                </button>
                <button class="quick-card location" @click="recordCurrentLocation">
                  <span class="quick-icon"><LocateFixed :size="22" /></span>
                  <span><strong>记录位置</strong><small>{{ editorLocation }}</small></span>
                  <ArrowRight :size="18" />
                </button>
              </div>

              <div class="content-grid">
                <section class="today-story">
                  <div class="section-heading"><div><span class="section-kicker">TODAY'S MOMENTS</span><h3>今天的片段</h3></div><button @click="navigate('journal')">查看手账 <ArrowRight :size="15" /></button></div>
                  <div class="timeline">
                    <article>
                      <time>08:40</time><span class="timeline-dot"></span>
                      <div class="moment-photo morning"><span>喜洲古镇</span></div>
                      <div class="moment-copy"><span class="mood-label">清晨 · 晴</span><h4>稻田边的第一杯咖啡</h4><p>风里有新鲜稻谷的味道，白族阿婆在门口晒着刚染好的扎染布。</p><div class="meta"><MapPin :size="13" /> 喜洲镇 · 18.4 km</div></div>
                    </article>
                    <article>
                      <time>16:25</time><span class="timeline-dot"></span>
                      <div class="moment-photo lake"><span>环海西路</span></div>
                      <div class="moment-copy"><span class="mood-label">午后 · 微风</span><h4>沿着洱海骑向日落</h4><p>没有目的地，只跟着水面上跳动的光一直向前。</p><div class="meta"><Mic :size="13" /> 00:38 声音片段</div></div>
                    </article>
                  </div>
                </section>

                <aside class="ai-card">
                  <div class="ai-orb"><Sparkles :size="25" /></div>
                  <span class="section-kicker">AI TRAVEL MUSE</span>
                  <h3>今天的故事，<br />让我替你起笔。</h3>
                  <p>已整理 12 张照片、2 段语音与 8.6 公里足迹。</p>
                  <div class="ai-materials"><span><Camera :size="15" /> 12</span><span><Mic :size="15" /> 02</span><span><Route :size="15" /> 8.6km</span></div>
                  <button class="primary" @click="openAi"><WandSparkles :size="17" /> AI 生成今日手账</button>
                  <small>你可以随时修改生成内容</small>
                </aside>
              </div>
            </section>

            <section v-else-if="activePage === 'journal'" class="journal-page">
              <div class="editor-toolbar surface">
                <div class="back-group"><button class="icon-button" @click="navigate('home')"><ArrowLeft :size="19" /></button><span><strong>大理 · 第四日</strong><small>草稿已自动保存</small></span></div>
                <div class="toolbar-actions"><button @click="openAi"><Sparkles :size="16" /> AI 灵感</button><button @click="shareJournal"><Share2 :size="16" /> 分享</button><button class="primary" @click="handleSaveJournal"><Check :size="16" /> 完成</button></div>
              </div>
              <div class="editor-layout">
                <div class="editor-panel surface">
                  <div class="editor-date"><span>2026</span><strong>18</strong><div>AUG<br/>MON</div></div>
                  <input v-model="editorTitle" class="title-input" aria-label="手账标题" />
                  <div class="entry-meta"><span><MapPin :size="14" /> {{ editorLocation }}</span><span><CloudSun :size="14" /> 23°C 晴</span><span class="mood-dot"></span>{{ mood }}</div>
                  <div class="photo-collage" :class="`layout-${layoutStyle}`">
                    <div class="photo-main" :style="uploadedPhotoUrl ? { backgroundImage: `url(${uploadedPhotoUrl})` } : null"></div>
                    <div class="photo-stack"><div class="photo-small one"></div><div class="photo-small two"></div></div>
                    <span class="photo-note">风把云<br/>吹成了诗</span>
                  </div>
                  <textarea ref="editorTextarea" v-model="editorText" aria-label="手账正文"></textarea>
                  <div class="voice-note"><button @click="isPlaying = !isPlaying"><component :is="isPlaying ? Pause : Play" :size="15" fill="currentColor" /></button><div class="wave"><i v-for="n in 28" :key="n" :style="{ height: `${8 + (n * 7) % 18}px` }"></i></div><span>00:38</span></div>
                  <div class="handwritten">“ 不必赶路，去感受路。 ”</div>
                </div>
                <aside class="edit-controls surface">
                  <span class="section-kicker">EDITING TOOLS</span><h3>记录这一刻</h3>
                  <div class="tool-grid"><button :disabled="isUploading" @click="openPhotoPicker"><ImagePlus :size="21" />{{ isUploading ? '分析中' : '照片' }}</button><button :class="{ active: isRecording }" @click="toggleVoiceRecording"><Mic :size="21" />{{ isRecording ? `${recordingSeconds}s` : '语音' }}</button><button @click="recordCurrentLocation"><MapPin :size="21" />位置</button><button @click="focusEditorText"><PenLine :size="21" />文字</button></div>
                  <div class="control-section"><label>今日心情</label><div class="mood-row"><button v-for="item in ['松弛','雀跃','治愈']" :key="item" :class="{ active: mood === item }" @click="mood = item">{{ item }}</button></div></div>
                  <div class="control-section layout-choice"><label>页面排版</label><div><button v-for="item in ['collage','hero','grid']" :key="item" :class="{ active: layoutStyle === item }" @click="layoutStyle = item"><span></span></button></div></div>
                  <button class="ai-soft" @click="openAi"><WandSparkles :size="18" /><span><strong>AI 帮我续写</strong><small>根据照片与足迹生成</small></span><ArrowRight :size="16" /></button>
                </aside>
              </div>
            </section>

            <section v-else-if="activePage === 'map'" class="map-page">
              <div class="map-page-head">
                <div class="map-trip-tabs"><button v-for="(trip, index) in trips" :key="trip.city" :class="{ active: selectedTrip === index }" @click="selectTrip(index)"><span :style="{ background: trip.color }"></span>{{ trip.city }}</button></div>
                <div v-if="routeInfo" class="route-result"><Route :size="15" />{{ routeInfo.distance }} · {{ routeInfo.duration }}</div>
              </div>
              <TravelMap :trip="currentTrip" @notify="notify" @located="applyLocatedPosition" @route-info="routeInfo = $event" />
              <div class="trip-drawer">
                <div class="trip-info"><span class="pin-large" :style="{ background: currentTrip.color }"><Navigation :size="21" /></span><div><span>{{ currentTrip.province }} · {{ currentTrip.days }}</span><h2>{{ currentTrip.city }}，一场缓慢的相遇</h2><p>{{ currentTrip.date }} · 24 个旅行片段</p></div></div>
                <div class="trip-thumbs"><div class="thumb t1"></div><div class="thumb t2"></div><div class="thumb t3"></div><button @click="navigate('journal')">+21</button></div>
                <button class="outline-button" @click="navigate('journal')">打开这本手账 <ArrowRight :size="16" /></button>
              </div>
            </section>

            <section v-else-if="activePage === 'memories'" class="memories-page">
              <article class="memory-feature">
                <div class="memory-bg"></div><div class="memory-shade"></div>
                <div class="memory-content"><span class="glass-tag"><Sparkles :size="14" /> AI 本周精选</span><p class="memory-date">AUGUST · 2026</p><h2>在风抵达的地方，<br/>我们也抵达了自己。</h2><p>大理慢游 · 6 天 5 夜 · 48 个珍贵瞬间</p><button class="play-button" @click="isPlaying = !isPlaying"><component :is="isPlaying ? Pause : Play" :size="19" fill="currentColor" /> {{ isPlaying ? '暂停播放' : '播放时光影片' }}</button></div>
                <button class="heart" :class="{ liked }" @click="liked = !liked"><Heart :size="21" :fill="liked ? 'currentColor' : 'none'" /></button>
              </article>
              <div class="memory-section-head"><div><span class="section-kicker">TIME CAPSULE</span><h3>往年的今天</h3></div><button @click="notify('已展示全部往年旅行回忆')">查看全部 <ArrowRight :size="15" /></button></div>
              <div class="memory-grid">
                <article class="memory-card"><div class="memory-img m1"><span>2025</span></div><div><small>一年前 · 京都</small><h4>红叶落在哲学之道</h4><p>18 张照片 · 1 段语音</p></div></article>
                <article class="memory-card"><div class="memory-img m2"><span>2024</span></div><div><small>两年前 · 青岛</small><h4>去海边浪费一个下午</h4><p>26 张照片 · 3 个地点</p></div></article>
                <article class="create-memory" @click="handleGenerateMemory"><span><Sparkles :size="25" /></span><h4>{{ generatedMemory ? generatedMemory.title : '生成九月旅行月刊' }}</h4><p>{{ generatedMemory ? generatedMemory.description : 'AI 已为你整理 86 个旅行片段' }}</p><button>{{ generatedMemory ? '已保存，再次生成' : '立即生成' }} <ArrowRight :size="15" /></button></article>
              </div>
            </section>

            <section v-else class="profile-page">
              <div class="profile-hero surface">
                <div class="cover-pattern"></div><button class="settings" @click="notify('个人设置将在这里统一管理')"><Settings :size="18" /></button>
                <div class="profile-identity"><img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=240&auto=format&fit=crop" alt="林屿" /><div><span>世界漫游者 · Lv.8</span><h2>林屿</h2><p>在地图上写诗，在风景里生活。</p></div></div>
                <div class="profile-stats"><div><strong>12</strong><span>城市</span></div><div><strong>38</strong><span>手账</span></div><div><strong>1,286</strong><span>照片</span></div><div><strong>42.6k</strong><span>公里</span></div></div>
              </div>
              <div class="profile-columns">
                <section class="surface achievements"><div class="section-heading"><div><span class="section-kicker">ACHIEVEMENTS</span><h3>旅行勋章</h3></div><span>8 / 24</span></div><div class="badge-row"><div><span class="badge sage"><Compass :size="27" /></span><b>初见远方</b><small>首段旅程</small></div><div><span class="badge gold"><Sun :size="27" /></span><b>追光的人</b><small>10 次日出</small></div><div><span class="badge terra"><Footprints :size="27" /></span><b>漫步成诗</b><small>100 公里</small></div><div class="locked"><span class="badge"><Moon :size="27" /></span><b>星夜旅人</b><small>待解锁</small></div></div></section>
                <section class="surface preferences"><span class="section-kicker">PREFERENCES</span><h3>我的偏爱</h3><div class="pref-tags"><span>🌿 自然风光</span><span>🏛 人文古迹</span><span>☕ 城市漫游</span><span>📷 胶片摄影</span></div><button @click="notify('偏好设置已打开')">编辑旅行偏好 <ArrowRight :size="15" /></button></section>
              </div>
              <button class="logout" @click="handleLogout">退出登录</button>
            </section>
          </div>
        </transition>

        <nav class="mobile-nav">
          <button v-for="item in navItems" :key="item.id" :class="{ active: activePage === item.id }" @click="navigate(item.id)"><component :is="item.icon" :size="20" /><span>{{ item.label }}</span></button>
          <button :class="{ active: activePage === 'profile' }" @click="navigate('profile')"><CircleUserRound :size="20" /><span>我的</span></button>
        </nav>
      </main>

      <transition name="sheet">
        <div v-if="isAiOpen" class="sheet-wrap" @click.self="isAiOpen = false">
          <section class="ai-sheet">
            <div class="sheet-head"><div class="ai-orb small"><Sparkles :size="19" /></div><div><span class="section-kicker">AI TRAVEL MUSE</span><h3>把今天写成故事</h3></div><button class="icon-button" @click="isAiOpen = false"><X :size="19" /></button></div>
            <p>我会结合今天的照片、声音和足迹，帮你写出一篇保留个人语气的旅行手账。</p>
            <div class="material-preview"><div class="material-images"><span></span><span></span><span></span></div><div><strong>已读取今日素材</strong><small>12 张照片 · 2 段语音 · 8.6 公里</small></div><Check :size="18" /></div>
            <label class="prompt-label">还想告诉我什么？<textarea v-model="aiPrompt" placeholder="比如：想写得轻松一些，多描写傍晚的风…"></textarea></label>
            <div class="style-choice"><span>文字风格</span><button v-for="style in ['散文随笔','轻盈日常','电影旁白']" :key="style" :class="{ active: aiStyle === style }" @click="aiStyle = style">{{ style }}</button></div>
            <button class="primary full generate" :disabled="isGenerating" @click="generateJournal"><span v-if="isGenerating" class="spinner"></span><WandSparkles v-else :size="18" /> {{ isGenerating ? '正在翻阅你的旅程…' : '生成今日手账' }}</button>
          </section>
        </div>
      </transition>
      <transition name="toast"><div v-if="toast" class="toast"><Check :size="16" />{{ toast }}</div></transition>
    </template>
  </div>
</template>
