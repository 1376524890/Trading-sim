<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useStockStore } from '@/stores/stock'

const store = useStockStore()

// 应用加载时获取后端数据
onMounted(async () => {
  await store.fetchAllData()
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
