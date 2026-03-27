<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
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
  ClipboardDocumentCheckIcon,
  BoltIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ArrowPathIcon as RefreshIcon,
  PlayIcon,
  PauseIcon
} from '@heroicons/vue/24/outline'

// 状态
const agentStatus = ref<any>({})
const tokenUsage = ref<any>({})
const decisionHistory = ref<any[]>([])
const workflowData = ref<any>({})
const workflowState = ref<any>({})
const schedulerStatus = ref<any>({})
const refreshing = ref(false)
const activeTab = ref<'workflow' | 'status' | 'history'>('workflow')

// 工作流状态轮询
const pollInterval = ref<number | null>(null)

// 展开的阶段
const expandedPhases = ref<Set<string>>(new Set(['explore', 'decide', 'evaluate']))

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

// 调度器运行状态
const isSchedulerRunning = computed(() => schedulerStatus.value?.running === true)

// 当前工作流运行状态
const isRunning = computed(() => workflowState.value?.status === 'running')
const currentPhase = computed(() => workflowState.value?.current_run?.current_phase)
const currentTool = computed(() => workflowState.value?.current_run?.current_tool)

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

// 格式化时间
const formatTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化持续时间
const formatDuration = (ms: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
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

// 获取工作流状态
const fetchWorkflowState = async () => {
  try {
    const response = await fetch('/api/agent/workflow/state')
    const data = await response.json()
    if (data.success) {
      workflowState.value = data
    }
  } catch (e) {
    console.error('获取工作流状态失败:', e)
  }
}

// 获取调度器状态
const fetchSchedulerStatus = async () => {
  try {
    const response = await fetch('/api/diversified/scheduler/status')
    schedulerStatus.value = await response.json()
  } catch (e) {
    console.error('获取调度器状态失败:', e)
  }
}

// 刷新所有数据
const refreshAll = async () => {
  refreshing.value = true
  await Promise.all([
    fetchAgentStatus(),
    fetchTokenUsage(),
    fetchDecisionHistory(),
    fetchWorkflow(),
    fetchWorkflowState(),
    fetchSchedulerStatus()
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

// 切换阶段展开状态
const togglePhase = (phase: string) => {
  if (expandedPhases.value.has(phase)) {
    expandedPhases.value.delete(phase)
  } else {
    expandedPhases.value.add(phase)
  }
}

// 获取阶段颜色
const getPhaseColor = (phase: string) => {
  switch (phase) {
    case 'explore': return { bg: 'bg-blue-600', border: 'border-blue-500', text: 'text-blue-400', light: 'bg-blue-600/20' }
    case 'decide': return { bg: 'bg-green-600', border: 'border-green-500', text: 'text-green-400', light: 'bg-green-600/20' }
    case 'evaluate': return { bg: 'bg-purple-600', border: 'border-purple-500', text: 'text-purple-400', light: 'bg-purple-600/20' }
    default: return { bg: 'bg-gray-600', border: 'border-gray-500', text: 'text-gray-400', light: 'bg-gray-600/20' }
  }
}

// 获取状态图标
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed': return CheckCircleIcon
    case 'running': return BoltIcon
    case 'failed': return XCircleIcon
    case 'skipped': return PauseIcon
    default: return ClockIcon
  }
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'text-green-400'
    case 'running': return 'text-yellow-400 animate-pulse'
    case 'failed': return 'text-red-400'
    case 'skipped': return 'text-gray-500'
    default: return 'text-gray-400'
  }
}

// 获取工具状态颜色
const getToolStatusColor = (status: string) => {
  switch (status) {
    case 'success': return 'border-green-500 bg-green-900/20'
    case 'running': return 'border-yellow-500 bg-yellow-900/20'
    case 'failed': return 'border-red-500 bg-red-900/20'
    default: return 'border-gray-600 bg-gray-800/50'
  }
}

// 开始轮询
const startPolling = () => {
  if (pollInterval.value) return
  pollInterval.value = window.setInterval(() => {
    fetchWorkflowState()
    fetchSchedulerStatus()
  }, 2000) // 2秒轮询一次
}

// 停止轮询
const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

// 页面加载时获取数据
onMounted(() => {
  refreshAll()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-8">
      <div class="flex items-center">
        <CpuChipIcon class="w-8 h-8 text-purple-400 mr-3" />
        <div>
          <h1 class="text-2xl font-bold text-white">LLM Agent 智能投资决策系统</h1>
          <p class="text-sm text-gray-400 mt-1">探索-决策-评估 三阶段投资分析工作流</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <button
          @click="refreshAll"
          :disabled="refreshing"
          class="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors disabled:opacity-50"
        >
          <RefreshIcon class="w-5 h-5 mr-2" :class="{ 'animate-spin': refreshing }" />
          刷新
        </button>
      </div>
    </div>

    <!-- 调度器状态卡片 -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 p-4 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div class="flex items-center">
            <div
              class="w-3 h-3 rounded-full mr-2"
              :class="isSchedulerRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'"
            ></div>
            <span class="text-white font-medium">
              {{ isSchedulerRunning ? '调度器运行中' : '调度器已停止' }}
            </span>
          </div>
          <div v-if="isSchedulerRunning" class="text-sm text-gray-400">
            <span>间隔: {{ schedulerStatus.interval_minutes }} 分钟</span>
          </div>
        </div>
        <div class="flex items-center space-x-4 text-sm">
          <div v-if="schedulerStatus.last_run" class="text-gray-400">
            <span class="text-gray-500">上次运行:</span>
            <span class="ml-1 text-white">{{ formatTime(schedulerStatus.last_run) }}</span>
          </div>
          <div v-if="schedulerStatus.next_run" class="text-gray-400">
            <span class="text-gray-500">下次运行:</span>
            <span class="ml-1 text-green-400">{{ formatTime(schedulerStatus.next_run) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab导航 -->
    <div class="flex space-x-2 mb-6 border-b border-gray-700 pb-4">
      <button
        @click="activeTab = 'workflow'"
        :class="activeTab === 'workflow' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        class="px-4 py-2 rounded-lg transition-colors text-sm font-medium"
      >
        🔄 工作流程
      </button>
      <button
        @click="activeTab = 'status'"
        :class="activeTab === 'status' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        class="px-4 py-2 rounded-lg transition-colors text-sm font-medium"
      >
        📊 运行状态
      </button>
      <button
        @click="activeTab = 'history'"
        :class="activeTab === 'history' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        class="px-4 py-2 rounded-lg transition-colors text-sm font-medium"
      >
        📜 决策历史
      </button>
    </div>

    <!-- 工作流程Tab -->
    <div v-if="activeTab === 'workflow'" class="space-y-6">
      <!-- 实时状态指示器 -->
      <div v-if="workflowState.current_run || isRunning" class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div class="bg-gradient-to-r from-purple-900/50 to-blue-900/50 px-4 py-3 border-b border-gray-700">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <BoltIcon class="w-5 h-5 text-yellow-400 mr-2 animate-pulse" />
              <span class="font-semibold text-white">正在执行工作流</span>
              <span class="ml-3 text-sm text-gray-400">
                {{ workflowState.current_run?.run_id }}
              </span>
            </div>
            <div v-if="workflowState.current_run?.duration_ms" class="text-sm text-gray-400">
              耗时: {{ formatDuration(workflowState.current_run.duration_ms) }}
            </div>
          </div>
        </div>

        <!-- 阶段进度条 -->
        <div class="p-4">
          <div class="flex items-center justify-between mb-4">
            <template v-for="(phase, index) in ['explore', 'decide', 'evaluate']" :key="phase">
              <div class="flex items-center">
                <div
                  class="w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all"
                  :class="[
                    workflowState.current_run?.phases?.[phase]?.status === 'completed'
                      ? 'bg-green-600 border-green-500'
                      : workflowState.current_run?.phases?.[phase]?.status === 'running'
                        ? 'bg-yellow-600 border-yellow-500 animate-pulse'
                        : 'bg-gray-700 border-gray-600'
                  ]"
                >
                  <MagnifyingGlassIcon v-if="phase === 'explore'" class="w-6 h-6 text-white" />
                  <LightBulbIcon v-else-if="phase === 'decide'" class="w-6 h-6 text-white" />
                  <ClipboardDocumentCheckIcon v-else class="w-6 h-6 text-white" />
                </div>
                <div class="ml-2">
                  <div class="text-sm font-medium text-white capitalize">{{ phase === 'explore' ? '探索' : phase === 'decide' ? '决策' : '评估' }}</div>
                  <div class="text-xs text-gray-400">
                    {{ workflowState.current_run?.phases?.[phase]?.status || 'pending' }}
                  </div>
                </div>
              </div>
              <div v-if="index < 2" class="flex-1 h-0.5 mx-4" :class="workflowState.current_run?.phases?.[phase]?.status === 'completed' ? 'bg-green-500' : 'bg-gray-700'"></div>
            </template>
          </div>
        </div>
      </div>

      <!-- 等待下次运行提示 -->
      <div v-else-if="isSchedulerRunning && schedulerStatus.next_run" class="bg-gray-800/50 rounded-xl border border-gray-700 p-6 text-center">
        <ClockIcon class="w-12 h-12 text-gray-500 mx-auto mb-3" />
        <p class="text-gray-400">等待下次分析运行</p>
        <p class="text-white text-lg font-medium mt-1">{{ formatTime(schedulerStatus.next_run) }}</p>
      </div>

      <!-- 阶段详细卡片 -->
      <div class="space-y-4">
        <template v-for="phase in ['explore', 'decide', 'evaluate']" :key="phase">
          <div
            class="bg-gray-800 rounded-xl border overflow-hidden transition-all"
            :class="currentPhase === phase ? 'border-yellow-500' : getPhaseColor(phase).border"
          >
            <!-- 阶段头部 -->
            <div
              @click="togglePhase(phase)"
              class="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-700/50 transition-colors"
              :class="getPhaseColor(phase).light"
            >
              <div class="flex items-center">
                <component
                  :is="expandedPhases.has(phase) ? ChevronDownIcon : ChevronRightIcon"
                  class="w-5 h-5 text-gray-400 mr-2"
                />
                <component
                  :is="getStatusIcon(workflowState.current_run?.phases?.[phase]?.status || 'pending')"
                  class="w-5 h-5 mr-2"
                  :class="getStatusColor(workflowState.current_run?.phases?.[phase]?.status || 'pending')"
                />
                <span class="font-semibold text-white">
                  {{ phase === 'explore' ? '探索阶段' : phase === 'decide' ? '决策阶段' : '评估阶段' }}
                </span>
              </div>
              <div class="flex items-center space-x-3 text-sm">
                <span v-if="workflowState.current_run?.phases?.[phase]?.duration_ms" class="text-gray-400">
                  {{ formatDuration(workflowState.current_run.phases[phase].duration_ms) }}
                </span>
                <span
                  class="px-2 py-0.5 rounded text-xs"
                  :class="getStatusColor(workflowState.current_run?.phases?.[phase]?.status || 'pending')"
                >
                  {{ workflowState.current_run?.phases?.[phase]?.status || 'pending' }}
                </span>
              </div>
            </div>

            <!-- 阶段内容 -->
            <div v-if="expandedPhases.has(phase)" class="border-t border-gray-700">
              <!-- 工具调用列表 -->
              <div v-if="workflowState.current_run?.phases?.[phase]?.tool_calls?.length" class="p-4 space-y-3">
                <div
                  v-for="(tool, idx) in workflowState.current_run.phases[phase].tool_calls"
                  :key="idx"
                  class="rounded-lg border p-3"
                  :class="getToolStatusColor(tool.status)"
                >
                  <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                      <BoltIcon class="w-4 h-4 mr-2" :class="tool.status === 'running' ? 'animate-pulse text-yellow-400' : 'text-gray-400'" />
                      <span class="font-medium text-white text-sm">{{ tool.tool_name }}</span>
                    </div>
                    <div class="flex items-center space-x-2 text-xs">
                      <span v-if="tool.duration_ms" class="text-gray-400">{{ formatDuration(tool.duration_ms) }}</span>
                      <span
                        class="px-2 py-0.5 rounded"
                        :class="{
                          'bg-green-900/50 text-green-400': tool.status === 'success',
                          'bg-yellow-900/50 text-yellow-400': tool.status === 'running',
                          'bg-red-900/50 text-red-400': tool.status === 'failed'
                        }"
                      >
                        {{ tool.status }}
                      </span>
                    </div>
                  </div>

                  <!-- 工具结果 -->
                  <div v-if="tool.result" class="mt-2 p-2 bg-gray-900/50 rounded text-xs">
                    <pre class="text-gray-300 whitespace-pre-wrap overflow-auto max-h-32">{{ JSON.stringify(tool.result, null, 2) }}</pre>
                  </div>
                  <div v-if="tool.error" class="mt-2 p-2 bg-red-900/30 rounded text-xs text-red-400">
                    {{ tool.error }}
                  </div>
                </div>
              </div>

              <!-- 阶段摘要 -->
              <div v-if="workflowState.current_run?.phases?.[phase]?.summary" class="px-4 pb-4">
                <div class="bg-gray-900/50 rounded-lg p-3 text-sm text-gray-300">
                  {{ workflowState.current_run.phases[phase].summary }}
                </div>
              </div>

              <!-- 决策记录 -->
              <div v-if="phase === 'decide' && workflowState.current_run?.decisions?.length" class="p-4">
                <h4 class="text-sm font-medium text-white mb-2">决策记录</h4>
                <div class="space-y-2">
                  <div
                    v-for="(decision, idx) in workflowState.current_run.decisions"
                    :key="idx"
                    class="bg-gray-900/50 rounded-lg p-3"
                  >
                    <div class="flex items-center justify-between">
                      <span class="font-medium text-white">{{ decision.skill }}</span>
                      <span
                        class="px-2 py-0.5 rounded text-xs"
                        :class="{
                          'bg-green-900/50 text-green-400': decision.skill === 'buy',
                          'bg-red-900/50 text-red-400': decision.skill === 'sell',
                          'bg-blue-900/50 text-blue-400': decision.skill === 'hold'
                        }"
                      >
                        {{ decision.skill }}
                      </span>
                    </div>
                    <p class="text-sm text-gray-400 mt-1">{{ decision.reason }}</p>
                  </div>
                </div>
              </div>

              <!-- 静态Skills列表 -->
              <div v-if="!workflowState.current_run" class="p-4 space-y-2">
                <div
                  v-for="skill in (phase === 'explore' ? exploreSkills : phase === 'decide' ? decideSkills : evaluateSkills)"
                  :key="skill.name"
                  class="bg-gray-900/50 rounded-lg p-3 hover:bg-gray-900/70 transition-colors"
                >
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-white font-medium text-sm">{{ skill.display_name }}</span>
                    <span class="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">P{{ skill.priority }}</span>
                  </div>
                  <p class="text-gray-400 text-xs">{{ skill.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </template>
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