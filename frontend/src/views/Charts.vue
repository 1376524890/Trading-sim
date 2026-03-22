<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useStockStore } from '@/stores/stock'
import type { KLineData } from '@/stores/stock'
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type HistogramData,
  type LineData,
  type Time
} from 'lightweight-charts'

const store = useStockStore()
const selectedStock = ref<string>('')
const klineHistory = ref<KLineData[]>([])
const loadingHistory = ref(false)

// 图表容器引用
const chartContainerRef = ref<HTMLElement | null>(null)
const volumeChartContainerRef = ref<HTMLElement | null>(null)
const macdChartContainerRef = ref<HTMLElement | null>(null)

// 图表实例
let mainChart: IChartApi | null = null
let volumeChart: IChartApi | null = null
let macdChart: IChartApi | null = null
let candlestickSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
let ma5Series: ISeriesApi<'Line'> | null = null
let ma10Series: ISeriesApi<'Line'> | null = null
let ma20Series: ISeriesApi<'Line'> | null = null
let macdHistogramSeries: ISeriesApi<'Histogram'> | null = null
let macdLineSeries: ISeriesApi<'Line'> | null = null
let signalLineSeries: ISeriesApi<'Line'> | null = null

// 时间周期选择
const timeRange = ref<string>('60')
const timeRangeOptions = [
  { value: '30', label: '近30天' },
  { value: '60', label: '近60天' },
  { value: '90', label: '近90天' },
  { value: '180', label: '近半年' },
  { value: '365', label: '近一年' }
]

// 技术指标开关
const showMA = ref(true)
const showMACD = ref(true)
const showVolume = ref(true)

// 初始化选中第一只股票
onMounted(() => {
  if (store.holdings.length > 0) {
    selectedStock.value = store.holdings[0].symbol
  }
})

// 监听持仓变化
watch(() => store.holdings, (newHoldings) => {
  if (newHoldings.length > 0) {
    const exists = newHoldings.find(h => h.symbol === selectedStock.value)
    if (!exists) {
      selectedStock.value = newHoldings[0].symbol
    }
  }
}, { immediate: true })

// 获取K线数据
const fetchKLineData = async () => {
  if (!selectedStock.value) return

  loadingHistory.value = true
  try {
    const data = await store.fetchStockHistory(selectedStock.value, parseInt(timeRange.value))
    klineHistory.value = data
  } catch (e) {
    console.error('Failed to fetch K-line data:', e)
    klineHistory.value = []
  } finally {
    loadingHistory.value = false
  }
}

// 监听选中股票和时间范围变化
watch([selectedStock, timeRange], fetchKLineData, { immediate: true })

// 计算技术指标
const calculateMA = (data: KLineData[], period: number): LineData<Time>[] => {
  const result: LineData<Time>[] = []
  for (let i = period - 1; i < data.length; i++) {
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    result.push({
      time: data[i].date as Time,
      value: sum / period
    })
  }
  return result
}

const calculateEMA = (data: number[], period: number): number[] => {
  const result: number[] = []
  const multiplier = 2 / (period + 1)
  let ema = data[0]
  result.push(ema)
  for (let i = 1; i < data.length; i++) {
    ema = (data[i] - ema) * multiplier + ema
    result.push(ema)
  }
  return result
}

const calculateMACD = (data: KLineData[]): {
  macd: LineData<Time>[]
  signal: LineData<Time>[]
  histogram: HistogramData<Time>[]
} => {
  const closes = data.map(d => d.close)
  const ema12 = calculateEMA(closes, 12)
  const ema26 = calculateEMA(closes, 26)

  const dif = ema12.map((v, i) => v - ema26[i])
  const dea = calculateEMA(dif, 9)

  const macd: LineData<Time>[] = []
  const signal: LineData<Time>[] = []
  const histogram: HistogramData<Time>[] = []

  for (let i = 0; i < data.length; i++) {
    const macdValue = (dif[i] - dea[i]) * 2
    macd.push({ time: data[i].date as Time, value: dif[i] })
    signal.push({ time: data[i].date as Time, value: dea[i] })
    histogram.push({
      time: data[i].date as Time,
      value: macdValue,
      color: macdValue >= 0 ? '#22c55e' : '#ef4444'
    })
  }

  return { macd, signal, histogram }
}

