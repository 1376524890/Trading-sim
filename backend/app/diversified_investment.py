#!/usr/bin/env python3
"""
智能多样化投资系统 v4.0
⚡ 模拟真实人类投资者行为 ⚡

功能:
1. 多板块、多股票分散投资
2. 长线/短线策略区分
3. 模拟人类投资决策
4. 自主仓位调整和调仓
5. 风险控制和资金管理

作者: 御坂美琴
创建时间: 2026-03-21
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import random
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from loguru import logger

# 配置日志
logger.remove()
logger.add(
    PROJECT_ROOT / "logs" / "diversified_investment.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
logger.add(sink=sys.stderr, level="INFO")


class InvestmentStyle(Enum):
    """投资风格"""
    CONSERVATIVE = "conservative"      # 保守型
    BALANCED = "balanced"              # 稳健型
    AGGRESSIVE = "aggressive"          # 激进型


class HoldingType(Enum):
    """持仓类型"""
    LONG_TERM = "long_term"           # 长线 (持有期 > 3个月)
    MID_TERM = "mid_term"             # 中线 (持有期 1-3个月)
    SHORT_TERM = "short_term"         # 短线 (持有期 < 1个月)


class Sector(Enum):
    """行业板块"""
    FINANCE = "金融"
    TECHNOLOGY = "科技"
    CONSUMER = "消费"
    HEALTHCARE = "医药"
    ENERGY = "能源"
    MATERIALS = "材料"
    INDUSTRIAL = "工业"
    REAL_ESTATE = "地产"
    UTILITIES = "公用事业"
    COMMUNICATION = "通信"


@dataclass
class StockInfo:
    """股票信息"""
    symbol: str
    name: str
    sector: Sector
    market_cap: str  # large, mid, small
    volatility: float  # 波动率
    dividend_yield: float  # 股息率
    is_blue_chip: bool = False  # 是否蓝筹股
    is_growth: bool = False  # 是否成长股


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    name: str
    shares: int
    avg_cost: float
    current_price: float
    holding_type: HoldingType
    sector: Sector
    buy_date: str
    strategy: str
    target_price: float = 0.0  # 目标价
    stop_loss: float = 0.0     # 止损价
    notes: str = ""


# 股票池配置 - 多板块精选股票
STOCK_POOL: Dict[Sector, List[StockInfo]] = {
    Sector.FINANCE: [
        StockInfo("601398.SS", "工商银行", Sector.FINANCE, "large", 0.15, 0.055, True, False),
        StockInfo("600036.SS", "招商银行", Sector.FINANCE, "large", 0.20, 0.025, True, False),
        StockInfo("601318.SS", "中国平安", Sector.FINANCE, "large", 0.25, 0.035, True, False),
        StockInfo("601166.SS", "兴业银行", Sector.FINANCE, "large", 0.22, 0.048, True, False),
        StockInfo("600000.SS", "浦发银行", Sector.FINANCE, "large", 0.18, 0.045, True, False),
    ],
    Sector.TECHNOLOGY: [
        StockInfo("300750.SZ", "宁德时代", Sector.TECHNOLOGY, "large", 0.35, 0.008, False, True),
        StockInfo("002594.SZ", "比亚迪", Sector.TECHNOLOGY, "large", 0.40, 0.005, False, True),
        StockInfo("000063.SZ", "中兴通讯", Sector.TECHNOLOGY, "mid", 0.35, 0.012, False, True),
        StockInfo("002475.SZ", "立讯精密", Sector.TECHNOLOGY, "mid", 0.38, 0.008, False, True),
        StockInfo("600276.SS", "恒瑞医药", Sector.HEALTHCARE, "large", 0.28, 0.015, True, False),
    ],
    Sector.CONSUMER: [
        StockInfo("600519.SS", "贵州茅台", Sector.CONSUMER, "large", 0.22, 0.015, True, False),
        StockInfo("000858.SZ", "五粮液", Sector.CONSUMER, "large", 0.25, 0.018, True, False),
        StockInfo("000333.SZ", "美的集团", Sector.CONSUMER, "large", 0.28, 0.025, True, False),
        StockInfo("000651.SZ", "格力电器", Sector.CONSUMER, "large", 0.26, 0.045, True, False),
        StockInfo("600887.SS", "伊利股份", Sector.CONSUMER, "large", 0.18, 0.028, True, False),
    ],
    Sector.HEALTHCARE: [
        StockInfo("600276.SS", "恒瑞医药", Sector.HEALTHCARE, "large", 0.30, 0.012, True, False),
        StockInfo("000538.SZ", "云南白药", Sector.HEALTHCARE, "mid", 0.25, 0.020, True, False),
        StockInfo("300760.SZ", "迈瑞医疗", Sector.HEALTHCARE, "large", 0.32, 0.010, False, True),
        StockInfo("002821.SZ", "凯莱英", Sector.HEALTHCARE, "mid", 0.38, 0.008, False, True),
    ],
    Sector.ENERGY: [
        StockInfo("601857.SS", "中国石油", Sector.ENERGY, "large", 0.20, 0.065, True, False),
        StockInfo("600028.SS", "中国石化", Sector.ENERGY, "large", 0.18, 0.085, True, False),
        StockInfo("601225.SS", "陕西煤业", Sector.ENERGY, "large", 0.28, 0.095, True, False),
        StockInfo("600019.SS", "宝钢股份", Sector.MATERIALS, "large", 0.25, 0.050, True, False),
    ],
    Sector.INDUSTRIAL: [
        StockInfo("600031.SS", "三一重工", Sector.INDUSTRIAL, "large", 0.32, 0.025, True, False),
        StockInfo("000333.SZ", "美的集团", Sector.CONSUMER, "large", 0.28, 0.025, True, False),
        StockInfo("601766.SS", "中国中车", Sector.INDUSTRIAL, "large", 0.22, 0.018, True, False),
    ],
    Sector.REAL_ESTATE: [
        StockInfo("000002.SZ", "万科A", Sector.REAL_ESTATE, "large", 0.35, 0.045, True, False),
        StockInfo("600048.SS", "保利发展", Sector.REAL_ESTATE, "large", 0.38, 0.042, True, False),
    ],
    Sector.UTILITIES: [
        StockInfo("600900.SS", "长江电力", Sector.UTILITIES, "large", 0.12, 0.038, True, False),
        StockInfo("600011.SS", "华能国际", Sector.UTILITIES, "large", 0.15, 0.035, True, False),
    ],
    Sector.COMMUNICATION: [
        StockInfo("600050.SS", "中国联通", Sector.COMMUNICATION, "large", 0.14, 0.028, True, False),
        StockInfo("600588.SS", "用友网络", Sector.TECHNOLOGY, "mid", 0.35, 0.008, False, True),
    ],
}


@dataclass
class InvestmentConfig:
    """投资配置"""
    initial_cash: float = 100000  # 初始资金 10万
    max_position_per_stock: float = 0.15  # 单只股票最大仓位 15%
    max_position_per_sector: float = 0.30  # 单板块最大仓位 30%
    min_cash_reserve: float = 0.15  # 最低现金储备 15%

    # 长线配置
    long_term_ratio: float = 0.50  # 长线仓位占比 50%
    long_term_stop_loss: float = -0.15  # 长线止损 -15%
    long_term_take_profit: float = 0.50  # 长线止盈 +50%

    # 短线配置
    short_term_ratio: float = 0.30  # 短线仓位占比 30%
    short_term_stop_loss: float = -0.05  # 短线止损 -5%
    short_term_take_profit: float = 0.15  # 短线止盈 +15%

    # 中线配置
    mid_term_ratio: float = 0.20  # 中线仓位占比 20%
    mid_term_stop_loss: float = -0.10  # 中线止损 -10%
    mid_term_take_profit: float = 0.30  # 中线止盈 +30%

    # 风格配置
    investment_style: InvestmentStyle = InvestmentStyle.BALANCED
    max_holdings: int = 10  # 最大持仓数
    rebalance_frequency: int = 30  # 调仓频率(天)


class HumanInvestorBehavior:
    """模拟人类投资者行为"""

    def __init__(self, config: InvestmentConfig):
        self.config = config
        self.mood = 0.5  # 情绪指标 0-1
        self.confidence = 0.5  # 信心指标 0-1
        self.recent_performance = []  # 近期表现
        self.trade_count_today = 0  # 今日交易次数
        self.last_trade_time = None

    def update_mood(self, pnl_pct: float):
        """更新情绪"""
        # 盈利时情绪上升，亏损时下降
        if pnl_pct > 0:
            self.mood = min(1.0, self.mood + pnl_pct * 0.1)
            self.confidence = min(1.0, self.confidence + 0.05)
        else:
            self.mood = max(0.0, self.mood + pnl_pct * 0.2)
            self.confidence = max(0.2, self.confidence - 0.1)

        self.recent_performance.append(pnl_pct)
        if len(self.recent_performance) > 10:
            self.recent_performance.pop(0)

    def should_trade(self, bypass_cooldown: bool = False) -> Tuple[bool, str]:
        """判断是否应该交易"""
        # 检查交易频率限制 (模拟人类不会过度交易)
        if self.trade_count_today > 10:  # 放宽限制
            return False, "今日交易次数已达上限"

        # 检查冷静期 (模拟人类思考时间) - 可跳过
        if not bypass_cooldown and self.last_trade_time:
            cooldown = (datetime.now() - self.last_trade_time).total_seconds()
            if cooldown < 30:  # 缩短到30秒
                return False, "交易冷静期中"

        # 情绪过低时减少交易
        if self.mood < 0.2:  # 降低阈值
            return False, "情绪不佳，暂停交易"

        return True, "可以交易"

    def decide_position_size(self, base_size: float, signal_strength: float) -> float:
        """决定仓位大小"""
        # 人类投资者会根据信心和信号强度调整仓位
        confidence_factor = self.confidence * 0.5 + 0.5  # 0.5-1.0
        mood_factor = self.mood * 0.3 + 0.7  # 0.7-1.0

        adjusted_size = base_size * confidence_factor * mood_factor * signal_strength

        # 添加一些随机性 (模拟人类决策的不确定性)
        noise = random.uniform(-0.1, 0.1)
        adjusted_size *= (1 + noise)

        return max(0, adjusted_size)

    def get_holding_type_preference(self) -> HoldingType:
        """获取当前偏好的持仓类型"""
        # 根据情绪和市场状态选择
        if self.mood > 0.7 and self.confidence > 0.6:
            # 情绪高涨，偏好短线
            return HoldingType.SHORT_TERM
        elif self.mood < 0.4:
            # 情绪低落，偏好长线稳健
            return HoldingType.LONG_TERM
        else:
            # 正常状态，偏好中线
            return HoldingType.MID_TERM


class DiversifiedInvestmentSystem:
    """多样化投资系统"""

    def __init__(self, config: InvestmentConfig = None, use_llm_agent: bool = False):
        """初始化"""
        self.config = config or InvestmentConfig()
        self.cash = self.config.initial_cash
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[dict] = []
        self.behavior = HumanInvestorBehavior(self.config)

        # LLM Agent 策略
        self.use_llm_agent = use_llm_agent
        self.llm_agent = None
        if use_llm_agent:
            try:
                from app.llm_agent import LLMAgentStrategy, AgentConfig
                agent_config = AgentConfig.from_env()
                if agent_config.enabled:
                    self.llm_agent = LLMAgentStrategy(self, agent_config)
                    logger.info("✅ LLM Agent策略已启用")
                else:
                    logger.info("ℹ️ LLM Agent配置为禁用状态")
            except Exception as e:
                logger.warning(f"⚠️ LLM Agent初始化失败: {e}")

        # 目录设置
        self.portfolio_dir = PROJECT_ROOT / "portfolio"
        self.reports_dir = PROJECT_ROOT / "reports"
        self.portfolio_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

        # 状态文件 (统一使用 positions.json)
        self.state_file = self.portfolio_dir / "positions.json"

        # 加载状态
        self._load_state()

        logger.info("=" * 60)
        logger.info("多样化投资系统 v4.0 初始化完成")
        logger.info(f"初始资金: ¥{self.config.initial_cash:,.2f}")
        logger.info(f"投资风格: {self.config.investment_style.value}")
        logger.info(f"最大持仓: {self.config.max_holdings} 只")
        logger.info("=" * 60)

    def _load_state(self):
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.cash = data.get('cash', self.config.initial_cash)
                self.trade_history = data.get('trades', [])

                # 重建持仓
                for symbol, pos_data in data.get('positions', {}).items():
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        name=pos_data['name'],
                        shares=pos_data['shares'],
                        avg_cost=pos_data['avg_cost'],
                        current_price=pos_data['current_price'],
                        holding_type=HoldingType(pos_data['holding_type']),
                        sector=Sector(pos_data['sector']),
                        buy_date=pos_data['buy_date'],
                        strategy=pos_data['strategy'],
                        target_price=pos_data.get('target_price', 0),
                        stop_loss=pos_data.get('stop_loss', 0),
                        notes=pos_data.get('notes', '')
                    )
                logger.info(f"状态已加载: {len(self.positions)} 只持仓")
            except Exception as e:
                logger.warning(f"加载状态失败: {e}")

    def _save_state(self):
        """保存状态"""
        data = {
            'cash': self.cash,
            'positions': {
                symbol: {
                    'name': pos.name,
                    'shares': pos.shares,
                    'avg_cost': pos.avg_cost,
                    'current_price': pos.current_price,
                    'holding_type': pos.holding_type.value,
                    'sector': pos.sector.value,
                    'buy_date': pos.buy_date,
                    'strategy': pos.strategy,
                    'target_price': pos.target_price,
                    'stop_loss': pos.stop_loss,
                    'notes': pos.notes
                }
                for symbol, pos in self.positions.items()
            },
            'trades': self.trade_history,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_stock_price(self, symbol: str) -> float:
        """获取股票价格 - 使用增强版数据获取器"""
        from app.services.data_fetcher_enhanced import EnhancedDataFetcher

        manager = EnhancedDataFetcher()

        try:
            price = manager.get_current_price(symbol)
            if price is None:
                # 降级：使用持仓的当前价格或成本价
                if symbol in self.positions:
                    price = self.positions[symbol].current_price or self.positions[symbol].avg_cost
                else:
                    raise ValueError(f"无法获取 {symbol} 价格")
            logger.debug(f"{symbol} 真实价格: ¥{price:.2f}")
            return price
        except Exception as e:
            logger.error(f"无法获取 {symbol} 真实价格: {e}")
            # 降级使用持仓价格
            if symbol in self.positions:
                return self.positions[symbol].current_price or self.positions[symbol].avg_cost
            raise ValueError(f"无法获取 {symbol} 的真实价格，请检查数据源")
        finally:
            if hasattr(manager, 'close'):
                manager.close()

    def get_total_equity(self) -> float:
        """计算总权益"""
        market_value = sum(
            pos.shares * self.get_stock_price(symbol)
            for symbol, pos in self.positions.items()
        )
        return self.cash + market_value

    def get_portfolio_analysis(self) -> dict:
        """分析投资组合"""
        analysis = {
            'total_equity': self.get_total_equity(),
            'cash': self.cash,
            'cash_ratio': self.cash / self.get_total_equity() if self.get_total_equity() > 0 else 1,
            'positions': [],
            'sector_allocation': {},
            'holding_type_allocation': {},
            'pnl': {}
        }

        # 持仓详情
        for symbol, pos in self.positions.items():
            current_price = self.get_stock_price(symbol)
            market_value = pos.shares * current_price
            pnl = market_value - (pos.shares * pos.avg_cost)
            pnl_pct = pnl / (pos.shares * pos.avg_cost) if pos.avg_cost > 0 else 0

            analysis['positions'].append({
                'symbol': symbol,
                'name': pos.name,
                'shares': pos.shares,
                'avg_cost': pos.avg_cost,
                'current_price': current_price,
                'market_value': market_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'holding_type': pos.holding_type.value,
                'sector': pos.sector.value
            })

            # 板块分配
            sector = pos.sector.value
            analysis['sector_allocation'][sector] = analysis['sector_allocation'].get(sector, 0) + market_value

            # 持仓类型分配
            htype = pos.holding_type.value
            analysis['holding_type_allocation'][htype] = analysis['holding_type_allocation'].get(htype, 0) + market_value

        # 盈亏统计
        total_pnl = analysis['total_equity'] - self.config.initial_cash
        analysis['pnl'] = {
            'total': total_pnl,
            'pct': total_pnl / self.config.initial_cash * 100 if self.config.initial_cash > 0 else 0
        }

        return analysis

    def select_stocks_to_buy(self) -> List[Tuple[StockInfo, float, str]]:
        """选择要买入的股票

        Returns:
            List of (StockInfo, signal_strength, reason)
        """
        candidates = []
        total_equity = self.get_total_equity()

        # 获取当前板块分配
        sector_values = {}
        for pos in self.positions.values():
            sector_values[pos.sector] = sector_values.get(pos.sector, 0) + pos.shares * self.get_stock_price(pos.symbol)

        # 遍历所有板块和股票
        for sector, stocks in STOCK_POOL.items():
            current_sector_value = sector_values.get(sector, 0)
            sector_limit = total_equity * self.config.max_position_per_sector

            # 如果板块已满，跳过
            if current_sector_value >= sector_limit:
                continue

            for stock in stocks:
                # 检查是否已持有
                if stock.symbol in self.positions:
                    continue

                # 计算信号强度
                signal = self._calculate_buy_signal(stock)

                if signal['strength'] > 0.3:  # 信号阈值
                    candidates.append((stock, signal['strength'], signal['reason']))

        # 按信号强度排序
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[:5]  # 返回前5个候选

    def _calculate_buy_signal(self, stock: StockInfo) -> dict:
        """计算买入信号"""
        signal = {'strength': 0.0, 'reason': ''}

        # 1. 蓝筹股加分
        if stock.is_blue_chip:
            signal['strength'] += 0.2
            signal['reason'] += '蓝筹股;'

        # 2. 股息率加分
        if stock.dividend_yield > 0.04:
            signal['strength'] += 0.15
            signal['reason'] += f'高股息{stock.dividend_yield:.1%};'

        # 3. 成长股加分 (根据投资风格)
        if stock.is_growth and self.config.investment_style == InvestmentStyle.AGGRESSIVE:
            signal['strength'] += 0.25
            signal['reason'] += '成长股;'

        # 4. 低波动率加分 (保守风格)
        if stock.volatility < 0.2 and self.config.investment_style == InvestmentStyle.CONSERVATIVE:
            signal['strength'] += 0.15
            signal['reason'] += '低波动;'

        # 5. 板块轮动 (随机因素，模拟市场判断)
        sector_momentum = random.uniform(-0.1, 0.3)
        signal['strength'] += sector_momentum
        if sector_momentum > 0.1:
            signal['reason'] += '板块走强;'

        # 6. 技术指标 (简化版)
        try:
            price = self.get_stock_price(stock.symbol)
            if price > 0:
                # 这里可以添加更多技术分析
                signal['strength'] += random.uniform(0, 0.2)
        except:
            pass

        return signal

    def execute_buy(self, stock: StockInfo, shares: int, holding_type: HoldingType,
                    strategy: str = "diversified", notes: str = "", bypass_cooldown: bool = False) -> bool:
        """执行买入"""
        # 检查交易限制
        can_trade, reason = self.behavior.should_trade(bypass_cooldown)
        if not can_trade:
            logger.warning(f"交易限制: {reason}")
            return False

        price = self.get_stock_price(stock.symbol)
        if price <= 0:
            logger.error(f"无法获取价格: {stock.symbol}")
            return False

        # 计算成本
        commission = max(shares * price * 0.003, 5.0)
        total_cost = shares * price + commission

        # 检查资金
        if total_cost > self.cash:
            logger.warning(f"资金不足: 需要 ¥{total_cost:,.2f}, 可用 ¥{self.cash:,.2f}")
            return False

        # 检查仓位限制
        total_equity = self.get_total_equity()
        if shares * price > total_equity * self.config.max_position_per_stock:
            logger.warning(f"超过单股仓位限制 {self.config.max_position_per_stock:.0%}")
            return False

        # 检查持仓数量
        if len(self.positions) >= self.config.max_holdings:
            logger.warning(f"已达最大持仓数 {self.config.max_holdings}")
            return False

        # 执行买入
        self.cash -= total_cost

        # 计算止损止盈价
        if holding_type == HoldingType.LONG_TERM:
            stop_loss = price * (1 + self.config.long_term_stop_loss)
            target = price * (1 + self.config.long_term_take_profit)
        elif holding_type == HoldingType.SHORT_TERM:
            stop_loss = price * (1 + self.config.short_term_stop_loss)
            target = price * (1 + self.config.short_term_take_profit)
        else:
            stop_loss = price * (1 + self.config.mid_term_stop_loss)
            target = price * (1 + self.config.mid_term_take_profit)

        # 创建持仓
        self.positions[stock.symbol] = Position(
            symbol=stock.symbol,
            name=stock.name,
            shares=shares,
            avg_cost=price,
            current_price=price,
            holding_type=holding_type,
            sector=stock.sector,
            buy_date=datetime.now().strftime('%Y-%m-%d'),
            strategy=strategy,
            target_price=target,
            stop_loss=stop_loss,
            notes=notes
        )

        # 记录交易
        self.trade_history.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'buy',
            'symbol': stock.symbol,
            'name': stock.name,
            'shares': shares,
            'price': price,
            'total_cost': total_cost,
            'holding_type': holding_type.value,
            'sector': stock.sector.value,
            'strategy': strategy
        })

        self.behavior.trade_count_today += 1
        self.behavior.last_trade_time = datetime.now()

        self._save_state()

        logger.info(f"✅ 买入 {stock.name}({stock.symbol}): {shares}股 @ ¥{price:.2f}")
        logger.info(f"   类型: {holding_type.value} | 板块: {stock.sector.value}")
        logger.info(f"   止损: ¥{stop_loss:.2f} | 目标: ¥{target:.2f}")

        return True

    def execute_sell(self, symbol: str, shares: int, reason: str = "") -> bool:
        """执行卖出"""
        if symbol not in self.positions:
            logger.warning(f"未持有: {symbol}")
            return False

        pos = self.positions[symbol]
        price = self.get_stock_price(symbol)

        if price <= 0:
            logger.error(f"无法获取价格: {symbol}")
            return False

        shares = min(shares, pos.shares)

        # 计算收入
        commission = max(shares * price * 0.003, 5.0)
        stamp_duty = shares * price * 0.001  # 印花税
        total_revenue = shares * price - commission - stamp_duty

        # 计算盈亏
        cost = shares * pos.avg_cost
        pnl = total_revenue - cost
        pnl_pct = pnl / cost * 100 if cost > 0 else 0

        # 更新资金
        self.cash += total_revenue

        # 更新情绪
        self.behavior.update_mood(pnl_pct / 100)

        # 记录交易
        self.trade_history.append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'sell',
            'symbol': symbol,
            'name': pos.name,
            'shares': shares,
            'price': price,
            'total_revenue': total_revenue,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason,
            'holding_days': (datetime.now() - datetime.strptime(pos.buy_date, '%Y-%m-%d')).days
        })

        # 更新持仓
        pos.shares -= shares
        if pos.shares <= 0:
            del self.positions[symbol]

        self.behavior.trade_count_today += 1
        self.behavior.last_trade_time = datetime.now()

        self._save_state()

        logger.info(f"✅ 卖出 {pos.name}({symbol}): {shares}股 @ ¥{price:.2f}")
        logger.info(f"   盈亏: ¥{pnl:+,.2f} ({pnl_pct:+.2f}%) | 原因: {reason}")

        return True

    def check_stop_loss_take_profit(self):
        """检查止损止盈"""
        for symbol, pos in list(self.positions.items()):
            current_price = self.get_stock_price(symbol)
            if current_price <= 0:
                continue

            pnl_pct = (current_price - pos.avg_cost) / pos.avg_cost * 100

            # 止损检查
            if current_price <= pos.stop_loss:
                logger.warning(f"⚠️ {pos.name} 触发止损: {pnl_pct:.2f}%")
                self.execute_sell(symbol, pos.shares, f"止损 {pnl_pct:.2f}%")

            # 止盈检查
            elif current_price >= pos.target_price:
                logger.info(f"💰 {pos.name} 触发止盈: +{pnl_pct:.2f}%")
                self.execute_sell(symbol, pos.shares, f"止盈 +{pnl_pct:.2f}%")

    def rebalance_portfolio(self):
        """调仓"""
        logger.info("🔄 执行调仓检查...")

        analysis = self.get_portfolio_analysis()

        # 1. 检查现金比例
        if analysis['cash_ratio'] < self.config.min_cash_reserve:
            logger.info(f"现金比例过低 {analysis['cash_ratio']:.1%}，考虑减仓")
            # 卖出表现最差的持仓
            worst_position = min(analysis['positions'], key=lambda x: x['pnl_pct'])
            if worst_position['pnl_pct'] < 0:
                self.execute_sell(worst_position['symbol'],
                                  self.positions[worst_position['symbol']].shares // 2,
                                  "调仓减仓")

        # 2. 检查板块集中度
        total_equity = analysis['total_equity']
        for sector, value in analysis['sector_allocation'].items():
            if value / total_equity > self.config.max_position_per_sector:
                logger.info(f"板块 {sector} 超配 {value/total_equity:.1%}，考虑减仓")
                # 找出该板块中表现最好的股票保留，卖出部分其他
                sector_positions = [p for p in analysis['positions'] if p['sector'] == sector]
                sector_positions.sort(key=lambda x: x['pnl_pct'], reverse=True)
                if len(sector_positions) > 1:
                    # 卖出表现较差的
                    for pos in sector_positions[1:]:
                        if pos['pnl_pct'] > 0:  # 有盈利才卖
                            self.execute_sell(pos['symbol'],
                                              self.positions[pos['symbol']].shares // 3,
                                              "板块调仓")
                            break

        # 3. 寻找新的投资机会
        if len(self.positions) < self.config.max_holdings and analysis['cash_ratio'] > self.config.min_cash_reserve:
            candidates = self.select_stocks_to_buy()
            for stock, strength, reason in candidates:
                if len(self.positions) >= self.config.max_holdings:
                    break

                # 决定持仓类型
                holding_type = self.behavior.get_holding_type_preference()

                # 决定买入数量
                base_size = total_equity * self.config.max_position_per_stock
                position_size = self.behavior.decide_position_size(base_size, strength)

                price = self.get_stock_price(stock.symbol)
                shares = int(position_size / price / 100) * 100

                if shares >= 100:
                    self.execute_buy(stock, shares, holding_type, "diversified", reason)

    def generate_report(self) -> str:
        """生成投资报告"""
        analysis = self.get_portfolio_analysis()

        report = f"""
