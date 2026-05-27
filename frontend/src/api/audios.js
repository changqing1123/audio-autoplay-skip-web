import { apiClient } from './request'

export async function fetchAudios() {
  const response = await apiClient.get('/audios/')
  return response.data
}

export async function fetchAudioBlob(audioId) {
  const response = await apiClient.get(`/audios/${audioId}/stream/`, {
    responseType: 'blob',
  })
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
