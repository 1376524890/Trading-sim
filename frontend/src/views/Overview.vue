<script setup lang="ts">
import { computed } from 'vue'
import { useStockStore } from '@/stores/stock'
import { 
  ArrowUpIcon, 
  ArrowDownIcon, 
  BanknotesIcon, 
  ChartBarIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  LightBulbIcon
} from '@heroicons/vue/24/outline'

const store = useStockStore()

const { stats, holdings, transactions, news, topGainer, topLoser } = store

// 计算属性：风险等级
const riskLevel = computed(() => {
  const concentration = store.riskAnalysis?.concentration ?? 45
  return {
    concentration,
    isHigh: concentration > 60,
    isMedium: concentration > 40 && concentration <= 60,
    isLow: concentration <= 40,
    label: concentration > 60 ? '偏高' : concentration > 40 ? '中等' : '偏低',
    colorClass: concentration > 60 ? 'text-red-400' : concentration > 40 ? 'text-yellow-400' : 'text-green-400',
    barClass: concentration > 60 ? 'bg-gradient-to-r from-red-500 to-red-400' : concentration > 40 ? 'bg-gradient-to-r from-yellow-500 to-yellow-400' : 'bg-gradient-to-r from-green-500 to-green-400'
  }
})

const formattedNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(num)
}

