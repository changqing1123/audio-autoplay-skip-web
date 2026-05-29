import { computed, reactive } from 'vue'
import { fetchCurrentUser, loginWithJwt } from '../api/auth'
import {
  fetchAudioPlayUrl,
  fetchAudios,
  fetchListenedIds,
  fetchListenedList,
  markAudioListened,
} from '../api/audios'
import { defaultAudioArtwork } from '../data/audios'
import { formatDate, formatDuration, getProgressPercent, truncateText } from '../lib/formatters'

const ACCESS_TOKEN_KEY = 'juejin_access_token'
const REFRESH_TOKEN_KEY = 'juejin_refresh_token'
const CURRENT_AUDIO_KEY = 'juejin_current_audio_id'
const PROGRESS_CACHE_KEY = 'juejin_audio_progress_cache'
const SAVE_INTERVAL_KEY = 'juejin_save_interval'
const SHOW_LISTENED_KEY = 'juejin_show_listened'
const SELECTED_TAB_KEY = 'juejin_selected_tab'
const MINI_PLAYER_CLOSED_KEY = 'juejin_mini_player_closed'
const PLAYBACK_RATE_KEY = 'juejin_playback_rate'

export const playbackRates = [1, 1.5, 2, 2.5, 3]

function normalizePlaybackRate(rate) {
  const numericRate = Number(rate)
  return playbackRates.includes(numericRate) ? numericRate : 1
}

function getSavedPlaybackRate() {
  return normalizePlaybackRate(localStorage.getItem(PLAYBACK_RATE_KEY) || 1)
}

const state = reactive({
  initialized: false,
  authLoading: false,
  dataLoading: false,
  audioLoading: false,
  audioError: '',
  loginError: '',
  user: null,
  rawAudios: [],
  listenedIds: [],
  listenedItems: [],
  currentAudioId: Number(localStorage.getItem(CURRENT_AUDIO_KEY)) || null,
  currentTime: 0,
  duration: 0,
  isPlaying: false,
  saveInterval: Number(localStorage.getItem(SAVE_INTERVAL_KEY) || 15),
  showListened: localStorage.getItem(SHOW_LISTENED_KEY) === 'true',
  selectedTab: localStorage.getItem(SELECTED_TAB_KEY) || 'all',
  miniPlayerClosed: localStorage.getItem(MINI_PLAYER_CLOSED_KEY) === 'true',
  playbackRate: getSavedPlaybackRate(),
  progressCache: loadProgressCache(),
})

export { state }

let audioElement = null
let activeSourceAudioId = null
let activeLoadToken = 0
let nextLoadToken = 0
let lastProgressSavedAt = 0
let pendingAutoPlay = false

function loadProgressCache() {
  try {
    return JSON.parse(localStorage.getItem(PROGRESS_CACHE_KEY) || '{}')
  } catch {
    return {}
  }
}

function persistProgressCache() {
  localStorage.setItem(PROGRESS_CACHE_KEY, JSON.stringify(state.progressCache))
}

function persistCurrentAudioId(audioId) {
  if (audioId) {
    localStorage.setItem(CURRENT_AUDIO_KEY, String(audioId))
  } else {
    localStorage.removeItem(CURRENT_AUDIO_KEY)
  }
}

function persistSelectedTab(tabId) {
  localStorage.setItem(SELECTED_TAB_KEY, tabId)
}

function persistMiniPlayerClosed(value) {
  localStorage.setItem(MINI_PLAYER_CLOSED_KEY, String(value))
}

function setTokens(access, refresh) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function hasAccessToken() {
  return Boolean(localStorage.getItem(ACCESS_TOKEN_KEY))
}

function normalizeAudio(item) {
  return {
    id: item.id,
    filename: item.filename,
    uploadTime: item.upload_time,
    durationSeconds: Number(item.duration || 0),
    groupName: item.group_name || state.user?.business_group || '默认分组',
    groupWeight: Number(item.group_weight || 100),
    groupCoverUrl: item.group_cover_url || '',
    playUrl: item.play_url || '',
  }
}

function getSavedProgress(audioId) {
  return state.progressCache[String(audioId)] || { currentTime: 0, duration: 0 }
}