const calculateRSI = (data: KLineData[], period: number = 14): LineData<Time>[] => {
  const result: LineData<Time>[] = []
  let gains = 0
  let losses = 0

  for (let i = 1; i <= period && i < data.length; i++) {
    const change = data[i].close - data[i - 1].close
    if (change >= 0) gains += change
    else losses -= change
  }

  let avgGain = gains / period
  let avgLoss = losses / period

  if (avgLoss === 0) {
    result.push({ time: data[period].date as Time, value: 100 })
  } else {
    const rs = avgGain / avgLoss
    result.push({ time: data[period].date as Time, value: 100 - (100 / (1 + rs)) })
  }

  for (let i = period + 1; i < data.length; i++) {
    const change = data[i].close - data[i - 1].close
    const gain = change >= 0 ? change : 0
    const loss = change < 0 ? -change : 0

    avgGain = (avgGain * (period - 1) + gain) / period
    avgLoss = (avgLoss * (period - 1) + loss) / period

    if (avgLoss === 0) {
      result.push({ time: data[i].date as Time, value: 100 })
    } else {
      const rs = avgGain / avgLoss
      result.push({ time: data[i].date as Time, value: 100 - (100 / (1 + rs)) })
    }
  }

  return result
}

// 初始化图表
const initCharts = () => {
  if (!chartContainerRef.value || klineHistory.value.length === 0) return

  // 清理旧图表
  if (mainChart) {
    mainChart.remove()
    mainChart = null
  }
  if (volumeChart) {
    volumeChart.remove()
    volumeChart = null
  }
  if (macdChart) {
    macdChart.remove()
    macdChart = null
  }

  const chartWidth = chartContainerRef.value.clientWidth

  // 主图 - K线图
  mainChart = createChart(chartContainerRef.value, {
    width: chartWidth,
    height: 400,
    layout: {
      background: { type: ColorType.Solid, color: '#1a1a2e' },
      textColor: '#9ca3af',
    },
    grid: {
      vertLines: { color: '#2d2d44' },
      horzLines: { color: '#2d2d44' },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: {
        color: '#758696',
        width: 1,
        style: 3,
        labelBackgroundColor: '#2962ff',
      },
      horzLine: {
        color: '#758696',
        width: 1,
        style: 3,
        labelBackgroundColor: '#2962ff',
      },
    },
    rightPriceScale: {
      borderColor: '#2d2d44',
      scaleMargins: { top: 0.1, bottom: 0.1 },
    },
    timeScale: {
      borderColor: '#2d2d44',
      timeVisible: true,
      secondsVisible: false,
    },
  })

  // 蜡烛图数据
  const candleData: CandlestickData<Time>[] = klineHistory.value.map(d => ({
    time: d.date as Time,
    open: d.open,
    high: d.high,
    low: d.low,
    close: d.close,
  }))

  candlestickSeries = mainChart.addSeries(CandlestickSeries, {
    upColor: '#22c55e',
    downColor: '#ef4444',
    borderUpColor: '#22c55e',
    borderDownColor: '#ef4444',
    wickUpColor: '#22c55e',
    wickDownColor: '#ef4444',
  })
  candlestickSeries.setData(candleData)

  // MA均线
  if (showMA.value) {
    const ma5Data = calculateMA(klineHistory.value, 5)
    const ma10Data = calculateMA(klineHistory.value, 10)
    const ma20Data = calculateMA(klineHistory.value, 20)

    ma5Series = mainChart.addSeries(LineSeries, {
      color: '#f59e0b',
      lineWidth: 1,
      crosshairMarkerVisible: false,
    })
    ma5Series.setData(ma5Data)

    ma10Series = mainChart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 1,
      crosshairMarkerVisible: false,
    })
    ma10Series.setData(ma10Data)

    ma20Series = mainChart.addSeries(LineSeries, {
      color: '#a855f7',
      lineWidth: 1,
      crosshairMarkerVisible: false,
    })
    ma20Series.setData(ma20Data)
  }

  // 成交量图
  if (showVolume.value && volumeChartContainerRef.value) {
    volumeChart = createChart(volumeChartContainerRef.value, {
      width: chartWidth,
      height: 120,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a2e' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#2d2d44' },
        horzLines: { color: '#2d2d44' },
      },
      rightPriceScale: {
        borderColor: '#2d2d44',
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: '#2d2d44',
        visible: false,
      },
    })

    const volumeData: HistogramData<Time>[] = klineHistory.value.map((d, i) => ({
      time: d.date as Time,
      value: d.volume,
      color: d.close >= (klineHistory.value[i - 1]?.close || d.open) ? '#22c55e80' : '#ef444480',
    }))

    volumeSeries = volumeChart.addSeries(HistogramSeries, {
      color: '#3b82f6',
      priceFormat: { type: 'volume' },
    })
    volumeSeries.setData(volumeData)
  }

  // MACD图
  if (showMACD.value && macdChartContainerRef.value) {
    macdChart = createChart(macdChartContainerRef.value, {
      width: chartWidth,
      height: 120,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a2e' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#2d2d44' },
        horzLines: { color: '#2d2d44' },
      },
      rightPriceScale: {
        borderColor: '#2d2d44',
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: '#2d2d44',
        visible: false,
      },
    })

    const macdData = calculateMACD(klineHistory.value)

    macdHistogramSeries = macdChart.addSeries(HistogramSeries, {
      priceFormat: { type: 'price', precision: 4 },
    })
    macdHistogramSeries.setData(macdData.histogram)

    macdLineSeries = macdChart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 1,
    })
    macdLineSeries.setData(macdData.macd)

    signalLineSeries = macdChart.addSeries(LineSeries, {
      color: '#f59e0b',
      lineWidth: 1,
    })
    signalLineSeries.setData(macdData.signal)
  }

  // 同步时间轴缩放
  if (mainChart && volumeChart) {
    mainChart.timeScale().subscribeVisibleTimeRangeChange(() => {
      const range = mainChart!.timeScale().getVisibleRange()
      if (range && volumeChart) {
        volumeChart.timeScale().setVisibleRange(range)
      }
      if (range && macdChart) {
        macdChart.timeScale().setVisibleRange(range)
      }
    })
  }

  // 自适应
  mainChart.timeScale().fitContent()
  volumeChart?.timeScale().fitContent()
  macdChart?.timeScale().fitContent()
}

