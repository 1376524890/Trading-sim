"""LLM Agent 主模块"""
import json
import os
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from loguru import logger

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

if TYPE_CHECKING:
    from app.diversified_investment import DiversifiedInvestmentSystem

from app.llm_agent.skill import TradingSkillRegistry
from app.llm_agent.context import ContextBuilder
from app.llm_agent.executor import DecisionExecutor
from app.llm_agent.config import AgentConfig


class LLMAgentStrategy:
    """LLM Agent策略 - 替代原有规则策略"""

    def __init__(self, system: 'DiversifiedInvestmentSystem', config: AgentConfig = None):
        self.system = system
        self.config = config or AgentConfig.from_env()
        self.skill_registry = TradingSkillRegistry()
        self.context_builder = ContextBuilder(system)
        self.executor = DecisionExecutor(system)

        # 初始化OpenAI客户端
        self.client = None
        if OpenAI and self.config.openai_api_key:
            try:
                # 支持自定义base_url（用于本地部署的LLM）
                if self.config.base_url:
                    self.client = OpenAI(
                        api_key=self.config.openai_api_key,
                        base_url=self.config.base_url
                    )
                    logger.info(f"✅ OpenAI客户端初始化成功 (base_url: {self.config.base_url})")
                else:
                    self.client = OpenAI(api_key=self.config.openai_api_key)
                    logger.info("✅ OpenAI客户端初始化成功")
            except Exception as e:
                logger.error(f"OpenAI客户端初始化失败: {e}")
        else:
            logger.warning("⚠️ OpenAI未安装或缺少API密钥")

        self.decision_history = []
        self.last_decision_time = None

    def is_available(self) -> bool:
        """检查Agent是否可用"""
        return self.client is not None and self.config.enabled

    def make_decision(self) -> List[Dict]:
        """主决策入口 - 生成交易决策（同步版本）"""
        if not self.is_available():
            logger.warning("LLM Agent不可用，跳过决策")
            return []

        try:
            # 1. 构建完整上下文
            logger.info("📊 构建决策上下文...")
            context = self.context_builder.build()

            # 2. 调用LLM生成决策
            logger.info("🤖 调用LLM生成决策...")
            response = self._call_llm(context)

            if not response:
                logger.error("LLM返回空响应")
                return []

            # 3. 解析并验证决策
            decisions = self._parse_response(response)
            validated = self._validate_decisions(decisions)

            # 4. 记录决策
            self._record_decision(context, response, validated)

            self.last_decision_time = datetime.now()

            logger.info(f"✅ LLM决策完成: {len(validated)}个有效决策")
            return validated

        except Exception as e:
            logger.error(f"LLM决策失败: {e}")
            return []

    def _call_llm(self, context: Dict) -> str:
        """调用OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI客户端未初始化")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(context)

        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """构建系统提示词 - 定义Skill格式"""
        skills_desc = self.skill_registry.get_skills_description()

        return f"""你是一个专业的股票交易决策AI。你必须严格遵守以下skill格式的交易策略。

可用Skills:
{json.dumps(skills_desc, indent=2, ensure_ascii=False)}

输出格式要求:
- 必须返回JSON对象，包含"decisions"字段（决策数组）
- 每个决策必须包含: skill名称, parameters参数对象, reason决策理由
- 参数必须符合Skill定义中的类型和约束
- confidence必须在0.0-1.0之间

示例输出:
{{
  "decisions": [
    {{
      "skill": "buy",
      "parameters": {{
        "symbol": "601398.SS",
        "shares": 1000,
        "holding_type": "long_term",
        "confidence": 0.85
      }},
      "reason": "金融板块走强，工商银行作为蓝筹股估值合理，股息率高"
    }},
    {{
      "skill": "hold",
      "parameters": {{
        "confidence": 0.7
      }},
      "reason": "市场方向不明，等待更明确信号"
    }}
  ]
}}

重要约束:
- 单只股票最大仓位: {self.system.config.max_position_per_stock:.0%}
- 单板块最大仓位: {self.system.config.max_position_per_sector:.0%}
- 最低现金储备: {self.system.config.min_cash_reserve:.0%}
- 最大持仓数: {self.system.config.max_holdings}
- 当前持仓数: {len(self.system.positions)}

你的决策应该基于提供的市场数据、持仓情况、新闻情绪等多维度信息。
优先选择符合当前投资风格的股票（蓝筹股、成长股等）。
如果市场不确定，可以选择"hold"观望。
"""

    def _build_user_prompt(self, context: Dict) -> str:
        """构建用户提示词"""
        return f"""基于以下市场数据做出交易决策:

