<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStockStore } from '@/stores/stock'
import { 
  DocumentTextIcon, 
  ArrowUpRightIcon, 
  ArrowDownLeftIcon,
  CalendarIcon,
  CurrencyDollarIcon
} from '@heroicons/vue/24/outline'

const store = useStockStore()
const selectedType = ref<string>('all')
const searchQuery = ref('')

const formattedNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(num)
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

const filteredTransactions = computed(() => {
  let transactions = [...store.transactions]
  
  // Filter by type
  if (selectedType.value !== 'all') {
    transactions = transactions.filter(t => t.type === selectedType.value)
  }
  
  // Filter by search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    transactions = transactions.filter(t => 
      t.symbol.toLowerCase().includes(query) ||
      t.id.toLowerCase().includes(query)
    )
  }
  
  return transactions
})

const stats = computed(() => {
  const totalBuy = store.transactions
    .filter(t => t.type === 'buy')
    .reduce((sum, t) => sum + t.total, 0)
  
  const totalSell = store.transactions
    .filter(t => t.type === 'sell')
    .reduce((sum, t) => sum + t.total, 0)
  
  const totalFees = store.transactions.reduce((sum, t) => sum + t.fees, 0)
  
  return {
    totalBuy,
    totalSell,
    totalFees,
    buyCount: store.transactions.filter(t => t.type === 'buy').length,
    sellCount: store.transactions.filter(t => t.type === 'sell').length
  }
})

const recentActivity = computed(() => store.calculateRecentActivity())
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">交易记录</h1>
      <p class="text-gray-400">查看历史交易和资金流水</p>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="stat-card">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-sm text-gray-400">买入总额</div>
            <div class="text-2xl font-bold text-green-400">{{ formattedNumber(stats.totalBuy) }}</div>
          </div>
          <div class="p-3 bg-green-900/50 rounded-lg">
            <ArrowUpRightIcon class="w-6 h-6 text-green-400" />
          </div>
        </div>
        <div class="text-sm text-gray-400">{{ stats.buyCount }} 笔买入</div>
      </div>
      
      <div class="stat-card">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-sm text-gray-400">卖出总额</div>
            <div class="text-2xl font-bold text-red-400">{{ formattedNumber(stats.totalSell) }}</div>
          </div>
          <div class="p-3 bg-red-900/50 rounded-lg">
            <ArrowDownLeftIcon class="w-6 h-6 text-red-400" />
          </div>
        </div>
        <div class="text-sm text-gray-400">{{ stats.sellCount }} 笔卖出</div>
      </div>
      
      <div class="stat-card">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div class="text-sm text-gray-400">总手续费</div>
            <div class="text-2xl font-bold text-yellow-400">{{ formattedNumber(stats.totalFees) }}</div>
          </div>
          <div class="p-3 bg-yellow-900/50 rounded-lg">
            <CurrencyDollarIcon class="w-6 h-6 text-yellow-400" />
          </div>
        </div>
        <div class="text-sm text-gray-400">已支付费用</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="card mb-6">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center space-x-4 flex-1">
          <div class="relative flex-1 max-w-md">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索股票代码或交易 ID..."
              class="input pl-4"
            />
          </div>
          
          <select 
            v-model="selectedType"
            class="input w-auto"
          >
            <option value="all">所有类型</option>
            <option value="buy">买入</option>
            <option value="sell">卖出</option>
          </select>
        </div>
        
        <div class="text-sm text-gray-400">
          共 {{ filteredTransactions.length }} 笔交易
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- Activity Chart (Visual) -->
      <div class="card lg:col-span-1">
        <div class="card-header">
          <h2 class="card-title">近期活动</h2>
        </div>
        <div class="space-y-3">
          <div 
            v-for="activity in recentActivity" 
            :key="activity.day"
            class="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <div class="font-medium text-white">{{ activity.day }}</div>
            <div class="flex items-center space-x-4">
              <div class="text-center">
                <div class="text-sm text-green-400">{{ activity.buys }}买</div>
                <div class="text-sm text-red-400">{{ activity.sells }}卖</div>
              </div>
              <div class="text-xs text-gray-400">{{ activity.volume }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Transaction List -->
      <div class="card lg:col-span-2">
        <div class="card-header">
          <h2 class="card-title">交易明细</h2>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-gray-400 text-sm border-b border-gray-700">
                <th class="pb-3 font-medium">交易 ID</th>
                <th class="pb-3 font-medium">股票</th>
                <th class="pb-3 font-medium text-center">类型</th>
                <th class="pb-3 font-medium text-right">数量</th>
                <th class="pb-3 font-medium text-right">价格</th>
                <th class="pb-3 font-medium text-right">总金额</th>
                <th class="pb-3 font-medium text-right">手续费</th>
                <th class="pb-3 font-medium">时间</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="txn in filteredTransactions" 
                :key="txn.id"
                class="border-b border-gray-700 last:border-0 hover:bg-gray-700/50 transition-colors"
              >
                <td class="py-4">
                  <span class="font-mono text-sm text-gray-400">{{ txn.id }}</span>
                </td>
                <td class="py-4">
                  <div class="font-medium text-white">{{ txn.symbol }}</div>
                </td>
                <td class="py-4 text-center">
                  <span 
                    :class="{
                      'bg-green-900 text-green-300': txn.type === 'buy',
                      'bg-red-900 text-red-300': txn.type === 'sell'
                    }"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  >
                    <component 
                      :is="txn.type === 'buy' ? ArrowUpRightIcon : ArrowDownLeftIcon" 
                      class="w-3 h-3 mr-1" 
                    />
                    {{ txn.type === 'buy' ? '买入' : '卖出' }}
                  </span>
                </td>
                <td class="py-4 text-right font-medium text-white">
                  {{ txn.shares.toLocaleString() }}
                </td>
                <td class="py-4 text-right text-gray-300">
                  {{ formattedNumber(txn.price) }}
                </td>
                <td class="py-4 text-right font-medium text-white">
                  {{ formattedNumber(txn.total) }}
                </td>
                <td class="py-4 text-right text-gray-400">
                  {{ formattedNumber(txn.fees) }}
                </td>
                <td class="py-4 text-gray-400">
                  {{ formatDate(txn.timestamp) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="filteredTransactions.length === 0" class="text-center py-12">
          <DocumentTextIcon class="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 class="text-xl font-medium text-gray-400 mb-2">暂无交易记录</h3>
          <p class="text-gray-500">暂无符合条件的交易</p>
        </div>
      </div>
    </div>

    <!-- Export Options -->
    <div class="card">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-white mb-1">导出交易记录</h3>
          <p class="text-sm text-gray-400">导出所有交易记录为 CSV 文件</p>
        </div>
        <button class="btn btn-primary flex items-center">
          <CalendarIcon class="w-5 h-5 mr-2" />
          导出 CSV
        </button>
      </div>
    </div>
  </div>
</template>
