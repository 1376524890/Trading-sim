import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// API 基础地址
const API_BASE = '/api'

export interface Stock {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  marketCap: string
}

export interface Holding {
  symbol: string
  name: string
  shares: number
  avgPrice: number
  currentPrice: number
  marketValue: number
  costBasis: number
  gainLoss: number
  gainLossPercent: number
}

export interface Transaction {
  id: string
  symbol: string
  type: 'buy' | 'sell'
  shares: number
  price: number
  total: number
  timestamp: Date
  fees: number
}

export interface MarketNews {
  id: string
  title: string
  summary: string
  source: string
  timestamp: Date
  sentiment: 'positive' | 'negative' | 'neutral'
  relatedSymbols: string[]
}

export interface SystemStats {
  totalEquity: number
  cash: number
  invested: number
  dayGain: number
  dayGainPercent: number
  totalGain: number
  totalGainPercent: number
  winRate: number
  totalTrades: number
  // 新增分析指标
  sharpeRatio?: number
  profitFactor?: number
  maxDrawdown?: number
  volatility?: number
}

// 风险分析接口
export interface RiskAnalysis {
  status: string
  position_count: number
  concentration: number
  max_drawdown: number
  diversification_score: number
}

// 个股表现接口
export interface StockPerformance {
  symbol: string
  name: string
  allocation: number
  change: number
}

// 近期活动接口
export interface RecentActivity {
  day: string
  buys: number
  sells: number
  volume: number
}

// AI建议接口
export interface AIRecommendation {
  symbol: string
  action: string
  reason: string
  confidence: number
  targetPrice: number
  timeHorizon: string
}

