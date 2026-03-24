<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, onUnmounted, ref } from 'vue'
import { useStockStore } from '@/stores/stock'

const store = useStockStore()
let refreshInterval: number | null = null

// 判断是否为交易时间 (A股: 9:30-11:30, 13:00-15:00)
const isTradingHours = (): boolean => {
  const now = new Date()
  const hour = now.getHours()
  const minute = now.getMinutes()
  const time = hour * 60 + minute

  // 上午: 9:30-11:30
  const morningStart = 9 * 60 + 30  // 570
  const morningEnd = 11 * 60 + 30   // 690

  // 下午: 13:00-15:00
  const afternoonStart = 13 * 60   // 780
  const afternoonEnd = 15 * 60    // 900

  // 周末不交易
  const day = now.getDay()
  if (day === 0 || day === 6) return false

  return (time >= morningStart && time <= morningEnd) ||
         (time >= afternoonStart && time <= afternoonEnd)
}

// 获取刷新间隔 (交易时间30秒，非交易时间60秒)
const getRefreshInterval = (): number => {
  return isTradingHours() ? 30000 : 60000
}

// 开始自动刷新
const startAutoRefresh = () => {
  // 立即刷新一次
  store.fetchAllData()

  // 设置定时刷新
  const interval = getRefreshInterval()
  refreshInterval = window.setInterval(() => {
    store.fetchAllData()
    console.log(`数据已刷新 (间隔: ${interval / 1000}秒)`)
  }, interval)
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshInterval !== null) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// 应用加载时获取后端数据
onMounted(async () => {
  await store.fetchAllData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="min-h-screen bg-gray-900">
    <nav class="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <h1 class="text-2xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                📈 股票交易模拟系统
              </h1>
            </div>
            <div class="hidden md:block">
              <div class="ml-10 flex items-baseline space-x-4">
                <router-link 
                  to="/" 
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  概览
                </router-link>
                <router-link 
                  to="/portfolio" 
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  持仓
                </router-link>
                <router-link 
                  to="/charts" 
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  K 线图
                </router-link>
                <router-link
                  to="/analysis"
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  分析
                </router-link>
                <router-link
                  to="/backtest"
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  回测
                </router-link>
                <router-link
                  to="/news"
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  新闻
                </router-link>
                <router-link
                  to="/transactions"
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  记录
                </router-link>
                <router-link
                  to="/agent"
                  class="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  Agent
                </router-link>
              </div>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <div class="text-sm text-gray-400">
              <span class="inline-block w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
              系统运行中
            </div>
          </div>
        </div>
      </div>
    </nav>
    
    <main>
      <RouterView />
    </main>
    
    <footer class="bg-gray-800 border-t border-gray-700 mt-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <p class="text-center text-gray-400 text-sm">
          © 2026 股票交易模拟系统 | powered by Vue 3 + Vite
        </p>
      </div>
    </footer>
  </div>
</template>
