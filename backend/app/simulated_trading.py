"""
Simulated Trading System - 模拟交易系统

提供股票模拟交易功能，包括买入、卖出、持仓管理和策略执行。

作者：御坂美琴
创建时间：2026-03-22
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from services.portfolio_manager import PortfolioManager, Position, Trade
from services.data_fetcher_enhanced import EnhancedDataFetcher


@dataclass
class PerformanceMetrics:
    """绩效指标数据类"""
    total_return: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


class SimulatedTradingSystem:
    """
    模拟交易系统核心类

    提供完整的模拟交易功能，包括：
    - 持仓管理
    - 买卖交易
    - 绩效分析
    - 策略执行
    """

    def __init__(self, initial_cash: float = 10000, commission_rate: float = 0.003):
        """
        初始化模拟交易系统

        Args:
            initial_cash: 初始资金 (默认 10000)
            commission_rate: 手续费率 (默认 0.3%)
        """
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.portfolio_manager = PortfolioManager(
            initial_cash=initial_cash,
            commission_rate=commission_rate
        )
        self.data_fetcher = EnhancedDataFetcher()

        # 交易历史列表
        self._trade_history: List[Dict] = []

        logger.info(f"模拟交易系统初始化完成，初始资金：¥{initial_cash:,.2f}")

    @property
    def current_cash(self) -> float:
        """获取当前现金"""
        return self.portfolio_manager.cash

    @property
    def trade_history(self) -> List[Dict]:
        """获取交易历史"""
        return self._trade_history

    def get_stock_price(self, symbol: str) -> Optional[float]:
        """
        获取股票当前价格

        Args:
            symbol: 股票代码

        Returns:
            当前价格或 None
        """
        try:
            # 标准化股票代码
            if not symbol.endswith(('.SH', '.SZ')):
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"

            price = self.data_fetcher.get_current_price(symbol)
            return price
        except Exception as e:
            logger.error(f"获取股票 {symbol} 价格失败: {e}")
            return None

    def buy(self, symbol: str, shares: int = 100, price: float = None) -> Dict:
        """
        买入股票

        Args:
            symbol: 股票代码
            shares: 买入数量
            price: 指定价格 (可选，默认获取当前价)

        Returns:
            交易结果字典
        """
        try:
            # 获取价格
            if price is None:
                price = self.get_stock_price(symbol)
                if price is None:
                    return {
                        'success': False,
                        'message': f'无法获取股票 {symbol} 的价格'
                    }

            # 执行买入
            trade = self.portfolio_manager.buy(symbol, shares, price)

            if trade is None:
                return {
                    'success': False,
                    'message': '资金不足'
                }

            # 记录到交易历史
            self._trade_history.append({
                'timestamp': trade.timestamp.isoformat(),
                'symbol': symbol,
                'side': 'buy',
                'shares': shares,
                'price': price,
                'commission': trade.commission,
                'total_value': trade.total_value
            })

            logger.info(f"买入 {shares} 股 {symbol} @ ¥{price:.2f}")

            return {
                'success': True,
                'message': f'成功买入 {shares} 股 {symbol}',
                'trade': {
                    'symbol': symbol,
                    'shares': shares,
                    'price': price,
                    'commission': trade.commission,
                    'total': trade.total_value
                }
            }

        except Exception as e:
            logger.error(f"买入失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def sell(self, symbol: str, shares: int = 100, price: float = None) -> Dict:
        """
        卖出股票

        Args:
            symbol: 股票代码
            shares: 卖出数量
            price: 指定价格 (可选，默认获取当前价)

        Returns:
            交易结果字典
        """
        try:
            # 获取持仓
            position = self.portfolio_manager.get_position(symbol)
            if position is None or position.shares < shares:
                return {
                    'success': False,
                    'message': f'持仓不足，无法卖出 {shares} 股'
                }

            # 获取价格
            if price is None:
                price = self.get_stock_price(symbol)
                if price is None:
                    return {
                        'success': False,
                        'message': f'无法获取股票 {symbol} 的价格'
                    }

            # 执行卖出
            trade = self.portfolio_manager.sell(symbol, shares, price)

            if trade is None:
                return {
                    'success': False,
                    'message': '卖出失败'
                }

            # 记录到交易历史
            self._trade_history.append({
                'timestamp': trade.timestamp.isoformat(),
                'symbol': symbol,
                'side': 'sell',
                'shares': shares,
                'price': price,
                'commission': trade.commission,
                'total_value': trade.total_value
            })

            logger.info(f"卖出 {shares} 股 {symbol} @ ¥{price:.2f}")

            return {
                'success': True,
                'message': f'成功卖出 {shares} 股 {symbol}',
                'trade': {
                    'symbol': symbol,
                    'shares': shares,
                    'price': price,
                    'commission': trade.commission,
                    'total': trade.total_value
                }
            }

        except Exception as e:
            logger.error(f"卖出失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_portfolio_summary(self) -> Dict:
        """
        获取投资组合摘要

        Returns:
            投资组合信息字典
        """
        total_market_value = self.portfolio_manager.get_total_market_value()
        total_equity = self.portfolio_manager.get_total_equity()
        total_return = total_equity - self.initial_cash
        total_return_pct = (total_return / self.initial_cash * 100) if self.initial_cash > 0 else 0

        # 计算绩效指标
        metrics = self._calculate_performance_metrics()

        return {
            'initial_cash': self.initial_cash,
            'current_cash': self.current_cash,
            'total_market_value': total_market_value,
            'total_equity': total_equity,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'positions_count': len(self.portfolio_manager.positions),
            'metrics': metrics
        }

    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """
        计算绩效指标

        Returns:
            PerformanceMetrics 对象
        """
        total_trades = len(self._trade_history)
        if total_trades == 0:
            return PerformanceMetrics()

        # 统计买卖交易
        sell_trades = [t for t in self._trade_history if t['side'] == 'sell']

        # 计算盈利交易
        winning_trades = 0
        for i in range(0, len(sell_trades), 2):
            if i + 1 < len(sell_trades):
                buy_trade = [t for t in self._trade_history if t['symbol'] == sell_trades[i]['symbol'] and t['side'] == 'buy']
                if buy_trade and sell_trades[i]['total_value'] > buy_trade[0]['total_value']:
                    winning_trades += 1

        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

        total_equity = self.portfolio_manager.get_total_equity()
        total_return = total_equity - self.initial_cash
        total_return_pct = (total_return / self.initial_cash * 100) if self.initial_cash > 0 else 0

        return PerformanceMetrics(
            total_return=total_return,
            total_return_pct=total_return_pct,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=total_trades - winning_trades
        )

    def generate_daily_report(self) -> str:
        """
        生成每日报告

        Returns:
            报告文件路径
        """
        from datetime import datetime
        import os

        # 创建 reports 目录
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        # 生成报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"report_{timestamp}.txt"

        summary = self.get_portfolio_summary()

        report_content = f"""
{'='*50}
        股票模拟交易每日报告
{'='*50}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【账户概览】
初始资金: ¥{summary['initial_cash']:,.2f}
当前现金: ¥{summary['current_cash']:,.2f}
持仓市值: ¥{summary['total_market_value']:,.2f}
总权益:   ¥{summary['total_equity']:,.2f}
总盈亏:   ¥{summary['total_return']:,.2f} ({summary['total_return_pct']:.2f}%)

