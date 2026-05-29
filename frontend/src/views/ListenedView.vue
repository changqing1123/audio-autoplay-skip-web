<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronLeft } from 'lucide-vue-next'
import { icons } from '../data/icons'
import { currentAudio, listenedAudios } from '../state/appState'

const router = useRouter()
const listenedList = computed(() => listenedAudios.value)

function backToSettings() {
  router.push({ name: 'settings' })
}

function goHome() {
  router.push({ name: 'home' })
}

function openCurrentPlayer() {
  if (!currentAudio.value) {
    return
  }
  router.push({ name: 'player', params: { id: currentAudio.value.id } })
}

function openPlayer(audio = currentAudio.value) {
  if (!audio) {
    return
  }
  router.push({ name: 'player', params: { id: audio.id } })
}
</script>

<template>
  <div class="phone-page listened-page">
    <header class="subpage-header">
      <button class="back-button" type="button" aria-label="返回设置" @click="backToSettings">
        <ChevronLeft :size="26" :stroke-width="2.6" />
      </button>
      <h1>已听播客</h1>
    </header>

    <section v-if="listenedList.length === 0" class="page-state" aria-label="空状态">
      当前还没有已听记录
    </section>
    <section v-else class="audio-list listened-audio-list" aria-label="已听播客列表">
      <article
        v-for="audio in listenedList"
        :key="audio.id"
        class="audio-item listened"
      >
        <button class="audio-cover-button" type="button" @click="openPlayer(audio)">
          <img class="audio-cover" :src="audio.cover" alt="" />
        </button>
        <button class="audio-info" type="button" @click="openPlayer(audio)">
          <h2>{{ audio.title }}</h2>
          <div class="audio-meta">
            <time>{{ audio.date }}</time>
            <span>{{ audio.listenedText }}</span>
          </div>
        </button>
        <button class="play-chip" type="button" :aria-label="`播放 ${audio.title}`" @click="openPlayer(audio)">
          <img :src="icons.playCircleOutline" alt="" />
        </button>
      </article>
    </section>

    <nav class="bottom-nav detail-nav" aria-label="主导航">
      <button class="nav-button" type="button" aria-label="首页" @click="goHome">
        <img :src="icons.navHomeInactive" alt="" />
      </button>
      <button class="nav-button" type="button" aria-label="播放器" @click="openCurrentPlayer">
        <img :src="icons.navPlayerInactive" alt="" />
      </button>
      <button class="nav-button active" type="button" aria-label="设置" @click="backToSettings">
        <img :src="icons.navSettingsActive" alt="" />
      </button>
    </nav>
  </div>
</template>
