#!/usr/bin/env python3
"""
多样化投资调度器
⚡ 定时执行投资策略和调仓 ⚡

功能:
1. 每日开盘前检查市场
2. 定时执行止损止盈检查
3. 自动调仓
4. 生成投资报告

作者: 御坂美琴
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import schedule

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


def check_positions_task():
    """检查持仓 - 止损止盈"""
    logger.info("=" * 50)
    logger.info("📊 持仓检查任务开始")
    logger.info("=" * 50)

    try:
        from diversified_investment import DiversifiedInvestmentSystem, InvestmentConfig, InvestmentStyle

        config = InvestmentConfig(
            initial_cash=100000,
            investment_style=InvestmentStyle.BALANCED,
            max_holdings=10
        )
        system = DiversifiedInvestmentSystem(config)

        # 执行止损止盈检查
        system.check_stop_loss_take_profit()

        logger.info("✅ 持仓检查完成")
    except Exception as e:
        logger.error(f"持仓检查失败: {e}")


def rebalance_task():
    """调仓任务"""
    logger.info("=" * 50)
    logger.info("🔄 调仓任务开始")
    logger.info("=" * 50)

    try:
        from diversified_investment import DiversifiedInvestmentSystem, InvestmentConfig, InvestmentStyle

        config = InvestmentConfig(
            initial_cash=100000,
            investment_style=InvestmentStyle.BALANCED,
            max_holdings=10
        )
        system = DiversifiedInvestmentSystem(config)

        # 执行调仓
        system.rebalance_portfolio()

        logger.info("✅ 调仓完成")
    except Exception as e:
        logger.error(f"调仓失败: {e}")


def daily_report_task():
    """生成日报"""
    logger.info("=" * 50)
    logger.info("📝 日报生成任务开始")
    logger.info("=" * 50)

    try:
        from diversified_investment import DiversifiedInvestmentSystem, InvestmentConfig, InvestmentStyle

        config = InvestmentConfig(
            initial_cash=100000,
            investment_style=InvestmentStyle.BALANCED,
            max_holdings=10
        )
        system = DiversifiedInvestmentSystem(config)

        # 生成报告
        report = system.generate_report()
        print(report)

        # 保存报告
        report_file = PROJECT_ROOT / "reports" / f"daily_investment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"✅ 日报已保存: {report_file}")
    except Exception as e:
        logger.error(f"日报生成失败: {e}")


def full_investment_task():
    """完整投资流程"""
    logger.info("=" * 60)
    logger.info("🚀 完整投资流程开始")
    logger.info("=" * 60)

    try:
        from diversified_investment import DiversifiedInvestmentSystem, InvestmentConfig, InvestmentStyle

        config = InvestmentConfig(
            initial_cash=100000,
            investment_style=InvestmentStyle.BALANCED,
            max_holdings=10
        )
        system = DiversifiedInvestmentSystem(config)

        # 运行完整投资流程
        system.run_auto_investment(initial_build=False)

        logger.info("✅ 完整投资流程完成")
    except Exception as e:
        logger.error(f"投资流程失败: {e}")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("📈 多样化投资调度器启动")
    logger.info("=" * 60)
    logger.info("定时任务配置:")
    logger.info("  - 每30分钟: 持仓检查 (止损止盈)")
    logger.info("  - 每2小时: 调仓检查")
    logger.info("  - 每日 12:30: 生成日报")
    logger.info("  - 每日 15:30: 完整投资流程")
    logger.info("  - 每日 20:00: 晚间调仓")
    logger.info("=" * 60)

    # 配置定时任务
    schedule.every(30).minutes.do(check_positions_task)
    schedule.every(2).hours.do(rebalance_task)
    schedule.every().day.at("12:30").do(daily_report_task)
    schedule.every().day.at("15:30").do(full_investment_task)
    schedule.every().day.at("20:00").do(rebalance_task)

    # 启动时运行一次
    logger.info("执行启动检查...")
    check_positions_task()

    # 运行调度循环
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


if __name__ == "__main__":
    main()