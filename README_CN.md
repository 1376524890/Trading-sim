# 股票投资模拟系统

一个专业的股票投资模拟与分析系统，具备智能投资组合管理、技术分析和自动化交易策略功能。

> 在线演示: [stock.plk161211.top](https://stock.plk161211.top)

## 功能特性

- **多策略投资系统** - 支持长线、中线、短线三种投资策略
- **实时投资组合管理** - 追踪持仓、盈亏、资产配置
- **技术分析** - 专业K线图表，支持MA、MACD、RSI指标
- **自动化交易** - 止损、止盈、自动调仓
- **LLM Agent智能决策** - 基于大语言模型的智能投资决策
- **多数据源支持** - 支持8+数据源自动切换
- **策略回测** - 历史数据回测验证策略效果
- **现代Web界面** - Vue 3 + TypeScript + Tailwind CSS

## 技术栈

### 后端
- Python 3.10+
- FastAPI
- Pandas / NumPy
- Loguru
- OpenAI API (LLM Agent)

### 前端
- Vue 3 + TypeScript
- Tailwind CSS
- Lightweight Charts (TradingView)
- Pinia 状态管理
- Vue Router

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- npm / pnpm

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 Windows: .\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动API服务
python app/api_server.py
```

后端API运行在 `http://localhost:8080`

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

前端运行在 `http://localhost:3000`

### 一键启动脚本

```bash
./start.sh [命令]

可用命令:
  setup           - 完整环境设置（检查 + 安装所有依赖）
  backend         - 启动后端 API 服务
  frontend        - 启动前端开发服务器
  all             - 启动全部服务
  restart         - 重启所有服务
  stop            - 停止所有服务
  status          - 查看服务状态
```

## 项目结构

```
Trading-sim/
├── backend/
│   ├── app/
│   │   ├── api_server.py           # FastAPI 应用入口
│   │   ├── diversified_investment.py  # 多样化投资系统核心
│   │   ├── market_analyzer.py      # 市场分析模块
│   │   ├── simulated_trading.py    # 模拟交易系统
│   │   ├── investment_scheduler.py # 投资调度器
│   │   ├── llm_agent/              # LLM Agent 智能决策模块
│   │   │   ├── agent.py            # Agent主模块
│   │   │   ├── config.py           # 配置管理
│   │   │   ├── context.py          # 上下文构建
│   │   │   ├── executor.py         # 决策执行器
│   │   │   └── skill.py            # 技能注册
│   │   └── services/
│   │       ├── data_fetcher_enhanced.py  # 多源数据获取
│   │       ├── portfolio_manager.py      # 投资组合管理
│   │       ├── performance_tracker.py    # 绩效追踪
│   │       └── news_scraper.py           # 新闻抓取
│   ├── data/                       # 数据缓存目录
│   ├── logs/                       # 日志文件
│   ├── portfolio/                  # 投资组合状态持久化
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/                  # 页面组件
│   │   │   ├── Overview.vue        # 总览页面
│   │   │   ├── Portfolio.vue       # 投资组合
│   │   │   ├── Charts.vue          # K线图表
│   │   │   ├── Analysis.vue        # 分析页面
│   │   │   ├── Backtest.vue        # 策略回测
│   │   │   ├── News.vue            # 新闻资讯
│   │   │   ├── Transactions.vue    # 交易记录
│   │   │   └── Agent.vue           # LLM Agent管理
│   │   ├── stores/                 # Pinia 状态管理
│   │   ├── router/                 # Vue Router 路由
│   │   └── style.css
│   ├── package.json
│   └── vite.config.ts
├── backtests/                      # 回测模块
│   ├── backtest_main.py
│   ├── backtest_config.json
│   └── results/                    # 回测结果
├── docs/                           # 文档
├── scripts/                        # 工具脚本
├── start.sh                        # 启动脚本
└── README.md
```

## API 接口

### 投资组合 API

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/diversified/summary` | GET | 投资组合摘要 |
| `/api/diversified/positions` | GET | 当前持仓列表 |
| `/api/diversified/stock-pool` | GET | 股票池 |
| `/api/diversified/initial-build` | POST | 初始建仓 |
| `/api/diversified/rebalance` | POST | 组合调仓 |
| `/api/diversified/auto-run` | POST | 自动投资流程 |
| `/api/diversified/check-stop-loss` | POST | 止损止盈检查 |
| `/api/diversified/buy` | POST | 手动买入 |
| `/api/diversified/sell` | POST | 手动卖出 |

### 股票数据 API

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/stock/price/{symbol}` | GET | 获取股票价格 |
| `/api/stock/history` | GET | K线历史数据 |

### 回测 API

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/backtest/run` | POST | 运行回测 |
| `/api/backtest/results` | GET | 回测结果列表 |
| `/api/backtest/strategies` | GET | 可用策略列表 |

### LLM Agent API

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/agent/status` | GET | Agent状态 |
| `/api/agent/decision` | POST | 触发Agent决策 |
| `/api/agent/auto-run` | POST | Agent自动投资 |
| `/api/agent/history` | GET | 决策历史 |
| `/api/agent/token-usage` | GET | Token使用统计 |

## 投资策略

### 投资风格
- **保守型 (Conservative)** - 低风险，专注蓝筹股
- **均衡型 (Balanced)** - 成长与价值平衡
- **激进型 (Aggressive)** - 高风险，追求高收益

### 持仓类型
- **长线 (>3个月)** - 止损15% / 止盈50%
- **中线 (1-3个月)** - 止损10% / 止盈30%
- **短线 (<1个月)** - 止损5% / 止盈15%

### 行业配置
- 金融 (25%)、消费 (20%)、科技 (15%)
- 医疗 (15%)、能源 (10%)、公用事业 (10%)

## 技术指标

系统支持专业技术分析：

- **均线 (MA)** - MA5、MA10、MA20
- **MACD** - DIF、DEA、MACD柱状图
- **RSI (14)** - 相对强弱指标
- **成交量分析** - 成交量柱状图与价格相关性

## LLM Agent配置

系统支持通过环境变量配置LLM Agent：

```bash
# .env 文件配置
AGENT_ENABLED=true
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，用于自定义LLM服务
OPENAI_MODEL=gpt-4                          # 模型选择
```

Agent功能：
- 智能分析市场状况
- 自动生成交易决策
- Token使用追踪
- 决策历史记录

## 回测策略

系统内置多种回测策略：

1. **均线交叉策略 (ma_cross)**
   - 短期均线上穿长期均线买入
   - 短期均线下穿长期均线卖出
   - 参数：short_period, long_period

2. **买入持有策略 (buy_hold)**
   - 简单买入并持有
   - 不进行调仓操作

3. **RSI均值回归策略 (rsi_mean_reversion)**
   - RSI低于超卖阈值买入
   - RSI高于超买阈值卖出
   - 参数：rsi_period, overbought, oversold

## 配置说明

核心配置在 `diversified_investment.py`：

```python
config = InvestmentConfig(
    initial_cash=100000,        # 初始资金
    investment_style=InvestmentStyle.BALANCED,  # 投资风格
    max_holdings=10,            # 最大持仓数
    max_position_pct=0.15,      # 单只股票最大仓位
    max_sector_pct=0.30,        # 行业最大仓位
    min_cash_reserve=0.15       # 最低现金储备
)
```

## 数据源

系统支持多数据源自动切换：

1. Akshare (主要)
2. Baostock
3. Tushare
4. Yahoo Finance
5. Sina Finance
6. East Money
7. 腾讯财经
8. 网易财经

## 页面功能

| 页面 | 功能描述 |
|------|----------|
| 总览 | 投资组合概览、关键指标、风险分析 |
| 投资组合 | 持仓详情、资产配置、交易操作 |
| 图表 | K线图、技术指标、成交量分析 |
| 分析 | 绩效分析、风险评估、收益统计 |
| 回测 | 策略回测、参数配置、结果查看 |
| 新闻 | 市场新闻、情绪分析、资讯聚合 |
| 交易记录 | 历史交易、成交明细、统计分析 |
| Agent | LLM Agent状态、决策历史、Token统计 |

## 在线演示

系统已部署在线演示环境：

**访问地址**: [stock.plk161211.top](https://stock.plk161211.top)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- TradingView Lightweight Charts
- FastAPI
- Vue 3
- Akshare / Baostock 数据源

---

> 由御坂网络第一代打造