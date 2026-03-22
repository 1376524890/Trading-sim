<script setup lang="ts">
import { computed, ref } from 'vue'
import { useStockStore } from '@/stores/stock'

const store = useStockStore()

// 操作状态
const isOperating = ref(false)
const operationMessage = ref('')
const showResult = ref(false)

const formattedNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(num)
}

const portfolioStats = computed(() => {
  const totalCost = store.holdings.reduce((sum, h) => sum + h.costBasis, 0)
  const totalMarket = store.holdings.reduce((sum, h) => sum + h.marketValue, 0)
  const totalGain = totalMarket - totalCost
  const gainPercent = totalCost > 0 ? (totalGain / totalCost) * 100 : 0

  return {
    totalCost,
    totalMarket,
    totalGain,
    gainPercent
  }
})

const sortKey = computed(() => 'marketValue' as const)
const sortOrder = computed(() => 'desc' as const)

const sortedHoldings = computed(() => {
  return [...store.holdings].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]
    return sortOrder.value === 'desc' ? (bVal > aVal ? 1 : -1) : (aVal > bVal ? 1 : -1)
  })
})

// 使用store中的stockPerformance（从持仓计算得出）
const stockPerformance = computed(() => store.stockPerformance)

// 操作处理
const handleOperation = async (operation: () => Promise<any>, operationName: string) => {
  isOperating.value = true
  operationMessage.value = `正在${operationName}...`
  showResult.value = true

  try {
    const result = await operation()
    operationMessage.value = result.message || `${operationName}成功`
    await store.fetchAllData()
  } catch (error: any) {
    operationMessage.value = `${operationName}失败: ${error.message || '未知错误'}`
  } finally {
    isOperating.value = false
    setTimeout(() => { showResult.value = false }, 3000)
  }
}

