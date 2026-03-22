<script setup lang="ts">
import { computed } from 'vue'
import { useStockStore } from '@/stores/stock'
import { ChartBarIcon, SparklesIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

const store = useStockStore()

const formattedNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(num)
}

// 从store获取性能指标
const performanceMetrics = computed(() => ({
  dailyReturn: store.stats.totalGainPercent / 30, // 估算日收益
  weeklyReturn: store.stats.totalGainPercent / 4, // 估算周收益
  monthlyReturn: store.stats.totalGainPercent,
  quarterlyReturn: store.stats.totalGainPercent * 3,
  sharpeRatio: store.stats.sharpeRatio || 0,
  maxDrawdown: store.stats.maxDrawdown || 0,
  volatility: store.stats.volatility || 12.45,
  beta: 1.12
}))

// 从store获取AI建议
const recommendations = computed(() => store.aiRecommendations)

// 从store获取风险分析
const riskAnalysis = computed(() => {
  if (!store.riskAnalysis) {
    return [
      {
        category: '市场风险',
        level: '中等',
        score: 50,
        description: '暂无风险分析数据'
      }
    ]
  }

  const ra = store.riskAnalysis
  return [
    {
      category: '市场风险',
      level: ra.diversification_score > 70 ? '低' : ra.diversification_score > 40 ? '中等' : '高',
      score: 100 - ra.diversification_score,
      description: ra.diversification_score > 70
        ? '市场波动适中，投资组合分散良好'
        : '建议适当分散投资以降低市场风险'
    },
    {
      category: '个股风险',
      level: ra.position_count > 5 ? '低' : ra.position_count > 2 ? '中等' : '高',
      score: ra.position_count > 5 ? 30 : ra.position_count > 2 ? 50 : 70,
      description: `当前持仓${ra.position_count}只股票，${ra.position_count > 5 ? '分散度良好' : '建议增加持仓数量'}`
    },
    {
      category: '集中度风险',
      level: ra.concentration > 60 ? '高' : ra.concentration > 40 ? '中等' : '低',
      score: Math.round(ra.concentration),
      description: `最大持仓占比${ra.concentration.toFixed(1)}%，${ra.concentration > 60 ? '建议适当分散' : '分散度良好'}`
    },
    {
      category: '流动性风险',
      level: '低',
      score: 20,
      description: '持仓股票流动性良好，变现能力强'
    }
  ]
})

