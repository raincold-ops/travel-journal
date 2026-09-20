/**
 * 前端唯一的后端请求入口。
 * 页面组件只关心“登录、生成、保存”，令牌和错误处理都集中在这里。
 */
const API_BASE = '/api/v1'

async function request(path, options = {}) {
  const token = localStorage.getItem('travel01_token')
  const isFormData = options.body instanceof FormData
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (response.status === 204) return null
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || '请求失败，请稍后重试')
  return data
}

/** 使用用户输入的账号登录，并在浏览器本地保存令牌。 */
export async function login(account, password) {
  const result = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ account, password }),
  })
  localStorage.setItem('travel01_token', result.access_token)
  return result.user
}

/** 创建新账号；注册成功后与登录一样保存令牌。 */
export async function register(username, email, password) {
  const result = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  })
  localStorage.setItem('travel01_token', result.access_token)
  return result.user
}

/** 开发演示时自动登录预置账号，避免用户必须先手工输入。 */
async function ensureDemoLogin() {
  if (localStorage.getItem('travel01_token')) return
  await login('demo', 'demo1234')
}

/** 调用后端 AI 服务生成并更新演示手账。 */
export async function generateJournal(prompt, style = '散文随笔') {
  await ensureDemoLogin()
  return request('/ai/journal', {
    method: 'POST',
    body: JSON.stringify({ journal_id: 1, prompt, style, save_as_draft: true }),
  })
}

/** 把编辑器当前内容保存进 SQLite。 */
export async function saveJournal({ title, content, mood, locationName, latitude, longitude }) {
  await ensureDemoLogin()
  return request('/journals/1', {
    method: 'PATCH',
    body: JSON.stringify({
      title, content, mood, location_name: locationName, latitude, longitude, is_draft: false,
    }),
  })
}

/** 上传照片或语音，并关联到演示手账。 */
export async function uploadMedia(file, { durationSeconds } = {}) {
  await ensureDemoLogin()
  const form = new FormData()
  form.append('file', file)
  form.append('journal_id', '1')
  if (durationSeconds) form.append('duration_seconds', String(durationSeconds))
  return request('/media/upload', { method: 'POST', body: form })
}

/** 使用华为云视觉模型分析一张已上传照片。 */
export async function analyzePhoto(mediaId, prompt = '') {
  await ensureDemoLogin()
  return request(`/media/${mediaId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ prompt: prompt || '识别旅行场景、地标、氛围和适合写入手账的细节' }),
  })
}

/** 根据演示行程生成并保存回忆精选。 */
export async function generateMemory() {
  await ensureDemoLogin()
  return request('/memories/generate', {
    method: 'POST',
    body: JSON.stringify({ trip_id: 1, period: '2026年8月', style: '温柔电影感' }),
  })
}

/** 清理本机令牌，不会删除任何服务端数据。 */
export function logout() {
  localStorage.removeItem('travel01_token')
}
