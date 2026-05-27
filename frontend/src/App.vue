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
      @ended="onEnded"
      @error="onAudioError"
      @loadedmetadata="onLoadedMetadata"
      @pause="onPause"
      @play="onPlay"
      @timeupdate="onTimeUpdate"
    ></audio>
  </main>
</template>
