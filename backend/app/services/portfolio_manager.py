"""
Portfolio Manager Module - 持仓管理模块

负责管理回测过程中的持仓信息、交易记录和投资组合状态。
提供持仓计算、仓位控制和交易执行等功能。

作者：御坂美琴
创建时间：2026-03-16
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger
import json
import os


@dataclass
class Position:
    """
    持仓信息类
    
    Attributes:
        symbol: 证券代码
        shares: 持股数量
        avg_cost: 平均成本价
        current_price: 当前价格
        market_value: 市值
        unrealized_pnl: 未实现盈亏
        unrealized_pnl_pct: 未实现盈亏百分比
    """
    symbol: str
    shares: float = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    def __init__(self, symbol: str, shares: float = 0, avg_cost: float = 0.0, current_price: float = 0.0):
        """
        初始化持仓信息
        
        Args:
            symbol: 证券代码
            shares: 持股数量
            avg_cost: 平均成本价
            current_price: 当前价格
        """
        self.symbol = symbol
        self.shares = shares
        self.avg_cost = avg_cost
        self.current_price = current_price
        self.market_value = shares * current_price
        self.unrealized_pnl = self.market_value - (shares * avg_cost) if shares > 0 and avg_cost > 0 else 0
        self.unrealized_pnl_pct = (self.unrealized_pnl / (shares * avg_cost) * 100) if shares > 0 and avg_cost > 0 else 0.0
    
    def update_price(self, price: float):
        """更新当前价格"""
        self.current_price = price
        self.market_value = self.shares * price if abs(self.shares) > 0.001 else 0
        self.unrealized_pnl = self.market_value - (self.shares * self.avg_cost) if abs(self.shares) > 0.001 and abs(self.avg_cost) > 0.001 else 0
        self.unrealized_pnl_pct = (self.unrealized_pnl / (self.shares * self.avg_cost) * 100) if abs(self.shares) > 0.001 and abs(self.avg_cost) > 0.001 else 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "shares": self.shares,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct
        }


@dataclass
class Trade:
    """
    交易记录类
    
    Attributes:
        timestamp: 交易时间
        symbol: 证券代码
        side: 交易方向 (buy/sell)
        shares: 交易数量
        price: 成交价格
        commission: 手续费
        total_value: 总价值
    """
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    shares: float
    price: float
    commission: float = 0.0
    total_value: float = 0.0
    
    def __post_init__(self):
        """计算总价值"""
        if self.side == 'buy':
            self.total_value = self.shares * self.price + self.commission
        else:
            self.total_value = self.shares * self.price - self.commission
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "side": self.side,
            "shares": self.shares,
            "price": self.price,
            "commission": self.commission,
            "total_value": self.total_value
        }


class PortfolioManager:
    """
    投资组合管理类
    
    管理回测过程中的持仓和交易记录
    """
    
    def __init__(self, initial_cash: float = 1000000, commission_rate: float = 0.003):
        """
        初始化组合管理器
        
        Args:
            initial_cash: 初始资金
            commission_rate: 手续费率 (默认为 0.3%)
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission_rate = commission_rate
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.trade_history: pd.DataFrame = pd.DataFrame()
        
        logger.info(f"组合初始化完成，初始资金：¥{initial_cash:,.2f}")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取特定持仓
        
        Args:
            symbol: 证券代码
            
        Returns:
            Position 或 None
        """
        return self.positions.get(symbol)
    
    def get_total_market_value(self) -> float:
        """
        计算总市值
        
        Returns:
            float: 所有持仓的总市值
        """
        return sum(pos.market_value for pos in self.positions.values())
    
    def get_total_equity(self) -> float:
        """
        计算总权益 (现金 + 市值)
        
        Returns:
            float: 总权益
        """
        return self.cash + self.get_total_market_value()
    
    def get_cash_percentage(self) -> float:
        """
        计算现金比例
        
        Returns:
            float: 现金占总权益的百分比
        """
        total_equity = self.get_total_equity()
        return (self.cash / total_equity * 100) if total_equity > 0 else 100.0
    
    def calculate_commission(self, trade_value: float) -> float:
        """
        计算手续费
        
        Args:
            trade_value: 交易价值
            
        Returns:
            float: 手续费金额
        """
        # A 股最低手续费 5 元
        commission = trade_value * self.commission_rate
        return max(commission, 5.0)
    
    def buy(
        self,
        symbol: str,
        shares: float,
        price: float,
        timestamp: datetime = None
    ) -> Optional[Trade]:
        """
        买入操作
        
        Args:
            symbol: 证券代码
            shares: 购买数量
            price: 成交价格
            timestamp: 交易时间
            
        Returns:
            Trade 或 None (如果资金不足)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 计算交易价值
        trade_value = shares * price
        commission = self.calculate_commission(trade_value)
        total_cost = trade_value + commission
        
        # 检查资金是否足够
        if total_cost > self.cash:
            logger.warning(f"资金不足，无法买入 {shares} 股 {symbol}")
            return None
        
        # 更新现金
        self.cash -= total_cost
        
        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            # 计算新的平均成本
            old_cost = pos.shares * pos.avg_cost
            new_cost = old_cost + trade_value
            pos.shares += shares
            pos.avg_cost = new_cost / pos.shares if abs(pos.shares) > 0.001 else 0.0
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                shares=shares,
                avg_cost=price,
                current_price=price
            )
        
        # 更新当前价格
        self.positions[symbol].update_price(price)
        
        # 记录交易
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            side='buy',
            shares=shares,
            price=price,
            commission=commission
        )
        self.trades.append(trade)
        self._update_trade_history(trade)
        
        logger.info(f"买入：{shares}股 {symbol} @ ¥{price:.2f}")
        return trade
    
    def sell(
        self,
        symbol: str,
        shares: float,
        price: float,
        timestamp: datetime = None
    ) -> Optional[Trade]:
        """
        卖出操作
        
        Args:
            symbol: 证券代码
            shares: 卖出数量
            price: 成交价格
            timestamp: 交易时间
            
        Returns:
            Trade 或 None (如果持仓不足)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 检查是否有足够的持仓
        if symbol not in self.positions or self.positions[symbol].shares < shares:
            logger.warning(f"持仓不足，无法卖出 {shares} 股 {symbol}")
            return None
        
        # 计算交易价值
        trade_value = shares * price
        commission = self.calculate_commission(trade_value)
        total_proceeds = trade_value - commission
        
        # 更新现金
        self.cash += total_proceeds
        
        # 更新持仓
        pos = self.positions[symbol]
        pos.shares -= shares
        
        # 如果全部卖出，删除持仓
        if pos.shares <= 0:
            del self.positions[symbol]
        else:
            # 更新当前价格
            pos.update_price(price)
        
        # 记录交易
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            side='sell',
            shares=shares,
            price=price,
            commission=commission
        )
        self.trades.append(trade)
        self._update_trade_history(trade)
        
        logger.info(f"卖出：{shares}股 {symbol} @ ¥{price:.2f}")
        return trade
    
    def _update_trade_history(self, trade: Trade):
        """更新交易历史数据框"""
        trade_df = pd.DataFrame([trade.to_dict()])
        self.trade_history = pd.concat([self.trade_history, trade_df], ignore_index=True)
    
    def update_all_prices(self, prices: Dict[str, float]):
        """
        批量更新所有持仓的价格
        
        Args:
            prices: {symbol: price} 字典
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)
    
    def get_portfolio_summary(self) -> Dict:
        """
        获取投资组合摘要
        
        Returns:
            Dict: 投资组合摘要信息
        """
        total_market_value = self.get_total_market_value()
        total_equity = self.get_total_equity()
        total_pnl = total_equity - self.initial_cash
        total_pnl_pct = (total_pnl / self.initial_cash * 100) if self.initial_cash > 0 else 0.0
        
        return {
            "initial_cash": self.initial_cash,
            "current_cash": self.cash,
            "total_market_value": total_market_value,
            "total_equity": total_equity,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "num_positions": len(self.positions),
            "cash_percentage": self.get_cash_percentage()
        }
    
    def save_trade_history(self, filepath: str = None):
        """
        保存交易历史到文件
        
        Args:
            filepath: 文件路径
        """
        if filepath is None:
            filepath = "trade_history.csv"
        
        if not self.trade_history.empty:
            self.trade_history.to_csv(filepath, index=False)
            logger.info(f"交易历史已保存到 {filepath}")
        else:
            logger.warning("没有交易历史可保存")
    
    def load_trade_history(self, filepath: str):
        """
        从文件加载交易历史
        
        Args:
            filepath: 文件路径
        """
        if os.path.exists(filepath):
            self.trade_history = pd.read_csv(filepath)
            logger.info(f"交易历史已从 {filepath} 加载")
        else:
            logger.warning(f"文件不存在：{filepath}")


def main():
    """测试函数"""
    # 初始化组合管理器
    portfolio = PortfolioManager(initial_cash=1000000)
    
    # 模拟交易
    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    
    # 买入操作
    portfolio.buy("600519.SS", 100, 1700.00, timestamp)
    portfolio.buy("000858.SZ", 200, 15.50, timestamp)
    
    # 更新价格
    prices = {"600519.SS": 1750.00, "000858.SZ": 16.20}
    portfolio.update_all_prices(prices)
    
    # 卖出操作
    portfolio.sell("600519.SS", 50, 1750.00, timestamp)
    
    # 获取组合摘要
    summary = portfolio.get_portfolio_summary()
    logger.info("投资组合摘要:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value:,.2f}")
    
    # 保存交易历史
    portfolio.save_trade_history("test_trade_history.csv")


if __name__ == "__main__":
    main()
