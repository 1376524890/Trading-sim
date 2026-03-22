<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStockStore } from '@/stores/stock'
import { 
  NewspaperIcon, 
  MagnifyingGlassCircleIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'

const store = useStockStore()
const searchQuery = ref('')
const selectedSentiment = ref<string>('all')
const sortBy = ref('latest')

const formattedDate = (date: Date) => {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const filteredNews = computed(() => {
  let news = [...store.news]
  
  // Filter by sentiment
  if (selectedSentiment.value !== 'all') {
    news = news.filter(n => n.sentiment === selectedSentiment.value)
  }
  
  // Filter by search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    news = news.filter(n => 
      n.title.toLowerCase().includes(query) ||
      n.summary.toLowerCase().includes(query) ||
      n.relatedSymbols.some(s => s.toLowerCase().includes(query))
    )
  }
  
  // Sort
  switch (sortBy.value) {
    case 'latest':
      news.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      break
    case 'oldest':
      news.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      break
    case 'positive':
      news.sort((a, b) => 
        (b.sentiment === 'positive' ? 1 : 0) - (a.sentiment === 'positive' ? 1 : 0)
      )
      break
    case 'negative':
      news.sort((a, b) => 
        (b.sentiment === 'negative' ? 1 : 0) - (a.sentiment === 'negative' ? 1 : 0)
      )
      break
  }
  
  return news
})

const sentimentCounts = computed(() => ({
  positive: store.news.filter(n => n.sentiment === 'positive').length,
  neutral: store.news.filter(n => n.sentiment === 'neutral').length,
  negative: store.news.filter(n => n.sentiment === 'negative').length
}))
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">新闻摘要</h1>
      <p class="text-gray-400">实时获取市场动态和财经新闻</p>
    </div>

    <!-- Sentiment Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="stat-card">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-400">利好消息</div>
            <div class="text-2xl font-bold text-green-400">{{ sentimentCounts.positive }}</div>
          </div>
          <div class="p-3 bg-green-900/50 rounded-lg">
            <span class="text-2xl">📈</span>
          </div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-400">中性消息</div>
            <div class="text-2xl font-bold text-blue-400">{{ sentimentCounts.neutral }}</div>
          </div>
          <div class="p-3 bg-blue-900/50 rounded-lg">
            <span class="text-2xl">➡️</span>
          </div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-400">利空消息</div>
            <div class="text-2xl font-bold text-red-400">{{ sentimentCounts.negative }}</div>
          </div>
          <div class="p-3 bg-red-900/50 rounded-lg">
            <span class="text-2xl">📉</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="card mb-6">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center space-x-4 flex-1">
          <!-- Search -->
          <div class="relative flex-1 max-w-md">
            <MagnifyingGlassCircleIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索新闻..."
              class="input pl-10"
            />
          </div>
          
          <!-- Sort -->
          <select 
            v-model="sortBy"
            class="input w-auto"
          >
            <option value="latest">最新发布</option>
            <option value="oldest">最早发布</option>
            <option value="positive">最利好</option>
            <option value="negative">最利空</option>
          </select>
        </div>
        
        <div class="text-sm text-gray-400">
          共 {{ filteredNews.length }} 条新闻
        </div>
      </div>
    </div>

    <!-- News Feed -->
    <div class="space-y-4">
      <div 
        v-for="article in filteredNews" 
        :key="article.id"
        class="card hover:shadow-2xl hover:shadow-primary-500/10 transition-all duration-300"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center space-x-2">
            <NewspaperIcon class="w-5 h-5 text-primary-400" />
            <span class="text-sm text-gray-400">{{ article.source }}</span>
            <span class="text-gray-600">•</span>
            <div class="flex items-center text-sm text-gray-400">
              <ClockIcon class="w-4 h-4 mr-1" />
              {{ formattedDate(article.timestamp) }}
            </div>
          </div>
          <span 
            :class="{
              'badge-success': article.sentiment === 'positive',
              'badge-danger': article.sentiment === 'negative',
              'badge-info': article.sentiment === 'neutral'
            }"
            class="badge"
          >
            {{ article.sentiment === 'positive' ? '利好' : article.sentiment === 'negative' ? '利空' : '中性' }}
          </span>
        </div>
        
        <h3 class="text-lg font-semibold text-white mb-2 hover:text-primary-400 cursor-pointer transition-colors">
          {{ article.title }}
        </h3>
        
        <p class="text-gray-300 mb-4 line-clamp-2">
          {{ article.summary }}
        </p>
        
        <div class="flex items-center justify-between pt-4 border-t border-gray-700">
          <div class="flex flex-wrap gap-2">
            <span class="text-xs text-gray-500">相关股票:</span>
            <div class="flex flex-wrap gap-1">
              <span 
                v-for="symbol in article.relatedSymbols" 
                :key="symbol"
                class="text-xs bg-primary-900/50 text-primary-300 px-2 py-1 rounded hover:bg-primary-800/50 transition-colors cursor-pointer"
              >
                {{ symbol }}
              </span>
            </div>
          </div>
          <button class="text-sm text-primary-400 hover:text-primary-300 transition-colors">
            查看详情 →
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="filteredNews.length === 0" class="text-center py-12">
      <NewspaperIcon class="w-16 h-16 text-gray-600 mx-auto mb-4" />
      <h3 class="text-xl font-medium text-gray-400 mb-2">暂无新闻</h3>
      <p class="text-gray-500">尝试调整筛选条件或搜索关键词</p>
    </div>
  </div>
</template>
