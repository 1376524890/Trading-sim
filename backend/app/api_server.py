#!/usr/bin/env python3
"""
股票交易系统 REST API - 修复版
⚡ 由御坂网络第一代打造 ⚡

功能:
1. 持仓管理 API
2. 交易执行 API
3. 数据分析 API
4. 新闻获取 API
5. K 线数据 API

API 地址：http://localhost:8080
"""

import sys
import os
from pathlib import Path

# 启动时加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量: {env_path}")

from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio

# 添加脚本路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from app.simulated_trading import SimulatedTradingSystem
from app.services.portfolio_manager import PortfolioManager

# 初始化 FastAPI 应用
app = FastAPI(
    title="股票交易系统 API",
    description="基于 FastAPI 的股票模拟交易系统后端",
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 初始化交易系统
trading_system = None

# 创建 Pydantic 模型
class StockPrice(BaseModel):
    symbol: str
    price: float
    timestamp: str

class TradeRequest(BaseModel):
    symbol: str
    shares: int

class TradeResult(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PortfolioResponse(BaseModel):
    symbol: str
    shares: int
    avg_price: float
    current_price: float
    market_value: float
    pnl: float
    pnl_pct: float

class SummaryResponse(BaseModel):
    time: str
    initial_cash: float
    current_cash: float
    total_equity: float
    positions_count: int
    total_market_value: float
    total_pnl: float
    total_pnl_pct: float
    total_trades: int
    win_rate: float

# 使用 lifespan 替换 deprecated on_event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global trading_system, diversified_system, auto_scheduler_running, scheduler_task, scheduler_interval_seconds

    try:
        # 检查是否启用LLM Agent
        agent_enabled = os.getenv("AGENT_ENABLED", "false").lower() == "true"
        if agent_enabled:
            logger.info("🤖 LLM Agent已启用")

        # 初始化多样化投资系统（主系统）
        from app.diversified_investment import DiversifiedInvestmentSystem, InvestmentConfig, InvestmentStyle
        config = InvestmentConfig(
            initial_cash=100000,
            investment_style=InvestmentStyle.BALANCED,
            max_holdings=10
        )
        diversified_system = DiversifiedInvestmentSystem(config, use_llm_agent=agent_enabled)
        logger.info("多样化投资系统初始化完成")

        # 保留旧系统兼容性（仅用于回测等）
        trading_system = SimulatedTradingSystem(initial_cash=10000)
        logger.info("交易系统初始化完成")

        # 自动启动调度器
        scheduler_interval_seconds = get_scheduler_interval()
        auto_scheduler_running = True
        scheduler_task = asyncio.create_task(scheduler_loop())
        logger.info(f"✅ 自动调度器已启动，间隔 {scheduler_interval_seconds}秒 ({scheduler_interval_seconds/60}分钟)")

    except Exception as e:
        logger.error(f"交易系统初始化失败：{e}")
        raise

    yield

    # 关闭前清理
    auto_scheduler_running = False
    if scheduler_task:
        logger.info("正在停止调度器...")
        try:
            await asyncio.wait_for(scheduler_task, timeout=5)
        except:
            scheduler_task.cancel()

    # 保存多样化系统状态
    if diversified_system:
        diversified_system._save_state()
        logger.info("多样化投资系统已关闭并保存")

app.router.lifespan_context = lifespan

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 健康检查 ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "股票交易系统 API",
        "version": "1.0.1",
        "status": "running",
        "timezone": "Asia/Shanghai"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "stock-api"
    }


# ============ 投资组合 API ============

@app.get("/api/portfolio/summary")
async def get_portfolio_summary():
    """获取投资组合摘要"""
    try:
        # 直接调用交易系统的 get_portfolio_summary
        result = trading_system.get_portfolio_summary()
        
        # PerformanceMetrics 需要转换为 dict
        if hasattr(result, 'to_dict'):
            return result.to_dict()
        return result
    except Exception as e:
        logger.error(f"获取组合摘要失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/positions")
async def get_portfolio_positions():
    """获取当前持仓"""
    try:
        # 从 PortfolioManager 获取持仓
        positions = trading_system.portfolio_manager.positions
        
        if not positions:
            return {"status": "empty", "positions": []}
        
        position_list = []
        for symbol, pos in positions.items():
            # 获取最新价格
            current_price = trading_system.get_stock_price(symbol)
            if current_price is None:
                current_price = pos.current_price if hasattr(pos, 'current_price') else pos.avg_cost
            
            market_value = pos.shares * current_price
            pnl = market_value - (pos.shares * pos.avg_cost)
            pnl_pct = (pnl / (pos.shares * pos.avg_cost) * 100) if pos.avg_cost > 0 else 0
            
            position_list.append({
                "symbol": symbol,
                "shares": pos.shares,
                "avg_price": pos.avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct
            })
        
        total_equity = trading_system.portfolio_manager.get_total_equity()
        total_market_value = trading_system.portfolio_manager.get_total_market_value()
        
        return {
            "status": "active",
            "positions": position_list,
            "cash": trading_system.current_cash,
            "total_value": total_market_value,
            "total_equity": total_equity
        }
    except Exception as e:
        logger.error(f"获取持仓失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 交易 API ============

@app.post("/api/trade/buy")
async def buy_stock(trade: TradeRequest):
    """买入股票"""
    try:
        result = trading_system.buy(trade.symbol, trade.shares)
        
        if result['success']:
            return TradeResult(
                success=True,
                message=f"成功买入 {trade.symbol}: {trade.shares} 股",
                data=result
            )
        else:
            return TradeResult(
                success=False,
                message=result['error']
            )
    except Exception as e:
        logger.error(f"买入股票失败：{e}")
        return TradeResult(
            success=False,
            message=f"买入失败：{str(e)}"
        )


@app.post("/api/trade/sell")
async def sell_stock(trade: TradeRequest):
    """卖出股票"""
    try:
        result = trading_system.sell(trade.symbol, trade.shares)
        
        if result['success']:
            return TradeResult(
                success=True,
                message=f"成功卖出 {trade.symbol}: {trade.shares} 股",
                data=result
            )
        else:
            return TradeResult(
                success=False,
                message=result['error']
            )
    except Exception as e:
        logger.error(f"卖出股票失败：{e}")
        return TradeResult(
            success=False,
            message=f"卖出失败：{str(e)}"
        )


@app.get("/api/trade/history")
async def get_trade_history():
    """获取交易历史记录"""
    try:
        history = trading_system.trade_history
        
        # 返回最近 100 条交易
        return {
            "total": len(history),
            "trades": history[-100:]
        }
    except Exception as e:
        logger.error(f"获取交易历史失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 股票数据 API ============

@app.get("/api/stock/price/{symbol}")
async def get_stock_price(symbol: str):
    """获取股票当前价格"""
    try:
        price = trading_system.get_stock_price(symbol)
        
        if price is None:
            raise HTTPException(status_code=404, detail="无法获取价格")
        
        return {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取价格失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/history")
async def get_stock_history(symbol: str, days: int = 30):
    """获取股票历史数据"""
    try:
        from app.services.data_fetcher_enhanced import EnhancedDataFetcher
        from datetime import datetime, timedelta

        data_fetcher = EnhancedDataFetcher()

        # 确保符号格式正确 (如果已包含 .SS 或 .SZ 则不再添加)
        fetch_symbol = symbol if '.' in symbol else f"{symbol}.SS"

        # 添加超时保护 - 使用简短超时以避免长时间等待
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("数据获取超时")

        # 设置超时为 5 秒
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)

        try:
            df = data_fetcher.fetch_stock_data(
                fetch_symbol,
                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            signal.alarm(0)  # 取消超时
        except TimeoutError:
            signal.alarm(0)
            logger.warning(f"获取 {symbol} 历史数据超时")
            return {"symbol": symbol, "data": [], "error": "数据获取超时"}
        except Exception as e:
            signal.alarm(0)
            logger.error(f"获取 {symbol} 历史数据失败: {e}")
            return {"symbol": symbol, "data": [], "error": str(e)}

        if df.empty:
            return {"symbol": symbol, "data": []}

        # 转换为 JSON 可序列化的格式
        history = []
        for _, row in df.iterrows():
            date_val = row.get('Date', row.get('date', ''))
            # 处理日期格式
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val).split(' ')[0]  # 取日期部分

            history.append({
                "date": date_str,
                "open": float(row.get('Open', row.get('open', 0))),
                "high": float(row.get('High', row.get('high', 0))),
                "low": float(row.get('Low', row.get('low', 0))),
                "close": float(row.get('Close', row.get('close', 0))),
                "volume": float(row.get('Volume', row.get('volume', 0)))
            })
        
        return {
            "symbol": symbol,
            "days": days,
            "data": history
        }
    except Exception as e:
        logger.error(f"获取历史数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 分析 API ============

@app.get("/api/analysis/summary")
async def get_analysis_summary():
    """获取投资分析摘要"""
    try:
        summary = trading_system.get_portfolio_summary()
        
        # 计算分析指标
        analytics = {
            "total_equity": summary['total_equity'],
            "initial_cash": summary['initial_cash'],
            "total_pnl": summary['total_pnl'],
            "total_pnl_pct": summary['total_pnl_pct'],
            "win_rate": summary['win_rate'],
            "profit_factor": summary['profit_factor'],
            "sharpe_ratio": summary['sharpe_ratio'],
            "total_trades": summary['total_trades'],
            "winning_trades": summary['winning_trades'],
            "losing_trades": summary['losing_trades']
        }
        
        return analytics
    except Exception as e:
        logger.error(f"获取分析摘要失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/risk")
async def get_risk_analysis():
    """获取风险分析"""
    try:
        positions = trading_system.portfolio_manager.positions
        
        if not positions:
            return {
                "status": "no_positions",
                "message": "暂无持仓"
            }
        
        # 计算风险指标
        total_equity = trading_system.portfolio_manager.get_total_equity()
        
        # 集中度分析
        position_values = [pos.shares * pos.current_price for pos in positions.values()]
        concentration = max(position_values) / total_equity * 100 if total_equity > 0 else 0
        
        # 最大回撤（简化版）
        max_drawdown = max(
            [pos.shares * (pos.current_price - pos.avg_cost) for pos in positions.values() if pos.shares > 0],
            default=0
        )
        
        return {
            "status": "active",
            "position_count": len(positions),
            "concentration": concentration,
            "max_drawdown": max_drawdown,
            "diversification_score": 100 - concentration if concentration < 50 else 50
        }
    except Exception as e:
        logger.error(f"获取风险分析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 每日报告 API ============

@app.get("/api/reports/daily")
async def get_daily_report():
    """获取每日报告"""
    try:
        report_file = trading_system.generate_daily_report()
        
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        return {
            "file": str(report_file),
            "generated_at": datetime.now().isoformat(),
            "content": report_content
        }
    except Exception as e:
        logger.error(f"生成报告失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 新闻 API ============

@app.get("/api/news")
async def get_news(limit: int = 10):
    """获取新闻摘要"""
    try:
        import asyncio
        from app.services.news_scraper import NewsScraper

        async def fetch_news():
            scraper = NewsScraper()
            return scraper.fetch_latest_news(limit=limit)

        # 添加超时保护 (5秒)
        try:
            news_items = await asyncio.wait_for(fetch_news(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("新闻获取超时")
            return {
                "total": 0,
                "categorized": {"positive": [], "neutral": [], "negative": []},
                "error": "新闻获取超时",
                "fetched_at": datetime.now().isoformat()
            }

        # 分类
        categorized_news = {
            "positive": [],
            "neutral": [],
            "negative": []
        }

        for news in news_items:
            sentiment = news.get('sentiment', 'neutral')
            if sentiment in categorized_news:
                categorized_news[sentiment].append(news)
            else:
                categorized_news['neutral'].append(news)

        return {
            "total": len(news_items),
            "categorized": categorized_news,
            "fetched_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取新闻失败：{e}")
        return {
            "total": 0,
            "categorized": {
                "positive": [],
                "neutral": [],
                "negative": []
            },
            "error": str(e)
        }


# ============ 回测 API ============

# 回测结果存储（内存中，实际应用应使用数据库）
backtest_results_db = []
backtest_results_counter = 0

# 项目根目录
project_root = Path(__file__).parent.parent

# 加载已有的回测结果
backtest_results_dir = project_root / "backtests" / "results"
backtest_results_dir.mkdir(parents=True, exist_ok=True)

def load_existing_backtest_results():
    """加载已有的回测结果"""
    global backtest_results_counter
    try:
        result_files = list(backtest_results_dir.glob("backtest_result_*.json"))
        for file_path in sorted(result_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'id' in data and data['id'] > backtest_results_counter:
                        backtest_results_counter = data['id']
                    backtest_results_db.append(data)
            except Exception as e:
                logger.error(f"加载回测结果失败 {file_path}: {e}")
        logger.info(f"已加载 {len(backtest_results_db)} 条回测结果")
    except Exception as e:
        logger.error(f"加载回测结果目录失败: {e}")

# 启动时加载已有结果
load_existing_backtest_results()

@app.get("/api/backtest/results")
async def get_backtest_results(limit: int = 10, offset: int = 0):
    """
    获取回测结果列表

    Args:
        limit: 返回数量限制
        offset: 偏移量
    """
    try:
        # 按时间倒序排列
        sorted_results = sorted(backtest_results_db, key=lambda x: x.get('timestamp', ''), reverse=True)
        total = len(sorted_results)
        results = sorted_results[offset:offset + limit]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "results": results
        }
    except Exception as e:
        logger.error(f"获取回测结果失败：{e}")
        return {
            "total": 0,
            "offset": offset,
            "limit": limit,
            "results": [],
            "error": str(e)
        }

@app.get("/api/backtest/results/{result_id}")
async def get_backtest_result_detail(result_id: int):
    """
    获取单个回测结果详情

    Args:
        result_id: 回测结果ID
    """
    try:
        result = next((r for r in backtest_results_db if r.get('id') == result_id), None)
        if result:
            return {
                "success": True,
                "result": result
            }
        else:
            return {
                "success": False,
                "error": "回测结果不存在"
            }
    except Exception as e:
        logger.error(f"获取回测详情失败：{e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/backtest/run")
async def run_backtest(
    symbol: str = Query(default="601398.SS", description="股票代码"),
    strategy: str = Query(default="ma_cross", description="策略名称"),
    start_date: str = Query(default=None, description="开始日期(YYYY-MM-DD)"),
    end_date: str = Query(default=None, description="结束日期(YYYY-MM-DD)"),
    initial_cash: float = Query(default=10000, description="初始资金"),
    short_period: int = Query(default=5, description="短期均线周期"),
    long_period: int = Query(default=10, description="长期均线周期")
):
    """
    运行回测

    Args:
        symbol: 股票代码
        strategy: 策略名称 (ma_cross/buy_hold)
        start_date: 开始日期，默认为一年前
        end_date: 结束日期，默认为今天
        initial_cash: 初始资金
        short_period: 短期均线周期
        long_period: 长期均线周期
    """
    try:
        import subprocess
        import sys

        # 设置默认日期
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # 构建回测命令
        backtest_script = project_root / "backtests" / "backtest_main.py"

        cmd = [
            sys.executable,
            str(backtest_script),
            '--symbol', symbol,
            '--start-date', start_date,
            '--end-date', end_date,
            '--initial-cash', str(initial_cash),
            '--short-period', str(short_period),
            '--long-period', str(long_period),
            '--config', str(project_root / 'backtests' / 'backtest_config.json')
        ]

        logger.info(f"执行回测命令: {' '.join(cmd)}")

        # 执行回测（异步）
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            logger.error(f"回测执行失败: {result.stderr}")
            return {
                "success": False,
                "error": "回测执行失败",
                "stderr": result.stderr
            }

        # 查找最新的回测结果文件
        result_files = list(backtest_results_dir.glob("backtest_result_*.json"))
        if result_files:
            latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                backtest_data = json.load(f)

            # 添加到内存数据库
            global backtest_results_counter
            backtest_results_counter += 1
            backtest_data['id'] = backtest_results_counter
            backtest_data['strategy'] = strategy
            backtest_data['timestamp'] = datetime.now().isoformat()
            backtest_results_db.append(backtest_data)

            return {
                "success": True,
                "result_id": backtest_results_counter,
                "result": backtest_data
            }
        else:
            return {
                "success": True,
                "message": "回测已执行，但未找到结果文件"
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "回测执行超时（5分钟）"
        }
    except Exception as e:
        logger.error(f"运行回测失败：{e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/backtest/strategies")
async def get_backtest_strategies():
    """获取可用的回测策略列表"""
    try:
        strategies = [
            {
                "name": "ma_cross",
                "display_name": "均线交叉策略",
                "description": "当短期均线上穿长期均线时买入，下穿时卖出",
                "params": [
                    {"name": "short_period", "type": "int", "default": 5, "description": "短期均线周期"},
                    {"name": "long_period", "type": "int", "default": 20, "description": "长期均线周期"}
                ]
            },
            {
                "name": "buy_hold",
                "display_name": "买入持有策略",
                "description": "简单买入并持有，不进行调仓",
                "params": []
            },
            {
                "name": "rsi_mean_reversion",
                "display_name": "RSI均值回归策略",
                "description": "基于RSI超买超卖信号进行交易",
                "params": [
                    {"name": "rsi_period", "type": "int", "default": 14, "description": "RSI计算周期"},
                    {"name": "overbought", "type": "int", "default": 70, "description": "超买阈值"},
                    {"name": "oversold", "type": "int", "default": 30, "description": "超卖阈值"}
                ]
            }
        ]
        return {
            "success": True,
            "strategies": strategies
        }
    except Exception as e:
        logger.error(f"获取策略列表失败：{e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============ 多样化投资 API ============

# 多样化投资系统实例
diversified_system = None

def get_diversified_system(use_llm_agent: bool = None):
    """获取多样化投资系统实例"""
    global diversified_system
    if diversified_system is None:
        try:
            from app.diversified_investment import DiversifiedInvestmentSystem, InvestmentConfig, InvestmentStyle
            from app.llm_agent.config import AgentConfig

            # 从环境变量读取 Agent 配置，默认根据 AGENT_ENABLED 决定是否启用
            agent_config = AgentConfig.from_env()
            if use_llm_agent is None:
                use_llm_agent = agent_config.enabled

            config = InvestmentConfig(
                initial_cash=100000,
                investment_style=InvestmentStyle.BALANCED,
                max_holdings=10
            )
            diversified_system = DiversifiedInvestmentSystem(config, use_llm_agent=use_llm_agent)
        except Exception as e:
            logger.error(f"初始化多样化投资系统失败: {e}")
    return diversified_system


@app.get("/api/diversified/summary")
async def get_diversified_summary():
    """获取多样化投资组合摘要"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        analysis = system.get_portfolio_analysis()

        return {
            "success": True,
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_equity": analysis['total_equity'],
            "cash": analysis['cash'],
            "cash_ratio": round(analysis['cash_ratio'] * 100, 1),
            "positions_count": len(analysis['positions']),
            "total_pnl": analysis['pnl']['total'],
            "total_pnl_pct": round(analysis['pnl']['pct'], 2),
            "sector_allocation": analysis['sector_allocation'],
            "holding_type_allocation": analysis['holding_type_allocation']
        }
    except Exception as e:
        logger.error(f"获取多样化摘要失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/diversified/positions")
async def get_diversified_positions():
    """获取多样化投资组合持仓"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        analysis = system.get_portfolio_analysis()

        return {
            "success": True,
            "positions": analysis['positions'],
            "sector_allocation": analysis['sector_allocation'],
            "holding_type_allocation": analysis['holding_type_allocation']
        }
    except Exception as e:
        logger.error(f"获取多样化持仓失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/diversified/stock-pool")
async def get_stock_pool():
    """获取股票池"""
    try:
        from app.diversified_investment import get_cached_stock_pool, Sector

        # 使用扩展股票池（从Baostock获取的5500+只股票）
        stock_pool = get_cached_stock_pool()

        pool_data = {}
        total_stocks = 0
        for sector, stocks in stock_pool.items():
            pool_data[sector.value] = [
                {
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "market_cap": stock.market_cap,
                    "volatility": stock.volatility,
                    "dividend_yield": stock.dividend_yield,
                    "is_blue_chip": stock.is_blue_chip,
                    "is_growth": stock.is_growth
                }
                for stock in stocks
            ]
            total_stocks += len(stocks)

        return {
            "success": True,
            "stock_pool": pool_data,
            "total_stocks": total_stocks
        }
    except Exception as e:
        logger.error(f"获取股票池失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/diversified/rebalance")
async def trigger_rebalance():
    """触发调仓"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        system.rebalance_portfolio()

        return {
            "success": True,
            "message": "调仓完成",
            "positions_count": len(system.positions)
        }
    except Exception as e:
        logger.error(f"调仓失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/diversified/initial-build")
async def initial_build():
    """初始建仓 - 构建多样化投资组合"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        # 执行初始建仓
        system.initial_portfolio_build()

        return {
            "success": True,
            "message": "初始建仓完成",
            "positions_count": len(system.positions),
            "cash": system.cash,
            "total_equity": system.get_total_equity()
        }
    except Exception as e:
        logger.error(f"初始建仓失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/diversified/auto-run")
async def auto_run():
    """运行自动投资流程（包含止损止盈检查和调仓）"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        # 执行自动投资
        report = system.run_auto_investment()

        return {
            "success": True,
            "message": "自动投资流程完成",
            "positions_count": len(system.positions),
            "cash": system.cash,
            "total_equity": system.get_total_equity(),
            "report": report
        }
    except Exception as e:
        logger.error(f"自动投资失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/diversified/check-stop-loss")
async def check_stop_loss():
    """检查止损止盈"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        system.check_stop_loss_take_profit()

        return {
            "success": True,
            "message": "止损止盈检查完成",
            "positions_count": len(system.positions)
        }
    except Exception as e:
        logger.error(f"止损止盈检查失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/diversified/buy")
async def manual_buy(symbol: str, shares: int = Query(..., description="买入股数")):
    """手动买入股票"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        # 查找股票信息
        from app.diversified_investment import STOCK_POOL, StockInfo, HoldingType
        stock_info = None
        for sector_stocks in STOCK_POOL.values():
            for stock in sector_stocks:
                if stock.symbol == symbol:
                    stock_info = stock
                    break
            if stock_info:
                break

        if stock_info is None:
            return {"success": False, "error": f"股票 {symbol} 不在股票池中"}

        # 默认中线持仓
        success = system.execute_buy(stock_info, shares, HoldingType.MID_TERM, "manual", "手动买入")

        return {
            "success": success,
            "message": f"买入 {symbol} {shares} 股" if success else "买入失败",
            "positions_count": len(system.positions),
            "cash": system.cash
        }
    except Exception as e:
        logger.error(f"买入失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/diversified/sell")
async def manual_sell(symbol: str, shares: int = Query(..., description="卖出股数")):
    """手动卖出股票"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        success = system.execute_sell(symbol, shares, "手动卖出")

        return {
            "success": success,
            "message": f"卖出 {symbol} {shares} 股" if success else "卖出失败",
            "positions_count": len(system.positions),
            "cash": system.cash
        }
    except Exception as e:
        logger.error(f"卖出失败: {e}")
        return {"success": False, "error": str(e)}


# ============ 自动调度器（真正实现） ============

# 调度器状态
auto_scheduler_running = False
scheduler_task = None
scheduler_interval_seconds = 300  # 默认5分钟，与AGENT_DECISION_INTERVAL同步
scheduler_last_run = None
scheduler_next_run = None


async def scheduler_loop():
    """调度器主循环 - 真正的后台任务"""
    global auto_scheduler_running, scheduler_last_run, scheduler_next_run

    logger.info("🔄 调度器后台任务启动")

    while auto_scheduler_running:
        try:
            # 计算下次运行时间
            scheduler_next_run = datetime.now() + timedelta(seconds=scheduler_interval_seconds)

            logger.info(f"📊 执行定时投资任务...")

            # 获取投资系统
            system = get_diversified_system()
            if system is None:
                logger.error("调度任务失败: 系统未初始化")
            else:
                # 1. 更新持仓价格（拉取最新数据）
                logger.info("   - 更新持仓价格...")
                try:
                    for symbol in list(system.positions.keys()):
                        price = system.get_stock_price(symbol)
                        if price:
                            system.positions[symbol].current_price = price
                except Exception as e:
                    logger.warning(f"   - 更新价格失败: {e}")

                # 2. 检查止损止盈
                logger.info("   - 检查止损止盈...")
                system.check_stop_loss_take_profit()

                # 3. 如果启用了Agent，执行Agent决策
                if system.use_llm_agent and system.llm_agent and system.llm_agent.is_available():
                    logger.info("   - 执行LLM Agent决策...")
                    try:
                        decisions = system.llm_agent.make_decision()
                        if decisions:
                            results = system.llm_agent.execute_decisions(decisions)
                            logger.info(f"   - Agent执行了 {len(decisions)} 个决策")
                    except Exception as e:
                        logger.error(f"   - Agent决策失败: {e}")
                else:
                    # 如果Agent不可用，执行常规调仓
                    logger.info("   - 执行常规调仓检查...")
                    system.rebalance_portfolio()

                # 4. 保存状态
                system._save_state()

            scheduler_last_run = datetime.now()
            next_run_str = scheduler_next_run.strftime('%H:%M:%S')
            logger.info(f"✅ 定时任务完成，下次运行: {next_run_str} (间隔 {scheduler_interval_seconds}秒)")

            # 等待下一次运行（每秒检查是否需要停止）
            for _ in range(scheduler_interval_seconds):
                if not auto_scheduler_running:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"调度任务异常: {e}")
            # 出错后等待一段时间再重试
            await asyncio.sleep(60)

    logger.info("🛑 调度器后台任务已停止")
    scheduler_next_run = None


def get_scheduler_interval() -> int:
    """获取调度间隔（秒），与Agent决策间隔同步"""
    # 从环境变量读取Agent决策间隔
    interval = int(os.getenv("AGENT_DECISION_INTERVAL", "300"))
    # 限制范围：最小60秒，最大3600秒
    return max(60, min(3600, interval))


@app.get("/api/diversified/scheduler/status")
async def get_scheduler_status():
    """获取自动调度状态"""
    return {
        "running": auto_scheduler_running,
        "interval_seconds": scheduler_interval_seconds,
        "interval_minutes": scheduler_interval_seconds / 60,
        "last_run": scheduler_last_run.isoformat() if scheduler_last_run else None,
        "next_run": scheduler_next_run.isoformat() if scheduler_next_run else None
    }


@app.post("/api/diversified/scheduler/start")
async def start_scheduler(interval_minutes: int = Query(default=None, description="调度间隔(分钟)，不设置则使用Agent配置")):
    """启动自动调度"""
    global auto_scheduler_running, scheduler_task, scheduler_interval_seconds

    if auto_scheduler_running:
        return {"success": False, "message": "调度器已在运行"}

    # 使用Agent配置的间隔或用户指定的间隔
    if interval_minutes is not None:
        scheduler_interval_seconds = interval_minutes * 60
    else:
        scheduler_interval_seconds = get_scheduler_interval()

    auto_scheduler_running = True

    # 启动后台任务
    scheduler_task = asyncio.create_task(scheduler_loop())

    logger.info(f"✅ 自动调度已启动，间隔 {scheduler_interval_seconds}秒 ({scheduler_interval_seconds/60}分钟)")

    return {
        "success": True,
        "message": f"自动调度已启动，间隔 {scheduler_interval_seconds/60} 分钟",
        "interval_seconds": scheduler_interval_seconds
    }


@app.post("/api/diversified/scheduler/stop")
async def stop_scheduler():
    """停止自动调度"""
    global auto_scheduler_running, scheduler_task

    if not auto_scheduler_running:
        return {"success": True, "message": "调度器未在运行"}

    auto_scheduler_running = False

    # 等待任务结束
    if scheduler_task:
        try:
            await asyncio.wait_for(scheduler_task, timeout=5)
        except asyncio.TimeoutError:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass
        scheduler_task = None

    logger.info("✅ 自动调度已停止")

    return {
        "success": True,
        "message": "自动调度已停止"
    }


@app.get("/api/diversified/report")
async def get_diversified_report():
    """获取多样化投资报告"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        report = system.generate_report()

        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(f"获取报告失败: {e}")
        return {"success": False, "error": str(e)}


# ============ LLM Agent API ============

@app.get("/api/agent/status")
async def get_agent_status():
    """获取LLM Agent状态"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        # 检查Agent是否初始化
        if not hasattr(system, 'llm_agent') or system.llm_agent is None:
            return {
                "success": True,
                "enabled": False,
                "available": False,
                "message": "LLM Agent未初始化"
            }

        status = system.llm_agent.get_status()
        return {
            "success": True,
            **status
        }
    except Exception as e:
        logger.error(f"获取Agent状态失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/agent/decision")
async def trigger_agent_decision():
    """手动触发LLM Agent决策"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        if not hasattr(system, 'llm_agent') or system.llm_agent is None:
            return {
                "success": False,
                "error": "LLM Agent未初始化"
            }

        if not system.llm_agent.is_available():
            return {
                "success": False,
                "error": "LLM Agent不可用（请检查配置和API密钥）"
            }

        # 执行Agent决策
        decisions = system.llm_agent.make_decision()

        if not decisions:
            return {
                "success": True,
                "message": "Agent未生成决策（可能处于观望状态）",
                "decisions": []
            }

        # 执行决策
        results = system.llm_agent.execute_decisions(decisions)

        return {
            "success": True,
            "message": f"Agent决策执行完成",
            "decisions": decisions,
            "results": results,
            "positions_count": len(system.positions),
            "cash": system.cash,
            "total_equity": system.get_total_equity()
        }
    except Exception as e:
        logger.error(f"Agent决策失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/agent/auto-run")
async def agent_auto_run(initial_build: bool = False):
    """使用Agent运行自动投资流程"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        # 检查Agent是否可用
        if not hasattr(system, 'llm_agent') or system.llm_agent is None:
            return {
                "success": False,
                "error": "LLM Agent未初始化，请在系统配置中启用"
            }

        if not system.llm_agent.is_available():
            return {
                "success": False,
                "error": "LLM Agent不可用（请检查配置和API密钥）"
            }

        # 运行自动投资流程（强制使用Agent）
        report = system.run_auto_investment(initial_build=initial_build, use_agent=True)

        return {
            "success": True,
            "message": "Agent自动投资流程完成",
            "positions_count": len(system.positions),
            "cash": system.cash,
            "total_equity": system.get_total_equity(),
            "report": report
        }
    except Exception as e:
        logger.error(f"Agent自动运行失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/agent/skills")
async def get_agent_skills():
    """获取Agent可用Skills"""
    try:
        from app.llm_agent import TradingSkillRegistry
        skills = TradingSkillRegistry.get_skills_description()
        return {
            "success": True,
            "skills": skills
        }
    except Exception as e:
        logger.error(f"获取Skills失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/agent/workflow")
async def get_agent_workflow():
    """获取投资决策工作流描述"""
    try:
        from app.llm_agent import InvestmentWorkflowSkills
        workflow = InvestmentWorkflowSkills.get_workflow_description()
        return {
            "success": True,
            "workflow": workflow
        }
    except Exception as e:
        logger.error(f"获取工作流失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/agent/workflow/skills/{phase}")
async def get_workflow_skills_by_phase(phase: str):
    """获取指定阶段的Skills"""
    try:
        from app.llm_agent import InvestmentWorkflowSkills, WorkflowPhase

        phase_map = {
            "explore": WorkflowPhase.EXPLORE,
            "decide": WorkflowPhase.DECIDE,
            "evaluate": WorkflowPhase.EVALUATE
        }

        if phase not in phase_map:
            return {"success": False, "error": f"无效的阶段: {phase}. 可选: explore, decide, evaluate"}

        skills = InvestmentWorkflowSkills.get_skills_by_phase(phase_map[phase])
        return {
            "success": True,
            "phase": phase,
            "skills": {name: skill.to_dict() for name, skill in skills.items()}
        }
    except Exception as e:
        logger.error(f"获取阶段Skills失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/agent/workflow/run-cycle")
async def run_workflow_cycle():
    """运行完整的探索-决策-评估循环"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        from app.llm_agent import WorkflowExecutor
        executor = WorkflowExecutor(system)
        result = executor.run_full_cycle()

        return {
            "success": True,
            "cycle_result": result
        }
    except Exception as e:
        logger.error(f"运行工作流循环失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/agent/history")
async def get_agent_history(limit: int = 10):
    """获取Agent决策历史"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        if not hasattr(system, 'llm_agent') or system.llm_agent is None:
            return {
                "success": True,
                "history": [],
                "message": "LLM Agent未初始化"
            }

        history = system.llm_agent.decision_history[-limit:]
        return {
            "success": True,
            "history": history,
            "total": len(system.llm_agent.decision_history)
        }
    except Exception as e:
        logger.error(f"获取Agent历史失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/agent/token-usage")
async def get_token_usage(limit: int = 20):
    """获取Token使用统计"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        if not hasattr(system, 'llm_agent') or system.llm_agent is None:
            return {
                "success": True,
                "summary": {},
                "recent_calls": [],
                "message": "LLM Agent未初始化"
            }

        # 获取token使用摘要
        summary = system.llm_agent.token_tracker.get_summary()

        # 获取最近的API调用记录
        recent_calls = system.llm_agent.token_tracker.get_recent_calls(limit)

        return {
            "success": True,
            "summary": summary,
            "recent_calls": recent_calls
        }
    except Exception as e:
        logger.error(f"获取Token使用失败: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/agent/token-usage/clear")
async def clear_token_usage():
    """清空Token使用记录"""
    try:
        system = get_diversified_system()
        if system is None:
            return {"error": "系统未初始化"}

        if not hasattr(system, 'llm_agent') or system.llm_agent is None:
            return {
                "success": False,
                "error": "LLM Agent未初始化"
            }

        system.llm_agent.token_tracker.clear()
        return {
            "success": True,
            "message": "Token使用记录已清空"
        }
    except Exception as e:
        logger.error(f"清空Token使用失败: {e}")
        return {"success": False, "error": str(e)}


# ============ 策略 API ============

@app.post("/api/strategy/run")
async def run_strategy(strategy_name: str = "ma_cross"):
    """运行交易策略"""
    try:
        result = trading_system.run_strategy(strategy_name)
        
        return {
            "success": True,
            "strategy": strategy_name,
            "result": result
        }
    except Exception as e:
        logger.error(f"运行策略失败：{e}")
        return {
            "success": False,
            "strategy": strategy_name,
            "error": str(e)
        }


# ============ 错误处理器 ============

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理异常：{exc}")
    return {
        "error": "Internal Server Error",
        "message": str(exc)
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("启动股票交易系统 API...")
    logger.info("API 地址：http://localhost:8080")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
