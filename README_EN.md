# Stock Investment System

A professional stock investment simulation and analysis system with intelligent portfolio management, technical analysis, and automated trading strategies.

> **Live Demo**: [stock.plk161211.top](https://stock.plk161211.top)

## Features

- **Multi-strategy Investment System** - Long-term, mid-term, and short-term investment strategies
- **Real-time Portfolio Management** - Track positions, P&L, and portfolio allocation
- **Technical Analysis** - Professional K-line charts with MA, MACD, RSI indicators
- **Automated Trading** - Stop-loss, take-profit, and rebalancing automation
- **LLM Agent Integration** - AI-powered intelligent investment decisions
- **Multiple Data Sources** - Support for 8+ data providers with automatic fallback
- **Strategy Backtesting** - Validate strategies with historical data
- **Modern Web Interface** - Vue 3 + TypeScript + Tailwind CSS frontend

## 投资决策工作流 (Investment Decision Workflow)

系统采用**探索-决策-评估**三步循环的专业投资决策流程，LLM Agent可根据市场情况自主选择合适的分析技能进行决策。

### 工作流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        投资决策三步循环                                        │
│                    Investment Decision Cycle                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────┐
    │                         🔄 循环迭代                                    │
    │                                                                      │
    │   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐│
    │   │                 │     │                 │     │                 ││
    │   │   🔍 探索阶段    │────▶│   🎯 决策阶段    │────▶│   📊 评估阶段    ││
    │   │   EXPLORE       │     │   DECIDE        │     │   EVALUATE      ││
    │   │                 │     │                 │     │                 ││
    │   └─────────────────┘     └─────────────────┘     └─────────────────┘│
    │          │                       │                       │          │
    │          ▼                       ▼                       ▼          │
    │   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐│
    │   │ • market_scan   │     │ • buy           │     │ • performance   ││
    │   │ • fundamental   │     │ • sell          │     │   _review       ││
    │   │   _analysis     │     │ • hold          │     │ • risk          ││
    │   │ • technical     │     │ • rebalance     │     │   _assessment   ││
    │   │   _analysis     │     │ • position      │     │ • portfolio     ││
    │   │ • news_sentiment│     │   _sizing       │     │   _analysis     ││
    │   │ • capital_flow  │     │                 │     │ • stop_loss     ││
    │   │ • sector        │     │                 │     │   _check        ││
    │   │   _rotation     │     │                 │     │ • take_profit   ││
    │   └─────────────────┘     └─────────────────┘     │   _check        ││
    │                                                   └─────────────────┘│
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
```

### 阶段详解

#### 🔍 探索阶段 (Explore Phase)

**目标**: 全面了解市场环境，识别投资机会与风险

| Skill | 名称 | 描述 | 输出 |
|-------|------|------|------|
| `market_scan` | 市场扫描 | 扫描市场整体行情、指数走势、涨跌分布 | 指数数据、市场宽度、热点板块 |
| `fundamental_analysis` | 基本面分析 | 分析PE/PB/ROE/营收增长等财务指标 | 估值、盈利能力、成长性 |
| `technical_analysis` | 技术面分析 | 分析均线、MACD、RSI、成交量形态 | 趋势、信号、支撑阻力 |
| `news_sentiment` | 新闻情绪分析 | 分析市场新闻情绪和关键事件 | 情绪得分、风险预警 |
| `capital_flow` | 资金流向分析 | 追踪主力资金、北向资金动向 | 净流入、板块资金流 |
| `sector_rotation` | 板块轮动分析 | 分析板块轮动和相对强弱 | 热点板块、轮动信号 |

#### 🎯 决策阶段 (Decide Phase)

**目标**: 基于探索结果做出最优交易决策

| Skill | 名称 | 描述 | 参数 |
|-------|------|------|------|
| `buy` | 买入决策 | 建立新仓位或加仓 | symbol, shares, holding_type, confidence |
| `sell` | 卖出决策 | 减仓或清仓 | symbol, shares, confidence |
| `hold` | 持有观望 | 保持当前仓位 | confidence, watch_list |
| `rebalance` | 调仓决策 | 调整持仓比例优化组合 | adjustments, confidence |
| `position_sizing` | 仓位管理 | 确定合适的仓位规模 | method, risk_tolerance |

#### 📊 评估阶段 (Evaluate Phase)

**目标**: 总结经验教训，持续改进投资策略

| Skill | 名称 | 描述 | 输出 |
|-------|------|------|------|
| `performance_review` | 绩效回顾 | 计算收益率、夏普比率、最大回撤 | 收益归因、风险调整收益 |
| `risk_assessment` | 风险评估 | 评估市场风险、集中度风险 | VaR、风险评分 |
| `portfolio_analysis` | 组合分析 | 分析资产配置、行业分布 | 分散度评分、风格暴露 |
| `stop_loss_check` | 止损检查 | 检查是否触发止损条件 | 触发持仓、建议操作 |
| `take_profit_check` | 止盈检查 | 检查是否触发止盈条件 | 触发持仓、潜在收益 |

### 循环迭代机制

每个三步循环完成后，系统会：
1. **记录决策**: 保存本轮决策过程和结果
2. **更新状态**: 更新持仓、资金、风险评估状态
3. **触发下一轮**: 根据调度器配置自动启动下一轮循环
4. **持续优化**: 基于评估结果优化后续决策策略

### API 接口

```bash
# 获取工作流描述
GET /api/agent/workflow

# 获取指定阶段的Skills
GET /api/agent/workflow/skills/{phase}  # phase: explore, decide, evaluate

# 运行完整循环
POST /api/agent/workflow/run-cycle

# 获取所有Skills
GET /api/agent/skills
```

## Tech Stack

### Backend
- Python 3.10+
- FastAPI
- Pandas / NumPy
- Loguru

### Frontend
- Vue 3 + TypeScript
- Tailwind CSS
- Lightweight Charts (TradingView)
- Pinia

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- pnpm / npm

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or .\venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start API server
python app/api_server.py
```

API will be available at `http://localhost:8080`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build
```

Frontend will be available at `http://localhost:3000`

## Project Structure

```
stock-investment-system/
├── backend/
│   ├── app/
│   │   ├── api_server.py       # FastAPI application
│   │   ├── diversified_investment.py  # Investment system
│   │   ├── market_analyzer.py  # Market analysis
│   │   └── services/
│   │       ├── data_fetcher_enhanced.py  # Multi-source data
│   │       ├── portfolio_manager.py
│   │       └── performance_tracker.py
│   ├── data/                   # Data cache
│   ├── logs/                   # Log files
│   ├── portfolio/              # Portfolio state
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/              # Page components
│   │   ├── stores/             # Pinia stores
│   │   ├── router/             # Vue Router
│   │   └── style.css
│   ├── package.json
│   └── vite.config.ts
├── docs/
├── scripts/                    # Utility scripts
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/diversified/summary` | GET | Portfolio summary |
| `/api/diversified/positions` | GET | Current positions |
| `/api/diversified/initial-build` | POST | Initial portfolio build |
| `/api/diversified/rebalance` | POST | Rebalance portfolio |
| `/api/diversified/auto-run` | POST | Run automated investment |
| `/api/stock/history` | GET | Stock K-line data |

## Investment Strategies

### Investment Styles
- **Conservative** - Lower risk, focus on blue-chip stocks
- **Balanced** - Mix of growth and value stocks
- **Aggressive** - Higher risk, growth-focused

### Position Types
- **Long-term** (>3 months) - 15% stop loss / 50% take profit
- **Mid-term** (1-3 months) - 10% stop loss / 30% take profit
- **Short-term** (<1 month) - 5% stop loss / 15% take profit

### Sector Allocation
- Finance (25%), Consumer (20%), Technology (15%)
- Healthcare (15%), Energy (10%), Utilities (10%)

## Technical Indicators

The system supports professional technical analysis:

- **MA (Moving Averages)** - MA5, MA10, MA20
- **MACD** - DIF, DEA, MACD histogram
- **RSI (14)** - Relative Strength Index
- **Volume Analysis** - Volume bars with price correlation

## LLM Agent Integration

The system supports AI-powered investment decisions through LLM Agent:

```bash
# .env configuration
AGENT_ENABLED=true
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, for custom LLM services
OPENAI_MODEL=gpt-4
```

Agent Features:
- Intelligent market analysis
- Automatic trading decision generation
- Token usage tracking
- Decision history logging

## Backtesting Strategies

Built-in backtesting strategies:

1. **MA Cross Strategy** - Buy when short MA crosses above long MA
2. **Buy & Hold Strategy** - Simple buy and hold without rebalancing
3. **RSI Mean Reversion** - Trade based on RSI overbought/oversold signals

## Data Sources

The system supports multiple data sources with automatic fallback:

1. Akshare (Primary)
2. Baostock
3. Tushare
4. Yahoo Finance
5. Sina Finance
6. East Money
7. Tencent Finance
8. NetEase Finance

## Pages Overview

| Page | Description |
|------|-------------|
| Overview | Portfolio summary, key metrics, risk analysis |
| Portfolio | Position details, asset allocation, trading operations |
| Charts | K-line charts, technical indicators, volume analysis |
| Analysis | Performance metrics, risk assessment, return statistics |
| Backtest | Strategy backtesting, parameter configuration |
| News | Market news, sentiment analysis |
| Transactions | Trade history, execution details |
| Agent | LLM Agent status, decision history, token usage |

## Live Demo

The system is deployed and accessible online:

**URL**: [stock.plk161211.top](https://stock.plk161211.top)

## Configuration

Key configuration in `diversified_investment.py`:

```python
config = InvestmentConfig(
    initial_cash=100000,        # Initial capital
    investment_style=InvestmentStyle.BALANCED,
    max_holdings=10,            # Maximum positions
    max_position_pct=0.15,      # Single position limit
    max_sector_pct=0.30,        # Sector limit
    min_cash_reserve=0.15       # Cash reserve
)
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- TradingView Lightweight Charts
- FastAPI
- Vue 3