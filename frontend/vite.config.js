import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 相对 base：让产物可托管到任意子路径(GitHub Pages 项目站 / 内网静态目录)
// 配合 hash 路由，刷新不会 404。
export default defineConfig({
  plugins: [vue()],
  base: './',
  server: {
    host: true, // 允许局域网访问，方便手机连同一 WiFi 调试
    port: 5173,
    proxy: {
      // 本地开发时把 /api 转发到后端，免去临时设置后端地址
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1500,
  },
})