// 从store获取市场情绪
const marketSentiment = computed(() => store.marketSentiment)
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">投资分析</h1>
      <p class="text-gray-400">全面的市场分析和投资策略建议</p>
    </div>

    <!-- Performance Metrics -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="stat-card">
        <div class="flex items-center mb-3">
          <span class="text-sm text-gray-400">月度收益</span>
        </div>
        <div class="text-2xl font-bold text-green-400">+{{ performanceMetrics.monthlyReturn.toFixed(2) }}%</div>
        <div class="text-xs text-gray-500 mt-1">近 30 天</div>
      </div>

      <div class="stat-card">
        <div class="flex items-center mb-3">
          <span class="text-sm text-gray-400">季度收益</span>
        </div>
        <div class="text-2xl font-bold text-blue-400">+{{ performanceMetrics.quarterlyReturn.toFixed(2) }}%</div>
        <div class="text-xs text-gray-500 mt-1">近 90 天</div>
      </div>

      <div class="stat-card">
        <div class="flex items-center mb-3">
          <ChartBarIcon class="w-5 h-5 text-purple-400 mr-2" />
          <span class="text-sm text-gray-400">夏普比率</span>
        </div>
        <div class="text-2xl font-bold text-purple-400">{{ performanceMetrics.sharpeRatio.toFixed(2) }}</div>
        <div class="text-xs text-gray-500 mt-1">风险调整后收益</div>
      </div>

      <div class="stat-card">
        <div class="flex items-center mb-3">
          <span class="text-sm text-gray-400">最大回撤</span>
        </div>
        <div class="text-2xl font-bold text-red-400">{{ performanceMetrics.maxDrawdown.toFixed(2) }}%</div>
        <div class="text-xs text-gray-500 mt-1">历史最大损失</div>
      </div>
    </div>

    <!-- Analysis Recommendations -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- AI Recommendations -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title flex items-center">
            <SparklesIcon class="w-5 h-5 text-yellow-400 mr-2" />
            AI 投资建议
          </h2>
        </div>
        <div class="space-y-4">
          <div 
            v-for="rec in recommendations" 
            :key="rec.symbol"
            class="p-4 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors border-l-4"
            :class="rec.action === '持有' ? 'border-blue-500' : rec.action === '加仓' ? 'border-green-500' : 'border-yellow-500'"
          >
            <div class="flex items-center justify-between mb-3">
              <div>
                <div class="font-bold text-xl text-white">{{ rec.symbol }}</div>
                <div class="text-sm text-gray-400">{{ rec.timeHorizon }}</div>
              </div>
              <span class="px-3 py-1 rounded-full text-sm font-medium" :class="
                rec.action === '持有' ? 'bg-blue-900 text-blue-300' : 
                rec.action === '加仓' ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'
              ">
                {{ rec.action }}
              </span>
            </div>
            <p class="text-sm text-gray-300 mb-3">{{ rec.reason }}</p>
            <div class="flex items-center justify-between">
              <div>
                <div class="text-xs text-gray-500">目标价格</div>
                <div class="font-medium text-green-400">{{ formattedNumber(rec.targetPrice) }}</div>
              </div>
              <div class="text-right">
                <div class="text-xs text-gray-500 mb-1">置信度</div>
                <div class="flex items-center space-x-2">
                  <div class="w-24 bg-gray-600 rounded-full h-2">
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

      <!-- Market Sentiment -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">市场情绪</h2>
        </div>
        <div class="space-y-4">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-400">总体情绪</span>
              <span class="text-sm text-green-400 font-medium">{{ marketSentiment.overall }}/100</span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-3">
              <div 
                class="h-3 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500" 
                :style="{ width: `${marketSentiment.overall}%` }"
              ></div>
            </div>
          </div>

          <div class="space-y-3 pt-4 border-t border-gray-700">
            <div v-for="(value, sector) in marketSentiment" :key="sector" class="flex items-center justify-between">
              <span class="text-sm text-gray-300 capitalize">{{ sector }}</span>
              <div class="flex items-center space-x-3">
                <div class="w-32 bg-gray-700 rounded-full h-2">
                  <div 
                    class="h-2 rounded-full"
                    :class="{
                      'bg-green-500': value >= 70,
                      'bg-yellow-500': value >= 50,
                      'bg-red-500': value < 50
                    }"
                    :style="{ width: `${value}%` }"
                  ></div>
                </div>
                <span class="text-sm font-medium text-white">{{ value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Risk Analysis -->
    <div class="card mb-8">
      <div class="card-header">
        <h2 class="card-title">风险评估</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div 
          v-for="risk in riskAnalysis" 
          :key="risk.category"
          class="p-4 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
        >
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-medium text-white">{{ risk.category }}</h3>
            <span :class="{
              'text-green-400': risk.score <= 30,
              'text-yellow-400': risk.score > 30 && risk.score <= 60,
              'text-red-400': risk.score > 60
            }" class="text-sm font-medium">
              {{ risk.level }}
            </span>
          </div>
          <div class="w-full bg-gray-600 rounded-full h-2 mb-3">
            <div 
              class="h-2 rounded-full transition-all duration-500"
              :class="{
                'bg-green-500': risk.score <= 30,
                'bg-yellow-500': risk.score > 30 && risk.score <= 60,
                'bg-red-500': risk.score > 60
              }"
              :style="{ width: `${risk.score}%` }"
            ></div>
          </div>
          <p class="text-xs text-gray-400">{{ risk.description }}</p>
        </div>
      </div>
    </div>

    <!-- Volatility Analysis -->
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">波动率分析</h2>
        <div class="flex items-center space-x-4">
          <button class="btn btn-primary text-sm flex items-center">
            <ArrowPathIcon class="w-4 h-4 mr-1" />
            刷新
          </button>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-4 bg-gray-700/50 rounded-lg">
          <div class="text-sm text-gray-400 mb-1">持仓波动率</div>
          <div class="text-2xl font-bold text-white">{{ performanceMetrics.volatility }}%</div>
          <div class="text-xs text-gray-500 mt-1">年化波动率</div>
        </div>
        <div class="p-4 bg-gray-700/50 rounded-lg">
          <div class="text-sm text-gray-400 mb-1">Beta 系数</div>
          <div class="text-2xl font-bold text-white">{{ performanceMetrics.beta }}</div>
          <div class="text-xs text-gray-500 mt-1">相对市场风险</div>
        </div>
        <div class="p-4 bg-gray-700/50 rounded-lg">
          <div class="text-sm text-gray-400 mb-1">VaR (95%)</div>
          <div class="text-2xl font-bold text-red-400">-4.2%</div>
          <div class="text-xs text-gray-500 mt-1">日度风险价值</div>
        </div>
      </div>
    </div>
  </div>
</template>
