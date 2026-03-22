# API Documentation

## Base URL

```
http://localhost:8080
```

## Endpoints

### Health Check

```
GET /
GET /health
```

Response:
```json
{
  "service": "股票交易系统 API",
  "version": "1.0.1",
  "status": "running"
}
```

---

## Diversified Investment API

### Get Portfolio Summary

```
GET /api/diversified/summary
```

Response:
```json
{
  "success": true,
  "time": "2026-03-22 12:00:00",
  "total_equity": 100000.00,
  "cash": 50000.00,
  "cash_ratio": 50.0,
  "positions_count": 5,
  "total_pnl": 1000.00,
  "total_pnl_pct": 1.0,
  "sector_allocation": {
    "金融": 15000.00,
    "消费": 12000.00
  }
}
```

### Get Positions

```
GET /api/diversified/positions
```

Response:
```json
{
  "success": true,
  "positions": [
    {
      "symbol": "600519.SS",
      "name": "贵州茅台",
      "shares": 100,
      "avg_cost": 1800.00,
      "current_price": 1850.00,
      "market_value": 185000.00,
      "pnl": 5000.00,
      "pnl_pct": 2.78,
      "holding_type": "long_term",
      "sector": "消费"
    }
  ]
}
```

### Initial Portfolio Build

```
POST /api/diversified/initial-build
```

Response:
```json
{
  "success": true,
  "message": "初始建仓完成",
  "positions_count": 5,
  "cash": 55000.00,
  "total_equity": 99800.00
}
```

### Rebalance Portfolio

```
POST /api/diversified/rebalance
```

### Run Automated Investment

```
POST /api/diversified/auto-run
```

### Check Stop Loss / Take Profit

```
POST /api/diversified/check-stop-loss
```

---

## Stock Data API

### Get Stock Price

```
GET /api/stock/price/{symbol}
```

### Get Stock History (K-Line Data)

```
GET /api/stock/history?symbol={symbol}&days={days}
```

Response:
```json
{
  "symbol": "600519.SS",
  "days": 30,
  "data": [
    {
      "date": "2026-03-01",
      "open": 1800.00,
      "high": 1820.00,
      "low": 1790.00,
      "close": 1810.00,
      "volume": 1000000
    }
  ]
}
```

---

## Error Responses

```json
{
  "success": false,
  "error": "Error message"
}
```