// 监听数据变化更新图表
watch([klineHistory, showMA, showMACD, showVolume], () => {
  nextTick(() => {
    initCharts()
  })
}, { deep: true })

// 窗口大小变化时重新渲染
const handleResize = () => {
  if (mainChart && chartContainerRef.value) {
    mainChart.applyOptions({ width: chartContainerRef.value.clientWidth })
  }
  if (volumeChart && volumeChartContainerRef.value) {
    volumeChart.applyOptions({ width: volumeChartContainerRef.value.clientWidth })
  }
  if (macdChart && macdChartContainerRef.value) {
    macdChart.applyOptions({ width: macdChartContainerRef.value.clientWidth })
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (mainChart) mainChart.remove()
  if (volumeChart) volumeChart.remove()
  if (macdChart) macdChart.remove()
})

// 技术指标计算显示
const technicalIndicators = computed(() => {
  if (klineHistory.value.length === 0) return null

  const data = klineHistory.value
  const last = data[data.length - 1]
  const prev = data[data.length - 2]

  // 计算各指标
  const ma5 = calculateMA(data, 5)
  const ma10 = calculateMA(data, 10)
  const ma20 = calculateMA(data, 20)
  const rsi14 = calculateRSI(data, 14)

  // 价格变化
  const priceChange = last.close - prev.close
  const priceChangePercent = (priceChange / prev.close) * 100

  // 计算日内振幅
  const dayRange = ((last.high - last.low) / last.low) * 100

  return {
    lastPrice: last.close,
    open: last.open,
    high: last.high,
    low: last.low,
    volume: last.volume,
    priceChange,
    priceChangePercent,
    dayRange,
    ma5: ma5[ma5.length - 1]?.value || 0,
    ma10: ma10[ma10.length - 1]?.value || 0,
    ma20: ma20[ma20.length - 1]?.value || 0,
    rsi: rsi14[rsi14.length - 1]?.value || 50,
  }
})

