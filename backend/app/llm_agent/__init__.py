"""
LLM Agent 交易决策模块

该模块提供基于LLM的智能交易决策能力，通过OpenAI API调用实现。
支持buy/sell/hold/rebalance四种Skill格式的交易决策。

使用方法:
    from app.llm_agent import LLMAgentStrategy

    agent = LLMAgentStrategy(investment_system)
    decisions = agent.make_decision()
    results = agent.execute_decisions(decisions)
"""

from app.llm_agent.agent import LLMAgentStrategy
from app.llm_agent.skill import TradingSkillRegistry, TradingSkill, SkillParameter
from app.llm_agent.context import ContextBuilder
from app.llm_agent.executor import DecisionExecutor
from app.llm_agent.config import AgentConfig

__all__ = [
    'LLMAgentStrategy',
    'TradingSkillRegistry',
    'TradingSkill',
    'SkillParameter',
    'ContextBuilder',
    'DecisionExecutor',
    'AgentConfig'
]