// K线数据接口
export interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export const useStockStore = defineStore('stock', () => {
  // Loading states
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdate = ref<Date | null>(null)

  // System Stats
  const stats = ref<SystemStats>({
    totalEquity: 0,
    cash: 0,
    invested: 0,
    dayGain: 0,
    dayGainPercent: 0,
    totalGain: 0,
    totalGainPercent: 0,
    winRate: 0,
    totalTrades: 0
  })

  // Holdings
  const holdings = ref<Holding[]>([])

  // Transactions
  const transactions = ref<Transaction[]>([])

  // News
  const news = ref<MarketNews[]>([])

  // 风险分析
  const riskAnalysis = ref<RiskAnalysis | null>(null)

  // 个股表现
  const stockPerformance = ref<StockPerformance[]>([])

  // AI建议
  const aiRecommendations = ref<AIRecommendation[]>([])

  // 股票池数据
  const stockPool = ref<any[]>([])

  // 市场情绪
  const marketSentiment = ref({
    overall: 50,
    technology: 50,
    healthcare: 50,
    finance: 50,
    consumer: 50,
    energy: 50
  })

  // 股票名称映射 (A 股代码 -> 名称)
  const stockNames: Record<string, string> = {
    '601398.SS': '工商银行',
    '600519.SS': '贵州茅台',
    '000001.SZ': '平安银行',
    '600036.SS': '招商银行',
    '601318.SS': '中国平安',
    '000858.SZ': '五粮液',
    '600000.SS': '浦发银行',
    '601166.SS': '兴业银行',
    '600276.SS': '恒瑞医药',
    '000333.SZ': '美的集团'
  }

  // 获取股票名称
  const getStockName = (symbol: string): string => {
    return stockNames[symbol] || symbol
  }

  // Fetch portfolio summary (多样化投资系统)
  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/diversified/summary`)
      const data = response.data

      if (!data.success) {
        throw new Error(data.error || '获取数据失败')
      }

      stats.value = {
        totalEquity: data.total_equity || 0,
        cash: data.cash || 0,
        invested: (data.total_equity || 0) - (data.cash || 0),
        dayGain: 0,
        dayGainPercent: 0,
        totalGain: data.total_pnl || 0,
        totalGainPercent: data.total_pnl_pct || 0,
        winRate: 0,
        totalTrades: 0,
        sharpeRatio: 0,
        profitFactor: 0,
        maxDrawdown: 0,
        volatility: 0
      }
    } catch (e) {
      console.error('Failed to fetch summary:', e)
      throw e
    }
  }

  // Fetch holdings (多样化投资系统)
  const fetchHoldings = async () => {
    try {
      const response = await axios.get(`${API_BASE}/diversified/positions`)
      const data = response.data

      if (!data.success || !data.positions) {
        holdings.value = []
        return
      }

      holdings.value = data.positions.map((pos: any) => ({
        symbol: pos.symbol,
        name: pos.name || getStockName(pos.symbol),
        shares: pos.shares,
        avgPrice: pos.avg_cost,
        currentPrice: pos.current_price,
        marketValue: pos.market_value,
        costBasis: pos.shares * pos.avg_cost,
        gainLoss: pos.pnl,
        gainLossPercent: pos.pnl_pct
      }))
    } catch (e) {
      console.error('Failed to fetch holdings:', e)
      throw e
    }
  }

  // Fetch trade history
  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/trade/history`)
      const data = response.data

      if (!data.trades) {
        transactions.value = []
        return
      }

      transactions.value = data.trades.map((trade: any, index: number) => ({
        id: `TXN${String(index + 1).padStart(3, '0')}`,
        symbol: trade.symbol,
        type: trade.type as 'buy' | 'sell',
        shares: trade.shares,
        price: trade.price,
        total: trade.shares * trade.price,
        timestamp: new Date(trade.time),
        fees: 5 // 默认手续费
      }))
    } catch (e) {
      console.error('Failed to fetch transactions:', e)
      throw e
    }
  }

  // Fetch news
  const fetchNews = async () => {
    try {
      const response = await axios.get(`${API_BASE}/news?limit=10`)
      const data = response.data

      // 如果后端有错误或没有数据，使用默认新闻
      if (data.error || data.total === 0) {
        news.value = getDefaultNews()
        return
      }

      const allNews: MarketNews[] = []

      // 合并所有分类的新闻
      for (const sentiment of ['positive', 'neutral', 'negative'] as const) {
        const items = data.categorized?.[sentiment] || []
        for (const item of items) {
          allNews.push({
            id: item.id || `NEWS${Date.now()}`,
            title: item.title || '',
            summary: item.summary || item.content || '',
            source: item.source || '财经资讯',
            timestamp: new Date(item.publish_time || item.timestamp || Date.now()),
            sentiment: sentiment,
            relatedSymbols: item.related_symbols || item.symbols || []
          })
        }
      }

      news.value = allNews.length > 0 ? allNews : getDefaultNews()
    } catch (e) {
      console.error('Failed to fetch news:', e)
      news.value = getDefaultNews()
    }
  }

  // 默认新闻 (当后端无法获取时使用)
  const getDefaultNews = (): MarketNews[] => [
    {
      id: 'NEWS001',
      title: 'A 股市场早报：关注金融板块走势',
      summary: '今日 A 股市场开盘，银行板块表现活跃，投资者关注金融股走势。',
      source: '财经日报',
      timestamp: new Date(),
      sentiment: 'neutral',
      relatedSymbols: ['601398.SS', '600036.SS']
    },
    {
      id: 'NEWS002',
      title: '央行发布最新货币政策报告',
      summary: '央行发布季度货币政策执行报告，强调保持流动性合理充裕。',
      source: '央行官网',
      timestamp: new Date(Date.now() - 3600000),
      sentiment: 'positive',
      relatedSymbols: []
    }
  ]

  // Fetch risk analysis
  const fetchRiskAnalysis = async () => {
    try {
      const response = await axios.get(`${API_BASE}/analysis/risk`)
      riskAnalysis.value = response.data
    } catch (e) {
      console.error('Failed to fetch risk analysis:', e)
      // 使用默认风险分析
      riskAnalysis.value = {
        status: 'no_positions',
        position_count: 0,
        concentration: 0,
        max_drawdown: 0,
        diversification_score: 50
      }
    }
  }

  // Calculate stock performance from holdings
  const calculateStockPerformance = () => {
    if (holdings.value.length === 0) {
      stockPerformance.value = []
      return
    }

    const totalMarketValue = holdings.value.reduce((sum, h) => sum + h.marketValue, 0)

    stockPerformance.value = holdings.value.map(holding => ({
      symbol: holding.symbol,
      name: holding.name,
      allocation: totalMarketValue > 0 ? (holding.marketValue / totalMarketValue) * 100 : 0,
      change: holding.gainLossPercent
    })).sort((a, b) => b.allocation - a.allocation)
  }

  // Calculate recent activity from transactions
  const calculateRecentActivity = (): RecentActivity[] => {
    if (transactions.value.length === 0) {
      return []
    }

    const activityMap = new Map<string, { buys: number, sells: number, volume: number }>()
    const now = new Date()

    // 初始化最近7天
    for (let i = 0; i < 7; i++) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const key = date.toDateString()
      activityMap.set(key, { buys: 0, sells: 0, volume: 0 })
    }

    // 统计交易
    transactions.value.forEach(txn => {
      const txnDate = new Date(txn.timestamp).toDateString()
      if (activityMap.has(txnDate)) {
        const activity = activityMap.get(txnDate)!
        if (txn.type === 'buy') {
          activity.buys++
        } else {
          activity.sells++
        }
        activity.volume += txn.total
      }
    })

    // 转换为数组格式
    const result: RecentActivity[] = []
    for (let i = 0; i < 7; i++) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const key = date.toDateString()
      const activity = activityMap.get(key)!

      let dayLabel: string
      if (i === 0) dayLabel = '今天'
      else if (i === 1) dayLabel = '昨天'
      else dayLabel = `${i} 天前`

      result.push({
        day: dayLabel,
        buys: activity.buys,
        sells: activity.sells,
        volume: activity.volume
      })
    }

    return result
  }

  // Fetch stock history (K-line data)
  const fetchStockHistory = async (symbol: string, days: number = 30): Promise<KLineData[]> => {
    try {
      const response = await axios.get(`${API_BASE}/stock/history?symbol=${symbol}&days=${days}`)
      const data = response.data

      if (!data.data || data.data.length === 0) {
        return []
      }

      return data.data.map((item: any) => ({
        date: item.date,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume
      }))
    } catch (e) {
      console.error('Failed to fetch stock history:', e)
      return []
    }
  }

  // 获取股票池
  const fetchStockPool = async () => {
    try {
      const response = await axios.get(`${API_BASE}/diversified/stock-pool`)
      const data = response.data

      if (!data.success || !data.stock_pool) {
        return []
      }

      // 将所有板块的股票合并为一个数组
      const allStocks: any[] = []
      for (const sector in data.stock_pool) {
        for (const stock of data.stock_pool[sector]) {
          allStocks.push({
            ...stock,
            sector
          })
        }
      }
      stockPool.value = allStocks
      return allStocks
    } catch (e) {
      console.error('Failed to fetch stock pool:', e)
      return []
    }
  }

  // Calculate AI recommendations from holdings
  const calculateAIRecommendations = (): AIRecommendation[] => {
    if (holdings.value.length === 0) {
      return []
    }

    return holdings.value.map(holding => {
      const gainPct = holding.gainLossPercent
      let action: string
      let reason: string
      let confidence: number
      let targetPrice: number

      if (gainPct < -5) {
        action = '加仓'
        reason = `${holding.name}当前跌幅较大，估值处于相对低位，建议逢低加仓以摊低成本`
        confidence = Math.min(70 + Math.abs(gainPct), 90)
        targetPrice = holding.currentPrice * 1.1
      } else if (gainPct > 10) {
        action = '持有'
        reason = `${holding.name}表现良好，建议继续持有，可关注止盈机会`
        confidence = Math.min(75 + gainPct / 2, 90)
        targetPrice = holding.currentPrice * 1.15
      } else {
        action = '观望'
        reason = `${holding.name}走势平稳，建议继续观察，等待更明确的信号`
        confidence = 65
        targetPrice = holding.currentPrice * 1.08
      }

      return {
        symbol: holding.symbol,
        action,
        reason,
        confidence,
        targetPrice,
        timeHorizon: '1-3 个月'
      }
    })
  }

  // Calculate market sentiment based on holdings performance
  const calculateMarketSentiment = () => {
    const gainers = holdings.value.filter(h => h.gainLossPercent > 0).length
    // const losers = holdings.value.filter(h => h.gainLossPercent < 0).length  // 暂不使用
    const total = holdings.value.length

    if (total === 0) {
      marketSentiment.value = {
        overall: 50,
        technology: 50,
        healthcare: 50,
        finance: 50,
        consumer: 50,
        energy: 50
      }
      return
    }

    const overallScore = Math.round((gainers / total) * 100)

    marketSentiment.value = {
      overall: overallScore,
      technology: Math.min(overallScore + 5, 100),
      healthcare: Math.min(overallScore + 3, 100),
      finance: Math.max(overallScore - 2, 0),
      consumer: overallScore,
      energy: Math.max(overallScore - 5, 0)
    }
  }
  const fetchAllData = async () => {
    loading.value = true
    error.value = null

    try {
      await Promise.all([
        fetchSummary(),
        fetchHoldings(),
        fetchTransactions(),
        fetchNews(),
        fetchRiskAnalysis()
      ])

      // 计算衍生数据
      calculateStockPerformance()
      calculateMarketSentiment()
      aiRecommendations.value = calculateAIRecommendations()

      lastUpdate.value = new Date()
    } catch (e: any) {
      error.value = e.message || '获取数据失败'
      console.error('Failed to fetch data:', e)
    } finally {
      loading.value = false
    }
  }

  // Execute buy order
  const buyStock = async (symbol: string, shares: number) => {
    try {
      const response = await axios.post(`${API_BASE}/trade/buy`, {
        symbol,
        shares
      })
      if (response.data.success) {
        await fetchAllData()
      }
      return response.data
    } catch (e) {
      console.error('Buy failed:', e)
      throw e
    }
  }

  // Execute sell order
  const sellStock = async (symbol: string, shares: number) => {
    try {
      const response = await axios.post(`${API_BASE}/trade/sell`, {
        symbol,
        shares
      })
      if (response.data.success) {
        await fetchAllData()
      }
      return response.data
    } catch (e) {
      console.error('Sell failed:', e)
      throw e
    }
  }

  // ============ 多样化投资控制 ============

  // 初始建仓
  const initialBuild = async () => {
    try {
      const response = await axios.post(`${API_BASE}/diversified/initial-build`)
      if (response.data.success) {
        await fetchAllData()
      }
      return response.data
    } catch (e) {
      console.error('Initial build failed:', e)
      throw e
    }
  }

  // 调仓
  const rebalance = async () => {
    try {
      const response = await axios.post(`${API_BASE}/diversified/rebalance`)
      if (response.data.success) {
        await fetchAllData()
      }
      return response.data
    } catch (e) {
      console.error('Rebalance failed:', e)
      throw e
    }
  }

  // 自动运行
  const autoRun = async () => {
    try {
      const response = await axios.post(`${API_BASE}/diversified/auto-run`)
      if (response.data.success) {
        await fetchAllData()
      }
      return response.data
    } catch (e) {
      console.error('Auto run failed:', e)
      throw e
    }
  }

  // 检查止损止盈
  const checkStopLoss = async () => {
    try {
      const response = await axios.post(`${API_BASE}/diversified/check-stop-loss`)
      if (response.data.success) {
        await fetchAllData()
      }
      return response.data
    } catch (e) {
      console.error('Check stop loss failed:', e)
      throw e
    }
  }

  // 获取调度器状态
  const getSchedulerStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/diversified/scheduler/status`)
      return response.data
    } catch (e) {
      console.error('Get scheduler status failed:', e)
      throw e
    }
  }

  // 启动调度器
  const startScheduler = async (intervalMinutes: number = 30) => {
    try {
      const response = await axios.post(`${API_BASE}/diversified/scheduler/start?interval_minutes=${intervalMinutes}`)
      return response.data
    } catch (e) {
      console.error('Start scheduler failed:', e)
      throw e
    }
  }

  // 停止调度器
  const stopScheduler = async () => {
    try {
      const response = await axios.post(`${API_BASE}/diversified/scheduler/stop`)
      return response.data
    } catch (e) {
      console.error('Stop scheduler failed:', e)
      throw e
    }
  }

  // Computed
  const totalMarketValue = computed(() =>
    holdings.value.reduce((sum, h) => sum + h.marketValue, 0)
  )

  const totalGainLoss = computed(() =>
    holdings.value.reduce((sum, h) => sum + h.gainLoss, 0)
  )

  const totalGainLossPercent = computed(() => {
    const totalCost = holdings.value.reduce((sum, h) => sum + h.costBasis, 0)
    if (totalCost === 0) return 0
    return (totalGainLoss.value / totalCost) * 100
  })

  const topGainer = computed(() => {
    if (holdings.value.length === 0) return null
    return holdings.value.reduce((prev, current) =>
      current.gainLossPercent > prev.gainLossPercent ? current : prev
    )
  })

  const topLoser = computed(() => {
    if (holdings.value.length === 0) return null
    return holdings.value.reduce((prev, current) =>
      current.gainLossPercent < prev.gainLossPercent ? current : prev
    )
  })

  return {
    // State
    stats,
    holdings,
    transactions,
    news,
    riskAnalysis,
    stockPerformance,
    aiRecommendations,
    marketSentiment,
    stockPool,
    loading,
    error,
    lastUpdate,

    // Actions
    fetchAllData,
    fetchSummary,
    fetchHoldings,
    fetchTransactions,
    fetchNews,
    fetchRiskAnalysis,
    fetchStockHistory,
    fetchStockPool,
    calculateRecentActivity,
    calculateAIRecommendations,
    buyStock,
    sellStock,

    // 多样化投资控制
    initialBuild,
    rebalance,
    autoRun,
    checkStopLoss,
    getSchedulerStatus,
    startScheduler,
    stopScheduler,

    // Computed
    totalMarketValue,
    totalGainLoss,
    totalGainLossPercent,
    topGainer,
    topLoser
  }
})