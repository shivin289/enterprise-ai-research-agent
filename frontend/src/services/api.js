/**
 * Central Axios client + typed-ish API calls. Every component talks to
 * the backend through this file only -- no stray fetch() calls scattered
 * around components.
 */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: API_BASE })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
    }
    return Promise.reject(error)
  },
)

// --- Auth ---
export async function register(email, password) {
  const { data } = await client.post('/api/auth/register', { email, password })
  localStorage.setItem('access_token', data.access_token)
  return data
}

export async function login(email, password) {
  const { data } = await client.post('/api/auth/login', { email, password })
  localStorage.setItem('access_token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('access_token')
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem('access_token'))
}

export async function getMe() {
  const { data } = await client.get('/api/auth/me')
  return data
}

// --- Research ---
export async function createResearch(query, depth = 'standard') {
  const { data } = await client.post('/api/research', { query, depth })
  return data
}

export async function listResearch() {
  const { data } = await client.get('/api/research')
  return data
}

export async function getResearchStatus(researchId) {
  const { data } = await client.get(`/api/research/${researchId}/status`)
  return data
}

export async function getResearchDetail(researchId) {
  const { data } = await client.get(`/api/research/${researchId}`)
  return data
}

export async function getSources(researchId) {
  const { data } = await client.get(`/api/research/${researchId}/sources`)
  return data
}

// --- Documents ---
export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post('/api/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function listDocuments() {
  const { data } = await client.get('/api/documents')
  return data
}

export default client