const handleInitialBuild = () => handleOperation(store.initialBuild, '初始建仓')
const handleRebalance = () => handleOperation(store.rebalance, '调仓')
const handleAutoRun = () => handleOperation(store.autoRun, '自动运行')
const handleCheckStopLoss = () => handleOperation(store.checkStopLoss, '检查止损止盈')
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">持仓管理</h1>
      <p class="text-gray-400">查看和管理您的投资组合</p>
    </div>

    <!-- Control Panel -->
    <div class="card mb-8">
      <div class="card-header">
        <h2 class="card-title">投资控制面板</h2>
      </div>
      <div class="p-4">
        <!-- 操作结果提示 -->
        <div v-if="showResult" class="mb-4 p-3 rounded-lg" :class="isOperating ? 'bg-blue-500/20 text-blue-300' : 'bg-green-500/20 text-green-300'">
          <div class="flex items-center">
            <svg v-if="isOperating" class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ operationMessage }}</span>
          </div>
        </div>

        <!-- 按钮组 -->
        <div class="flex flex-wrap gap-3">
          <button
            @click="handleInitialBuild"
            :disabled="isOperating"
            class="btn-primary"
            title="根据配置自动建仓，分散投资于多个板块"
          >
            <span class="flex items-center">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              初始建仓
            </span>
          </button>

          <button
            @click="handleAutoRun"
            :disabled="isOperating"
            class="btn-primary"
            title="自动运行投资流程：检查止损止盈、调仓"
          >
            <span class="flex items-center">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              自动运行
            </span>
          </button>

          <button
            @click="handleRebalance"
            :disabled="isOperating"
            class="btn-secondary"
            title="根据当前市场情况调整仓位"
          >
            <span class="flex items-center">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              调仓
            </span>
          </button>

          <button
            @click="handleCheckStopLoss"
            :disabled="isOperating"
            class="btn-secondary"
            title="检查持仓是否触发止损或止盈"
          >
            <span class="flex items-center">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
              </svg>
              止损止盈
            </span>
          </button>

          <button
            @click="store.fetchAllData"
            :disabled="isOperating || store.loading"
            class="btn-secondary"
            title="刷新数据"
          >
            <span class="flex items-center">
              <svg class="w-5 h-5 mr-2" :class="store.loading ? 'animate-spin' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              刷新数据
            </span>
          </button>
        </div>

        <!-- 系统信息 -->
        <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div class="bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-400">总资产</div>
            <div class="text-lg font-bold text-white">{{ formattedNumber(store.stats.totalEquity) }}</div>
          </div>
          <div class="bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-400">现金</div>
            <div class="text-lg font-bold text-green-400">{{ formattedNumber(store.stats.cash) }}</div>
          </div>
          <div class="bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-400">持仓数量</div>
            <div class="text-lg font-bold text-purple-400">{{ store.holdings.length }} 只</div>
          </div>
          <div class="bg-gray-700/50 rounded-lg p-3">
            <div class="text-gray-400">总收益</div>
            <div class="text-lg font-bold" :class="store.stats.totalGain >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ store.stats.totalGain >= 0 ? '+' : '' }}{{ formattedNumber(store.stats.totalGain) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Portfolio Summary -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="stat-card">
        <p class="stat-label">总市值</p>
        <p class="stat-value text-white">{{ formattedNumber(portfolioStats.totalMarket) }}</p>
        <p class="text-sm text-gray-400 mt-1">占总权益的 {{ ((portfolioStats.totalMarket / store.stats.totalEquity) * 100).toFixed(1) }}%</p>
      </div>
      
      <div class="stat-card">
        <p class="stat-label">总成本</p>
        <p class="stat-value text-blue-400">{{ formattedNumber(portfolioStats.totalCost) }}</p>
        <p class="text-sm text-gray-400 mt-1">持仓成本总额</p>
      </div>
      
      <div class="stat-card">
        <p class="stat-label">总盈亏</p>
        <p class="stat-value" :class="portfolioStats.totalGain >= 0 ? 'text-green-400' : 'text-red-400'">
          {{ portfolioStats.totalGain >= 0 ? '+' : '' }}{{ formattedNumber(portfolioStats.totalGain) }}
        </p>
        <p class="text-sm" :class="portfolioStats.gainPercent >= 0 ? 'text-green-400' : 'text-red-400'">
          {{ portfolioStats.gainPercent >= 0 ? '+' : '' }}{{ portfolioStats.gainPercent.toFixed(2) }}%
        </p>
      </div>
      
      <div class="stat-card">
        <p class="stat-label">持仓数量</p>
        <p class="stat-value text-purple-400">{{ store.holdings.length }}</p>
        <p class="text-sm text-gray-400 mt-1">只股票</p>
      </div>
    </div>

    <!-- Holdings Table -->
    <div class="card mb-8">
      <div class="card-header">
        <h2 class="card-title">持仓明细</h2>
        <div class="flex items-center space-x-4">
          <select v-model="sortKey" class="input w-auto text-sm">
            <option value="marketValue">市值从高到低</option>
            <option value="gainLoss">盈亏从高到低</option>
            <option value="gainLossPercent">涨幅从高到低</option>
          </select>
        </div>
      </div>
      
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-gray-400 text-sm border-b border-gray-700">
              <th class="pb-3 font-medium">股票信息</th>
              <th class="pb-3 font-medium text-right">持股数量</th>
              <th class="pb-3 font-medium text-right">平均成本</th>
              <th class="pb-3 font-medium text-right">当前价格</th>
              <th class="pb-3 font-medium text-right">市值</th>
              <th class="pb-3 font-medium text-right">盈亏金额</th>
              <th class="pb-3 font-medium text-right">盈亏比例</th>
              <th class="pb-3 font-medium text-right">占比</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="holding in sortedHoldings" 
              :key="holding.symbol"
              class="border-b border-gray-700 last:border-0 hover:bg-gray-700/50 transition-colors"
            >
              <td class="py-4">
                <div>
                  <div class="font-medium text-white text-lg">{{ holding.symbol }}</div>
                  <div class="text-sm text-gray-400">{{ holding.name }}</div>
                </div>
              </td>
              <td class="py-4 text-right">{{ holding.shares.toLocaleString() }}</td>
              <td class="py-4 text-right">{{ formattedNumber(holding.avgPrice) }}</td>
              <td class="py-4 text-right">{{ formattedNumber(holding.currentPrice) }}</td>
              <td class="py-4 text-right">{{ formattedNumber(holding.marketValue) }}</td>
              <td class="py-4 text-right">
                <span :class="holding.gainLoss >= 0 ? 'text-green-400' : 'text-red-400'" class="font-medium">
                  {{ holding.gainLoss >= 0 ? '+' : '' }}{{ formattedNumber(holding.gainLoss) }}
                </span>
              </td>
              <td class="py-4 text-right">
                <span :class="holding.gainLossPercent >= 0 ? 'text-green-400' : 'text-red-400'" class="font-medium">
                  {{ holding.gainLossPercent >= 0 ? '+' : '' }}{{ holding.gainLossPercent.toFixed(2) }}%
                </span>
              </td>
              <td class="py-4 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <div class="w-16 bg-gray-700 rounded-full h-1.5">
                    <div 
                      class="h-1.5 rounded-full" 
                      :class="holding.gainLossPercent >= 0 ? 'bg-green-500' : 'bg-red-500'"
                      :style="{ width: `${Math.min(Math.abs(holding.gainLossPercent), 100)}%` }"
                    ></div>
                  </div>
                  <span class="text-sm text-gray-400">{{ ((holding.marketValue / portfolioStats.totalMarket) * 100).toFixed(1) }}%</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Performance Summary -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Stock Performance -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">个股表现</h2>
        </div>
        <div class="space-y-4">
          <div 
            v-for="stock in stockPerformance" 
            :key="stock.symbol"
            class="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 bg-gradient-to-br from-gray-600 to-gray-700 rounded-lg flex items-center justify-center font-bold text-white">
                {{ stock.symbol[0] }}
              </div>
              <div>
                <div class="font-medium text-white">{{ stock.symbol }}</div>
                <div class="text-sm text-gray-400">{{ stock.name }}</div>
              </div>
            </div>
            <div class="text-right">
              <div class="font-medium text-white">{{ stock.allocation }}%</div>
              <div :class="stock.change >= 0 ? 'text-green-400' : 'text-red-400'" class="text-sm">
                {{ stock.change >= 0 ? '+' : '' }}{{ stock.change.toFixed(2) }}%
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Allocation Chart (Visual) -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">资产配置</h2>
        </div>
        <div class="space-y-6">
          <!-- Circular Chart -->
          <div class="flex justify-center">
            <div class="relative w-48 h-48">
              <svg viewBox="0 0 100 100" class="w-full h-full">
                <circle 
                  v-for="(stock, index) in stockPerformance" 
                  :key="stock.symbol"
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="currentColor"
                  :stroke-width="15"
                  :stroke-dasharray="`${stock.allocation * 2.51} 251`"
                  :stroke-offset="-62.8"
                  :class="index === 0 ? 'text-blue-500' : index === 1 ? 'text-purple-500' : index === 2 ? 'text-pink-500' : index === 3 ? 'text-red-500' : 'text-green-500'"
                  transform="rotate(-90 50 50)"
                />
                <circle 
                  cx="50"
                  cy="50"
                  r="30"
                  fill="#1f2937"
                />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-xs text-gray-400">总市值</div>
                  <div class="text-sm font-bold text-white">{{ formattedNumber(portfolioStats.totalMarket) }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Legend -->
          <div class="space-y-2">
            <div v-for="stock in stockPerformance" :key="stock.symbol" class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full" :class="
                  stock.symbol === 'AAPL' ? 'bg-blue-500' : 
                  stock.symbol === 'MSFT' ? 'bg-purple-500' : 
                  stock.symbol === 'GOOGL' ? 'bg-pink-500' : 
                  stock.symbol === 'TSLA' ? 'bg-red-500' : 'bg-green-500'
                "></div>
                <span class="text-sm text-gray-300">{{ stock.symbol }}</span>
              </div>
              <span class="text-sm font-medium text-white">{{ stock.allocation }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
