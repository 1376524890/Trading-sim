<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStockStore } from '@/stores/stock'
import {
  ChartBarIcon,
  PlayIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  DocumentChartBarIcon
} from '@heroicons/vue/24/outline'

const store = useStockStore()

// 状态
const backtestResults = ref<any[]>([])
const strategies = ref<any[]>([])
const loading = ref(false)
const runningBacktest = ref(false)
const selectedStrategy = ref('ma_cross')
const selectedSymbol = ref('601398.SS')
const startDate = ref('')
const endDate = ref('')
const initialCash = ref(10000)

// 获取回测结果
const fetchBacktestResults = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/backtest/results?limit=20')
    const data = await response.json()
    backtestResults.value = data.results || []
  } catch (e) {
    console.error('获取回测结果失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取策略列表
const fetchStrategies = async () => {
  try {
    const response = await fetch('/api/backtest/strategies')
    const data = await response.json()
    if (data.success) {
      strategies.value = data.strategies
    }
  } catch (e) {
    console.error('获取策略列表失败:', e)
  }
}

// 运行回测
const runBacktest = async () => {
  runningBacktest.value = true
  try {
    const params = new URLSearchParams({
      symbol: selectedSymbol.value,
      strategy: selectedStrategy.value,
      initial_cash: initialCash.value.toString()
    })

    if (startDate.value) params.append('start_date', startDate.value)
    if (endDate.value) params.append('end_date', endDate.value)

    const response = await fetch(`/api/backtest/run?${params}`, {
      method: 'POST'
    })
    const data = await response.json()

    if (data.success) {
      await fetchBacktestResults()
    } else {
      alert('回测执行失败: ' + (data.error || '未知错误'))
    }
  } catch (e) {
    console.error('运行回测失败:', e)
    alert('运行回测失败')
  } finally {
    runningBacktest.value = false
  }
}

// 格式化数字
const formattedNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(num)
}

const formattedPercent = (num: number) => {
  return (num * 100).toFixed(2) + '%'
}

// 计算统计数据
const stats = computed(() => {
  if (backtestResults.value.length === 0) return null

  const totalReturn = backtestResults.value.reduce((sum, r) => sum + (r.total_return || 0), 0)
  const avgReturn = totalReturn / backtestResults.value.length

  const winners = backtestResults.value.filter(r => (r.total_return || 0) > 0).length
  const losers = backtestResults.value.filter(r => (r.total_return || 0) < 0).length

  return {
    totalCount: backtestResults.value.length,
    avgReturn,
    winRate: backtestResults.value.length > 0 ? (winners / backtestResults.value.length) * 100 : 0,
    winners,
    losers
  }
})

// 初始化日期
const initDates = () => {
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 3)

  endDate.value = end.toISOString().split('T')[0]
  startDate.value = start.toISOString().split('T')[0]
}

