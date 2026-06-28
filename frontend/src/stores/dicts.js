import { defineStore } from 'pinia'
import http from '../api'

// 字典数据缓存：避免每次切换页面、每次 DictSelect 挂载都重新请求字典，
// 显著减少切页时的 API 往返（后端经 Cloudflare 隧道延迟较高）。
const TTL = 10 * 60 * 1000 // 缓存 10 分钟

export const useDictStore = defineStore('dicts', {
  state: () => ({ cache: {} }), // { [dtype]: { items, ts } }
  actions: {
    // 返回启用中的字典项（active=true）。force=true 强制刷新。
    async get(type, force = false) {
      const c = this.cache[type]
      const fresh = c && Date.now() - c.ts < TTL
      if (c && fresh && !force) return c.items
      const { data } = await http.get(`/api/dicts/${type}`, { params: { active: true } })
      this.cache[type] = { items: data, ts: Date.now() }
      return data
    },
    invalidate(type) {
      delete this.cache[type]
    },
    invalidateAll() {
      this.cache = {}
    },
  },
})
