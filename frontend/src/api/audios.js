import { apiClient } from './request'

export async function fetchAudios() {
  const response = await apiClient.get('/audios/')
  return response.data
}

export async function fetchAudioPlayUrl(audioId) {
  const response = await apiClient.get(`/audios/${audioId}/play-url/`)
  return response.data
}

export async function fetchListenedIds() {
  const response = await apiClient.get('/listened/ids/')
  return response.data
}

export async function fetchListenedList() {
  const response = await apiClient.get('/listened/')
  return response.data
}

export async function markAudioListened(audioId) {
  const response = await apiClient.post('/listened/mark/', {
    audio_id: audioId,
  })
  return response.data
}
