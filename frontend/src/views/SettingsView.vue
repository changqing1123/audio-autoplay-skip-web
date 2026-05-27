<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  Eye,
  LockKeyhole,
  LogOut,
  Music,
  UserRound,
} from 'lucide-vue-next'
import { icons } from '../data/icons'
import {
  currentAudio,
  isAuthenticated,
  listenedCount,
  login,
  logout as clearSession,
  state,
  toggleShowListened,
  updateSaveInterval,
} from '../state/appState'

const router = useRouter()
const username = ref('')
const password = ref('')
const playbackSettingsOpen = ref(false)
const displayName = computed(() => state.user?.username || '未登录')
const groupName = computed(() => state.user?.business_group || '未分组')

async function submitLogin() {
  try {
    await login(username.value.trim(), password.value.trim())
    username.value = ''
    password.value = ''
    router.replace({ name: 'home' })
  } catch {
    password.value = ''
  }
}

function logout() {
  clearSession()
  router.push({ name: 'settings' })
}

function goHome() {
  router.push({ name: 'home' })
}

function openPlayer() {
  if (!currentAudio.value) {
    return
  }
  router.push({ name: 'player', params: { id: currentAudio.value.id } })
}

function openListened() {
  router.push({ name: 'listened' })
}
</script>

<template>
  <div class="phone-page settings-page">
    <template v-if="!isAuthenticated">
      <section class="login-panel" aria-label="登录">
        <div class="login-mark">
          <Music :size="34" :stroke-width="2.5" />
        </div>
        <h1>登录</h1>
        <p>登录后查看所属分组音频、已听列表和播放设置。</p>

        <form class="login-form" @submit.prevent="submitLogin">
          <label class="field-row">
            <UserRound :size="20" />
            <input v-model="username" type="text" autocomplete="username" placeholder="用户名" />
          </label>
          <label class="field-row">
            <LockKeyhole :size="20" />
            <input v-model="password" type="password" autocomplete="current-password" placeholder="密码" />
          </label>
          <p v-if="state.loginError" class="form-error">{{ state.loginError }}</p>
          <button class="primary-login-button" type="submit" :disabled="state.authLoading">
            {{ state.authLoading ? '登录中...' : '登录' }}
          </button>
        </form>
      </section>
    </template>

    <template v-else>
      <header class="settings-header">
        <h1>我的</h1>
      </header>

      <section class="profile-panel">
        <div class="profile-avatar">
          <UserRound :size="32" :stroke-width="2.4" />
        </div>
        <div class="profile-copy">
          <strong>{{ displayName }}</strong>
          <span>{{ groupName }} · 已听 {{ listenedCount }} 首</span>
        </div>
      </section>

      <section class="settings-section" aria-label="个人功能">
        <button class="settings-row menu-row" type="button" @click="openListened">
          <img class="setting-icon-img" :src="icons.iconListenedList" alt="" />
          <span>
            <strong>已听歌曲</strong>
            <small>查看完整已听列表</small>
          </span>
          <ChevronRight :size="18" />
        </button>
      </section>

      <section class="settings-section" aria-label="设置列表">
        <button class="settings-row menu-row" type="button" @click="playbackSettingsOpen = !playbackSettingsOpen">
          <img class="setting-icon-img square" :src="icons.iconSettingsGradient" alt="" />
          <span>
            <strong>播放设置</strong>
            <small>进度保存、已听显示、完成规则</small>
          </span>
          <ChevronDown v-if="playbackSettingsOpen" :size="18" />
          <ChevronRight v-else :size="18" />
        </button>

        <div v-if="playbackSettingsOpen" class="settings-foldout">
          <div class="settings-row">
            <Clock3 :size="22" />
            <span>
              <strong>进度保存间隔</strong>
              <small>{{ state.saveInterval }} 秒</small>
            </span>
          </div>
          <div class="interval-options" aria-label="进度保存间隔">
            <button
              v-for="value in [5, 15, 30]"
              :key="value"
              :class="{ active: state.saveInterval === value }"
              type="button"
              @click="updateSaveInterval(value)"
            >
              {{ value }}秒
            </button>
          </div>

          <button class="settings-row" type="button" @click="toggleShowListened">
            <Eye :size="22" />
            <span>
              <strong>首页显示已听歌曲</strong>
              <small>{{ state.showListened ? '显示' : '隐藏' }}</small>
            </span>
            <span class="toggle-pill" :class="{ active: state.showListened }"><i></i></span>
          </button>

          <div class="settings-row">
            <CheckCircle2 :size="22" />
            <span>
              <strong>播放完成规则</strong>
              <small>听到100%后标记</small>
            </span>
          </div>
        </div>

        <button class="logout-button" type="button" @click="logout">
          <LogOut :size="20" />
          退出登录
        </button>
      </section>
    </template>

    <nav class="bottom-nav detail-nav" aria-label="主导航">
      <button class="nav-button" type="button" aria-label="首页" @click="goHome">
        <img :src="icons.navHomeInactive" alt="" />
      </button>
      <button class="nav-button" type="button" aria-label="播放器" @click="openPlayer">
        <img :src="icons.navPlayerInactive" alt="" />
      </button>
      <button class="nav-button active" type="button" aria-label="设置">
        <img :src="icons.navSettingsActive" alt="" />
      </button>
    </nav>
  </div>
</template>