================================================================================
                     多样化投资组合报告
================================================================================

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
投资风格: {self.config.investment_style.value}

【资金概况】
初始资金: ¥{self.config.initial_cash:,.2f}
当前现金: ¥{self.cash:,.2f}
总权益:   ¥{analysis['total_equity']:,.2f}
总盈亏:   ¥{analysis['pnl']['total']:+,.2f} ({analysis['pnl']['pct']:+.2f}%)
现金比例: {analysis['cash_ratio']:.1%}

【持仓概况】
持仓数量: {len(self.positions)} 只
最大持仓: {self.config.max_holdings} 只

【持仓明细】
"""
        for pos in analysis['positions']:
            report += f"""
{pos['name']}({pos['symbol']})
  持仓: {pos['shares']}股 @ ¥{pos['avg_cost']:.2f}
  现价: ¥{pos['current_price']:.2f} | 市值: ¥{pos['market_value']:,.2f}
  盈亏: ¥{pos['pnl']:+,.2f} ({pos['pnl_pct']:+.2f}%)
  类型: {pos['holding_type']} | 板块: {pos['sector']}
"""

        report += f"""
【板块配置】
"""
        for sector, value in analysis['sector_allocation'].items():
            pct = value / analysis['total_equity'] * 100
            report += f"  {sector}: ¥{value:,.2f} ({pct:.1f}%)\n"

        report += f"""