onMounted(() => {
  fetchBacktestResults()
  fetchStrategies()
  initDates()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">策略回测</h1>
      <p class="text-gray-400">运行和查看策略回测结果</p>
    </div>

    <!-- Statistics Cards -->
    <div v-if="stats" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="stat-card">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-sm text-gray-400">回测次数</div>
            <div class="text-2xl font-bold text-white">{{ stats.totalCount }}</div>
          </div>
          <div class="p-3 bg-blue-900/50 rounded-lg">
            <DocumentChartBarIcon class="w-6 h-6 text-blue-400" />
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-sm text-gray-400">平均收益率</div>
            <div class="text-2xl font-bold" :class="stats.avgReturn >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ stats.avgReturn >= 0 ? '+' : '' }}{{ formattedPercent(stats.avgReturn) }}
            </div>
          </div>
          <div class="p-3 bg-green-900/50 rounded-lg">
            <ArrowTrendingUpIcon class="w-6 h-6 text-green-400" />
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-sm text-gray-400">胜率</div>
            <div class="text-2xl font-bold text-blue-400">{{ stats.winRate.toFixed(1) }}%</div>
          </div>
          <div class="p-3 bg-purple-900/50 rounded-lg">
            <ChartBarIcon class="w-6 h-6 text-purple-400" />
          </div>
        </div>
        <div class="text-sm text-gray-400">{{ stats.winners }} 胜 / {{ stats.losers }} 负</div>
      </div>

      <div class="stat-card">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-sm text-gray-400">最近更新</div>
            <div class="text-lg font-bold text-white">
              {{ backtestResults[0]?.timestamp ? new Date(backtestResults[0].timestamp).toLocaleDateString('zh-CN') : '-' }}
            </div>
          </div>
          <div class="p-3 bg-yellow-900/50 rounded-lg">
            <ClockIcon class="w-6 h-6 text-yellow-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- Run Backtest Panel -->
    <div class="card mb-8">
      <div class="card-header">
        <h2 class="card-title">运行回测</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div>
          <label class="block text-sm text-gray-400 mb-2">股票代码</label>
          <select v-model="selectedSymbol" class="input w-full">
            <option v-for="holding in store.holdings" :key="holding.symbol" :value="holding.symbol">
              {{ holding.symbol }} - {{ holding.name }}
            </option>
            <option value="601398.SS">601398.SS - 工商银行</option>
            <option value="601318.SS">601318.SS - 中国平安</option>
            <option value="600036.SS">600036.SS - 招商银行</option>
          </select>
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-2">策略</label>
          <select v-model="selectedStrategy" class="input w-full">
            <option v-for="strategy in strategies" :key="strategy.name" :value="strategy.name">
              {{ strategy.display_name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-2">开始日期</label>
          <input v-model="startDate" type="date" class="input w-full" />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-2">结束日期</label>
          <input v-model="endDate" type="date" class="input w-full" />
        </div>

        <div class="flex items-end">
          <button
            @click="runBacktest"
            :disabled="runningBacktest"
            class="btn btn-primary w-full flex items-center justify-center"
          >
            <PlayIcon v-if="!runningBacktest" class="w-5 h-5 mr-2" />
            <span v-if="runningBacktest" class="animate-spin mr-2">⏳</span>
            {{ runningBacktest ? '运行中...' : '运行回测' }}
          </button>
        </div>
      </div>

      <!-- Strategy Description -->
      <div v-if="selectedStrategy" class="mt-4 p-4 bg-gray-700/50 rounded-lg">
        <div class="text-sm text-gray-300">
          {{ strategies.find(s => s.name === selectedStrategy)?.description }}
        </div>
      </div>
    </div>

    <!-- Results Table -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">回测结果</h2>
        <button @click="fetchBacktestResults" class="btn btn-secondary text-sm">
          刷新
        </button>
      </div>

      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
        <p class="text-gray-400">加载中...</p>
      </div>

      <div v-else-if="backtestResults.length === 0" class="text-center py-12">
        <DocumentChartBarIcon class="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h3 class="text-xl font-medium text-gray-400 mb-2">暂无回测结果</h3>
        <p class="text-gray-500">运行回测后将在此显示结果</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-gray-400 text-sm border-b border-gray-700">
              <th class="pb-3 font-medium">ID</th>
              <th class="pb-3 font-medium">股票</th>
              <th class="pb-3 font-medium">策略</th>
              <th class="pb-3 font-medium">回测期间</th>
              <th class="pb-3 font-medium text-right">初始资金</th>
              <th class="pb-3 font-medium text-right">最终资金</th>
              <th class="pb-3 font-medium text-right">收益率</th>
              <th class="pb-3 font-medium">时间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="result in backtestResults"
              :key="result.id"
              class="border-b border-gray-700 last:border-0 hover:bg-gray-700/50 transition-colors"
            >
              <td class="py-4">
                <span class="font-mono text-sm text-gray-400">#{{ result.id }}</span>
              </td>
              <td class="py-4">
                <div class="font-medium text-white">{{ result.symbol }}</div>
              </td>
              <td class="py-4">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-900 text-blue-300">
                  {{ result.strategy || 'ma_cross' }}
                </span>
              </td>
              <td class="py-4 text-sm text-gray-300">
                {{ result.start_date }} ~ {{ result.end_date }}
              </td>
              <td class="py-4 text-right text-gray-300">
                {{ formattedNumber(result.initial_cash) }}
              </td>
              <td class="py-4 text-right font-medium text-white">
                {{ formattedNumber(result.final_value) }}
              </td>
              <td class="py-4 text-right">
                <span
                  :class="result.total_return >= 0 ? 'text-green-400' : 'text-red-400'"
                  class="font-medium"
                >
                  {{ result.total_return >= 0 ? '+' : '' }}{{ formattedPercent(result.total_return) }}
                </span>
              </td>
              <td class="py-4 text-sm text-gray-400">
                {{ result.timestamp ? new Date(result.timestamp).toLocaleString('zh-CN') : '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
