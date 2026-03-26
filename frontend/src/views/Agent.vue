<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  CpuChipIcon,
  ClockIcon,
  ChartBarIcon,
  DocumentTextIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  LightBulbIcon,
  ClipboardDocumentCheckIcon
} from '@heroicons/vue/24/outline'

// 状态
const agentStatus = ref<any>({})
const tokenUsage = ref<any>({})
const decisionHistory = ref<any[]>([])
const workflowData = ref<any>({})
const refreshing = ref(false)
const activeTab = ref<'status' | 'workflow' | 'history'>('workflow')

// 计算属性
const exploreSkills = computed(() => {
  return workflowData.value?.phases?.find((p: any) => p.name === 'explore')?.skills || []
})

const decideSkills = computed(() => {
  return workflowData.value?.phases?.find((p: any) => p.name === 'decide')?.skills || []
})

const evaluateSkills = computed(() => {
  return workflowData.value?.phases?.find((p: any) => p.name === 'evaluate')?.skills || []
})

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化货币
const formatCurrency = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 4
  }).format(num)
}

// 格式化数字
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

// 获取Agent状态
const fetchAgentStatus = async () => {
  try {
    const response = await fetch('/api/agent/status')
    const data = await response.json()
    if (data.success) {
      agentStatus.value = data
    }
  } catch (e) {
    console.error('获取Agent状态失败:', e)
  }
}

// 获取Token使用统计
const fetchTokenUsage = async () => {
  try {
    const response = await fetch('/api/agent/token-usage?limit=30')
    const data = await response.json()
    if (data.success) {
      tokenUsage.value = data
    }
  } catch (e) {
    console.error('获取Token使用统计失败:', e)
  }
}

// 获取决策历史
const fetchDecisionHistory = async () => {
  try {
    const response = await fetch('/api/agent/history?limit=20')
    const data = await response.json()
    if (data.success) {
      decisionHistory.value = data.history || []
    }
  } catch (e) {
    console.error('获取决策历史失败:', e)
  }
}

// 获取工作流数据
const fetchWorkflow = async () => {
  try {
    const response = await fetch('/api/agent/workflow')
    const data = await response.json()
    if (data.success) {
      workflowData.value = data.workflow
    }
  } catch (e) {
    console.error('获取工作流失败:', e)
  }
}

// 刷新所有数据
const refreshAll = async () => {
  refreshing.value = true
  await Promise.all([
    fetchAgentStatus(),
    fetchTokenUsage(),
    fetchDecisionHistory(),
    fetchWorkflow()
  ])
  refreshing.value = false
}

// 清空Token记录
const clearTokenUsage = async () => {
  if (!confirm('确定要清空Token使用记录吗？')) return

  try {
    const response = await fetch('/api/agent/token-usage/clear', {
      method: 'POST'
    })
    const data = await response.json()
    if (data.success) {
      await fetchTokenUsage()
    } else {
      alert('清空失败: ' + (data.error || '未知错误'))
    }
  } catch (e) {
    console.error('清空Token记录失败:', e)
    alert('清空失败')
  }
}

// 获取Skill图标
const getSkillIcon = (category: string) => {
  switch (category) {
    case 'exploration':
      return MagnifyingGlassIcon
    case 'decision':
      return LightBulbIcon
    case 'evaluation':
      return ClipboardDocumentCheckIcon
    default:
      return DocumentTextIcon
  }
}

// 获取阶段颜色
const getPhaseColor = (phase: string) => {
  switch (phase) {
    case 'explore':
      return 'blue'
    case 'decide':
      return 'green'
    case 'evaluate':
      return 'purple'
    default:
      return 'gray'
  }
}