【持仓类型分布】
"""
        for htype, value in analysis['holding_type_allocation'].items():
            pct = value / analysis['total_equity'] * 100
            report += f"  {htype}: ¥{value:,.2f} ({pct:.1f}%)\n"

        report += f"""
【交易统计】
总交易次数: {len(self.trade_history)}
买入次数: {len([t for t in self.trade_history if t['type'] == 'buy'])}
卖出次数: {len([t for t in self.trade_history if t['type'] == 'sell'])}

盈利交易: {len([t for t in self.trade_history if t['type'] == 'sell' and t.get('pnl', 0) > 0])}
亏损交易: {len([t for t in self.trade_history if t['type'] == 'sell' and t.get('pnl', 0) <= 0])}

【投资者情绪】
情绪指数: {self.behavior.mood:.2f}
信心指数: {self.behavior.confidence:.2f}

================================================================================
"""
        return report

    def run_auto_investment(self, initial_build: bool = False, use_agent: bool = None):
        """自动投资运行

        Args:
            initial_build: 是否执行初始建仓
            use_agent: 是否使用LLM Agent（None表示使用系统配置）
        """
        logger.info("=" * 60)
        logger.info("🚀 开始自动投资流程")
        if use_agent or (use_agent is None and self.use_llm_agent and self.llm_agent):
            logger.info("🤖 使用LLM Agent策略")
        logger.info("=" * 60)

        # 0. 初始建仓（如果需要）
        if initial_build and len(self.positions) < 3:
            self.initial_portfolio_build()

        # 1. 检查止损止盈（始终执行，风控兜底）
        self.check_stop_loss_take_profit()

        # 2. 决策层 - 根据配置选择策略
        should_use_agent = use_agent or (use_agent is None and self.use_llm_agent and self.llm_agent)

        if should_use_agent and self.llm_agent and self.llm_agent.is_available():
            # 使用LLM Agent决策
            try:
                logger.info("🤖 LLM Agent正在生成决策...")
                decisions = self.llm_agent.make_decision()
                if decisions:
                    logger.info(f"📋 LLM Agent生成 {len(decisions)} 个决策")
                    results = self.llm_agent.execute_decisions(decisions)
                    for result in results:
                        status = result.get("status", "unknown")
                        action = result.get("action", "unknown")
                        if status == "success":
                            logger.info(f"  ✅ {action}: {result.get('symbol', 'N/A')}")
                        elif status == "failed":
                            logger.warning(f"  ⚠️ {action}失败: {result.get('error', 'unknown')}")
                        else:
                            logger.error(f"  ❌ {action}错误: {result.get('error', 'unknown')}")
                else:
                    logger.info("📋 LLM Agent未生成决策（可能处于观望状态）")
            except Exception as e:
                logger.error(f"❌ LLM Agent决策失败: {e}")
                logger.info("🔄 降级到规则策略")
                self.rebalance_portfolio()
        else:
            # 使用原有规则策略
            logger.info("📊 使用规则策略")
            self.rebalance_portfolio()

        # 3. 生成报告
        report = self.generate_report()
        print(report)

        # 保存报告
        report_file = self.reports_dir / f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"📄 报告已保存: {report_file}")

        return report

    def initial_portfolio_build(self):
        """初始建仓 - 构建多样化投资组合"""
        logger.info("🏗️ 开始初始建仓...")

        total_equity = self.get_total_equity()
        target_positions = min(self.config.max_holdings, 6)  # 初始建仓6只

        # 按板块分配
        sector_allocation = {
            Sector.FINANCE: 0.25,      # 金融 25%
            Sector.CONSUMER: 0.20,     # 消费 20%
            Sector.TECHNOLOGY: 0.15,   # 科技 15%
            Sector.HEALTHCARE: 0.15,   # 医药 15%
            Sector.ENERGY: 0.10,       # 能源 10%
            Sector.UTILITIES: 0.10,    # 公用事业 10%
        }

        # 持仓类型分配
        holding_types = [
            (HoldingType.LONG_TERM, 0.5),   # 长线 50%
            (HoldingType.MID_TERM, 0.3),    # 中线 30%
            (HoldingType.SHORT_TERM, 0.2),  # 短线 20%
        ]

        positions_built = 0
        for sector, allocation in sector_allocation.items():
            if positions_built >= target_positions:
                break

            if sector not in STOCK_POOL:
                continue

            # 选择该板块的最佳股票
            sector_stocks = STOCK_POOL[sector]
            for stock in sector_stocks:
                if stock.symbol in self.positions:
                    continue

                # 决定持仓类型
                holding_type = holding_types[positions_built % len(holding_types)][0]

                # 计算买入金额
                position_value = total_equity * allocation * 0.8  # 留些余地

                # 获取价格
                price = self.get_stock_price(stock.symbol)
                if price <= 0:
                    logger.warning(f"无法获取 {stock.symbol} 价格，跳过")
                    continue

                # 计算股数（整手）
                shares = int(position_value / price / 100) * 100
                if shares < 100:
                    logger.warning(f"{stock.symbol} 资金不足买入100股，跳过")
                    continue

                # 执行买入（跳过冷静期）
                if self.execute_buy(stock, shares, holding_type, "initial_build",
                                   f"初始建仓 - {sector.value}", bypass_cooldown=True):
                    positions_built += 1
                    logger.info(f"建仓进度: {positions_built}/{target_positions}")
                    break

        logger.info(f"✅ 初始建仓完成，共建立 {len(self.positions)} 个持仓")


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='多样化投资系统')
    parser.add_argument('--init', action='store_true', help='执行初始建仓')
    parser.add_argument('--cash', type=float, default=100000, help='初始资金')
    parser.add_argument('--style', type=str, default='balanced',
                       choices=['conservative', 'balanced', 'aggressive'],
                       help='投资风格')
    args = parser.parse_args()

    # 投资风格映射
    style_map = {
        'conservative': InvestmentStyle.CONSERVATIVE,
        'balanced': InvestmentStyle.BALANCED,
        'aggressive': InvestmentStyle.AGGRESSIVE
    }

    # 初始化配置
    config = InvestmentConfig(
        initial_cash=args.cash,
        investment_style=style_map[args.style],
        max_holdings=10
    )

    # 创建系统
    system = DiversifiedInvestmentSystem(config)

    # 运行自动投资
    system.run_auto_investment(initial_build=args.init)


if __name__ == "__main__":
    main()