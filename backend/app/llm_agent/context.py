"""LLM Agent 上下文构建模块"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING
import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from app.diversified_investment import DiversifiedInvestmentSystem


class ContextBuilder:
    """构建LLM决策所需的完整上下文"""

    def __init__(self, system: 'DiversifiedInvestmentSystem'):
        self.system = system
        self.config = system.config

    def build(self) -> Dict:
        """构建完整上下文"""
        try:
            from app.services.data_fetcher_enhanced import EnhancedDataFetcher
            from app.market_analyzer import MarketAnalyzer

            self.data_fetcher = EnhancedDataFetcher()
            self.market_analyzer = MarketAnalyzer()

            context = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "portfolio": self._get_portfolio_context(),
                "market": self._get_market_context(),
                "candidates": self._get_candidate_stocks(),
                "news": self._get_news_context(),
                "constraints": self._get_constraints(),
                "history": self._get_recent_trades()
            }

            self.data_fetcher.close()
            return context

        except Exception as e:
            logger.error(f"构建上下文失败: {e}")
            return self._get_minimal_context()

    def _get_portfolio_context(self) -> Dict:
        """获取投资组合上下文"""
        try:
            analysis = self.system.get_portfolio_analysis()
            return {
                "cash": self.system.cash,
                "total_equity": analysis['total_equity'],
                "cash_ratio": round(analysis['cash_ratio'] * 100, 1),
                "positions": [
                    {
                        "symbol": p['symbol'],
                        "name": p['name'],
                        "shares": p['shares'],
                        "avg_cost": p['avg_cost'],
                        "current_price": p['current_price'],
                        "pnl_pct": round(p['pnl_pct'], 2),
                        "holding_type": p['holding_type'],
                        "sector": p['sector'],
                        "stop_loss": self.system.positions[p['symbol']].stop_loss,
                        "target_price": self.system.positions[p['symbol']].target_price
                    }
                    for p in analysis['positions']
                ],
                "sector_allocation": {
                    k: round(v, 2) for k, v in analysis['sector_allocation'].items()
                },
                "holding_type_allocation": {
                    k: round(v, 2) for k, v in analysis['holding_type_allocation'].items()
                },
                "pnl": {
                    "total": round(analysis['pnl']['total'], 2),
                    "pct": round(analysis['pnl']['pct'], 2)
                }
            }
        except Exception as e:
            logger.error(f"获取组合上下文失败: {e}")
            return {"cash": self.system.cash, "positions": []}

    def _get_market_context(self) -> Dict:
        """获取市场分析上下文"""
        try:
            return {
                "sector_analysis": self.market_analyzer.analyze_sector_rotation(),
                "market_sentiment": self.market_analyzer.analyze_market_sentiment(),
                "risk_assessment": self.market_analyzer.assess_risk()
            }
        except Exception as e:
            logger.error(f"获取市场上下文失败: {e}")
            return {}

    def _get_candidate_stocks(self) -> List[Dict]:
        """获取候选股票及其指标"""
        try:
            from app.diversified_investment import STOCK_POOL

            candidates = []
            for sector, stocks in STOCK_POOL.items():
                for stock in stocks:
                    if stock.symbol not in self.system.positions:
                        # 获取技术指标
                        tech = self._get_technical_indicators(stock.symbol)
                        try:
                            price = self.system.get_stock_price(stock.symbol)
                        except:
                            price = 0

                        candidates.append({
                            "symbol": stock.symbol,
                            "name": stock.name,
                            "sector": stock.sector.value,
                            "price": price,
                            "market_cap": stock.market_cap,
                            "dividend_yield": stock.dividend_yield,
                            "volatility": stock.volatility,
                            "is_blue_chip": stock.is_blue_chip,
                            "is_growth": stock.is_growth,
                            "technical": tech
                        })

            # 按板块分组返回
            sector_candidates = {}
            for c in candidates:
                sector = c['sector']
                if sector not in sector_candidates:
                    sector_candidates[sector] = []
                sector_candidates[sector].append(c)

            return sector_candidates

        except Exception as e:
            logger.error(f"获取候选股票失败: {e}")
            return {}

    def _get_technical_indicators(self, symbol: str) -> Dict:
        """获取技术指标"""
        try:
            df = self.data_fetcher.fetch_stock_data(
                symbol,
                start_date=(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            if df.empty or len(df) < 20:
                return {}

            # 计算基础技术指标
            close = df['close'].values
            return {
                "ma_5": round(float(np.mean(close[-5:])), 2),
                "ma_20": round(float(np.mean(close[-20:])), 2),
                "trend": "up" if close[-1] > np.mean(close[-20:]) else "down",
                "recent_change_pct": round(float((close[-1] - close[-5]) / close[-5] * 100), 2)
            }
        except Exception as e:
            logger.debug(f"获取技术指标失败 {symbol}: {e}")
            return {}

    def _get_news_context(self) -> List[Dict]:
        """获取新闻上下文"""
        try:
            from app.services.news_scraper import NewsScraper
            scraper = NewsScraper()
            news = scraper.fetch_latest_news(limit=10)
            return [{"title": n["title"], "sentiment": n["sentiment"]} for n in news]
        except Exception as e:
            logger.warning(f"获取新闻失败: {e}")
            return []

    def _get_constraints(self) -> Dict:
        """获取约束条件"""
        return {
            "max_position_per_stock": self.config.max_position_per_stock,
            "max_position_per_sector": self.config.max_position_per_sector,
            "min_cash_reserve": self.config.min_cash_reserve,
            "max_holdings": self.config.max_holdings,
            "available_cash": self.system.cash,
            "current_holdings_count": len(self.system.positions)
        }

    def _get_recent_trades(self) -> List[Dict]:
        """获取近期交易历史"""
        trades = self.system.trade_history[-10:]  # 最近10笔
        return [
            {
                "time": t.get("time", ""),
                "type": t.get("type", ""),
                "symbol": t.get("symbol", ""),
                "name": t.get("name", ""),
                "shares": t.get("shares", 0),
                "price": t.get("price", 0),
                "pnl": t.get("pnl", 0)
            }
            for t in trades
        ]

    def _get_minimal_context(self) -> Dict:
        """获取最小上下文（降级方案）"""
        return {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "portfolio": {
                "cash": self.system.cash,
                "positions": [
                    {
                        "symbol": p.symbol,
                        "name": p.name,
                        "shares": p.shares,
                        "avg_cost": p.avg_cost,
                        "current_price": p.current_price,
                        "sector": p.sector.value
                    }
                    for p in self.system.positions.values()
                ]
            },
            "constraints": self._get_constraints(),
            "history": self._get_recent_trades()
        }
