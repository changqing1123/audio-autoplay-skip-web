<script setup>
import { computed } from 'vue'
import { X } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { icons } from '../data/icons'
import {
  closeMiniPlayer,
  currentAudio,
  homeTabs,
  miniPlayerVisible,
  playNextAudio,
  playPreviousAudio,
  seekTo,
  setSelectedTab,
  state,
  togglePlayback,
  visibleAudios,
} from '../state/appState'

const router = useRouter()

const homeAudios = computed(() => visibleAudios.value)
const miniPlayButtonIcon = computed(() => (state.isPlaying ? icons.controlPause : icons.controlPlay))

async function openPlayer(audio = currentAudio.value, autoPlay = false) {
  if (!audio) {
    return
  }
  const shouldAutoPlay = autoPlay || (state.isPlaying && currentAudio.value?.id !== audio.id)
  router.push({
    name: 'player',
    params: { id: audio.id },
    query: shouldAutoPlay ? { autoplay: '1' } : {},
  })
}

function openSettings() {
  router.push({ name: 'settings' })
}

function openCurrentPlayer() {
  if (!currentAudio.value) {
    return
  }
  router.push({ name: 'player', params: { id: currentAudio.value.id } })
}

function selectTab(tabId) {
  setSelectedTab(tabId)
}

function closeMiniBar() {
  closeMiniPlayer()
}

function handleMiniSeek(event) {
  seekTo(Number(event.target.value))
}
</script>

<template>
  <div class="phone-page home-page">
    <nav class="category-tabs" aria-label="音频分类">
      <button
        v-for="tab in homeTabs"
        :key="tab.id"
        class="tab-button"
        :class="{ active: state.selectedTab === tab.id }"
        type="button"
        @click="selectTab(tab.id)"
      >
        {{ tab.label }}
      </button>
    </nav>

    <section v-if="state.dataLoading" class="page-state" aria-label="加载中">
      正在加载音频列表...
    </section>
    <section v-else-if="homeAudios.length === 0" class="page-state" aria-label="空状态">
      当前分类下还没有可播放的音频
    </section>
    <section v-else class="audio-list" aria-label="音频列表">
      <article
        v-for="audio in homeAudios"
        :key="audio.id"
        class="audio-item"
        :class="{ listened: audio.listened }"
        @click="openPlayer(audio, true)"
      >
        <button class="audio-cover-button" type="button" @click.stop="openPlayer(audio, true)">
          <img class="audio-cover" :src="audio.cover" alt="" />
        </button>
        <button class="audio-info" type="button" @click.stop="openPlayer(audio, true)">
          <h2>{{ audio.title }}</h2>
          <div class="audio-meta">
            <time>{{ audio.date }}</time>
            <span v-if="audio.progressText">{{ audio.progressText }}</span>
          </div>
        </button>
        <button class="play-chip" type="button" :aria-label="`播放 ${audio.title}`" @click.stop="openPlayer(audio, true)">
          <img :src="icons.playCircleOutline" alt="" />
        </button>
      </article>
    </section>

    <p v-if="state.audioError" class="audio-error-tip">{{ state.audioError }}</p>

    <div class="bottom-stack">
      <div
        v-if="miniPlayerVisible && currentAudio"
        class="mini-player"
        aria-label="打开播放器详情"
        @click="openPlayer()"
      >
        <div class="play-progress"><span :style="{ width: `${currentAudio.progress}%` }"></span></div>
        <input
          class="mini-progress-range"
          type="range"
          min="0"
          :max="Math.max(currentAudio.durationSeconds || state.duration || 0, 1)"
          :value="currentAudio.currentTimeSeconds"
          step="1"
          @input.stop="handleMiniSeek"
          @click.stop
        />
        <button class="close-player" type="button" aria-label="关闭播放器" @click.stop="closeMiniBar">
          <X :size="18" />
        </button>
        <img class="mini-cover" :src="currentAudio.cover" alt="" />
        <span class="mini-info">
          <strong>{{ currentAudio.shortTitle }}</strong>
          <span>{{ currentAudio.date }}</span>
        </span>
        <span class="mini-controls" aria-label="播放控制">
          <button class="icon-button" type="button" aria-label="上一首" @click.stop="playPreviousAudio">
            <img :src="icons.controlPrev" alt="" />
          </button>
          <button class="main-play-button" type="button" :aria-label="state.isPlaying ? '暂停' : '播放'" @click.stop="togglePlayback">
            <img :src="miniPlayButtonIcon" alt="" />
          </button>
          <button class="icon-button" type="button" aria-label="下一首" @click.stop="playNextAudio">
            <img :src="icons.controlNext" alt="" />
          </button>
        </span>
      </div>

      <nav class="bottom-nav" aria-label="主导航">
        <button class="nav-button active" type="button" aria-label="首页">
          <img :src="icons.navHomeActive" alt="" />
        </button>
        <button class="nav-button" type="button" aria-label="播放器" @click="openCurrentPlayer">
          <img :src="icons.navPlayerInactive" alt="" />
        </button>
        <button class="nav-button" type="button" aria-label="设置" @click="openSettings">
          <img :src="icons.navSettingsInactive" alt="" />
        </button>
      </nav>
    </div>
  </div>
</template>
