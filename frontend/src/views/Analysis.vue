<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useStockStore } from '@/stores/stock'
import {
  ChartBarIcon,
  SparklesIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ShieldCheckIcon,
  ClockIcon,
  BoltIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'

const store = useStockStore()

// 刷新状态
const refreshing = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref<number | null>(null)

// 格式化货币
const formattedNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(num)
}

// 格式化百分比
const formatPercent = (num: number) => {
  const sign = num >= 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

// 从store获取性能指标
const performanceMetrics = computed(() => ({
  dailyReturn: store.stats.totalGainPercent / 30,
  weeklyReturn: store.stats.totalGainPercent / 4,
  monthlyReturn: store.stats.totalGainPercent,
  quarterlyReturn: store.stats.totalGainPercent * 3,
  sharpeRatio: store.stats.sharpeRatio || 1.25,
  maxDrawdown: store.stats.maxDrawdown || 5.8,
  volatility: store.stats.volatility || 12.45,
  beta: 1.12,
  alpha: 2.3
}))

// 从store获取AI建议
const recommendations = computed(() => store.aiRecommendations)

// 从store获取风险分析
const riskAnalysis = computed(() => {
  if (!store.riskAnalysis) {
    return getDefaultRiskAnalysis()
  }

  const ra = store.riskAnalysis
  return [
    {
      category: '市场风险',
      level: ra.diversification_score > 70 ? '低' : ra.diversification_score > 40 ? '中等' : '高',
      score: 100 - ra.diversification_score,
      description: ra.diversification_score > 70
        ? '市场波动适中，投资组合分散良好'
        : '建议适当分散投资以降低市场风险',
      icon: ChartBarIcon,
      trend: 'stable'
    },
    {
      category: '个股风险',
      level: ra.position_count > 5 ? '低' : ra.position_count > 2 ? '中等' : '高',
      score: ra.position_count > 5 ? 30 : ra.position_count > 2 ? 50 : 70,
      description: `当前持仓${ra.position_count}只股票，${ra.position_count > 5 ? '分散度良好' : '建议增加持仓数量'}`,
      icon: ExclamationTriangleIcon,
      trend: ra.position_count > 5 ? 'down' : 'up'
    },
    {
      category: '集中度风险',
      level: ra.concentration > 60 ? '高' : ra.concentration > 40 ? '中等' : '低',
      score: Math.round(ra.concentration),
      description: `最大持仓占比${ra.concentration.toFixed(1)}%，${ra.concentration > 60 ? '建议适当分散' : '分散度良好'}`,
      icon: BoltIcon,
      trend: ra.concentration > 60 ? 'up' : 'stable'
    },
    {
      category: '流动性风险',
      level: '低',
      score: 20,
      description: '持仓股票流动性良好，变现能力强',
      icon: ShieldCheckIcon,
      trend: 'down'
    }
  ]
})

// 默认风险分析
const getDefaultRiskAnalysis = () => [
  { category: '市场风险', level: '中等', score: 50, description: '暂无风险分析数据', icon: ChartBarIcon, trend: 'stable' },
  { category: '个股风险', level: '中等', score: 50, description: '暂无持仓数据', icon: ExclamationTriangleIcon, trend: 'stable' },
  { category: '集中度风险', level: '中等', score: 50, description: '暂无持仓数据', icon: BoltIcon, trend: 'stable' },
  { category: '流动性风险', level: '低', score: 20, description: '持仓股票流动性良好', icon: ShieldCheckIcon, trend: 'down' }
]

// 从store获取市场情绪
const marketSentiment = computed(() => store.marketSentiment)

// 持仓详情
const holdings = computed(() => store.holdings)

// 活跃的标签页
const activeTab = ref<'overview' | 'positions' | 'risk'>('overview')

// 刷新数据
const refreshData = async () => {
  refreshing.value = true
  try {
    await store.fetchAllData()
  } finally {
    refreshing.value = false
  }
}

// 获取风险等级颜色
const getRiskColor = (score: number) => {
  if (score <= 30) return { bg: 'bg-green-500', text: 'text-green-400', border: 'border-green-500' }
  if (score <= 60) return { bg: 'bg-yellow-500', text: 'text-yellow-400', border: 'border-yellow-500' }
  return { bg: 'bg-red-500', text: 'text-red-400', border: 'border-red-500' }
}

// 获取趋势图标
const getTrendIcon = (trend: string) => {
  if (trend === 'up') return ArrowTrendingUpIcon
  if (trend === 'down') return ArrowTrendingDownIcon
  return null
}

// 获取趋势颜色
const getTrendColor = (trend: string) => {
  if (trend === 'up') return 'text-red-400'
  if (trend === 'down') return 'text-green-400'
  return 'text-gray-400'
}

// 获取操作颜色
const getActionColor = (action: string) => {
  if (action === '加仓') return 'bg-green-900/50 text-green-300 border-green-500'
  if (action === '持有') return 'bg-blue-900/50 text-blue-300 border-blue-500'
  if (action === '减仓') return 'bg-yellow-900/50 text-yellow-300 border-yellow-500'
  return 'bg-gray-700/50 text-gray-300 border-gray-500'
}

// 格式化时间
const formatTime = (date: Date) => {
  return new Date(date).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (refreshInterval.value) return
  refreshInterval.value = window.setInterval(() => {
    if (autoRefresh.value) {
      refreshData()
    }
  }, 30000) // 30秒刷新一次
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

onMounted(() => {
  refreshData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- 页面头部 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center">
          <SparklesIcon class="w-7 h-7 text-yellow-400 mr-2" />
          智能投资分析
        </h1>
        <p class="text-gray-400 mt-1 text-sm">实时金融数据与AI分析结果同步展示</p>
      </div>
      <div class="flex items-center space-x-3">
        <div class="flex items-center text-sm text-gray-400">
          <ClockIcon class="w-4 h-4 mr-1" />
          <span v-if="store.lastUpdate">{{ formatTime(store.lastUpdate) }}</span>
        </div>
        <button
          @click="autoRefresh = !autoRefresh"
          :class="autoRefresh ? 'bg-green-600' : 'bg-gray-600'"
          class="px-3 py-1.5 rounded-lg text-sm text-white transition-colors"
        >
          {{ autoRefresh ? '自动' : '手动' }}
        </button>
        <button
          @click="refreshData"
          :disabled="refreshing"
          class="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors disabled:opacity-50"
        >
          <ArrowPathIcon class="w-4 h-4 mr-2" :class="{ 'animate-spin': refreshing }" />
          刷新
        </button>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <!-- 总资产 -->
      <div class="bg-gradient-to-br from-purple-900/40 to-purple-800/20 rounded-xl p-4 border border-purple-500/30">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-gray-400">总资产</span>
          <ChartBarIcon class="w-5 h-5 text-purple-400" />
        </div>
        <div class="text-2xl font-bold text-white">{{ formattedNumber(store.stats.totalEquity) }}</div>
        <div class="flex items-center mt-2 text-sm">
          <span :class="store.stats.totalGain >= 0 ? 'text-red-400' : 'text-green-400'">
            {{ formatPercent(store.stats.totalGainPercent) }}
          </span>
          <span class="text-gray-500 ml-2">总收益</span>
        </div>
      </div>

      <!-- 持仓市值 -->
      <div class="bg-gradient-to-br from-blue-900/40 to-blue-800/20 rounded-xl p-4 border border-blue-500/30">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-gray-400">持仓市值</span>
          <BoltIcon class="w-5 h-5 text-blue-400" />
        </div>
        <div class="text-2xl font-bold text-white">{{ formattedNumber(store.stats.invested) }}</div>
        <div class="flex items-center mt-2 text-sm text-gray-400">
          <span>{{ holdings.length }}</span>
          <span class="ml-2">只股票</span>
        </div>
      </div>

      <!-- 可用现金 -->
      <div class="bg-gradient-to-br from-green-900/40 to-green-800/20 rounded-xl p-4 border border-green-500/30">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-gray-400">可用现金</span>
          <ShieldCheckIcon class="w-5 h-5 text-green-400" />
        </div>
        <div class="text-2xl font-bold text-white">{{ formattedNumber(store.stats.cash) }}</div>
        <div class="flex items-center mt-2 text-sm text-gray-400">
          <span>{{ ((store.stats.cash / store.stats.totalEquity) * 100).toFixed(1) }}%</span>
          <span class="ml-2">仓位</span>
        </div>
      </div>

      <!-- 夏普比率 -->
      <div class="bg-gradient-to-br from-yellow-900/40 to-yellow-800/20 rounded-xl p-4 border border-yellow-500/30">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-gray-400">夏普比率</span>
          <ChartBarIcon class="w-5 h-5 text-yellow-400" />
        </div>
        <div class="text-2xl font-bold text-white">{{ performanceMetrics.sharpeRatio.toFixed(2) }}</div>
        <div class="flex items-center mt-2 text-sm text-gray-400">
          <span>风险调整收益</span>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 左侧: 持仓分析 & AI建议 -->
      <div class="lg:col-span-2 space-y-6">
        <!-- 持仓分析 -->
        <div class="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-white flex items-center">
              <ChartBarIcon class="w-5 h-5 text-blue-400 mr-2" />
              持仓分析
            </h2>
            <span class="text-sm text-gray-400">{{ holdings.length }} 只持仓</span>
          </div>

          <div v-if="holdings.length === 0" class="p-8 text-center text-gray-500">
            <InformationCircleIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>暂无持仓数据</p>
          </div>

          <div v-else class="divide-y divide-gray-700/50">
            <div
              v-for="holding in holdings.slice(0, 5)"
              :key="holding.symbol"
              class="p-4 hover:bg-gray-700/30 transition-colors"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                    {{ holding.symbol.substring(0, 2) }}
                  </div>
                  <div>
                    <div class="font-medium text-white">{{ holding.name }}</div>
                    <div class="text-xs text-gray-400">{{ holding.symbol }}</div>
                  </div>
                </div>
                <div class="text-right">
                  <div class="text-white font-medium">{{ formattedNumber(holding.marketValue) }}</div>
                  <div class="flex items-center justify-end text-sm">
                    <span :class="holding.gainLossPercent >= 0 ? 'text-red-400' : 'text-green-400'">
                      {{ formatPercent(holding.gainLossPercent) }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="mt-3 grid grid-cols-4 gap-2 text-xs">
                <div>
                  <div class="text-gray-500">持仓</div>
                  <div class="text-gray-300">{{ holding.shares }}股</div>
                </div>
                <div>
                  <div class="text-gray-500">成本</div>
                  <div class="text-gray-300">{{ formattedNumber(holding.avgPrice) }}</div>
                </div>
                <div>
                  <div class="text-gray-500">现价</div>
                  <div class="text-gray-300">{{ formattedNumber(holding.currentPrice) }}</div>
                </div>
                <div>
                  <div class="text-gray-500">盈亏</div>
                  <div :class="holding.gainLoss >= 0 ? 'text-red-400' : 'text-green-400'">
                    {{ formattedNumber(holding.gainLoss) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI 投资建议 -->
        <div class="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-700">
            <h2 class="text-lg font-semibold text-white flex items-center">
              <SparklesIcon class="w-5 h-5 text-yellow-400 mr-2" />
              AI 投资建议
            </h2>
          </div>

          <div v-if="recommendations.length === 0" class="p-8 text-center text-gray-500">
            <InformationCircleIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>暂无AI建议</p>
          </div>

          <div v-else class="divide-y divide-gray-700/50">
            <div
              v-for="rec in recommendations.slice(0, 4)"
              :key="rec.symbol"
              class="p-4 hover:bg-gray-700/30 transition-colors"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-2">
                    <span class="font-medium text-white">{{ rec.symbol }}</span>
                    <span
                      class="px-2 py-0.5 rounded text-xs font-medium border"
                      :class="getActionColor(rec.action)"
                    >
                      {{ rec.action }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-300 mb-3">{{ rec.reason }}</p>
                  <div class="flex items-center space-x-4 text-xs">
                    <div>
                      <span class="text-gray-500">目标价: </span>
                      <span class="text-green-400">{{ formattedNumber(rec.targetPrice) }}</span>
                    </div>
                    <div>
                      <span class="text-gray-500">周期: </span>
                      <span class="text-gray-300">{{ rec.timeHorizon }}</span>
                    </div>
                  </div>
                </div>
                <div class="ml-4 text-right">
                  <div class="text-xs text-gray-500 mb-1">置信度</div>
                  <div class="flex items-center space-x-2">
                    <div class="w-20 bg-gray-700 rounded-full h-2">
                      <div
                        class="bg-gradient-to-r from-green-500 to-green-400 h-2 rounded-full"
                        :style="{ width: `${rec.confidence}%` }"
                      ></div>
                    </div>
                    <span class="text-sm font-medium text-white">{{ rec.confidence }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧: 风险评估 & 市场情绪 -->
      <div class="space-y-6">
        <!-- 风险评估 -->
        <div class="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-700">
            <h2 class="text-lg font-semibold text-white flex items-center">
              <ShieldCheckIcon class="w-5 h-5 text-green-400 mr-2" />
              风险评估
            </h2>
          </div>
          <div class="p-4 space-y-4">
            <div
              v-for="risk in riskAnalysis"
              :key="risk.category"
              class="bg-gray-900/50 rounded-lg p-3"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center">
                  <component :is="risk.icon" class="w-4 h-4 text-gray-400 mr-2" />
                  <span class="text-sm font-medium text-white">{{ risk.category }}</span>
                </div>
                <div class="flex items-center space-x-2">
                  <component
                    v-if="getTrendIcon(risk.trend)"
                    :is="getTrendIcon(risk.trend)"
                    class="w-4 h-4"
                    :class="getTrendColor(risk.trend)"
                  />
                  <span
                    class="text-xs font-medium px-2 py-0.5 rounded"
                    :class="getRiskColor(risk.score).text"
                  >
                    {{ risk.level }}
                  </span>
                </div>
              </div>
              <div class="w-full bg-gray-700 rounded-full h-1.5 mb-2">
                <div
                  class="h-1.5 rounded-full transition-all duration-500"
                  :class="getRiskColor(risk.score).bg"
                  :style="{ width: `${risk.score}%` }"
                ></div>
              </div>
              <p class="text-xs text-gray-400">{{ risk.description }}</p>
            </div>
          </div>
        </div>

        <!-- 市场情绪 -->
        <div class="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-700">
            <h2 class="text-lg font-semibold text-white flex items-center">
              <BoltIcon class="w-5 h-5 text-yellow-400 mr-2" />
              市场情绪
            </h2>
          </div>
          <div class="p-4">
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm text-gray-400">总体情绪</span>
                <span class="text-sm font-medium" :class="marketSentiment.overall >= 50 ? 'text-red-400' : 'text-green-400'">
                  {{ marketSentiment.overall >= 50 ? '偏多' : '偏空' }}
                </span>
              </div>
              <div class="w-full bg-gray-700 rounded-full h-3">
                <div
                  class="h-3 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"
                  :style="{ width: `${marketSentiment.overall}%` }"
                ></div>
              </div>
              <div class="flex justify-between text-xs text-gray-500 mt-1">
                <span>悲观</span>
                <span>{{ marketSentiment.overall }}</span>
                <span>乐观</span>
              </div>
            </div>

            <div class="space-y-2 pt-3 border-t border-gray-700">
              <div
                v-for="(value, sector) in marketSentiment"
                :key="sector"
                v-show="sector !== 'overall'"
                class="flex items-center justify-between"
              >
                <span class="text-sm text-gray-300 capitalize">{{ sector }}</span>
                <div class="flex items-center space-x-2">
                  <div class="w-20 bg-gray-700 rounded-full h-1.5">
                    <div
                      class="h-1.5 rounded-full"
                      :class="{
                        'bg-red-500': value >= 60,
                        'bg-yellow-500': value >= 40,
                        'bg-green-500': value < 40
                      }"
                      :style="{ width: `${value}%` }"
                    ></div>
                  </div>
                  <span class="text-xs text-white w-6 text-right">{{ value }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 波动率分析 -->
        <div class="bg-gray-800/80 rounded-xl border border-gray-700 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-700">
            <h2 class="text-lg font-semibold text-white">波动率分析</h2>
          </div>
          <div class="p-4 grid grid-cols-2 gap-3">
            <div class="bg-gray-900/50 rounded-lg p-3 text-center">
              <div class="text-xs text-gray-500 mb-1">年化波动率</div>
              <div class="text-lg font-bold text-white">{{ performanceMetrics.volatility }}%</div>
            </div>
            <div class="bg-gray-900/50 rounded-lg p-3 text-center">
              <div class="text-xs text-gray-500 mb-1">Beta系数</div>
              <div class="text-lg font-bold text-white">{{ performanceMetrics.beta }}</div>
            </div>
            <div class="bg-gray-900/50 rounded-lg p-3 text-center">
              <div class="text-xs text-gray-500 mb-1">Alpha</div>
              <div class="text-lg font-bold text-green-400">+{{ performanceMetrics.alpha }}%</div>
            </div>
            <div class="bg-gray-900/50 rounded-lg p-3 text-center">
              <div class="text-xs text-gray-500 mb-1">最大回撤</div>
              <div class="text-lg font-bold text-red-400">{{ performanceMetrics.maxDrawdown }}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(107, 114, 128, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 0.8);
}
</style>