// 页面加载时获取数据
onMounted(() => {
  refreshAll()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-8">
      <div class="flex items-center">
        <CpuChipIcon class="w-8 h-8 text-purple-400 mr-3" />
        <h1 class="text-2xl font-bold text-white">LLM Agent 智能投资决策系统</h1>
      </div>
      <button
        @click="refreshAll"
        :disabled="refreshing"
        class="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors disabled:opacity-50"
      >
        <ArrowPathIcon class="w-5 h-5 mr-2" :class="{ 'animate-spin': refreshing }" />
        刷新
      </button>
    </div>

    <!-- Tab导航 -->
    <div class="flex space-x-4 mb-6">
      <button
        @click="activeTab = 'workflow'"
        :class="activeTab === 'workflow' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        class="px-4 py-2 rounded-lg transition-colors"
      >
        🔄 工作流程
      </button>
      <button
        @click="activeTab = 'status'"
        :class="activeTab === 'status' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        class="px-4 py-2 rounded-lg transition-colors"
      >
        📊 运行状态
      </button>
      <button
        @click="activeTab = 'history'"
        :class="activeTab === 'history' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        class="px-4 py-2 rounded-lg transition-colors"
      >
        📜 决策历史
      </button>
    </div>

    <!-- 工作流程Tab -->
    <div v-if="activeTab === 'workflow'" class="space-y-6">
      <!-- 工作流程说明 -->
      <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h2 class="text-xl font-semibold text-white mb-4">{{ workflowData.name }}</h2>
        <p class="text-gray-300 mb-6">{{ workflowData.description }}</p>

        <!-- 流程图 -->
        <div class="flex items-center justify-center mb-8">
          <div class="flex items-center space-x-4">
            <!-- 探索 -->
            <div class="flex flex-col items-center">
              <div class="w-16 h-16 bg-blue-600/30 rounded-full flex items-center justify-center border-2 border-blue-500">
                <MagnifyingGlassIcon class="w-8 h-8 text-blue-400" />
              </div>
              <span class="text-blue-400 mt-2 font-medium">探索</span>
              <span class="text-gray-500 text-xs">EXPLORE</span>
            </div>

            <div class="flex items-center text-gray-500">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>

            <!-- 决策 -->
            <div class="flex flex-col items-center">
              <div class="w-16 h-16 bg-green-600/30 rounded-full flex items-center justify-center border-2 border-green-500">
                <LightBulbIcon class="w-8 h-8 text-green-400" />
              </div>
              <span class="text-green-400 mt-2 font-medium">决策</span>
              <span class="text-gray-500 text-xs">DECIDE</span>
            </div>

            <div class="flex items-center text-gray-500">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>

            <!-- 评估 -->
            <div class="flex flex-col items-center">
              <div class="w-16 h-16 bg-purple-600/30 rounded-full flex items-center justify-center border-2 border-purple-500">
                <ClipboardDocumentCheckIcon class="w-8 h-8 text-purple-400" />
              </div>
              <span class="text-purple-400 mt-2 font-medium">评估</span>
              <span class="text-gray-500 text-xs">EVALUATE</span>
            </div>

            <!-- 循环箭头 -->
            <div class="flex items-center text-gray-500 ml-4">
              <svg class="w-8 h-8 transform rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- 三个阶段卡片 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 探索阶段 -->
        <div class="bg-gray-800 rounded-xl border border-blue-500/30 overflow-hidden">
          <div class="bg-blue-600/20 px-4 py-3 border-b border-blue-500/30">
            <div class="flex items-center">
              <MagnifyingGlassIcon class="w-5 h-5 text-blue-400 mr-2" />
              <h3 class="text-lg font-semibold text-blue-400">探索阶段</h3>
            </div>
            <p class="text-gray-400 text-sm mt-1">信息收集与市场分析</p>
          </div>
          <div class="p-4 space-y-3">
            <div
              v-for="skill in exploreSkills"
              :key="skill.name"
              class="bg-gray-900/50 rounded-lg p-3 hover:bg-gray-900/70 transition-colors"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-white font-medium">{{ skill.display_name }}</span>
                <span class="text-blue-400 text-xs px-2 py-0.5 bg-blue-900/30 rounded">P{{ skill.priority }}</span>
              </div>
              <p class="text-gray-400 text-sm">{{ skill.description }}</p>
            </div>
          </div>
        </div>

        <!-- 决策阶段 -->
        <div class="bg-gray-800 rounded-xl border border-green-500/30 overflow-hidden">
          <div class="bg-green-600/20 px-4 py-3 border-b border-green-500/30">
            <div class="flex items-center">
              <LightBulbIcon class="w-5 h-5 text-green-400 mr-2" />
              <h3 class="text-lg font-semibold text-green-400">决策阶段</h3>
            </div>
            <p class="text-gray-400 text-sm mt-1">交易决策与执行</p>
          </div>
          <div class="p-4 space-y-3">
            <div
              v-for="skill in decideSkills"
              :key="skill.name"
              class="bg-gray-900/50 rounded-lg p-3 hover:bg-gray-900/70 transition-colors"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-white font-medium">{{ skill.display_name }}</span>
                <span class="text-green-400 text-xs px-2 py-0.5 bg-green-900/30 rounded">P{{ skill.priority }}</span>
              </div>
              <p class="text-gray-400 text-sm">{{ skill.description }}</p>
            </div>
          </div>
        </div>

        <!-- 评估阶段 -->
        <div class="bg-gray-800 rounded-xl border border-purple-500/30 overflow-hidden">
          <div class="bg-purple-600/20 px-4 py-3 border-b border-purple-500/30">
            <div class="flex items-center">
              <ClipboardDocumentCheckIcon class="w-5 h-5 text-purple-400 mr-2" />
              <h3 class="text-lg font-semibold text-purple-400">评估阶段</h3>
            </div>
            <p class="text-gray-400 text-sm mt-1">结果评估与策略优化</p>
          </div>
          <div class="p-4 space-y-3">
            <div
              v-for="skill in evaluateSkills"
              :key="skill.name"
              class="bg-gray-900/50 rounded-lg p-3 hover:bg-gray-900/70 transition-colors"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-white font-medium">{{ skill.display_name }}</span>
                <span class="text-purple-400 text-xs px-2 py-0.5 bg-purple-900/30 rounded">P{{ skill.priority }}</span>
              </div>
              <p class="text-gray-400 text-sm">{{ skill.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 循环说明 -->
      <div class="bg-gradient-to-r from-blue-900/30 via-green-900/30 to-purple-900/30 rounded-xl p-6 border border-gray-700">
        <h3 class="text-lg font-semibold text-white mb-3">🔄 持续迭代机制</h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-2xl mb-1">📝</div>
            <p class="text-gray-300 text-sm">记录决策过程</p>
          </div>
          <div class="text-center">
            <div class="text-2xl mb-1">💾</div>
            <p class="text-gray-300 text-sm">更新持仓状态</p>
          </div>
          <div class="text-center">
            <div class="text-2xl mb-1">⏰</div>
            <p class="text-gray-300 text-sm">自动触发下轮</p>
          </div>
          <div class="text-center">
            <div class="text-2xl mb-1">📈</div>
            <p class="text-gray-300 text-sm">持续优化策略</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 运行状态Tab -->
    <div v-if="activeTab === 'status'" class="space-y-6">
      <!-- Agent状态卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- 可用状态 -->
        <div class="stat-card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <p class="stat-label">Agent状态</p>
              <div class="flex items-center mt-1">
                <CheckCircleIcon v-if="agentStatus.available" class="w-6 h-6 text-green-400 mr-2" />
                <XCircleIcon v-else class="w-6 h-6 text-red-400 mr-2" />
                <span :class="agentStatus.available ? 'text-green-400' : 'text-red-400'" class="font-medium">
                  {{ agentStatus.available ? '可用' : '不可用' }}
                </span>
              </div>
            </div>
          </div>
          <p class="text-gray-400 text-sm">
            {{ agentStatus.enabled ? '已启用' : '已禁用' }}
          </p>
        </div>

        <!-- 模型信息 -->
        <div class="stat-card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <p class="stat-label">使用模型</p>
              <p class="stat-value text-purple-400">{{ agentStatus.model || '-' }}</p>
            </div>
            <div class="p-3 bg-purple-900/50 rounded-lg">
              <CpuChipIcon class="w-8 h-8 text-purple-400" />
            </div>
          </div>
          <p class="text-gray-400 text-sm">
            Temperature: {{ agentStatus.temperature }}
          </p>
        </div>

        <!-- API调用次数 -->
        <div class="stat-card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <p class="stat-label">API调用次数</p>
              <p class="stat-value text-blue-400">{{ formatNumber(tokenUsage.summary?.total_calls || 0) }}</p>
            </div>
            <div class="p-3 bg-blue-900/50 rounded-lg">
              <ChartBarIcon class="w-8 h-8 text-blue-400" />
            </div>
          </div>
          <p class="text-gray-400 text-sm">
            决策次数: {{ agentStatus.decision_history_count || 0 }}
          </p>
        </div>

        <!-- 总费用 -->
        <div class="stat-card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <p class="stat-label">累计费用</p>
              <p class="stat-value text-yellow-400">{{ formatCurrency(tokenUsage.summary?.total_cost || 0) }}</p>
            </div>
            <div class="p-3 bg-yellow-900/50 rounded-lg">
              <ChartBarIcon class="w-8 h-8 text-yellow-400" />
            </div>
          </div>
          <p class="text-gray-400 text-sm">
            平均每次: {{ formatCurrency(tokenUsage.summary?.avg_cost_per_call || 0) }}
          </p>
        </div>
      </div>

      <!-- Token使用详情 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Token统计 -->
        <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-white flex items-center">
              <ChartBarIcon class="w-5 h-5 mr-2 text-purple-400" />
              Token 使用统计
            </h2>
            <button
              @click="clearTokenUsage"
              class="flex items-center px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-sm transition-colors"
            >
              <TrashIcon class="w-4 h-4 mr-1" />
              清空记录
            </button>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div class="bg-gray-900/50 rounded-lg p-4">
              <p class="text-gray-400 text-sm mb-1">输入Token</p>
              <p class="text-2xl font-bold text-blue-400">
                {{ formatNumber(tokenUsage.summary?.total_tokens?.prompt || 0) }}
              </p>
            </div>
            <div class="bg-gray-900/50 rounded-lg p-4">
              <p class="text-gray-400 text-sm mb-1">输出Token</p>
              <p class="text-2xl font-bold text-green-400">
                {{ formatNumber(tokenUsage.summary?.total_tokens?.completion || 0) }}
              </p>
            </div>
            <div class="bg-gray-900/50 rounded-lg p-4">
              <p class="text-gray-400 text-sm mb-1">总Token</p>
              <p class="text-2xl font-bold text-purple-400">
                {{ formatNumber(tokenUsage.summary?.total_tokens?.all || 0) }}
              </p>
            </div>
          </div>

          <div class="mt-4 bg-gray-900/50 rounded-lg p-4">
            <div class="flex justify-between items-center">
              <span class="text-gray-400">平均每次调用Token</span>
              <span class="text-white font-medium">
                {{ formatNumber(tokenUsage.summary?.avg_tokens_per_call || 0) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 最近API调用记录 -->
        <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 class="text-lg font-semibold text-white flex items-center mb-4">
            <ClockIcon class="w-5 h-5 mr-2 text-blue-400" />
            最近API调用
          </h2>

          <div class="space-y-3 max-h-64 overflow-y-auto">
            <div
              v-for="(call, index) in tokenUsage.recent_calls"
              :key="index"
              class="bg-gray-900/50 rounded-lg p-3 flex items-center justify-between"
            >
              <div>
                <p class="text-white text-sm font-medium">{{ call.model }}</p>
                <p class="text-gray-400 text-xs">{{ formatDate(call.timestamp) }}</p>
              </div>
              <div class="text-right">
                <p class="text-blue-400 text-sm">{{ call.prompt_tokens }} + {{ call.completion_tokens }}</p>
                <p class="text-yellow-400 text-xs">{{ formatCurrency(call.total_cost) }}</p>
              </div>
            </div>

            <div v-if="!tokenUsage.recent_calls?.length" class="text-center py-8 text-gray-500">
              <ExclamationTriangleIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>暂无API调用记录</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 决策历史Tab -->
    <div v-if="activeTab === 'history'" class="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h2 class="text-lg font-semibold text-white flex items-center mb-4">
        <DocumentTextIcon class="w-5 h-5 mr-2 text-green-400" />
        决策历史
      </h2>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-gray-400 text-sm border-b border-gray-700">
              <th class="pb-3 pr-4">时间</th>
              <th class="pb-3 pr-4">操作</th>
              <th class="pb-3 pr-4">详情</th>
              <th class="pb-3 pr-4">理由</th>
              <th class="pb-3">置信度</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(record, index) in decisionHistory"
              :key="index"
              class="border-b border-gray-700/50 hover:bg-gray-700/30"
            >
              <td class="py-3 pr-4 text-gray-300 text-sm">
                {{ formatDate(record.timestamp) }}
              </td>
              <td class="py-3 pr-4">
                <span
                  :class="{
                    'bg-green-900/50 text-green-400': record.validated_decisions?.[0]?.skill === 'buy',
                    'bg-red-900/50 text-red-400': record.validated_decisions?.[0]?.skill === 'sell',
                    'bg-blue-900/50 text-blue-400': record.validated_decisions?.[0]?.skill === 'hold',
                    'bg-purple-900/50 text-purple-400': record.validated_decisions?.[0]?.skill === 'rebalance'
                  }"
                  class="px-2 py-1 rounded text-xs font-medium"
                >
                  {{ record.validated_decisions?.[0]?.skill || '-' }}
                </span>
              </td>
              <td class="py-3 pr-4 text-gray-300 text-sm">
                <template v-if="record.validated_decisions?.[0]?.parameters">
                  <span v-if="record.validated_decisions[0].parameters.symbol">
                    {{ record.validated_decisions[0].parameters.symbol }}
                  </span>
                  <span v-if="record.validated_decisions[0].parameters.shares" class="ml-2">
                    {{ record.validated_decisions[0].parameters.shares }}股
                  </span>
                </template>
                <span v-else>-</span>
              </td>
              <td class="py-3 pr-4 text-gray-300 text-sm max-w-xs truncate">
                {{ record.validated_decisions?.[0]?.reason || '-' }}
              </td>
              <td class="py-3">
                <div class="flex items-center">
                  <div class="w-16 bg-gray-700 rounded-full h-2 mr-2">
                    <div
                      class="bg-purple-500 h-2 rounded-full"
                      :style="{ width: (record.validated_decisions?.[0]?.parameters?.confidence || 0) * 100 + '%' }"
                    ></div>
                  </div>
                  <span class="text-gray-400 text-sm">
                    {{ ((record.validated_decisions?.[0]?.parameters?.confidence || 0) * 100).toFixed(0) }}%
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="!decisionHistory.length" class="text-center py-12 text-gray-500">
          <ExclamationTriangleIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>暂无决策历史</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  @apply bg-gray-800 rounded-xl p-6 border border-gray-700;
}

.stat-label {
  @apply text-gray-400 text-sm mb-1;
}

.stat-value {
  @apply text-2xl font-bold;
}
</style>