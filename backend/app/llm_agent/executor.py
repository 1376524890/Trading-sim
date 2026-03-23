"""LLM Agent 决策执行模块"""
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from loguru import logger

if TYPE_CHECKING:
    from app.diversified_investment import DiversifiedInvestmentSystem, StockInfo, HoldingType, STOCK_POOL, Sector


class DecisionExecutor:
    """执行LLM生成的决策"""

    def __init__(self, system: 'DiversifiedInvestmentSystem'):
        self.system = system

    async def execute(self, decisions: List[Dict]) -> List[Dict]:
        """执行决策列表"""
        results = []
        for decision in decisions:
            result = await self._execute_single(decision)
            results.append(result)
        return results

    async def execute_sync(self, decisions: List[Dict]) -> List[Dict]:
        """同步执行决策列表"""
        results = []
        for decision in decisions:
            result = self._execute_single_sync(decision)
            results.append(result)
        return results

    async def _execute_single(self, decision: Dict) -> Dict:
        """异步执行单个决策"""
        return self._execute_single_sync(decision)

    def _execute_single_sync(self, decision: Dict) -> Dict:
        """同步执行单个决策"""
        skill = decision.get("skill")
        params = decision.get("parameters", {})
        reason = decision.get("reason", "")
        confidence = params.get("confidence", 0.5)

        if skill == "buy":
            return self._execute_buy(params, reason, confidence)
        elif skill == "sell":
            return self._execute_sell(params, reason, confidence)
        elif skill == "hold":
            return {"action": "hold", "status": "success", "reason": reason, "confidence": confidence}
        elif skill == "rebalance":
            return self._execute_rebalance(params, reason, confidence)
        else:
            return {"action": skill, "status": "error", "error": f"未知skill: {skill}"}

    def _execute_buy(self, params: Dict, reason: str, confidence: float) -> Dict:
        """执行买入"""
        symbol = params.get("symbol")
        shares = params.get("shares")
        holding_type_str = params.get("holding_type", "mid_term")

        if not symbol or not shares:
            return {"action": "buy", "status": "error", "error": "缺少symbol或shares参数"}

        # 查找股票信息
        stock_info = self._find_stock_info(symbol)
        if not stock_info:
            return {"action": "buy", "status": "error", "error": f"股票 {symbol} 不在股票池"}

        # 转换持仓类型
        try:
            from app.diversified_investment import HoldingType
            holding_type = HoldingType(holding_type_str)
        except:
            holding_type = HoldingType.MID_TERM

        # 复用系统原有买入逻辑
        try:
            success = self.system.execute_buy(
                stock=stock_info,
                shares=shares,
                holding_type=holding_type,
                strategy="llm_agent",
                notes=reason,
                bypass_cooldown=True  # LLM决策跳过冷静期
            )

            if success:
                logger.info(f"✅ LLM Agent买入成功: {symbol} {shares}股")
                return {
                    "action": "buy",
                    "status": "success",
                    "symbol": symbol,
                    "shares": shares,
                    "reason": reason,
                    "confidence": confidence
                }
            else:
                return {
                    "action": "buy",
                    "status": "failed",
                    "symbol": symbol,
                    "error": "买入被系统风控拒绝"
                }
        except Exception as e:
            logger.error(f"LLM Agent买入失败 {symbol}: {e}")
            return {"action": "buy", "status": "error", "error": str(e)}

    def _execute_sell(self, params: Dict, reason: str, confidence: float) -> Dict:
        """执行卖出"""
        symbol = params.get("symbol")
        shares = params.get("shares", 0)

        if not symbol:
            return {"action": "sell", "status": "error", "error": "缺少symbol参数"}

        if symbol not in self.system.positions:
            return {"action": "sell", "status": "error", "error": f"未持有 {symbol}"}

        # 如果shares为0或None，卖出全部
        if not shares:
            shares = self.system.positions[symbol].shares

        try:
            success = self.system.execute_sell(symbol, shares, reason)

            if success:
                logger.info(f"✅ LLM Agent卖出成功: {symbol} {shares}股")
                return {
                    "action": "sell",
                    "status": "success",
                    "symbol": symbol,
                    "shares": shares,
                    "reason": reason,
                    "confidence": confidence
                }
            else:
                return {
                    "action": "sell",
                    "status": "failed",
                    "symbol": symbol,
                    "error": "卖出失败"
                }
        except Exception as e:
            logger.error(f"LLM Agent卖出失败 {symbol}: {e}")
            return {"action": "sell", "status": "error", "error": str(e)}

    def _execute_rebalance(self, params: Dict, reason: str, confidence: float) -> Dict:
        """执行调仓"""
        adjustments = params.get("adjustments", [])

        if not adjustments:
            return {"action": "rebalance", "status": "error", "error": "缺少adjustments参数"}

        results = []
        for adj in adjustments:
            symbol = adj.get("symbol")
            target_weight = adj.get("target_weight", 0)

            if not symbol or symbol not in self.system.positions:
                continue

            # 计算当前权重和目标股数
            current_price = self.system.get_stock_price(symbol)
            total_equity = self.system.get_total_equity()

            if total_equity <= 0:
                continue

            target_value = total_equity * target_weight
            target_shares = int(target_value / current_price / 100) * 100

            current_shares = self.system.positions[symbol].shares
            diff = target_shares - current_shares

            if diff > 0:
                # 需要买入
                result = self._execute_buy({
                    "symbol": symbol,
                    "shares": diff,
                    "confidence": confidence
                }, f"调仓: {reason}", confidence)
                results.append(result)
            elif diff < 0:
                # 需要卖出
                result = self._execute_sell({
                    "symbol": symbol,
                    "shares": abs(diff)
                }, f"调仓: {reason}", confidence)
                results.append(result)

        return {
            "action": "rebalance",
            "status": "success",
            "adjustments": len(results),
            "results": results,
            "reason": reason,
            "confidence": confidence
        }

    def _find_stock_info(self, symbol: str) -> Optional['StockInfo']:
        """查找股票信息"""
        try:
            from app.diversified_investment import STOCK_POOL

            for sector, stocks in STOCK_POOL.items():
                for stock in stocks:
                    if stock.symbol == symbol:
                        return stock
            return None
        except Exception as e:
            logger.error(f"查找股票信息失败 {symbol}: {e}")
            return None
