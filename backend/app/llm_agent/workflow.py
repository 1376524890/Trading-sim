"""
投资决策工作流模块
定义探索-决策-评估三步循环的投资决策流程

工作流程:
1. 探索阶段 (Explore) - 信息收集与市场分析
2. 决策阶段 (Decide) - 交易决策与执行
3. 评估阶段 (Evaluate) - 结果评估与策略优化
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from datetime import datetime
from loguru import logger


class WorkflowPhase(Enum):
    """工作流阶段"""
    EXPLORE = "explore"      # 探索阶段
    DECIDE = "decide"        # 决策阶段
    EVALUATE = "evaluate"    # 评估阶段


class SkillCategory(Enum):
    """Skill分类"""
    EXPLORATION = "exploration"       # 探索类
    DECISION = "decision"             # 决策类
    EVALUATION = "evaluation"         # 评估类
    RISK_MANAGEMENT = "risk_management"  # 风险管理类


@dataclass
class SkillParameter:
    """Skill参数定义"""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestmentSkill:
    """投资分析Skill"""
    name: str
    display_name: str
    description: str
    category: SkillCategory
    phase: WorkflowPhase
    parameters: List[SkillParameter]
    output_fields: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, 10最高
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他skill
    examples: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "phase": self.phase.value,
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
            "output_fields": self.output_fields,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "examples": self.examples
        }


class InvestmentWorkflowSkills:
    """投资工作流Skill注册表"""

    # ============ 探索阶段 Skills ============

    MARKET_SCAN = InvestmentSkill(
        name="market_scan",
        display_name="市场扫描",
        description="扫描市场整体行情，获取指数走势、成交量、涨跌分布等宏观数据",
        category=SkillCategory.EXPLORATION,
        phase=WorkflowPhase.EXPLORE,
        parameters=[
            SkillParameter(
                name="scan_type",
                description="扫描类型: full(全市场), index(指数), sector(板块)",
                type="string",
                required=False,
                default="full",
                constraints={"options": ["full", "index", "sector"]}
            ),
            SkillParameter(
                name="timeframe",
                description="时间范围: 1d(今日), 5d(近5日), 20d(近20日)",
                type="string",
                required=False,
                default="1d"
            )
        ],
        output_fields=["index_data", "market_breadth", "volume_analysis", "hot_sectors", "cold_sectors"],
        priority=9,
        examples=[
            {
                "skill": "market_scan",
                "parameters": {"scan_type": "full", "timeframe": "1d"},
                "expected_output": {
                    "index_data": {"sh000001": {"close": 3050, "change_pct": 0.5}},
                    "market_breadth": {"up_count": 2500, "down_count": 1800}
                }
            }
        ]
    )

    FUNDAMENTAL_ANALYSIS = InvestmentSkill(
        name="fundamental_analysis",
        display_name="基本面分析",
        description="分析股票基本面指标，包括PE/PB/ROE/营收增长/利润率等财务指标",
        category=SkillCategory.EXPLORATION,
        phase=WorkflowPhase.EXPLORE,
        parameters=[
            SkillParameter(
                name="symbol",
                description="股票代码，如 '600519.SS'",
                type="string",
                required=True
            ),
            SkillParameter(
                name="metrics",
                description="分析指标列表",
                type="array",
                required=False,
                default=["pe", "pb", "roe", "revenue_growth", "profit_margin"]
            ),
            SkillParameter(
                name="compare_peers",
                description="是否对比同行业公司",
                type="boolean",
                required=False,
                default=True
            )
        ],
        output_fields=["valuation", "profitability", "growth", "financial_health", "peer_comparison"],
        priority=8,
        dependencies=["market_scan"],
        examples=[
            {
                "skill": "fundamental_analysis",
                "parameters": {
                    "symbol": "600519.SS",
                    "metrics": ["pe", "pb", "roe"],
                    "compare_peers": True
                },
                "expected_output": {
                    "valuation": {"pe": 25.5, "pb": 8.2, "pe_percentile": 60},
                    "profitability": {"roe": 0.28, "profit_margin": 0.52}
                }
            }
        ]
    )

    TECHNICAL_ANALYSIS = InvestmentSkill(
        name="technical_analysis",
        display_name="技术面分析",
        description="分析股票技术指标，包括均线系统、MACD、RSI、成交量形态等",
        category=SkillCategory.EXPLORATION,
        phase=WorkflowPhase.EXPLORE,
        parameters=[
            SkillParameter(
                name="symbol",
                description="股票代码",
                type="string",
                required=True
            ),
            SkillParameter(
                name="indicators",
                description="技术指标列表",
                type="array",
                required=False,
                default=["ma", "macd", "rsi", "volume", "bollinger"]
            ),
            SkillParameter(
                name="period",
                description="分析周期(天)",
                type="integer",
                required=False,
                default=60
            )
        ],
        output_fields=["trend", "signals", "support_resistance", "volume_pattern", "momentum"],
        priority=8,
        dependencies=["market_scan"],
        examples=[
            {
                "skill": "technical_analysis",
                "parameters": {"symbol": "601398.SS", "indicators": ["ma", "macd", "rsi"]},
                "expected_output": {
                    "trend": "upward",
                    "signals": [{"type": "golden_cross", "indicator": "ma"}],
                    "momentum": {"rsi": 55, "macd": "positive"}
                }
            }
        ]
    )

    NEWS_SENTIMENT = InvestmentSkill(
        name="news_sentiment",
        display_name="新闻情绪分析",
        description="分析市场新闻和公告，提取情绪倾向和关键事件",
        category=SkillCategory.EXPLORATION,
        phase=WorkflowPhase.EXPLORE,
        parameters=[
            SkillParameter(
                name="scope",
                description="分析范围: market(全市场), sector(板块), stock(个股)",
                type="string",
                required=False,
                default="market"
            ),
            SkillParameter(
                name="symbol",
                description="股票代码(scope=stock时必需)",
                type="string",
                required=False
            ),
            SkillParameter(
                name="days",
                description="分析最近N天新闻",
                type="integer",
                required=False,
                default=7
            )
        ],
        output_fields=["sentiment_score", "key_events", "risk_alerts", "opportunities"],
        priority=7,
        examples=[
            {
                "skill": "news_sentiment",
                "parameters": {"scope": "market", "days": 3},
                "expected_output": {
                    "sentiment_score": 0.65,
                    "key_events": ["央行降准", "财报季开启"],
                    "risk_alerts": []
                }
            }
        ]
    )

    CAPITAL_FLOW = InvestmentSkill(
        name="capital_flow",
        display_name="资金流向分析",
        description="追踪主力资金、北向资金、机构持仓变化等资金动向",
        category=SkillCategory.EXPLORATION,
        phase=WorkflowPhase.EXPLORE,
        parameters=[
            SkillParameter(
                name="flow_type",
                description="资金类型: main(主力), north(北向), institution(机构)",
                type="string",
                required=False,
                default="main"
            ),
            SkillParameter(
                name="symbol",
                description="股票代码(可选，不填则分析全市场)",
                type="string",
                required=False
            ),
            SkillParameter(
                name="days",
                description="分析天数",
                type="integer",
                required=False,
                default=5
            )
        ],
        output_fields=["net_inflow", "top_inflows", "top_outflows", "sector_flow"],
        priority=8,
        examples=[
            {
                "skill": "capital_flow",
                "parameters": {"flow_type": "north", "days": 5},
                "expected_output": {
                    "net_inflow": 150.5,
                    "top_inflows": [{"symbol": "600519.SS", "amount": 25.3}],
                    "sector_flow": {"finance": 45.2, "tech": -12.5}
                }
            }
        ]
    )

    SECTOR_ROTATION = InvestmentSkill(
        name="sector_rotation",
        display_name="板块轮动分析",
        description="分析板块资金轮动和相对强弱，识别热点切换",
        category=SkillCategory.EXPLORATION,
        phase=WorkflowPhase.EXPLORE,
        parameters=[
            SkillParameter(
                name="method",
                description="分析方法: rsi(相对强弱), momentum(动量), flow(资金流)",
                type="string",
                required=False,
                default="rsi"
            ),
            SkillParameter(
                name="period",
                description="分析周期(天)",
                type="integer",
                required=False,
                default=20
            )
        ],
        output_fields=["hot_sectors", "cold_sectors", "rotation_signal", "leading_stocks"],
        priority=7,
        dependencies=["market_scan"],
        examples=[
            {
                "skill": "sector_rotation",
                "parameters": {"method": "momentum", "period": 10},
                "expected_output": {
                    "hot_sectors": [{"name": "AI", "score": 85}],
                    "cold_sectors": [{"name": "房地产", "score": 25}],
                    "rotation_signal": "科技板块走强"
                }
            }
        ]
    )

    # ============ 决策阶段 Skills ============

    BUY_DECISION = InvestmentSkill(
        name="buy",
        display_name="买入决策",
        description="执行买入操作，建立新仓位或加仓",
        category=SkillCategory.DECISION,
        phase=WorkflowPhase.DECIDE,
        parameters=[
            SkillParameter(
                name="symbol",
                description="股票代码",
                type="string",
                required=True
            ),
            SkillParameter(
                name="shares",
                description="买入股数(100的整数倍)",
                type="integer",
                required=True,
                constraints={"min": 100, "step": 100}
            ),
            SkillParameter(
                name="holding_type",
                description="持仓类型: long_term(长线>3月), mid_term(中线1-3月), short_term(短线<1月)",
                type="string",
                required=False,
                default="mid_term",
                constraints={"options": ["long_term", "mid_term", "short_term"]}
            ),
            SkillParameter(
                name="confidence",
                description="决策置信度 0.0-1.0",
                type="float",
                required=True,
                constraints={"min": 0.0, "max": 1.0}
            ),
            SkillParameter(
                name="reason",
                description="买入理由",
                type="string",
                required=False
            )
        ],
        output_fields=["execution_status", "filled_price", "filled_shares", "commission"],
        priority=9,
        dependencies=["fundamental_analysis", "technical_analysis"],
        examples=[
            {
                "skill": "buy",
                "parameters": {
                    "symbol": "601398.SS",
                    "shares": 1000,
                    "holding_type": "long_term",
                    "confidence": 0.85,
                    "reason": "金融板块走强，估值合理，股息率高"
                }
            }
        ]
    )

    SELL_DECISION = InvestmentSkill(
        name="sell",
        display_name="卖出决策",
        description="执行卖出操作，减仓或清仓",
        category=SkillCategory.DECISION,
        phase=WorkflowPhase.DECIDE,
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
                description="决策置信度",
                type="float",
                required=True,
                constraints={"min": 0.0, "max": 1.0}
            ),
            SkillParameter(
                name="reason",
                description="卖出理由",
                type="string",
                required=False
            )
        ],
        output_fields=["execution_status", "filled_price", "filled_shares", "realized_pnl"],
        priority=9,
        examples=[
            {
                "skill": "sell",
                "parameters": {
                    "symbol": "000858.SZ",
                    "shares": 0,
                    "confidence": 0.75,
                    "reason": "触及止盈目标，消费板块短期过热"
                }
            }
        ]
    )

    HOLD_DECISION = InvestmentSkill(
        name="hold",
        display_name="持有观望",
        description="保持当前持仓不变，观望市场",
        category=SkillCategory.DECISION,
        phase=WorkflowPhase.DECIDE,
        parameters=[
            SkillParameter(
                name="confidence",
                description="观望决策置信度",
                type="float",
                required=True,
                constraints={"min": 0.0, "max": 1.0}
            ),
            SkillParameter(
                name="reason",
                description="观望理由",
                type="string",
                required=False
            ),
            SkillParameter(
                name="watch_list",
                description="关注股票列表",
                type="array",
                required=False
            )
        ],
        output_fields=["status", "watching_stocks"],
        priority=5,
        examples=[
            {
                "skill": "hold",
                "parameters": {
                    "confidence": 0.8,
                    "reason": "市场方向不明，等待更明确信号",
                    "watch_list": ["600519.SS", "601398.SS"]
                }
            }
        ]
    )

    REBALANCE_DECISION = InvestmentSkill(
        name="rebalance",
        display_name="调仓决策",
        description="调整持仓比例，优化投资组合配置",
        category=SkillCategory.DECISION,
        phase=WorkflowPhase.DECIDE,
        parameters=[
            SkillParameter(
                name="adjustments",
                description="调整列表，每个元素包含symbol和target_weight",
                type="array",
                required=True
            ),
            SkillParameter(
                name="confidence",
                description="决策置信度",
                type="float",
                required=True,
                constraints={"min": 0.0, "max": 1.0}
            ),
            SkillParameter(
                name="reason",
                description="调仓理由",
                type="string",
                required=False
            )
        ],
        output_fields=["adjustments_made", "new_allocation"],
        priority=8,
        dependencies=["portfolio_analysis", "sector_rotation"],
        examples=[
            {
                "skill": "rebalance",
                "parameters": {
                    "adjustments": [
                        {"symbol": "601398.SS", "target_weight": 0.10},
                        {"symbol": "600519.SS", "target_weight": 0.12}
                    ],
                    "confidence": 0.8,
                    "reason": "金融板块配置偏低，消费板块估值合理"
                }
            }
        ]
    )

    POSITION_SIZING = InvestmentSkill(
        name="position_sizing",
        display_name="仓位管理",
        description="根据风险承受能力和市场状况确定合适的仓位规模",
        category=SkillCategory.DECISION,
        phase=WorkflowPhase.DECIDE,
        parameters=[
            SkillParameter(
                name="method",
                description="计算方法: kelly(凯利公式), risk_parity(风险平价), equal(等权)",
                type="string",
                required=False,
                default="risk_parity",
                constraints={"options": ["kelly", "risk_parity", "equal"]}
            ),
            SkillParameter(
                name="risk_tolerance",
                description="风险承受度 0.0-1.0",
                type="float",
                required=False,
                default=0.5,
                constraints={"min": 0.0, "max": 1.0}
            ),
            SkillParameter(
                name="max_position",
                description="单股最大仓位比例",
                type="float",
                required=False,
                default=0.15
            )
        ],
        output_fields=["recommended_positions", "cash_reserve", "risk_adjusted_size"],
        priority=7,
        dependencies=["risk_assessment"],
        examples=[
            {
                "skill": "position_sizing",
                "parameters": {"method": "risk_parity", "risk_tolerance": 0.5},
                "expected_output": {
                    "recommended_positions": [{"symbol": "601398.SS", "weight": 0.12}],
                    "cash_reserve": 0.20
                }
            }
        ]
    )

    # ============ 评估阶段 Skills ============

    PERFORMANCE_REVIEW = InvestmentSkill(
        name="performance_review",
        display_name="绩效回顾",
        description="回顾投资组合表现，计算收益率、夏普比率、最大回撤等指标",
        category=SkillCategory.EVALUATION,
        phase=WorkflowPhase.EVALUATE,
        parameters=[
            SkillParameter(
                name="period",
                description="回顾周期: 1d, 1w, 1m, 3m, 1y, all",
                type="string",
                required=False,
                default="1m"
            ),
            SkillParameter(
                name="benchmark",
                description="基准指数: hs300, zz500, sz50",
                type="string",
                required=False,
                default="hs300"
            ),
            SkillParameter(
                name="include_details",
                description="是否包含详细分析",
                type="boolean",
                required=False,
                default=True
            )
        ],
        output_fields=["total_return", "annualized_return", "sharpe_ratio", "max_drawdown", "win_rate", "attribution"],
        priority=8,
        examples=[
            {
                "skill": "performance_review",
                "parameters": {"period": "1m", "benchmark": "hs300"},
                "expected_output": {
                    "total_return": 0.08,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": -0.05,
                    "win_rate": 0.65
                }
            }
        ]
    )

    RISK_ASSESSMENT = InvestmentSkill(
        name="risk_assessment",
        display_name="风险评估",
        description="评估投资组合风险敞口，包括市场风险、集中度风险、波动风险等",
        category=SkillCategory.EVALUATION,
        phase=WorkflowPhase.EVALUATE,
        parameters=[
            SkillParameter(
                name="risk_types",
                description="评估的风险类型列表",
                type="array",
                required=False,
                default=["market", "concentration", "volatility", "liquidity"]
            ),
            SkillParameter(
                name="confidence_level",
                description="置信水平(用于VaR计算)",
                type="float",
                required=False,
                default=0.95
            )
        ],
        output_fields=["risk_score", "var", "concentration_risk", "volatility_risk", "risk_alerts"],
        priority=9,
        examples=[
            {
                "skill": "risk_assessment",
                "parameters": {"risk_types": ["market", "concentration"]},
                "expected_output": {
                    "risk_score": 45,
                    "var": {"95%": -0.03},
                    "concentration_risk": {"max_single": 0.12, "top3": 0.35}
                }
            }
        ]
    )

    PORTFOLIO_ANALYSIS = InvestmentSkill(
        name="portfolio_analysis",
        display_name="组合分析",
        description="分析投资组合结构，包括资产配置、行业分布、风格暴露等",
        category=SkillCategory.EVALUATION,
        phase=WorkflowPhase.EVALUATE,
        parameters=[
            SkillParameter(
                name="analysis_type",
                description="分析类型: allocation(配置), sector(行业), style(风格), all(全部)",
                type="string",
                required=False,
                default="all"
            )
        ],
        output_fields=["asset_allocation", "sector_allocation", "style_exposure", "diversification_score"],
        priority=7,
        examples=[
            {
                "skill": "portfolio_analysis",
                "parameters": {"analysis_type": "all"},
                "expected_output": {
                    "asset_allocation": {"stock": 0.75, "cash": 0.25},
                    "sector_allocation": {"finance": 0.25, "consumer": 0.20},
                    "diversification_score": 0.72
                }
            }
        ]
    )

    STOP_LOSS_CHECK = InvestmentSkill(
        name="stop_loss_check",
        display_name="止损检查",
        description="检查持仓是否触发止损条件，生成止损建议",
        category=SkillCategory.RISK_MANAGEMENT,
        phase=WorkflowPhase.EVALUATE,
        parameters=[
            SkillParameter(
                name="symbol",
                description="股票代码(可选，不填则检查全部持仓)",
                type="string",
                required=False
            ),
            SkillParameter(
                name="stop_loss_pct",
                description="止损比例(默认使用持仓类型对应的止损线)",
                type="float",
                required=False
            )
        ],
        output_fields=["triggered_positions", "suggested_actions", "total_risk"],
        priority=10,
        examples=[
            {
                "skill": "stop_loss_check",
                "parameters": {},
                "expected_output": {
                    "triggered_positions": [{"symbol": "000333.SZ", "loss_pct": -0.08}],
                    "suggested_actions": [{"symbol": "000333.SZ", "action": "sell"}]
                }
            }
        ]
    )

    TAKE_PROFIT_CHECK = InvestmentSkill(
        name="take_profit_check",
        display_name="止盈检查",
        description="检查持仓是否触发止盈条件，生成止盈建议",
        category=SkillCategory.RISK_MANAGEMENT,
        phase=WorkflowPhase.EVALUATE,
        parameters=[
            SkillParameter(
                name="symbol",
                description="股票代码(可选)",
                type="string",
                required=False
            ),
            SkillParameter(
                name="take_profit_pct",
                description="止盈比例",
                type="float",
                required=False
            )
        ],
        output_fields=["triggered_positions", "suggested_actions", "potential_profit"],
        priority=9,
        examples=[
            {
                "skill": "take_profit_check",
                "parameters": {},
                "expected_output": {
                    "triggered_positions": [{"symbol": "600519.SS", "profit_pct": 0.35}],
                    "suggested_actions": [{"symbol": "600519.SS", "action": "consider_selling"}]
                }
            }
        ]
    )

    @classmethod
    def get_all_skills(cls) -> Dict[str, InvestmentSkill]:
        """获取所有Skill"""
        return {
            # 探索阶段
            "market_scan": cls.MARKET_SCAN,
            "fundamental_analysis": cls.FUNDAMENTAL_ANALYSIS,
            "technical_analysis": cls.TECHNICAL_ANALYSIS,
            "news_sentiment": cls.NEWS_SENTIMENT,
            "capital_flow": cls.CAPITAL_FLOW,
            "sector_rotation": cls.SECTOR_ROTATION,
            # 决策阶段
            "buy": cls.BUY_DECISION,
            "sell": cls.SELL_DECISION,
            "hold": cls.HOLD_DECISION,
            "rebalance": cls.REBALANCE_DECISION,
            "position_sizing": cls.POSITION_SIZING,
            # 评估阶段
            "performance_review": cls.PERFORMANCE_REVIEW,
            "risk_assessment": cls.RISK_ASSESSMENT,
            "portfolio_analysis": cls.PORTFOLIO_ANALYSIS,
            "stop_loss_check": cls.STOP_LOSS_CHECK,
            "take_profit_check": cls.TAKE_PROFIT_CHECK,
        }

    @classmethod
    def get_skills_by_phase(cls, phase: WorkflowPhase) -> Dict[str, InvestmentSkill]:
        """按阶段获取Skills"""
        return {
            name: skill for name, skill in cls.get_all_skills().items()
            if skill.phase == phase
        }

    @classmethod
    def get_skills_by_category(cls, category: SkillCategory) -> Dict[str, InvestmentSkill]:
        """按分类获取Skills"""
        return {
            name: skill for name, skill in cls.get_all_skills().items()
            if skill.category == category
        }

    @classmethod
    def get_workflow_description(cls) -> Dict:
        """获取工作流描述"""
        return {
            "name": "投资决策三步循环",
            "description": "探索-决策-评估的迭代投资决策流程",
            "phases": [
                {
                    "name": "explore",
                    "display_name": "探索阶段",
                    "description": "信息收集与市场分析，建立决策所需的信息基础",
                    "skills": [s.to_dict() for s in cls.get_skills_by_phase(WorkflowPhase.EXPLORE).values()],
                    "objective": "全面了解市场环境，识别投资机会与风险"
                },
                {
                    "name": "decide",
                    "display_name": "决策阶段",
                    "description": "基于探索结果做出交易决策并执行",
                    "skills": [s.to_dict() for s in cls.get_skills_by_phase(WorkflowPhase.DECIDE).values()],
                    "objective": "做出最优交易决策，执行买卖操作"
                },
                {
                    "name": "evaluate",
                    "display_name": "评估阶段",
                    "description": "评估决策效果，优化后续策略",
                    "skills": [s.to_dict() for s in cls.get_skills_by_phase(WorkflowPhase.EVALUATE).values()],
                    "objective": "总结经验教训，持续改进投资策略"
                }
            ],
            "cycle_description": "每完成一个三步循环后，根据评估结果启动下一轮探索，形成持续迭代的投资决策闭环"
        }


class WorkflowExecutor:
    """工作流执行器"""

    def __init__(self, system):
        self.system = system
        self.skill_handlers = {}
        self._register_handlers()

        # 引用DecisionExecutor用于执行交易决策
        from app.llm_agent.executor import DecisionExecutor
        self.decision_executor = DecisionExecutor(system)

    def _register_handlers(self):
        """注册Skill处理函数"""
        # 探索阶段处理函数
        self.skill_handlers["market_scan"] = self._handle_market_scan
        self.skill_handlers["fundamental_analysis"] = self._handle_fundamental
        self.skill_handlers["technical_analysis"] = self._handle_technical
        self.skill_handlers["news_sentiment"] = self._handle_news
        self.skill_handlers["capital_flow"] = self._handle_capital_flow
        self.skill_handlers["sector_rotation"] = self._handle_sector_rotation

        # 决策阶段处理函数（通过DecisionExecutor实现）
        self.skill_handlers["buy"] = self._handle_buy
        self.skill_handlers["sell"] = self._handle_sell
        self.skill_handlers["hold"] = self._handle_hold
        self.skill_handlers["rebalance"] = self._handle_rebalance
        self.skill_handlers["position_sizing"] = self._handle_position_sizing

        # 评估阶段处理函数
        self.skill_handlers["performance_review"] = self._handle_performance
        self.skill_handlers["risk_assessment"] = self._handle_risk
        self.skill_handlers["portfolio_analysis"] = self._handle_portfolio
        self.skill_handlers["stop_loss_check"] = self._handle_stop_loss
        self.skill_handlers["take_profit_check"] = self._handle_take_profit

    def execute_skill(self, skill_name: str, parameters: Dict) -> Dict:
        """执行单个Skill"""
        handler = self.skill_handlers.get(skill_name)
        if not handler:
            return {"error": f"未知的Skill: {skill_name}"}

        try:
            return handler(parameters)
        except Exception as e:
            logger.error(f"执行Skill {skill_name} 失败: {e}")
            return {"error": str(e)}

    def run_phase(self, phase: WorkflowPhase, context: Dict) -> Dict:
        """运行指定阶段"""
        skills = InvestmentWorkflowSkills.get_skills_by_phase(phase)
        results = {}

        for skill_name, skill in sorted(skills.items(), key=lambda x: x[1].priority, reverse=True):
            logger.info(f"执行 {skill.display_name}...")
            result = self.execute_skill(skill_name, context.get(skill_name, {}))
            results[skill_name] = result

        return results

    def run_full_cycle(self) -> Dict:
        """运行完整的探索-决策-评估循环"""
        cycle_result = {
            "timestamp": datetime.now().isoformat(),
            "phases": {}
        }

        # 阶段1: 探索
        logger.info("🔍 开始探索阶段...")
        context = {"portfolio": self.system.get_portfolio_analysis() if hasattr(self.system, 'get_portfolio_analysis') else {}}
        cycle_result["phases"]["explore"] = self.run_phase(WorkflowPhase.EXPLORE, context)

        # 阶段2: 决策 (由LLM Agent或规则系统决定)
        logger.info("🎯 进入决策阶段...")
        cycle_result["phases"]["decide"] = {"status": "waiting_for_agent"}

        # 阶段3: 评估
        logger.info("📊 执行评估阶段...")
        cycle_result["phases"]["evaluate"] = self.run_phase(WorkflowPhase.EVALUATE, context)

        return cycle_result

    # ============ 探索阶段处理函数 ============

    def _handle_market_scan(self, params: Dict) -> Dict:
        """处理市场扫描"""
        try:
            from app.market_analyzer import MarketAnalyzer
            analyzer = MarketAnalyzer()
            result = {
                "sector_analysis": analyzer.analyze_sector_rotation(),
                "market_sentiment": analyzer.analyze_market_sentiment(),
                "risk_assessment": analyzer.assess_risk()
            }
            return result
        except Exception as e:
            return {"error": str(e)}

    def _handle_fundamental(self, params: Dict) -> Dict:
        """处理基本面分析"""
        symbol = params.get("symbol")
        if not symbol:
            return {"error": "缺少股票代码"}

        # 简化实现 - 实际应接入财务数据API
        return {
            "symbol": symbol,
            "status": "analyzed",
            "note": "基本面分析结果"
        }

    def _handle_technical(self, params: Dict) -> Dict:
        """处理技术分析"""
        symbol = params.get("symbol")
        if not symbol:
            return {"error": "缺少股票代码"}

        try:
            from app.services.data_fetcher_enhanced import EnhancedDataFetcher
            fetcher = EnhancedDataFetcher()
            df = fetcher.fetch_stock_data(symbol, days=params.get("period", 60))
            fetcher.close()

            if df.empty:
                return {"error": "无法获取数据"}

            import numpy as np
            close = df['close'].values

            return {
                "symbol": symbol,
                "trend": "up" if close[-1] > np.mean(close[-20:]) else "down",
                "ma_5": float(np.mean(close[-5:])),
                "ma_20": float(np.mean(close[-20:])),
                "recent_change": float((close[-1] - close[-5]) / close[-5] * 100)
            }
        except Exception as e:
            return {"error": str(e)}

    def _handle_news(self, params: Dict) -> Dict:
        """处理新闻情绪分析"""
        try:
            from app.services.news_scraper import NewsScraper
            scraper = NewsScraper()
            news = scraper.fetch_latest_news(limit=params.get("limit", 10))

            positive = sum(1 for n in news if n.get("sentiment") == "positive")
            negative = sum(1 for n in news if n.get("sentiment") == "negative")

            return {
                "news_count": len(news),
                "sentiment_score": (positive - negative) / len(news) if news else 0,
                "news": news
            }
        except Exception as e:
            return {"error": str(e)}

    def _handle_capital_flow(self, params: Dict) -> Dict:
        """处理资金流向分析"""
        return {
            "status": "analyzed",
            "note": "资金流向分析结果"
        }

    def _handle_sector_rotation(self, params: Dict) -> Dict:
        """处理板块轮动分析"""
        try:
            from app.market_analyzer import MarketAnalyzer
            analyzer = MarketAnalyzer()
            return analyzer.analyze_sector_rotation()
        except Exception as e:
            return {"error": str(e)}

    # ============ 决策阶段处理函数 ============

    def _handle_buy(self, params: Dict) -> Dict:
        """处理买入决策 - 通过DecisionExecutor执行"""
        decision = {
            "skill": "buy",
            "parameters": params,
            "reason": params.get("reason", "工作流触发买入")
        }
        results = self.decision_executor.execute_sync([decision])
        return results[0] if results else {"status": "error", "error": "执行失败"}

    def _handle_sell(self, params: Dict) -> Dict:
        """处理卖出决策 - 通过DecisionExecutor执行"""
        decision = {
            "skill": "sell",
            "parameters": params,
            "reason": params.get("reason", "工作流触发卖出")
        }
        results = self.decision_executor.execute_sync([decision])
        return results[0] if results else {"status": "error", "error": "执行失败"}

    def _handle_hold(self, params: Dict) -> Dict:
        """处理持有决策"""
        return {
            "status": "holding",
            "watch_list": params.get("watch_list", []),
            "reason": params.get("reason", "观望市场")
        }

    def _handle_rebalance(self, params: Dict) -> Dict:
        """处理调仓决策 - 通过DecisionExecutor执行"""
        decision = {
            "skill": "rebalance",
            "parameters": params,
            "reason": params.get("reason", "工作流触发调仓")
        }
        results = self.decision_executor.execute_sync([decision])
        return results[0] if results else {"status": "error", "error": "执行失败"}

    def _handle_position_sizing(self, params: Dict) -> Dict:
        """处理仓位管理 - 计算建议仓位"""
        try:
            total_equity = self.system.get_total_equity() if hasattr(self.system, 'get_total_equity') else 0
            cash = self.system.cash if hasattr(self.system, 'cash') else 0

            risk_tolerance = params.get("risk_tolerance", 0.5)
            max_position = params.get("max_position", 0.15)

            # 根据风险承受度计算建议仓位
            suggested_investment = total_equity * (0.5 + risk_tolerance * 0.3)  # 50%-80%
            cash_reserve = total_equity - suggested_investment

            return {
                "method": params.get("method", "risk_parity"),
                "total_equity": total_equity,
                "available_cash": cash,
                "suggested_investment": round(suggested_investment, 2),
                "recommended_cash_reserve": round(cash_reserve / total_equity, 2) if total_equity > 0 else 0,
                "max_single_position": max_position
            }
        except Exception as e:
            return {"error": str(e)}

    # ============ 评估阶段处理函数 ============

    def _handle_performance(self, params: Dict) -> Dict:
        """处理绩效回顾"""
        if hasattr(self.system, 'get_portfolio_analysis'):
            analysis = self.system.get_portfolio_analysis()
            return {
                "total_equity": analysis.get("total_equity"),
                "pnl": analysis.get("pnl"),
                "positions_count": len(analysis.get("positions", []))
            }
        return {"status": "not_available"}

    def _handle_risk(self, params: Dict) -> Dict:
        """处理风险评估"""
        try:
            from app.market_analyzer import MarketAnalyzer
            analyzer = MarketAnalyzer()
            return analyzer.assess_risk()
        except Exception as e:
            return {"error": str(e)}

    def _handle_portfolio(self, params: Dict) -> Dict:
        """处理组合分析"""
        if hasattr(self.system, 'get_portfolio_analysis'):
            return self.system.get_portfolio_analysis()
        return {"status": "not_available"}

    def _handle_stop_loss(self, params: Dict) -> Dict:
        """处理止损检查"""
        if hasattr(self.system, 'check_stop_loss_take_profit'):
            self.system.check_stop_loss_take_profit()
            return {"status": "checked"}
        return {"status": "not_available"}

    def _handle_take_profit(self, params: Dict) -> Dict:
        """处理止盈检查"""
        if hasattr(self.system, 'check_stop_loss_take_profit'):
            self.system.check_stop_loss_take_profit()
            return {"status": "checked"}
        return {"status": "not_available"}