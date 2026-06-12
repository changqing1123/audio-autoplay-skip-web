<script setup>
import { onMounted, ref } from 'vue'
import { RouterView } from 'vue-router'
import {
  initializeAppState,
  onAudioError,
  onEnded,
  onLoadedMetadata,
  onPause,
  onPlay,
  onAudioPlaying,
  onAudioStalled,
  onAudioSuspend,
  onAudioWaiting,
  onTimeUpdate,
  registerAudioElement,
} from './state/appState'

const audioRef = ref(null)

onMounted(async () => {
  registerAudioElement(audioRef.value)
  await initializeAppState()
})
</script>

<template>
  <main class="app-shell">
    <RouterView />
    <audio
      ref="audioRef"
      class="global-audio-element"
      preload="auto"
      playsinline
      webkit-playsinline="true"
      aria-hidden="true"
      @ended="onEnded"
      @error="onAudioError"
      @loadedmetadata="onLoadedMetadata"
      @pause="onPause"
      @play="onPlay"
      @playing="onAudioPlaying"
      @stalled="onAudioStalled"
      @suspend="onAudioSuspend"
      @timeupdate="onTimeUpdate"
      @waiting="onAudioWaiting"
    ></audio>
  </main>
</template>

