"""
LLM Agent Skill 定义模块
定义交易决策可用的Skill格式和约束
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class SkillType(Enum):
    """Skill类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REBALANCE = "rebalance"


@dataclass
class SkillParameter:
    """Skill参数定义"""
    name: str
    description: str
    type: str = "string"  # string, integer, float, boolean
    required: bool = True
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingSkill:
    """交易Skill格式定义"""
    name: str
    description: str
    parameters: List[SkillParameter]
    constraints: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典格式供LLM使用"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [
                {
                    "name": p.name,
                    "description": p.description,
                    "type": p.type,
                    "required": p.required,
                    "default": p.default,
                    "constraints": p.constraints
                }
                for p in self.parameters
            ],
            "constraints": self.constraints,
            "examples": self.examples
        }


class TradingSkillRegistry:
    """Skill注册表 - 定义可用交易策略"""

    # 预定义的Skill模板
    BUY_SKILL = TradingSkill(
        name="buy",
        description="买入指定股票，增加持仓",
        parameters=[
            SkillParameter(
                name="symbol",
                description="股票代码，例如 '601398.SS'",
                type="string",
                required=True
            ),
            SkillParameter(
                name="shares",
                description="买入股数，必须是100的整数倍",
                type="integer",
                required=True,
                constraints={"min": 100, "step": 100}
            ),
            SkillParameter(
                name="holding_type",
                description="持仓类型: long_term(长线>3月), mid_term(中线1-3月), short_term(短线<1月)",
                type="string",
                required=False,
                default="mid_term"
            ),
            SkillParameter(
                name="confidence",
                description="决策置信度 0.0-1.0",
                type="float",
                required=True,
                constraints={"min": 0.0, "max": 1.0}
            )
        ],
        constraints={
            "max_position_per_stock": 0.15,  # 最大单股仓位15%
            "max_sector_exposure": 0.30,     # 最大板块暴露30%
            "min_cash_reserve": 0.15,        # 最低现金储备15%
            "max_holdings": 10               # 最大持仓数
        },
        examples=[
            {
                "skill": "buy",
                "parameters": {
                    "symbol": "601398.SS",
                    "shares": 1000,
                    "holding_type": "long_term",
                    "confidence": 0.85
                },
                "reason": "金融板块走强，工商银行作为蓝筹股估值合理，股息率高"
            }
        ]
    )

    SELL_SKILL = TradingSkill(
        name="sell",
        description="卖出指定股票，减少或清空持仓",
        parameters=[
            SkillParameter(
                name="symbol",
                description="股票代码",
                type="string",
                required=True
            ),
            SkillParameter(
                name="shares",
                description="卖出股数，0表示全部卖出",
                type="integer",
                required=False,
                default=0,
                constraints={"min": 0}
            ),
            SkillParameter(
                name="confidence",
                description="决策置信度 0.0-1.0",
                type="float",
                required=True,
                constraints={"min": 0.0, "max": 1.0}
            )
        ],
        constraints={
            "respect_stop_loss": True,       # 必须尊重止损
            "respect_take_profit": True,     # 必须尊重止盈
            "allow_partial_sell": True       # 允许部分卖出
        },
        examples=[
            {
                "skill": "sell",
                "parameters": {
                    "symbol": "000858.SZ",
                    "shares": 0,
                    "confidence": 0.75
                },
                "reason": "触及止盈目标，消费板块短期过热，建议获利了结"
            }
        ]
    )

    HOLD_SKILL = TradingSkill(
        name="hold",
        description="保持当前持仓不变，观望市场",
        parameters=[
            SkillParameter(
                name="confidence",
                description="观望决策置信度",
                type="float",
                required=True
            )
        ],
        constraints={},
        examples=[
            {
                "skill": "hold",
                "parameters": {
                    "confidence": 0.8
                },
                "reason": "市场方向不明，等待更明确的信号"
            }
        ]
    )

    REBALANCE_SKILL = TradingSkill(
        name="rebalance",
        description="调仓 - 调整持仓比例以优化组合",
        parameters=[
            SkillParameter(
                name="adjustments",
                description="调整列表，每个元素包含symbol和target_weight(目标权重0-1)",
                type="array",
                required=True
            ),
            SkillParameter(
                name="confidence",
                description="决策置信度",
                type="float",
                required=True
            )
        ],
        constraints={
            "max_turnover": 0.30,            # 最大换手率30%
            "max_single_adjustment": 0.15    # 单次最大调整幅度
        },
        examples=[
            {
                "skill": "rebalance",
                "parameters": {
                    "adjustments": [
                        {"symbol": "601398.SS", "target_weight": 0.10},
                        {"symbol": "600519.SS", "target_weight": 0.15}
                    ],
                    "confidence": 0.8
                },
                "reason": "金融板块配置偏低，消费板块估值合理，建议调整配比"
            }
        ]
    )

    @classmethod
    def get_all_skills(cls) -> Dict[str, TradingSkill]:
        """获取所有可用Skill"""
        return {
            "buy": cls.BUY_SKILL,
            "sell": cls.SELL_SKILL,
            "hold": cls.HOLD_SKILL,
            "rebalance": cls.REBALANCE_SKILL
        }

    @classmethod
    def get_skills_description(cls) -> Dict:
        """获取Skill描述（供LLM使用）"""
        return {
            name: skill.to_dict()
            for name, skill in cls.get_all_skills().items()
        }

    @classmethod
    def validate_decision(cls, skill_name: str, parameters: Dict) -> tuple[bool, str]:
        """验证决策参数是否符合Skill定义"""
        skills = cls.get_all_skills()
        if skill_name not in skills:
            return False, f"未知Skill: {skill_name}"

        skill = skills[skill_name]
        for param in skill.parameters:
            if param.required and param.name not in parameters:
                return False, f"缺少必需参数: {param.name}"

            if param.name in parameters:
                value = parameters[param.name]
                # 类型检查
                if param.type == "integer" and not isinstance(value, int):
                    return False, f"参数 {param.name} 必须是整数"
                if param.type == "float" and not isinstance(value, (int, float)):
                    return False, f"参数 {param.name} 必须是数字"

                # 约束检查
                if "min" in param.constraints and value < param.constraints["min"]:
                    return False, f"参数 {param.name} 最小值为 {param.constraints['min']}"
                if "max" in param.constraints and value > param.constraints["max"]:
                    return False, f"参数 {param.name} 最大值为 {param.constraints['max']}"

        return True, "验证通过"
