import { defineStore } from 'pinia'
import http, { setBackend } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('ff_token') || '',
    user: JSON.parse(localStorage.getItem('ff_user') || 'null'),
    backend: localStorage.getItem('ff_backend_url') || '',
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    hasBackend: (s) => !!s.backend,
  },
  actions: {
    setBackendUrl(url) {
      setBackend(url)
      this.backend = localStorage.getItem('ff_backend_url') || ''
    },
    async login(username, password) {
      const { data } = await http.post('/api/auth/login', { username, password })
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('ff_token', this.token)
      localStorage.setItem('ff_user', JSON.stringify(this.user))
    },
    async fetchMe() {
      const { data } = await http.get('/api/auth/me')
      this.user = data
      localStorage.setItem('ff_user', JSON.stringify(data))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('ff_token')
      localStorage.removeItem('ff_user')
    },
  },
})
