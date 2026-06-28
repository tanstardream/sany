import axios from 'axios'
import { ElMessage } from 'element-plus'

// 后端地址：由前端运行时选择(存 localStorage)，支持任意静态托管(GitHub Pages 等)。
let baseURL = localStorage.getItem('ff_backend_url') || ''

const http = axios.create({ baseURL, timeout: 15000 })

export function setBackend(url) {
  baseURL = (url || '').replace(/\/$/, '')
  http.defaults.baseURL = baseURL
  localStorage.setItem('ff_backend_url', baseURL)
}
export function getBackend() {
  return baseURL
}

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('ff_token')
  if (token) cfg.headers.Authorization = 'Bearer ' + token
  return cfg
})

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response) {
      const status = err.response.status
      const detail = err.response.data?.detail
      const msg = typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : err.message
      if (status === 401) {
        localStorage.removeItem('ff_token')
        if (!location.hash.includes('/login') && !location.hash.includes('/settings')) {
          location.hash = '#/login'
        }
      }
      ElMessage.error(msg)
    } else {
      ElMessage.error('网络错误：无法连接后端，请检查"后端设置"中的服务器地址')
    }
    return Promise.reject(err)
  }
)

export default http