## 投资组合概况
```json
{json.dumps(context.get('portfolio', {}), indent=2, ensure_ascii=False)}
```

## 市场分析
```json
{json.dumps(context.get('market', {}), indent=2, ensure_ascii=False)}
```

## 候选股票
```json
{json.dumps(context.get('candidates', {}), indent=2, ensure_ascii=False, default=str)}
```

## 最新新闻
```json
{json.dumps(context.get('news', []), indent=2, ensure_ascii=False)}
```

## 风控约束
```json
{json.dumps(context.get('constraints', {}), indent=2, ensure_ascii=False)}
```

## 近期交易历史
```json
{json.dumps(context.get('history', []), indent=2, ensure_ascii=False)}
```

请根据以上信息，做出交易决策。考虑以下因素:
1. 当前持仓的盈亏情况
2. 各板块配置比例
3. 市场情绪和风险评估
4. 候选股票的基本面和技术面
5. 新闻情绪影响

返回JSON格式的决策列表。"""

    def _parse_response(self, response: str) -> List[Dict]:
        """解析LLM响应"""
        try:
            data = json.loads(response)

            # 支持多种可能的格式
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "decisions" in data:
                    return data["decisions"]
                elif "actions" in data:
                    return data["actions"]
                else:
                    # 可能是单个决策
                    return [data]
            else:
                logger.error(f"无法解析LLM响应: {response[:200]}")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应: {response[:500]}")
            return []

    def _validate_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """验证并过滤决策"""
        validated = []

        for decision in decisions:
            skill_name = decision.get("skill")
            params = decision.get("parameters", {})
            confidence = params.get("confidence", 0)

            # 检查置信度
            if confidence < self.config.min_confidence_threshold:
                logger.debug(f"决策置信度{confidence}低于阈值，跳过")
                continue

            # 验证Skill格式
            is_valid, msg = self.skill_registry.validate_decision(skill_name, params)
            if not is_valid:
                logger.warning(f"决策验证失败: {msg}")
                continue

            # 额外风控检查
            if skill_name == "buy":
                if not self._check_buy_constraints(params):
                    continue
            elif skill_name == "sell":
                if not self._check_sell_constraints(params):
                    continue

            validated.append(decision)

        # 限制决策数量
        if len(validated) > self.config.max_decisions_per_run:
            validated = validated[:self.config.max_decisions_per_run]

        return validated

    def _check_buy_constraints(self, params: Dict) -> bool:
        """检查买入约束"""
        symbol = params.get("symbol")
        shares = params.get("shares", 0)

        # 检查持仓数量限制
        if len(self.system.positions) >= self.system.config.max_holdings:
            logger.warning(f"已达最大持仓数限制: {self.system.config.max_holdings}")
            return False

        # 检查是否已持有
        if symbol in self.system.positions:
            # 可以加仓，但需要检查仓位限制
            current_value = self.system.positions[symbol].shares * self.system.positions[symbol].current_price
            new_value = shares * self.system.get_stock_price(symbol)
            total_equity = self.system.get_total_equity()

            if total_equity > 0 and (current_value + new_value) / total_equity > self.system.config.max_position_per_stock:
                logger.warning(f"加仓将超过单股仓位限制")
                return False

        return True

    def _check_sell_constraints(self, params: Dict) -> bool:
        """检查卖出约束"""
        symbol = params.get("symbol")

        # 检查是否持有
        if symbol not in self.system.positions:
            logger.warning(f"未持有股票: {symbol}")
            return False

        return True

    def _record_decision(self, context: Dict, response: str, decisions: List[Dict]):
        """记录决策历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "context_summary": {
                "cash": context.get("portfolio", {}).get("cash"),
                "position_count": len(context.get("portfolio", {}).get("positions", [])),
                "total_equity": context.get("portfolio", {}).get("total_equity")
            },
            "llm_response": response,
            "validated_decisions": decisions
        }
        self.decision_history.append(record)

        # 保持历史记录在合理范围内
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]

    def execute_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """执行决策列表"""
        return self.executor.execute_sync(decisions)

    def get_status(self) -> Dict:
        """获取Agent状态"""
        return {
            "available": self.is_available(),
            "enabled": self.config.enabled,
            "model": self.config.openai_model,
            "temperature": self.config.temperature,
            "last_decision_time": self.last_decision_time.isoformat() if self.last_decision_time else None,
            "decision_history_count": len(self.decision_history),
            "config": self.config.to_dict()
        }
