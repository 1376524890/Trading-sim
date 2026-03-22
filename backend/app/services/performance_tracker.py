"""
Performance Tracker Module - 绩效追踪模块

负责计算和追踪回测策略的各种绩效指标。
包括收益、风险、夏普比率、最大回撤等关键指标。

作者：御坂美琴
创建时间：2026-03-16
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import json
import os


@dataclass
class PerformanceMetrics:
    """
    绩效指标数据类
    
    Attributes:
        total_return: 总收益率
        annualized_return: 年化收益率
        volatility: 年化波动率
        sharpe_ratio: 夏普比率
        sortino_ratio: 索提诺比率
        max_drawdown: 最大回撤
        max_drawdown_duration: 最大回撤持续时间 (天)
        win_rate: 胜率
        profit_factor: 盈亏比
        calmar_ratio: 卡尔玛比率
        total_trades: 总交易次数
        winning_trades: 盈利交易次数
        losing_trades: 亏损交易次数
        avg_win: 平均盈利
        avg_loss: 平均亏损
        largest_win: 最大盈利
        largest_loss: 最大亏损
    """
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_duration": self.max_drawdown_duration,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "calmar_ratio": self.calmar_ratio,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss
        }


class PerformanceTracker:
    """
    绩效追踪类
    
    计算和追踪回测策略的各项绩效指标
    """
    
    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化绩效追踪器
        
        Args:
            risk_free_rate: 无风险利率 (默认 3%)
        """
        self.risk_free_rate = risk_free_rate
        self.equity_curve: List[float] = []
        self.dates: List[datetime] = []
        self.trades: List[Dict] = []
        self.daily_returns: List[float] = []
        
        logger.info("绩效追踪器初始化完成")
    
    def add_data_point(self, date: datetime, equity: float):
        """
        添加数据点
        
        Args:
            date: 日期
            equity: 权益值
        """
        self.dates.append(date)
        self.equity_curve.append(equity)
    
    def add_trade(self, trade: Dict):
        """
        添加交易记录
        
        Args:
            trade: 交易字典
        """
        self.trades.append(trade)
    
    def calculate_daily_returns(self):
        """
        计算日收益率
        
        Returns:
            List[float]: 日收益率列表
        """
        if len(self.equity_curve) < 2:
            return []
        
        self.daily_returns = []
        for i in range(1, len(self.equity_curve)):
            daily_return = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            self.daily_returns.append(daily_return)
        
        return self.daily_returns
    
    def calculate_total_return(self) -> float:
        """
        计算总收益率
        
        Returns:
            float: 总收益率
        """
        if not self.equity_curve:
            return 0.0
        
        initial = self.equity_curve[0]
        final = self.equity_curve[-1]
        return (final - initial) / initial if initial > 0 else 0.0
    
    def calculate_annualized_return(self) -> float:
        """
        计算年化收益率
        
        Returns:
            float: 年化收益率
        """
        if len(self.dates) < 2:
            return 0.0
        
        # 计算时间跨度 (年)
        days = (self.dates[-1] - self.dates[0]).days
        years = days / 365.0
        
        if years <= 0:
            return 0.0
        
        total_return = self.calculate_total_return()
        return (1 + total_return) ** (1 / years) - 1
    
    def calculate_volatility(self) -> float:
        """
        计算年化波动率
        
        Returns:
            float: 年化波动率
        """
        if len(self.daily_returns) < 2:
            return 0.0
        
        # 计算日收益率标准差
        daily_std = np.std(self.daily_returns)
        
        # 年化 (假设 252 个交易日)
        return daily_std * np.sqrt(252)
    
    def calculate_sharpe_ratio(self) -> float:
        """
        计算夏普比率
        
        Returns:
            float: 夏普比率
        """
        if not self.daily_returns:
            return 0.0
        
        # 计算日收益率均值
        daily_mean_return = np.mean(self.daily_returns)
        
        # 年化
        annual_return = daily_mean_return * 252
        
        # 年化波动率
        annual_volatility = self.calculate_volatility()
        
        if annual_volatility == 0:
            return 0.0
        
        # 夏普比率
        return (annual_return - self.risk_free_rate) / annual_volatility
    
    def calculate_sortino_ratio(self) -> float:
        """
        计算索提诺比率
        
        Returns:
            float: 索提诺比率
        """
        if len(self.daily_returns) < 2:
            return 0.0
        
        # 只计算负收益率的标准差
        negative_returns = [r for r in self.daily_returns if r < 0]
        if not negative_returns:
            return float('inf')
        
        downside_std = np.std(negative_returns)
        annual_downside_std = downside_std * np.sqrt(252)
        
        if annual_downside_std == 0:
            return 0.0
        
        annual_return = self.calculate_annualized_return()
        return (annual_return - self.risk_free_rate) / annual_downside_std
    
    def calculate_max_drawdown(self) -> Tuple[float, int]:
        """
        计算最大回撤和回撤持续天数
        
        Returns:
            Tuple[float, int]: (最大回撤百分比，最大回撤持续天数)
        """
        if len(self.equity_curve) < 2:
            return 0.0, 0
        
        # 计算累积最大值
        running_max = np.maximum.accumulate(self.equity_curve)
        
        # 计算回撤
        drawdowns = (running_max - np.array(self.equity_curve)) / running_max
        
        # 最大回撤
        max_dd = np.max(drawdowns)
        
        # 计算最大回撤持续天数
        dd_duration = self._calculate_drawdown_duration(drawdowns)
        
        return max_dd, dd_duration
    
    def _calculate_drawdown_duration(self, drawdowns: np.ndarray) -> int:
        """
        计算最大回撤持续天数
        
        Args:
            drawdowns: 回撤数组
            
        Returns:
            int: 最大回撤持续天数
        """
        max_dd = np.max(drawdowns)
        
        # 找到最大回撤的起始和结束点
        in_drawdown = False
        start_idx = 0
        max_duration = 0
        
        for i, dd in enumerate(drawdowns):
            if dd > 0 and not in_drawdown:
                in_drawdown = True
                start_idx = i
            elif dd == 0 and in_drawdown:
                duration = i - start_idx
                max_duration = max(max_duration, duration)
                in_drawdown = False
        
        return max_duration
    
    def calculate_win_rate(self) -> float:
        """
        计算胜率
        
        Returns:
            float: 胜率
        """
        if not self.trades:
            return 0.0
        
        winning_trades = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
        return winning_trades / len(self.trades) * 100
    
    def calculate_profit_factor(self) -> float:
        """
        计算盈亏比
        
        Returns:
            float: 盈亏比
        """
        if not self.trades:
            return 0.0
        
        gains = sum(t.get('pnl', 0) for t in self.trades if t.get('pnl', 0) > 0)
        losses = abs(sum(t.get('pnl', 0) for t in self.trades if t.get('pnl', 0) < 0))
        
        if losses == 0:
            return float('inf') if gains > 0 else 0.0
        
        return gains / losses
    
    def calculate_calmar_ratio(self) -> float:
        """
        计算卡尔玛比率
        
        Returns:
            float: 卡尔玛比率
        """
        annual_return = self.calculate_annualized_return()
        max_dd, _ = self.calculate_max_drawdown()
        
        if max_dd == 0:
            return 0.0
        
        return annual_return / max_dd
    
    def analyze_trades(self) -> Dict:
        """
        分析交易记录
        
        Returns:
            Dict: 交易分析结果
        """
        if not self.trades:
            return {}
        
        pnls = [t.get('pnl', 0) for t in self.trades]
        winning_pnls = [p for p in pnls if p > 0]
        losing_pnls = [p for p in pnls if p < 0]
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning_pnls),
            "losing_trades": len(losing_pnls),
            "win_rate": self.calculate_win_rate(),
            "avg_win": np.mean(winning_pnls) if winning_pnls else 0,
            "avg_loss": np.mean(losing_pnls) if losing_pnls else 0,
            "largest_win": max(winning_pnls) if winning_pnls else 0,
            "largest_loss": min(losing_pnls) if losing_pnls else 0,
            "profit_factor": self.calculate_profit_factor()
        }
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        获取所有绩效指标
        
        Returns:
            PerformanceMetrics: 绩效指标对象
        """
        # 确保已计算日收益率
        if not self.daily_returns:
            self.calculate_daily_returns()
        
        max_dd, dd_duration = self.calculate_max_drawdown()
        
        return PerformanceMetrics(
            total_return=self.calculate_total_return(),
            annualized_return=self.calculate_annualized_return(),
            volatility=self.calculate_volatility(),
            sharpe_ratio=self.calculate_sharpe_ratio(),
            sortino_ratio=self.calculate_sortino_ratio(),
            max_drawdown=max_dd,
            max_drawdown_duration=dd_duration,
            win_rate=self.calculate_win_rate(),
            profit_factor=self.calculate_profit_factor(),
            calmar_ratio=self.calculate_calmar_ratio(),
            **self.analyze_trades()
        )
    
    def calculate_var(self, confidence: float = 0.95) -> float:
        """
        计算在险价值 (VaR)
        
        Args:
            confidence: 置信度 (默认 95%)
            
        Returns:
            float: VaR 值
        """
        if not self.daily_returns:
            return 0.0
        
        return np.percentile(self.daily_returns, (1 - confidence) * 100)
    
    def calculate_cvar(self, confidence: float = 0.95) -> float:
        """
        计算条件在险价值 (CVaR/Expected Shortfall)
        
        Args:
            confidence: 置信度 (默认 95%)
            
        Returns:
            float: CVaR 值
        """
        if not self.daily_returns:
            return 0.0
        
        var = self.calculate_var(confidence)
        return np.mean([r for r in self.daily_returns if r <= var])
    
    def save_metrics(self, filepath: str = "performance_metrics.json"):
        """
        保存绩效指标到文件
        
        Args:
            filepath: 文件路径
        """
        metrics = self.get_performance_metrics()
        metrics_dict = metrics.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"绩效指标已保存到 {filepath}")


def main():
    """测试函数"""
    # 初始化绩效追踪器
    tracker = PerformanceTracker(risk_free_rate=0.03)
    
    # 模拟权益曲线
    dates = [datetime(2024, i, 1) for i in range(1, 13)]
    equity = [1000000]
    
    # 生成模拟数据
    np.random.seed(42)
    daily_returns = np.random.normal(0.001, 0.02, 11)
    for ret in daily_returns:
        new_equity = equity[-1] * (1 + ret)
        equity.append(new_equity)
    
    # 添加数据点
    for date, eq in zip(dates, equity):
        tracker.add_data_point(date, eq)
    
    # 添加模拟交易
    tracker.add_trade({"pnl": 5000})
    tracker.add_trade({"pnl": -2000})
    tracker.add_trade({"pnl": 8000})
    tracker.add_trade({"pnl": -1000})
    tracker.add_trade({"pnl": 3000})
    
    # 计算绩效指标
    metrics = tracker.get_performance_metrics()
    
    # 输出结果
    logger.info("=" * 50)
    logger.info("绩效分析结果:")
    logger.info("=" * 50)
    logger.info(f"总收益率：{metrics.total_return * 100:.2f}%")
    logger.info(f"年化收益率：{metrics.annualized_return * 100:.2f}%")
    logger.info(f"年化波动率：{metrics.volatility * 100:.2f}%")
    logger.info(f"夏普比率：{metrics.sharpe_ratio:.2f}")
    logger.info(f"索提诺比率：{metrics.sortino_ratio:.2f}")
    logger.info(f"最大回撤：{metrics.max_drawdown * 100:.2f}%")
    logger.info(f"最大回撤持续：{metrics.max_drawdown_duration}天")
    logger.info(f"胜率：{metrics.win_rate:.2f}%")
    logger.info(f"盈亏比：{metrics.profit_factor:.2f}")
    logger.info(f"卡尔玛比率：{metrics.calmar_ratio:.2f}")
    logger.info(f"总交易次数：{metrics.total_trades}")
    logger.info("=" * 50)
    
    # 保存指标
    tracker.save_metrics("test_performance_metrics.json")


if __name__ == "__main__":
    main()
