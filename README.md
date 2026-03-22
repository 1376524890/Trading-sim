# Stock Investment System

A professional stock investment simulation and analysis system with intelligent portfolio management, technical analysis, and automated trading strategies.

## Features

- **Multi-strategy Investment System** - Long-term, mid-term, and short-term investment strategies
- **Real-time Portfolio Management** - Track positions, P&L, and portfolio allocation
- **Technical Analysis** - Professional K-line charts with MA, MACD, RSI indicators
- **Automated Trading** - Stop-loss, take-profit, and rebalancing automation
- **Multiple Data Sources** - Support for 8+ data providers with automatic fallback
- **Modern Web Interface** - Vue 3 + TypeScript + Tailwind CSS frontend

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