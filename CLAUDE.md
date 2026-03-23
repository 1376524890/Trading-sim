# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A stock investment simulation and analysis system with portfolio management, technical analysis, and automated trading strategies. The system supports multiple investment styles (Conservative/Balanced/Aggressive), position types (Long-term/Mid-term/Short-term), and sector allocation.

## Common Commands

### Backend (Python 3.10+, runs on port 8080)

```bash
cd backend
source venv/bin/activate
python app/api_server.py
```

### Frontend (Vue 3 + TypeScript, runs on port 3000)

```bash
cd frontend
npm install
npm run dev
```

### Combined Start Script

```bash
./start.sh [backend|frontend|all|setup|status]
```

- `backend` - Start only the API server
- `frontend` - Start only the frontend
- `all` - Start both backend and frontend
- `setup` - Install all dependencies
- `status` - Check running services

## Architecture

### Backend Structure

- `backend/app/api_server.py` - FastAPI application with REST endpoints
- `backend/app/diversified_investment.py` - Core investment system with portfolio management
- `backend/app/market_analyzer.py` - Market analysis and stock screening
- `backend/app/services/portfolio_manager.py` - Position tracking and portfolio operations
- `backend/app/services/data_fetcher_enhanced.py` - Multi-source stock data fetching with fallback
- `backend/app/services/performance_tracker.py` - Performance metrics calculation

### Frontend Structure

- `frontend/src/views/` - Page components (Overview, Portfolio, Charts, Analysis, Backtest, News, Transactions)
- `frontend/src/stores/stock.ts` - Pinia store for state management
- `frontend/src/router/index.ts` - Vue Router configuration
- Uses Tailwind CSS for styling and Lightweight Charts (TradingView) for K-line charts

### Key API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/diversified/summary` | Portfolio summary |
| `/api/diversified/positions` | Current positions |
| `/api/diversified/initial-build` | Initial portfolio build |
| `/api/diversified/rebalance` | Rebalance portfolio |
| `/api/diversified/auto-run` | Automated investment workflow |
| `/api/stock/history` | K-line data |
| `/api/backtest/run` | Run backtest strategies |

### Data Flow

Frontend (Vue 3) → HTTP API (port 8080) → FastAPI → Python trading logic → JSON response → Frontend updates via Pinia stores

## Configuration

Key settings in `diversified_investment.py`:

```python
config = InvestmentConfig(
    initial_cash=100000,
    investment_style=InvestmentStyle.BALANCED,
    max_holdings=10,
    max_position_pct=0.15,
    max_sector_pct=0.30,
    min_cash_reserve=0.15
)
```

## Important Notes

- The main trading system is `DiversifiedInvestmentSystem` in `diversified_investment.py`
- Portfolio state is persisted to JSON files in `backend/portfolio/`
- Stock data is cached in `backend/data/`
- Logs are stored in `backend/logs/` and root `logs/` directories