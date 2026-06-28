import { onBeforeUnmount, onMounted, ref } from 'vue'

// 响应式断点：默认 768px 以下视为移动端。
// 每个使用它的组件各自订阅 matchMedia，互不影响。
export function useBreakpoint(max = 768) {
  const isMobile = ref(typeof window !== 'undefined' && window.innerWidth <= max)
  let mql = null
  let handler = null

  const update = () => {
    isMobile.value = window.innerWidth <= max
  }

  onMounted(() => {
    update()
    mql = window.matchMedia(`(max-width: ${max}px)`)
    handler = () => update()
    mql.addEventListener('change', handler)
  })

  onBeforeUnmount(() => {
    if (mql && handler) mql.removeEventListener('change', handler)
  })

  return { isMobile }
}
