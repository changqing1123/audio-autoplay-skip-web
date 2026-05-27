<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { icons } from '../data/icons'
import {
  currentAudio,
  openAudio,
  playNextAudio,
  playPreviousAudio,
  seekTo,
  state,
  togglePlayback,
} from '../state/appState'

const route = useRoute()
const router = useRouter()

const audio = computed(() => currentAudio.value)
const playButtonIcon = computed(() => (state.isPlaying ? icons.controlPause : icons.controlPlay))

watch(
  () => [route.params.id, route.query.autoplay],
  async ([audioId, autoPlay]) => {
    if (audioId) {
      await openAudio(Number(audioId), autoPlay === '1')
    }
  },
  { immediate: true },
)

function goHome() {
  router.push({ name: 'home' })
}

function openSettings() {
  router.push({ name: 'settings' })
}

function handleSeek(event) {
  seekTo(Number(event.target.value))
}
</script>

<template>
  <div class="phone-page player-page">
    <header class="player-header">
      <h1>{{ audio?.category || '播放器' }}</h1>
    </header>

    <section v-if="audio" class="player-main" aria-label="播放器详情">
      <img class="player-cover" :src="audio.largeCover" alt="" />

      <div class="player-copy">
        <h2>{{ audio.title }}</h2>
        <time>{{ audio.date }}</time>
      </div>

      <div class="detail-progress" aria-label="播放进度">
        <div class="detail-progress-track">
          <span :style="{ width: `${audio.progress}%` }"></span>
        </div>
        <input
          class="detail-progress-range"
          type="range"
          min="0"
          :max="Math.max(audio.durationSeconds || state.duration || 0, 1)"
          :value="audio.currentTimeSeconds"
          step="1"
          @input="handleSeek"
        />
        <div class="detail-times">
          <span>{{ audio.currentTime }}</span>
          <span>{{ audio.duration }}</span>
        </div>
      </div>

      <p v-if="state.audioError" class="audio-error-tip player-audio-error">{{ state.audioError }}</p>

      <div class="player-controls" aria-label="播放控制">
        <button class="detail-skip-button" type="button" aria-label="上一首" @click="playPreviousAudio">
          <img :src="icons.controlPrev" alt="" />
        </button>
        <button class="detail-play-button" type="button" :aria-label="state.isPlaying ? '暂停' : '播放'" @click="togglePlayback">
          <img :src="playButtonIcon" alt="" />
        </button>
        <button class="detail-skip-button" type="button" aria-label="下一首" @click="playNextAudio">
          <img :src="icons.controlNext" alt="" />
        </button>
      </div>
    </section>

    <section v-else class="page-state" aria-label="空状态">没有可播放的音频</section>

    <nav class="bottom-nav detail-nav" aria-label="主导航">
      <button class="nav-button" type="button" aria-label="首页" @click="goHome">
        <img :src="icons.navHomeInactive" alt="" />
      </button>
      <button class="nav-button active" type="button" aria-label="播放器">
        <img :src="icons.navPlayerActive" alt="" />
      </button>
      <button class="nav-button" type="button" aria-label="设置" @click="openSettings">
        <img :src="icons.navSettingsInactive" alt="" />
      </button>
    </nav>
  </div>
</template>
