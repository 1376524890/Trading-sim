#!/usr/bin/env python3
"""
市场综合分析器
⚡ 由御坂网络第一代打造 ⚡

功能:
1. 多股票技术分析
2. 板块轮动检测
3. 市场情绪分析
4. 资金流向追踪
5. 风险评估预警
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger


class MarketAnalyzer:
    """市场综合分析器"""

    # 主要A股代码
    MARKET_LEADERS = {
        '金融': ['601398.SS', '600036.SS', '601318.SS'],  # 工商银行、招商银行、中国平安
        '消费': ['600519.SS', '000858.SZ', '000333.SZ'],  # 贵州茅台、五粮液、美的集团
        '科技': ['300750.SZ', '002594.SZ', '600276.SS'],  # 宁德时代、比亚迪、恒瑞医药
        '地产': ['000002.SZ', '600048.SH'],  # 万科A、保利发展
    }

    # 指数代码
    INDICES = {
        '上证指数': '000001.SH',
        '深证成指': '399001.SZ',
        '创业板指': '399006.SZ',
        '沪深300': '000300.SH'
    }

    def __init__(self):
        """初始化"""
        self.project_root = PROJECT_ROOT
        self.analysis_result = {}
        logger.info("市场综合分析器初始化完成")

    def analyze_technical(self, symbol: str) -> dict:
        """技术分析"""
        try:
            from data_fetcher_enhanced import EnhancedDataFetcher
            from technical_analysis import TechnicalAnalysis

            fetcher = EnhancedDataFetcher()
            analyzer = TechnicalAnalysis()

            df = fetcher.fetch_stock_data(
                symbol,
                start_date=(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )

            if df.empty:
                return {}

            df = analyzer.calculate_all_indicators(df)
            latest = df.iloc[-1]

            result = {
                'symbol': symbol,
                'close': latest.get('close', 0),
                'ma_5': latest.get('ma_5', 0),
                'ma_20': latest.get('ma_20', 0),
                'rsi_14': latest.get('rsi_14', 50),
                'trend': 'up' if latest.get('ma_5', 0) > latest.get('ma_20', 0) else 'down',
                'rsi_status': 'oversold' if latest.get('rsi_14', 50) < 30 else 'overbought' if latest.get('rsi_14', 50) > 70 else 'neutral'
            }

            fetcher.close()
            return result

        except Exception as e:
            logger.error(f"技术分析失败 {symbol}: {e}")
            return {}

    def analyze_sector_rotation(self) -> dict:
        """板块轮动分析"""
        logger.info("分析板块轮动...")

        sector_analysis = {}

        for sector, symbols in self.MARKET_LEADERS.items():
            sector_results = []
            for symbol in symbols:
                result = self.analyze_technical(symbol)
                if result:
                    sector_results.append(result)

            if sector_results:
                avg_trend = sum(1 for r in sector_results if r.get('trend') == 'up') / len(sector_results)
                avg_rsi = sum(r.get('rsi_14', 50) for r in sector_results) / len(sector_results)

                sector_analysis[sector] = {
                    'avg_trend': 'up' if avg_trend > 0.5 else 'down',
                    'avg_rsi': avg_rsi,
                    'strength': avg_trend,
                    'recommendation': self._get_sector_recommendation(avg_trend, avg_rsi)
                }

                logger.info(f"  {sector}: {'强势' if avg_trend > 0.5 else '弱势'} (RSI: {avg_rsi:.1f})")

        return sector_analysis

    def _get_sector_recommendation(self, trend: float, rsi: float) -> str:
        """获取板块建议"""
        if trend > 0.6 and rsi < 70:
            return '重点关注'
        elif trend > 0.5:
            return '适度配置'
        elif trend < 0.4 and rsi > 30:
            return '暂时回避'
        else:
            return '观望'

    def analyze_market_sentiment(self) -> dict:
        """市场情绪分析"""
        logger.info("分析市场情绪...")

        try:
            from news_scraper import NewsScraper

            scraper = NewsScraper()
            news = scraper.fetch_latest_news(limit=20)

            if not news:
                return {'sentiment': 'neutral', 'score': 50, 'news_count': 0}

            positive = sum(1 for n in news if n.get('sentiment') == 'positive')
            negative = sum(1 for n in news if n.get('sentiment') == 'negative')
            total = len(news)

            sentiment_score = 50 + (positive - negative) * 5

            sentiment = 'bullish' if sentiment_score > 60 else 'bearish' if sentiment_score < 40 else 'neutral'

            result = {
                'sentiment': sentiment,
                'score': min(100, max(0, sentiment_score)),
                'positive_news': positive,
                'negative_news': negative,
                'news_count': total
            }

            logger.info(f"  市场情绪: {sentiment} (得分: {sentiment_score})")

            return result

        except Exception as e:
            logger.error(f"情绪分析失败: {e}")
            return {'sentiment': 'neutral', 'score': 50, 'news_count': 0}

    def assess_risk(self, portfolio: dict = None) -> dict:
        """风险评估"""
        logger.info("评估市场风险...")

        # 分析板块轮动
        sectors = self.analyze_sector_rotation()

        # 统计强势板块
        strong_sectors = sum(1 for s in sectors.values() if s.get('avg_trend') == 'up')
        total_sectors = len(sectors)

        market_strength = strong_sectors / total_sectors if total_sectors > 0 else 0.5

        # 风险等级
        if market_strength > 0.7:
            risk_level = 'low'
            risk_score = 30
        elif market_strength > 0.5:
            risk_level = 'medium'
            risk_score = 50
        elif market_strength > 0.3:
            risk_level = 'medium_high'
            risk_score = 70
        else:
            risk_level = 'high'
            risk_score = 85

        result = {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'market_strength': market_strength,
            'strong_sectors': strong_sectors,
            'total_sectors': total_sectors,
            'position_advice': self._get_position_advice(risk_level)
        }

        logger.info(f"  风险等级: {risk_level} (得分: {risk_score})")

        return result

    def _get_position_advice(self, risk_level: str) -> str:
        """获取仓位建议"""
        advice = {
            'low': '建议仓位: 70-80%，可积极布局',
            'medium': '建议仓位: 50-60%，均衡配置',
            'medium_high': '建议仓位: 30-40%，谨慎参与',
            'high': '建议仓位: 10-20%，以防御为主'
        }
        return advice.get(risk_level, '建议仓位: 50%')

    def run_full_analysis(self) -> dict:
        """运行完整分析"""
        logger.info("=" * 50)
        logger.info("市场综合分析开始")
        logger.info("=" * 50)

        self.analysis_result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sector_analysis': self.analyze_sector_rotation(),
            'market_sentiment': self.analyze_market_sentiment(),
            'risk_assessment': self.assess_risk()
        }

        # 保存分析结果
        result_file = self.project_root / "reports" / "market_analysis.json"
        result_file.parent.mkdir(exist_ok=True)
        with open(result_file, 'w') as f:
            json.dump(self.analysis_result, f, indent=2, ensure_ascii=False, default=str)

        logger.info("\n" + "=" * 50)
        logger.info("市场分析完成")
        logger.info("=" * 50)

        return self.analysis_result


def main():
    """主函数"""
    analyzer = MarketAnalyzer()
    result = analyzer.run_full_analysis()

    print("\n【市场分析摘要】")
    print(f"  时间: {result['timestamp']}")

    risk = result.get('risk_assessment', {})
    print(f"  风险等级: {risk.get('risk_level', 'N/A')}")
    print(f"  {risk.get('position_advice', '')}")

    sentiment = result.get('market_sentiment', {})
    print(f"  市场情绪: {sentiment.get('sentiment', 'N/A')} ({sentiment.get('score', 0)}分)")


if __name__ == "__main__":
    main()