const formatNumber = (num: number) => {
  if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (num >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toFixed(2)
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-white mb-2">专业K线分析</h1>
      <p class="text-gray-400">专业技术分析图表，支持多种技术指标</p>
    </div>

    <!-- 控制栏 -->
    <div class="card mb-6">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <!-- 股票选择 -->
        <div class="flex flex-wrap gap-2">
          <button
            v-for="stock in store.holdings"
            :key="stock.symbol"
            @click="selectedStock = stock.symbol"
            :class="[
              'px-4 py-2 rounded-lg transition-all duration-200 min-w-[100px]',
              selectedStock === stock.symbol
                ? 'bg-primary-600 text-white ring-2 ring-primary-400'
                : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
            ]"
          >
            <div class="font-bold">{{ stock.symbol }}</div>
            <div class="text-xs opacity-75">{{ stock.name }}</div>
          </button>
        </div>

        <!-- 时间周期 -->
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-400">时间范围:</span>
          <select v-model="timeRange" class="input w-auto text-sm">
            <option v-for="opt in timeRangeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <!-- 指标开关 -->
        <div class="flex items-center gap-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="showMA" class="w-4 h-4 accent-primary-500">
            <span class="text-sm text-gray-300">MA均线</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="showMACD" class="w-4 h-4 accent-primary-500">
            <span class="text-sm text-gray-300">MACD</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="showVolume" class="w-4 h-4 accent-primary-500">
            <span class="text-sm text-gray-300">成交量</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 股票信息卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6" v-if="technicalIndicators">
      <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">最新价</div>
        <div class="text-xl font-bold" :class="technicalIndicators.priceChange >= 0 ? 'text-red-400' : 'text-green-400'">
          {{ technicalIndicators.lastPrice.toFixed(2) }}
        </div>
        <div class="text-xs" :class="technicalIndicators.priceChange >= 0 ? 'text-red-400' : 'text-green-400'">
          {{ technicalIndicators.priceChange >= 0 ? '+' : '' }}{{ technicalIndicators.priceChangePercent.toFixed(2) }}%
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">今开</div>
        <div class="text-lg font-bold text-white">{{ technicalIndicators.open.toFixed(2) }}</div>
        <div class="text-xs text-gray-500">最高: {{ technicalIndicators.high.toFixed(2) }}</div>
      </div>

      <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">最低</div>
        <div class="text-lg font-bold text-white">{{ technicalIndicators.low.toFixed(2) }}</div>
        <div class="text-xs text-gray-500">振幅: {{ technicalIndicators.dayRange.toFixed(2) }}%</div>
      </div>

      <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">成交量</div>
        <div class="text-lg font-bold text-white">{{ formatNumber(technicalIndicators.volume) }}</div>
      </div>

      <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">RSI(14)</div>
        <div class="text-lg font-bold" :class="technicalIndicators.rsi > 70 ? 'text-red-400' : technicalIndicators.rsi < 30 ? 'text-green-400' : 'text-white'">
          {{ technicalIndicators.rsi.toFixed(1) }}
        </div>
        <div class="text-xs text-gray-500">
          {{ technicalIndicators.rsi > 70 ? '超买' : technicalIndicators.rsi < 30 ? '超卖' : '正常' }}
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">MA均线</div>
        <div class="text-xs space-y-1">
          <div><span class="text-yellow-500">MA5:</span> {{ technicalIndicators.ma5.toFixed(2) }}</div>
          <div><span class="text-blue-400">MA10:</span> {{ technicalIndicators.ma10.toFixed(2) }}</div>
          <div><span class="text-purple-400">MA20:</span> {{ technicalIndicators.ma20.toFixed(2) }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="space-y-1" v-if="!loadingHistory && klineHistory.length > 0">
      <!-- K线主图 -->
      <div class="bg-[#1a1a2e] rounded-t-lg border border-gray-700 border-b-0">
        <div class="px-4 py-2 border-b border-gray-700 flex items-center gap-4">
          <span class="text-sm font-medium text-white">K线图</span>
          <div class="flex gap-3 text-xs">
            <span class="flex items-center gap-1">
              <span class="w-3 h-0.5 bg-yellow-500"></span>
              <span class="text-gray-400">MA5</span>
            </span>
            <span class="flex items-center gap-1">
              <span class="w-3 h-0.5 bg-blue-400"></span>
              <span class="text-gray-400">MA10</span>
            </span>
            <span class="flex items-center gap-1">
              <span class="w-3 h-0.5 bg-purple-400"></span>
              <span class="text-gray-400">MA20</span>
            </span>
          </div>
        </div>
        <div ref="chartContainerRef" class="chart-container"></div>
      </div>

      <!-- 成交量图 -->
      <div v-if="showVolume" class="bg-[#1a1a2e] border border-gray-700 border-b-0">
        <div class="px-4 py-2 border-b border-gray-700">
          <span class="text-sm font-medium text-white">成交量</span>
        </div>
        <div ref="volumeChartContainerRef" class="chart-container-sm"></div>
      </div>

      <!-- MACD图 -->
      <div v-if="showMACD" class="bg-[#1a1a2e] rounded-b-lg border border-gray-700">
        <div class="px-4 py-2 border-b border-gray-700 flex items-center gap-4">
          <span class="text-sm font-medium text-white">MACD</span>
          <div class="flex gap-3 text-xs">
            <span class="flex items-center gap-1">
              <span class="w-3 h-0.5 bg-blue-400"></span>
              <span class="text-gray-400">DIF</span>
            </span>
            <span class="flex items-center gap-1">
              <span class="w-3 h-0.5 bg-yellow-500"></span>
              <span class="text-gray-400">DEA</span>
            </span>
            <span class="flex items-center gap-1">
              <span class="w-3 h-2 bg-green-500/50 border-l-2 border-green-500"></span>
              <span class="text-gray-400">MACD柱</span>
            </span>
          </div>
        </div>
        <div ref="macdChartContainerRef" class="chart-container-sm"></div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="loadingHistory" class="card">
      <div class="flex items-center justify-center h-96">
        <div class="text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent mx-auto mb-4"></div>
          <div class="text-gray-400">加载中...</div>
        </div>
      </div>
    </div>

    <!-- 无数据 -->
    <div v-else class="card">
      <div class="flex items-center justify-center h-96">
        <div class="text-center">
          <svg class="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
          <div class="text-gray-400">暂无K线数据</div>
          <div class="text-sm text-gray-500 mt-2">请选择股票或检查数据获取</div>
        </div>
      </div>
    </div>

    <!-- 技术分析说明 -->
    <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-3">MA移动平均线</h3>
        <div class="text-sm text-gray-400 space-y-2">
          <p>MA5 (黄色): 短期趋势，快速反应价格变化</p>
          <p>MA10 (蓝色): 中短期趋势确认</p>
          <p>MA20 (紫色): 中期趋势，重要支撑阻力位</p>
          <p class="text-primary-400 mt-2">金叉信号: 短期均线上穿长期均线</p>
          <p class="text-red-400">死叉信号: 短期均线下穿长期均线</p>
        </div>
      </div>

      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-3">MACD指标</h3>
        <div class="text-sm text-gray-400 space-y-2">
          <p><span class="text-blue-400">DIF线</span>: 快线(EMA12-EMA26)</p>
          <p><span class="text-yellow-400">DEA线</span>: 慢线(DIF的9日EMA)</p>
          <p><span class="text-green-400">红柱</span>: DIF > DEA，多头信号</p>
          <p><span class="text-red-400">绿柱</span>: DIF < DEA，空头信号</p>
          <p class="text-primary-400 mt-2">零轴上方: 多头市场</p>
          <p class="text-red-400">零轴下方: 空头市场</p>
        </div>
      </div>

      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-3">RSI指标</h3>
        <div class="text-sm text-gray-400 space-y-2">
          <p>RSI > 70: <span class="text-red-400">超买区域</span>，可能回调</p>
          <p>RSI < 30: <span class="text-green-400">超卖区域</span>，可能反弹</p>
          <p>50为多空分界线</p>
          <p class="text-primary-400 mt-2">背离信号:</p>
          <p>顶背离: 价格新高RSI不新高</p>
          <p>底背离: 价格新低RSI不新低</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px;
}

.chart-container-sm {
  width: 100%;
  height: 120px;
}

:deep(.tv-lightweight-charts) {
  border-radius: 0 0 8px 8px;
}
</style>