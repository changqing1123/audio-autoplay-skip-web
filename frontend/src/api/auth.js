import { apiClient } from './request'

export async function loginWithJwt(username, password) {
  const response = await apiClient.post('/auth/jwt/create/', {
    username,
    password,
  })
  return response.data
}

export async function fetchCurrentUser() {
  const response = await apiClient.get('/auth/users/me/')
  return response.data
}
