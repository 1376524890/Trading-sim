#!/usr/bin/env python3
"""
多样化投资调度器
⚡ 定时执行投资策略和调仓 ⚡

功能:
1. 每日开盘前检查市场
2. 定时执行止损止盈检查
3. 自动调仓
4. LLM Agent智能决策
5. 生成投资报告

作者: 御坂美琴
"""

import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量: {env_path}")

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from loguru import logger

# 配置日志
logger.remove()
logger.add(
    PROJECT_ROOT / "logs" / "investment_scheduler.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
logger.add(sink=sys.stderr, level="INFO")

# 检查是否启用LLM Agent
AGENT_ENABLED = os.getenv("AGENT_ENABLED", "false").lower() == "true"


def get_system(use_agent: bool = None):
    """获取投资系统实例"""
    from app.diversified_investment import DiversifiedInvestmentSystem, InvestmentConfig, InvestmentStyle

    if use_agent is None:
        use_agent = AGENT_ENABLED

    config = InvestmentConfig(
        initial_cash=100000,
        investment_style=InvestmentStyle.BALANCED,
        max_holdings=10
    )

    system = DiversifiedInvestmentSystem(config, use_llm_agent=use_agent)

    if use_agent and system.llm_agent:
        logger.info(f"🤖 LLM Agent已启用 - Model: {system.llm_agent.config.openai_model}")

    return system


def check_positions_task():
    """检查持仓 - 止损止盈"""
    logger.info("=" * 50)
    logger.info("📊 持仓检查任务开始")
    logger.info("=" * 50)

    try:
        system = get_system()

        # 执行止损止盈检查
        system.check_stop_loss_take_profit()

        # 保存状态
        system._save_state()

        logger.info("✅ 持仓检查完成")
    except Exception as e:
        logger.error(f"持仓检查失败: {e}")


def rebalance_task():
    """调仓任务"""
    logger.info("=" * 50)
    logger.info("🔄 调仓任务开始")
    logger.info("=" * 50)

    try:
        system = get_system()

        # 执行调仓
        system.rebalance_portfolio()

        # 保存状态
        system._save_state()

        logger.info("✅ 调仓完成")
    except Exception as e:
        logger.error(f"调仓失败: {e}")


def agent_decision_task():
    """LLM Agent决策任务"""
    if not AGENT_ENABLED:
        logger.debug("LLM Agent未启用，跳过决策任务")
        return

    logger.info("=" * 50)
    logger.info("🤖 LLM Agent决策任务开始")
    logger.info("=" * 50)

    try:
        system = get_system(use_agent=True)

        if not system.llm_agent or not system.llm_agent.is_available():
            logger.warning("LLM Agent不可用，跳过决策")
            return

        # 执行Agent决策
        decisions = system.llm_agent.make_decision()

        if decisions:
            logger.info(f"📊 Agent生成了 {len(decisions)} 个决策")
            results = system.llm_agent.execute_decisions(decisions)
            logger.info(f"✅ 决策执行完成: {len(results)} 个结果")
        else:
            logger.info("📊 Agent未生成决策（可能处于观望状态）")

        # 保存状态
        system._save_state()

        logger.info("✅ LLM Agent决策任务完成")
    except Exception as e:
        logger.error(f"LLM Agent决策失败: {e}")


def full_investment_task(use_agent: bool = True):
    """完整投资流程"""
    logger.info("=" * 60)
    logger.info("🚀 完整投资流程开始")
    logger.info("=" * 60)

    try:
        system = get_system(use_agent=use_agent and AGENT_ENABLED)

        # 运行完整投资流程
        report = system.run_auto_investment(initial_build=False, use_agent=use_agent and AGENT_ENABLED)

        # 保存状态
        system._save_state()

        logger.info("✅ 完整投资流程完成")
    except Exception as e:
        logger.error(f"投资流程失败: {e}")


def daily_report_task():
    """生成日报"""
    logger.info("=" * 50)
    logger.info("📝 日报生成任务开始")
    logger.info("=" * 50)

    try:
        system = get_system()

        # 生成报告
        report = system.generate_report()
        print(report)

        # 保存报告
        report_dir = PROJECT_ROOT / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"daily_investment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"✅ 日报已保存: {report_file}")
    except Exception as e:
        logger.error(f"日报生成失败: {e}")


def run_with_schedule():
    """使用定时调度运行"""
    import schedule

    logger.info("=" * 60)
    logger.info("📈 多样化投资调度器启动")
    logger.info("=" * 60)
    logger.info(f"LLM Agent: {'已启用' if AGENT_ENABLED else '未启用'}")
    logger.info("")
    logger.info("定时任务配置:")
    logger.info("  - 每30分钟: 持仓检查 (止损止盈)")
    logger.info("  - 每1小时: LLM Agent决策")
    logger.info("  - 每2小时: 调仓检查")
    logger.info("  - 每日 12:30: 生成日报")
    logger.info("  - 每日 15:30: 完整投资流程")
    logger.info("  - 每日 20:00: 晚间调仓")
    logger.info("=" * 60)

    # 配置定时任务
    schedule.every(30).minutes.do(check_positions_task)

    if AGENT_ENABLED:
        schedule.every(1).hours.do(agent_decision_task)

    schedule.every(2).hours.do(rebalance_task)
    schedule.every().day.at("12:30").do(daily_report_task)
    schedule.every().day.at("15:30").do(lambda: full_investment_task(use_agent=True))
    schedule.every().day.at("20:00").do(rebalance_task)

    # 启动时运行一次
    logger.info("执行启动检查...")
    check_positions_task()
    if AGENT_ENABLED:
        agent_decision_task()

    # 运行调度循环
    logger.info("进入调度循环...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("调度器停止")
            break
        except Exception as e:
            logger.error(f"调度错误: {e}")
            time.sleep(60)


def run_once(task: str):
    """运行单次任务"""
    tasks = {
        'check': check_positions_task,
        'rebalance': rebalance_task,
        'agent': agent_decision_task,
        'report': daily_report_task,
        'full': lambda: full_investment_task(use_agent=True),
    }

    if task not in tasks:
        logger.error(f"未知任务: {task}")
        logger.info(f"可用任务: {list(tasks.keys())}")
        return

    logger.info(f"执行单次任务: {task}")
    tasks[task]()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多样化投资调度器")
    parser.add_argument('--task', '-t', type=str, default=None,
                        help='运行单次任务 (check/rebalance/agent/report/full)')
    parser.add_argument('--no-agent', action='store_true',
                        help='禁用LLM Agent')

    args = parser.parse_args()

    # 如果指定了禁用Agent
    global AGENT_ENABLED
    if args.no_agent:
        AGENT_ENABLED = False

    if args.task:
        run_once(args.task)
    else:
        run_with_schedule()


if __name__ == "__main__":
    main()