const formatPercent = (num: number) => {
  return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`
}

const formatDate = (date: Date) => {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <!-- Total Equity -->
      <div class="stat-card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="stat-label">总权益</p>
            <p class="stat-value text-green-400">{{ formattedNumber(stats.totalEquity) }}</p>
          </div>
          <div class="p-3 bg-green-900/50 rounded-lg">
            <CurrencyDollarIcon class="w-8 h-8 text-green-400" />
          </div>
        </div>
        <div class="flex items-center">
          <ArrowUpIcon class="w-5 h-5 text-green-400 mr-1" />
          <span class="text-green-400 text-sm font-medium">+{{ formatPercent(stats.dayGainPercent) }}</span>
          <span class="text-gray-400 text-sm ml-2">今日</span>
        </div>
      </div>

      <!-- Cash -->
      <div class="stat-card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="stat-label">可用资金</p>
            <p class="stat-value text-blue-400">{{ formattedNumber(stats.cash) }}</p>
          </div>
          <div class="p-3 bg-blue-900/50 rounded-lg">
            <BanknotesIcon class="w-8 h-8 text-blue-400" />
          </div>
        </div>
        <div class="text-gray-400 text-sm">
          持仓占比：{{ ((stats.invested / stats.totalEquity) * 100).toFixed(1) }}%
        </div>
      </div>

      <!-- Total Gain -->
      <div class="stat-card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="stat-label">总盈亏</p>
            <p class="stat-value text-green-400">{{ formattedNumber(stats.totalGain) }}</p>
          </div>
          <div class="p-3 bg-green-900/50 rounded-lg">
            <ChartBarIcon class="w-8 h-8 text-green-400" />
          </div>
        </div>
        <div class="flex items-center">
          <ArrowUpIcon class="w-5 h-5 text-green-400 mr-1" />
          <span class="text-green-400 text-sm font-medium">+{{ formatPercent(stats.totalGainPercent) }}</span>
          <span class="text-gray-400 text-sm ml-2">累计</span>
        </div>
      </div>

      <!-- Win Rate -->
      <div class="stat-card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="stat-label">胜率</p>
            <p class="stat-value text-purple-400">{{ stats.winRate }}%</p>
          </div>
          <div class="p-3 bg-purple-900/50 rounded-lg">
            <LightBulbIcon class="w-8 h-8 text-purple-400" />
          </div>
        </div>
        <div class="text-gray-400 text-sm">
          总交易：{{ stats.totalTrades }} 笔
        </div>
      </div>
    </div>

    <!-- Holdings Overview & Analysis -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <!-- Holdings Overview -->
      <div class="card lg:col-span-2">
        <div class="card-header">
          <h2 class="card-title">持仓概览</h2>
          <router-link to="/portfolio" class="text-primary-400 hover:text-primary-300 text-sm">
            查看全部 →
          </router-link>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-gray-400 text-sm border-b border-gray-700">
                <th class="pb-3 font-medium">股票</th>
                <th class="pb-3 font-medium text-right">数量</th>
                <th class="pb-3 font-medium text-right">现价</th>
                <th class="pb-3 font-medium text-right">市值</th>
                <th class="pb-3 font-medium text-right">盈亏</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="holding in holdings.slice(0, 5)" 
                :key="holding.symbol"
                class="border-b border-gray-700 last:border-0 hover:bg-gray-700/50 transition-colors"
              >
                <td class="py-4">
                  <div>
                    <div class="font-medium text-white">{{ holding.symbol }}</div>
                    <div class="text-sm text-gray-400">{{ holding.name }}</div>
                  </div>
                </td>
                <td class="py-4 text-right">{{ holding.shares.toLocaleString() }}</td>
                <td class="py-4 text-right">{{ formattedNumber(holding.currentPrice) }}</td>
                <td class="py-4 text-right">{{ formattedNumber(holding.marketValue) }}</td>
                <td class="py-4 text-right">
                  <span :class="holding.gainLoss >= 0 ? 'text-green-400' : 'text-red-400'" class="font-medium">
                    {{ holding.gainLoss >= 0 ? '+' : '' }}{{ formattedNumber(holding.gainLoss) }}
                  </span>
                  <div :class="holding.gainLossPercent >= 0 ? 'text-green-400' : 'text-red-400'" class="text-xs">
                    {{ holding.gainLossPercent >= 0 ? '+' : '' }}{{ holding.gainLossPercent.toFixed(2) }}%
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Analysis Summary -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">分析摘要</h2>
        </div>
        <div class="space-y-4">
          <!-- Market Sentiment -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-400">市场情绪</span>
              <span :class="store.marketSentiment.overall >= 60 ? 'text-green-400' : store.marketSentiment.overall >= 40 ? 'text-yellow-400' : 'text-red-400'" class="text-sm font-medium">
                {{ store.marketSentiment.overall >= 60 ? '看涨' : store.marketSentiment.overall >= 40 ? '中性' : '看跌' }}
              </span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-500"
                :class="store.marketSentiment.overall >= 60 ? 'bg-gradient-to-r from-green-500 to-green-400' : store.marketSentiment.overall >= 40 ? 'bg-gradient-to-r from-yellow-500 to-yellow-400' : 'bg-gradient-to-r from-red-500 to-red-400'"
                :style="{ width: `${store.marketSentiment.overall}%` }"
              ></div>
            </div>
          </div>

          <!-- Risk Level -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-400">风险等级</span>
              <span :class="riskLevel.colorClass" class="text-sm font-medium">
                {{ riskLevel.label }}
              </span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-500"
                :class="riskLevel.barClass"
                :style="{ width: `${riskLevel.concentration}%` }"
              ></div>
            </div>
          </div>

          <!-- Top Performer -->
          <div class="pt-4 border-t border-gray-700">
            <div class="text-sm text-gray-400 mb-1">最佳表现</div>
            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-white">{{ topGainer?.symbol }}</div>
                <div class="text-sm text-green-400">+{{ topGainer?.gainLossPercent.toFixed(2) }}%</div>
              </div>
              <ArrowUpIcon class="w-5 h-5 text-green-400" />
            </div>
          </div>

          <!-- Underperformer -->
          <div class="pt-4 border-t border-gray-700">
            <div class="text-sm text-gray-400 mb-1">需关注</div>
            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-white">{{ topLoser?.symbol }}</div>
                <div class="text-sm text-red-400">{{ topLoser?.gainLossPercent.toFixed(2) }}%</div>
              </div>
              <ArrowDownIcon class="w-5 h-5 text-red-400" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Transactions & News -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Transactions -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">最近交易</h2>
          <router-link to="/transactions" class="text-primary-400 hover:text-primary-300 text-sm">
            查看全部 →
          </router-link>
        </div>
        <div class="space-y-3">
          <div 
            v-for="txn in transactions.slice(0, 4)" 
            :key="txn.id"
            class="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <div class="flex items-center space-x-3">
              <div :class="txn.type === 'buy' ? 'bg-green-900/50' : 'bg-red-900/50'" class="p-2 rounded-lg">
                <DocumentTextIcon :class="txn.type === 'buy' ? 'w-5 h-5 text-green-400' : 'w-5 h-5 text-red-400'" />
              </div>
              <div>
                <div class="font-medium text-white">{{ txn.type === 'buy' ? '买入' : '卖出' }} {{ txn.symbol }}</div>
                <div class="text-sm text-gray-400">{{ formatDate(txn.timestamp) }}</div>
              </div>
            </div>
            <div class="text-right">
              <div :class="txn.type === 'buy' ? 'text-green-400' : 'text-red-400'" class="font-medium">
                {{ txn.shares }}股 @ {{ formattedNumber(txn.price) }}
              </div>
              <div class="text-sm text-gray-400">{{ formattedNumber(txn.total) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- News Feed -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">最新资讯</h2>
          <router-link to="/news" class="text-primary-400 hover:text-primary-300 text-sm">
            查看全部 →
          </router-link>
        </div>
        <div class="space-y-4">
          <div 
            v-for="article in news.slice(0, 4)" 
            :key="article.id"
            class="border-b border-gray-700 last:border-0 pb-4 last:pb-0"
          >
            <div class="flex items-start justify-between mb-2">
              <span :class="{
                'text-green-400': article.sentiment === 'positive',
                'text-red-400': article.sentiment === 'negative',
                'text-gray-400': article.sentiment === 'neutral'
              }" class="text-xs px-2 py-1 rounded-full capitalize">
                {{ article.sentiment === 'positive' ? '利好' : article.sentiment === 'negative' ? '利空' : '中性' }}
              </span>
              <span class="text-xs text-gray-400">{{ formatDate(article.timestamp) }}</span>
            </div>
            <h3 class="font-medium text-white mb-1 hover:text-primary-400 cursor-pointer">{{ article.title }}</h3>
            <p class="text-sm text-gray-400 line-clamp-2">{{ article.summary }}</p>
            <div class="flex items-center mt-2 space-x-2">
              <span class="text-xs text-gray-500">{{ article.source }}</span>
              <span v-if="article.relatedSymbols.length > 0" class="text-xs text-gray-500">|</span>
              <div class="flex space-x-1">
                <span 
                  v-for="symbol in article.relatedSymbols.slice(0, 3)" 
                  :key="symbol"
                  class="text-xs bg-gray-700 px-2 py-0.5 rounded text-gray-300"
                >
                  {{ symbol }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
