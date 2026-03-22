import { createRouter, createWebHistory } from 'vue-router'
import Overview from '@/views/Overview.vue'
import Portfolio from '@/views/Portfolio.vue'
import Charts from '@/views/Charts.vue'
import Analysis from '@/views/Analysis.vue'
import News from '@/views/News.vue'
import Transactions from '@/views/Transactions.vue'
import Backtest from '@/views/Backtest.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Overview',
      component: Overview
    },
    {
      path: '/portfolio',
      name: 'Portfolio',
      component: Portfolio
    },
    {
      path: '/charts',
      name: 'Charts',
      component: Charts
    },
    {
      path: '/analysis',
      name: 'Analysis',
      component: Analysis
    },
    {
      path: '/backtest',
      name: 'Backtest',
      component: Backtest
    },
    {
      path: '/news',
      name: 'News',
      component: News
    },
    {
      path: '/transactions',
      name: 'Transactions',
      component: Transactions
    }
  ]
})

export default router