function getCurrentTimeForAudio(item) {
  if (item.id === state.currentAudioId) {
    return state.currentTime
  }
  return getSavedProgress(item.id).currentTime || 0
}

function getDurationForAudio(item) {
  if (item.id === state.currentAudioId && state.duration > 0) {
    return state.duration
  }
  return item.durationSeconds || getSavedProgress(item.id).duration || 0
}

function decorateAudio(item) {
  const listened = state.listenedIds.includes(item.id)
  const isCurrentAudio = item.id === state.currentAudioId
  const currentTimeSeconds = getCurrentTimeForAudio(item)
  const durationSeconds = getDurationForAudio(item)
  const progressPercent = listened && !isCurrentAudio ? 100 : getProgressPercent(currentTimeSeconds, durationSeconds)
  const artwork = item.groupCoverUrl
    ? { cover: item.groupCoverUrl, largeCover: item.groupCoverUrl }
    : defaultAudioArtwork
  const progressText = listened
    ? '已听完'
    : progressPercent > 0
      ? `已听${progressPercent}%`
      : ''

  return {
    ...item,
    ...artwork,
    title: item.filename,
    shortTitle: truncateText(item.filename, 14),
    date: formatDate(item.uploadTime),
    durationSeconds,
    duration: formatDuration(durationSeconds),
    currentTimeSeconds,
    currentTime: formatDuration(currentTimeSeconds),
    progress: progressPercent,
    progressText,
    listened,
    listenedText: progressText,
    category: item.groupName,
  }
}

function decorateListenedItem(item) {
  const artwork = item.group_cover_url
    ? { cover: item.group_cover_url, largeCover: item.group_cover_url }
    : defaultAudioArtwork

  return {
    id: item.id,
    title: item.filename,
    shortTitle: truncateText(item.filename, 14),
    filename: item.filename,
    uploadTime: item.upload_time,
    groupName: item.group_name || '',
    groupWeight: Number(item.group_weight || 100),
    playUrl: item.play_url || '',
    listenedTime: item.listened_time,
    date: formatDate(item.upload_time),
    listenedDate: formatDate(item.listened_time),
    listenedText: '已听完',
    ...artwork,
  }
}

function hasPlaybackHistory() {
  if (state.currentAudioId) {
    return true
  }
  return Object.keys(state.progressCache).length > 0
}

function chooseCurrentAudioId() {
  const persistedId = state.currentAudioId
  if (
    persistedId &&
    state.rawAudios.some((audio) => audio.id === persistedId) &&
    !state.listenedIds.includes(persistedId)
  ) {
    return persistedId
  }
  if (!hasPlaybackHistory()) {
    return null
  }
  const firstUnfinished = state.rawAudios.find((audio) => !state.listenedIds.includes(audio.id))
  return firstUnfinished?.id || state.rawAudios[0]?.id || null
}

