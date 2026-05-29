<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { icons } from '../data/icons'
import {
  currentAudio,
  openAudio,
  playNextAudio,
  playPreviousAudio,
  playbackRates,
  seekTo,
  setPlaybackRate,
  state,
  togglePlayback,
} from '../state/appState'

const route = useRoute()
const router = useRouter()

const audio = computed(() => currentAudio.value)
const playButtonIcon = computed(() => (state.isPlaying ? icons.controlPause : icons.controlPlay))
const speedMenuOpen = ref(false)

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

function formatPlaybackRate(rate) {
  return Number.isInteger(rate) ? String(rate) : String(rate)
}

function toggleSpeedMenu() {
  speedMenuOpen.value = !speedMenuOpen.value
}

function choosePlaybackRate(rate) {
  setPlaybackRate(rate)
  speedMenuOpen.value = false
}
</script>

<template>
  <div class="phone-page player-page">
    <section v-if="audio" class="player-main" aria-label="播放器详情">
      <img class="player-cover" :src="audio.largeCover" alt="" />

      <div class="player-copy">
        <h2>{{ audio.title }}</h2>
        <time>{{ audio.date }}</time>
      </div>

      <div class="detail-progress" aria-label="播放进度">
        <div class="detail-progress-head" aria-label="播放倍速">
          <div class="playback-rate-menu">
            <button class="playback-rate-trigger" type="button" @click="toggleSpeedMenu">
              {{ formatPlaybackRate(state.playbackRate) }}倍速
            </button>
            <div v-if="speedMenuOpen" class="playback-rate-options">
              <button
                v-for="rate in playbackRates"
                :key="rate"
                class="playback-rate-option"
                :class="{ active: state.playbackRate === rate }"
                type="button"
                @click="choosePlaybackRate(rate)"
              >
                {{ formatPlaybackRate(rate) }}倍速
              </button>
            </div>
          </div>
        </div>
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
        <button class="detail-skip-button" type="button" aria-label="上一期" @click="playPreviousAudio">
          <img :src="icons.controlPrev" alt="" />
        </button>
        <button class="detail-play-button" type="button" :aria-label="state.isPlaying ? '暂停' : '播放'" @click="togglePlayback">
          <img :src="playButtonIcon" alt="" />
        </button>
        <button class="detail-skip-button" type="button" aria-label="下一期" @click="playNextAudio">
          <img :src="icons.controlNext" alt="" />
        </button>
      </div>
    </section>

    <section v-else class="page-state" aria-label="空状态">没有可播放的播客</section>

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