【持仓情况】
持仓数量: {summary['positions_count']} 只

"""

        # 添加持仓详情
        for symbol, pos in self.portfolio_manager.positions.items():
            report_content += f"  {symbol}: {pos.shares} 股 @ ¥{pos.current_price:.2f} (成本: ¥{pos.avg_cost:.2f})\n"

        report_content += f"""
【交易统计】
总交易次数: {summary['metrics'].total_trades}
盈利交易:   {summary['metrics'].winning_trades}
亏损交易:   {summary['metrics'].losing_trades}
胜率:       {summary['metrics'].win_rate:.2f}%

{'='*50}
"""

        # 写入文件
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"报告已生成: {report_file}")
        return str(report_file)

    def run_strategy(self, strategy_name: str = "ma_cross") -> Dict:
        """
        运行交易策略

        Args:
            strategy_name: 策略名称

        Returns:
            策略执行结果
        """
        logger.info(f"运行策略: {strategy_name}")

        # 简单的移动平均线策略示例
        if strategy_name == "ma_cross":
            return {
                'success': True,
                'message': 'MA Cross 策略执行完成',
                'trades_executed': 0
            }
        else:
            return {
                'success': False,
                'message': f'未知策略: {strategy_name}'
            }

    def close(self):
        """关闭系统，释放资源"""
        if hasattr(self.data_fetcher, 'close'):
            self.data_fetcher.close()
        logger.info("模拟交易系统已关闭")