function resetPlaybackState() {
  state.currentTime = 0
  state.duration = 0
  state.isPlaying = false
  state.audioError = ''
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchAudioPlayUrlWithRetry(audioId) {
  try {
    return await fetchAudioPlayUrl(audioId)
  } catch (error) {
    const status = error?.response?.status
    if (status && status < 500) {
      throw error
    }
    await sleep(250)
    return fetchAudioPlayUrl(audioId)
  }
}

function getCachedPlayUrl(audioId) {
  return state.rawAudios.find((audio) => audio.id === audioId)?.playUrl || ''
}

async function loadCurrentAudioSource(autoPlay = false) {
  const current = currentAudio.value
  if (!audioElement || !current) {
    return
  }

  if (activeSourceAudioId === current.id && audioElement.src) {
    if (autoPlay) {
      await playElement()
    }
    return
  }

  const loadToken = ++nextLoadToken
  activeLoadToken = loadToken
  if (audioElement.src) {
    audioElement.pause()
    audioElement.removeAttribute('src')
    audioElement.load()
  }
  state.audioLoading = true
  state.audioError = ''
  pendingAutoPlay = autoPlay

  try {
    const cachedPlayUrl = getCachedPlayUrl(current.id)
    const response = cachedPlayUrl ? null : await fetchAudioPlayUrlWithRetry(current.id)
    if (activeLoadToken !== loadToken) {
      return
    }
    const streamUrl = cachedPlayUrl || response?.data?.stream_url
    if (!streamUrl) {
      throw new Error('missing-stream-url')
    }
    activeSourceAudioId = current.id
    audioElement.src = streamUrl
    audioElement.load()
    applyPlaybackRate()
  } catch {
    if (activeLoadToken === loadToken) {
      activeSourceAudioId = null
      state.audioError = '播客音频流加载失败，请检查音频文件或后端接口'
      pendingAutoPlay = false
    }
  } finally {
    if (activeLoadToken === loadToken) {
      state.audioLoading = false
    }
  }
}

async function playElement() {
  if (!audioElement) {
    return
  }
  try {
    await audioElement.play()
    state.isPlaying = true
    state.audioError = ''
  } catch {
    state.isPlaying = false
    state.audioError = '浏览器阻止了自动播放，请再次点击播放按钮'
  }
}

function pauseElement() {
  if (!audioElement) {
    return
  }
  audioElement.pause()
  state.isPlaying = false
}

function applyPlaybackRate() {
  if (audioElement) {
    audioElement.playbackRate = state.playbackRate
  }
}

export const audios = computed(() => state.rawAudios.map(decorateAudio))
export const currentAudio = computed(() => audios.value.find((audio) => audio.id === state.currentAudioId) || null)
export const listenedAudios = computed(() => state.listenedItems.map(decorateListenedItem))
export const homeTabs = computed(() => {
  const tabs = [{ id: 'all', label: '所有播客' }]
  const groups = new Map()
  audios.value.forEach((audio) => {
    if (!audio.groupName) {
      return
    }
    const existing = groups.get(audio.groupName)
    if (!existing || audio.groupWeight < existing.weight) {
      groups.set(audio.groupName, {
        name: audio.groupName,
        weight: audio.groupWeight,
      })
    }
  })
  ;[...groups.values()].sort((left, right) => {
    if (left.weight !== right.weight) {
      return left.weight - right.weight
    }
    return left.name.localeCompare(right.name, 'zh-Hans')
  }).forEach((group) => {
    tabs.push({
      id: group.name,
      label: group.name,
    })
  })
  return tabs
})
export const visibleAudios = computed(() => {
  let items = audios.value
  if (!state.showListened) {
    items = items.filter((audio) => !audio.listened)
  }
  if (state.selectedTab !== 'all') {
    items = items.filter((audio) => audio.groupName === state.selectedTab)
  }
  return items
})
export const miniPlayerVisible = computed(() => {
  return Boolean(currentAudio.value) && hasPlaybackHistory() && !state.miniPlayerClosed
})
export const listenedCount = computed(() => state.listenedIds.length)
export const isAuthenticated = computed(() => Boolean(state.user) && hasAccessToken())

export function registerAudioElement(element) {
  audioElement = element
  applyPlaybackRate()
  if (audioElement && currentAudio.value) {
    loadCurrentAudioSource(false)
  }
}

export async function initializeAppState() {
  if (state.initialized) {
    return
  }
  if (hasAccessToken()) {
    try {
      await syncAuthenticatedState()
    } catch {
      clearSession()
    }
  }
  state.initialized = true
}

export async function syncAuthenticatedState() {
  state.dataLoading = true
  try {
    const [userData, audioData, listenedIdData, listenedListData] = await Promise.all([
      fetchCurrentUser(),
      fetchAudios(),
      fetchListenedIds(),
      fetchListenedList(),
    ])
    state.user = userData
    state.listenedIds = listenedIdData.data || []
    state.listenedItems = listenedListData.data || []
    state.rawAudios = (audioData.data || []).map(normalizeAudio)
    if (!homeTabs.value.some((tab) => tab.id === state.selectedTab)) {
      state.selectedTab = 'all'
      persistSelectedTab('all')
    }
    setCurrentAudioId(chooseCurrentAudioId(), false)
  } finally {
    state.dataLoading = false
  }
}

function getRequestErrorMessage(error) {
  const status = error?.response?.status
  if (status === 401) {
    return '用户名或密码错误'
  }
  if (status === 403) {
    return '当前账号没有权限登录'
  }
  if (status === 404) {
    return '登录接口不存在，请检查后端路由'
  }
  if (status) {
    return `登录请求失败（${status}）`
  }
  return '无法连接到后端，请确认 8000 服务已启动'
}

export async function login(username, password) {
  state.authLoading = true
  state.loginError = ''

  try {
    const tokenData = await loginWithJwt(username, password)
    setTokens(tokenData.access, tokenData.refresh)
  } catch (error) {
    clearTokens()
    state.loginError = getRequestErrorMessage(error)
    throw new Error('login-failed')
  }

  try {
    await syncAuthenticatedState()
  } catch (error) {
    clearTokens()
    state.loginError = error?.response?.status
      ? `登录成功，但初始化数据失败（${error.response.status}）`
      : '登录成功，但无法获取用户或播客数据'
    throw new Error('post-login-init-failed')
  } finally {
    state.authLoading = false
  }
}

export function clearSession() {
  clearTokens()
  state.user = null
  state.rawAudios = []
  state.listenedIds = []
  state.listenedItems = []
  state.currentAudioId = null
  state.selectedTab = 'all'
  state.miniPlayerClosed = false
  resetPlaybackState()
  activeSourceAudioId = null
  pendingAutoPlay = false
  if (audioElement) {
    audioElement.pause()
    audioElement.removeAttribute('src')
    audioElement.load()
  }
  persistCurrentAudioId(null)
  persistSelectedTab('all')
  persistMiniPlayerClosed(false)
}

export function logout() {
  clearSession()
}

export function updateSaveInterval(value) {
  state.saveInterval = Number(value)
  localStorage.setItem(SAVE_INTERVAL_KEY, String(value))
}

export function toggleShowListened() {
  state.showListened = !state.showListened
  localStorage.setItem(SHOW_LISTENED_KEY, String(state.showListened))
}

export function setPlaybackRate(rate) {
  state.playbackRate = normalizePlaybackRate(rate)
  localStorage.setItem(PLAYBACK_RATE_KEY, String(state.playbackRate))
  applyPlaybackRate()
}

export function setSelectedTab(tabId) {
  state.selectedTab = tabId
  persistSelectedTab(tabId)
}

export function closeMiniPlayer() {
  persistCurrentProgress()
  pauseElement()
  state.miniPlayerClosed = true
  persistMiniPlayerClosed(true)
}

export function reopenMiniPlayer() {
  state.miniPlayerClosed = false
  persistMiniPlayerClosed(false)
}

export function setCurrentAudioId(audioId, persist = true) {
  state.currentAudioId = audioId
  if (persist) {
    persistCurrentAudioId(audioId)
  }
}

export async function openAudio(audioId, autoPlay = false) {
  const previousAudioId = state.currentAudioId
  const shouldAutoPlay = autoPlay || (state.isPlaying && previousAudioId !== audioId)
  const hasCurrentSource = Boolean(audioElement && activeSourceAudioId === audioId && audioElement.src)
  const keepCurrentPlayback = previousAudioId === audioId && hasCurrentSource && !audioElement.ended
  if (previousAudioId && previousAudioId !== audioId) {
    persistCurrentProgress()
  }
  setCurrentAudioId(audioId)
  const saved = getSavedProgress(audioId)
  const replayFromBeginning = state.listenedIds.includes(audioId) && !keepCurrentPlayback
  state.currentTime = keepCurrentPlayback
    ? Number(audioElement.currentTime || state.currentTime || 0)
    : replayFromBeginning
      ? 0
      : saved.currentTime || 0
  state.duration = keepCurrentPlayback
    ? Number(audioElement.duration || state.duration || saved.duration || 0)
    : saved.duration || 0
  state.audioError = ''
  reopenMiniPlayer()
  if (replayFromBeginning && audioElement && activeSourceAudioId === audioId && audioElement.src) {
    audioElement.currentTime = 0
  }
  await loadCurrentAudioSource(shouldAutoPlay)
}

export async function togglePlayback() {
  if (!currentAudio.value) {
    const firstId = chooseCurrentAudioId()
    if (firstId) {
      await openAudio(firstId, true)
    }
    return
  }

  if (!audioElement || activeSourceAudioId !== currentAudio.value.id || !audioElement.src) {
    await loadCurrentAudioSource(true)
    return
  }

  if (state.isPlaying) {
    pauseElement()
  } else {
    await playElement()
  }
}

export async function playNextAudio() {
  const currentId = currentAudio.value?.id
  const nextAudio = state.rawAudios.find(
    (audio) => audio.id !== currentId && !state.listenedIds.includes(audio.id),
  )
  if (nextAudio) {
    await openAudio(nextAudio.id, true)
  } else {
    pauseElement()
  }
}

function findFirstUnfinishedAudio() {
  return state.rawAudios.find((audio) => !state.listenedIds.includes(audio.id)) || null
}

export async function playPreviousAudio() {
  if (!currentAudio.value) {
    return
  }
  const currentIndex = state.rawAudios.findIndex((audio) => audio.id === currentAudio.value.id)
  if (currentIndex <= 0) {
    return
  }
  await openAudio(state.rawAudios[currentIndex - 1].id, true)
}

export function seekTo(seconds) {
  if (!audioElement || !currentAudio.value) {
    return
  }
  const targetTime = Math.min(
    Math.max(0, Number(seconds) || 0),
    state.duration || currentAudio.value.durationSeconds || 0,
  )
  audioElement.currentTime = targetTime
  state.currentTime = targetTime
  persistCurrentProgress()
}

export function onLoadedMetadata() {
  if (!audioElement || !currentAudio.value) {
    return
  }
  applyPlaybackRate()
  const saved = getSavedProgress(currentAudio.value.id)
  const duration = Number(audioElement.duration || currentAudio.value.durationSeconds || saved.duration || 0)
  state.duration = duration
  if (state.listenedIds.includes(currentAudio.value.id)) {
    audioElement.currentTime = 0
    state.currentTime = 0
  } else if (saved.currentTime) {
    const resumeAt = Math.min(saved.currentTime, Math.max(0, duration - 1))
    audioElement.currentTime = resumeAt
    state.currentTime = resumeAt
  }
  if (pendingAutoPlay) {
    pendingAutoPlay = false
    playElement()
  }
}

function updateCurrentAudioDuration() {
  const current = currentAudio.value
  if (!current) {
    return
  }
  const target = state.rawAudios.find((audio) => audio.id === current.id)
  if (target) {
    target.durationSeconds = state.duration || target.durationSeconds
  }
}

export function onTimeUpdate() {
  if (!audioElement || !currentAudio.value) {
    return
  }
  state.currentTime = audioElement.currentTime
  state.duration = Number(audioElement.duration || state.duration || currentAudio.value.durationSeconds || 0)
  updateCurrentAudioDuration()
  const now = Date.now()
  if (now - lastProgressSavedAt >= state.saveInterval * 1000) {
    persistCurrentProgress()
    lastProgressSavedAt = now
  }
}

export function onPlay() {
  state.isPlaying = true
}

export function onPause() {
  state.isPlaying = false
  persistCurrentProgress()
}

export function onAudioError() {
  state.audioLoading = false
  state.isPlaying = false
  state.audioError = '播客播放失败，请确认文件格式和音频流是否可用'
}

function clearSavedProgress(audioId) {
  delete state.progressCache[String(audioId)]
  persistProgressCache()
}

export async function onEnded() {
  const finishedAudio = currentAudio.value
  if (!finishedAudio) {
    return
  }
  clearSavedProgress(finishedAudio.id)
  await markAudioListened(finishedAudio.id)
  await syncAuthenticatedState()
  const nextAudio = findFirstUnfinishedAudio()
  if (nextAudio) {
    await openAudio(nextAudio.id, true)
  } else {
    pauseElement()
  }
}

export function persistCurrentProgress() {
  const current = currentAudio.value
  if (!current || !audioElement || state.listenedIds.includes(current.id)) {
    return
  }
  state.progressCache[String(current.id)] = {
    currentTime: Number(audioElement.currentTime || state.currentTime || 0),
    duration: Number(audioElement.duration || state.duration || current.durationSeconds || 0),
  }
  persistProgressCache()
}
