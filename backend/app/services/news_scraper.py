#!/usr/bin/env python3
"""
news_scraper.py - 财经新闻抓取模块

抓取多个财经新闻源，支持配置文件管理

作者：御坂美琴
创建时间：2026-03-17
更新时间：2026-03-26
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime, timedelta
import re
import time
import json
from dataclasses import dataclass, asdict
from pathlib import Path
import random


@dataclass
class NewsArticle:
    """新闻文章数据类"""
    title: str
    url: str
    source: str
    publish_time: str
    summary: str = ""
    content: str = ""
    keywords: List[str] = None
    sentiment: str = "neutral"  # positive, negative, neutral
    sentiment_score: float = 0.0
    importance: str = "medium"  # high, medium, low
    category: str = "unknown"  # policy, industry, stock, market
    stock_symbols: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.stock_symbols is None:
            self.stock_symbols = []

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class NewsSource:
    """新闻源配置"""
    name: str
    url: str
    source_type: str
    priority: int


class NewsScraper:
    """
    财经新闻爬虫类

    从多个财经新闻源抓取最新新闻，支持配置文件管理
    """

    def __init__(self, delay: float = 1.0, config_path: str = None):
        """
        初始化新闻爬虫

        Args:
            delay: 请求间隔时间 (秒)
            config_path: 配置文件路径
        """
        self.delay = delay
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }

        # 加载配置
        self.sources = self._load_config(config_path)

        logger.info(f"新闻爬虫初始化完成，已加载 {len(self.sources)} 个新闻源")

    def _load_config(self, config_path: str = None) -> List[NewsSource]:
        """加载新闻源配置"""
        sources = []

        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "news_sources.txt"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_sources()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split('|')
                    if len(parts) >= 4:
                        sources.append(NewsSource(
                            name=parts[0].strip(),
                            url=parts[1].strip(),
                            source_type=parts[2].strip(),
                            priority=int(parts[3].strip())
                        ))

            # 按优先级排序
            sources.sort(key=lambda x: x.priority)
            logger.info(f"从配置文件加载了 {len(sources)} 个新闻源")

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_sources()

        return sources

    def _get_default_sources(self) -> List[NewsSource]:
        """获取默认新闻源"""
        return [
            NewsSource("sina", "https://finance.sina.com.cn/", "main", 1),
            NewsSource("eastmoney", "https://finance.eastmoney.com/", "main", 1),
            NewsSource("tonghuashun", "https://www.10jqka.com.cn/", "main", 1),
            NewsSource("tencent", "https://news.qq.com/ch/finance", "finance", 1),
            NewsSource("netease", "https://money.163.com/", "main", 1),
            NewsSource("stcn", "https://stcn.com/", "main", 1),
            NewsSource("caixin", "https://www.caixin.com/", "main", 1),
            NewsSource("yicai", "https://www.yicai.com/", "main", 1),
        ]

    def _make_request(self, url: str, timeout: int = 10) -> Optional[str]:
        """发送 HTTP 请求"""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            time.sleep(self.delay)
            return response.text
        except Exception as e:
            logger.error(f"请求失败 {url}: {str(e)[:100]}")
            return None

    def scrape_sina(self, count: int = 10) -> List[NewsArticle]:
        """抓取新浪财经新闻"""
        logger.info("正在抓取新浪财经新闻...")
        articles = []

        urls = [
            "https://finance.sina.com.cn/stock/",
            "https://finance.sina.com.cn/7x24/",
        ]

        for url in urls:
            html = self._make_request(url)
            if not html:
                continue

            try:
                soup = BeautifulSoup(html, 'html.parser')

                # 查找新闻链接
                news_items = soup.find_all('a', href=re.compile(r'sina\.com\.cn'))

                for item in news_items[:count//2]:
                    title = item.get_text(strip=True)
                    href = item.get('href', '')

                    if not href or not title or len(title) < 10:
                        continue

                    if not title[0].isalnum() and not title[0] in '【《"\'':
                        continue

                    article = NewsArticle(
                        title=title[:100],
                        url=href,
                        source='新浪财经',
                        publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                        category=self._classify_news(title)
                    )
                    articles.append(article)

                    if len(articles) >= count:
                        break

            except Exception as e:
                logger.error(f"解析新浪财经失败：{str(e)[:50]}")
                continue

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_eastmoney(self, count: int = 10) -> List[NewsArticle]:
        """抓取东方财富新闻"""
        logger.info("正在抓取东方财富新闻...")
        articles = []

        urls = [
            "https://news.eastmoney.com/",
            "https://finance.eastmoney.com/",
        ]

        for url in urls:
            html = self._make_request(url)
            if not html:
                continue

            try:
                soup = BeautifulSoup(html, 'html.parser')
                news_items = soup.find_all('a', href=re.compile(r'eastmoney\.com'))

                for item in news_items[:count//2]:
                    title = item.get_text(strip=True)
                    href = item.get('href', '')

                    if not href or not title or len(title) < 10:
                        continue

                    article = NewsArticle(
                        title=title[:100],
                        url=href,
                        source='东方财富',
                        publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                        category=self._classify_news(title)
                    )
                    articles.append(article)

                    if len(articles) >= count:
                        break

            except Exception as e:
                logger.error(f"解析东方财富失败：{str(e)[:50]}")
                continue

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_tonghuashun(self, count: int = 10) -> List[NewsArticle]:
        """抓取同花顺新闻"""
        logger.info("正在抓取同花顺新闻...")
        articles = []

        url = "https://www.10jqka.com.cn/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'10jqka\.com\.cn'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='同花顺',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析同花顺失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_tencent(self, count: int = 10) -> List[NewsArticle]:
        """抓取腾讯财经新闻"""
        logger.info("正在抓取腾讯财经新闻...")
        articles = []

        url = "https://news.qq.com/ch/finance"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'qq\.com'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='腾讯财经',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析腾讯财经失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_netease(self, count: int = 10) -> List[NewsArticle]:
        """抓取网易财经新闻"""
        logger.info("正在抓取网易财经新闻...")
        articles = []

        url = "https://money.163.com/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'163\.com'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='网易财经',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析网易财经失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_stcn(self, count: int = 10) -> List[NewsArticle]:
        """抓取证券时报新闻"""
        logger.info("正在抓取证券时报新闻...")
        articles = []

        url = "https://stcn.com/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'stcn\.com'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                if not href.startswith('http'):
                    href = 'https://stcn.com' + href

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='证券时报',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析证券时报失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_caixin(self, count: int = 10) -> List[NewsArticle]:
        """抓取财新网新闻"""
        logger.info("正在抓取财新网新闻...")
        articles = []

        url = "https://www.caixin.com/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'caixin\.com'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='财新网',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析财新网失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_yicai(self, count: int = 10) -> List[NewsArticle]:
        """抓取第一财经新闻"""
        logger.info("正在抓取第一财经新闻...")
        articles = []

        url = "https://www.yicai.com/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'yicai\.com'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                if not href.startswith('http'):
                    href = 'https://www.yicai.com' + href

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='第一财经',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析第一财经失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_nbd(self, count: int = 10) -> List[NewsArticle]:
        """抓取每日经济新闻"""
        logger.info("正在抓取每日经济新闻...")
        articles = []

        url = "https://www.nbd.com.cn/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'nbd\.com\.cn'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='每日经济新闻',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析每日经济新闻失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_21jingji(self, count: int = 10) -> List[NewsArticle]:
        """抓取21世纪经济报道"""
        logger.info("正在抓取21世纪经济报道...")
        articles = []

        url = "https://www.21jingji.com/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'21jingji\.com'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='21世纪经济报道',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析21世纪经济报道失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_jiemian(self, count: int = 10) -> List[NewsArticle]:
        """抓取澎湃新闻"""
        logger.info("正在抓取澎湃新闻...")
        articles = []

        url = "https://www.jiemian.com/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'jiemian\.com'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='澎湃新闻',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析澎湃新闻失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def scrape_eeo(self, count: int = 10) -> List[NewsArticle]:
        """抓取经济观察网"""
        logger.info("正在抓取经济观察网...")
        articles = []

        url = "https://www.eeo.com.cn/"
        html = self._make_request(url)

        if not html:
            return articles

        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('a', href=re.compile(r'eeo\.com\.cn'))

            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')

                if not href or not title or len(title) < 10:
                    continue

                article = NewsArticle(
                    title=title[:100],
                    url=href,
                    source='经济观察网',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"解析经济观察网失败：{str(e)[:50]}")

        logger.info(f"抓取完成：{len(articles)} 条新闻")
        return articles[:count]

    def _classify_news(self, title: str) -> str:
        """新闻分类"""
        title_lower = title.lower()

        policy_keywords = ['政策', '监管', '央行', '国务院', '证监会', '发改委', '发布', '通知', '办法', '银保监']
        industry_keywords = ['行业', '产业', '板块', '概念', '新能源', '人工智能', '半导体', '芯片']
        stock_pattern = r'\d{6}'

        if any(word in title_lower for word in policy_keywords):
            return 'policy'
        elif any(word in title_lower for word in industry_keywords):
            return 'industry'
        elif re.search(stock_pattern, title):
            return 'stock'
        else:
            return 'market'

    def get_all_news(self, total_count: int = 50) -> List[NewsArticle]:
        """从所有源抓取新闻"""
        logger.info(f"开始从所有源抓取新闻，总计 {total_count} 条")

        all_articles = []

        # 定义抓取函数
        scrapers = [
            (self.scrape_sina, 5),
            (self.scrape_eastmoney, 5),
            (self.scrape_tonghuashun, 5),
            (self.scrape_tencent, 5),
            (self.scrape_netease, 5),
            (self.scrape_stcn, 5),
            (self.scrape_caixin, 4),
            (self.scrape_yicai, 4),
            (self.scrape_nbd, 4),
            (self.scrape_21jingji, 4),
            (self.scrape_jiemian, 3),
            (self.scrape_eeo, 3),
        ]

        for scraper_func, count in scrapers:
            try:
                articles = scraper_func(count)
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"抓取失败: {str(e)[:50]}")
                continue

        # 去重
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title_key = article.title[:30]  # 用前30字符去重
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)

        logger.info(f"去重后剩余 {len(unique_articles)} 条新闻")
        return unique_articles[:total_count]

    def _generate_fallback_news(self, count: int = 10) -> List[NewsArticle]:
        """生成备用新闻"""
        fallback_news = [
            ("央行持续优化货币政策，保持流动性合理充裕", "policy", "positive"),
            ("A股市场震荡上行，金融板块表现亮眼", "market", "positive"),
            ("科技股迎来反弹契机，投资者关注成长主线", "industry", "positive"),
            ("银行股估值修复持续，机构看好长期价值", "stock", "neutral"),
            ("新能源赛道景气度回升，产业链企业订单饱满", "industry", "positive"),
            ("消费复苏势头良好，零售数据超预期", "market", "positive"),
            ("医药板块调整后现配置价值", "stock", "neutral"),
            ("北向资金持续流入，外资看好A股市场", "market", "positive"),
            ("房地产政策持续优化，市场信心逐步恢复", "policy", "neutral"),
            ("制造业PMI重回扩张区间，经济复苏信号明确", "market", "positive"),
            ("券商板块异动，市场交投活跃度提升", "stock", "positive"),
            ("芯片国产化进程加速，半导体板块受关注", "industry", "positive"),
            ("白酒龙头业绩稳健，消费升级趋势延续", "stock", "neutral"),
            ("新能源汽车销量创新高，产业链景气持续", "industry", "positive"),
            ("美联储加息周期接近尾声，全球市场迎来喘息", "policy", "positive"),
        ]

        articles = []
        selected = random.sample(fallback_news, min(count, len(fallback_news)))

        for i, (title, category, sentiment) in enumerate(selected):
            article = NewsArticle(
                title=title,
                url=f"#fallback-{i}",
                source="财经资讯",
                publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                category=category,
                sentiment=sentiment,
                summary=f"这是一条关于{category}领域的财经资讯。"
            )
            articles.append(article)

        return articles

    def fetch_latest_news(self, limit: int = 10) -> List[Dict]:
        """获取最新新闻（API接口使用）"""
        articles = self.get_all_news(total_count=limit)

        if not articles:
            logger.warning("未能从新闻源获取数据，使用备用新闻")
            articles = self._generate_fallback_news(count=limit)

        return [article.to_dict() for article in articles]


def main():
    """测试函数"""
    scraper = NewsScraper(delay=0.5)

    articles = scraper.get_all_news(total_count=30)

    print(f"\n=== 抓取到 {len(articles)} 条新闻 ===\n")

    for i, article in enumerate(articles[:10], 1):
        print(f"{i}. [{article.source}] {article.category}")
        print(f"   标题：{article.title}")
        print(f"   链接：{article.url}")
        print()

    # 统计
    sources = {}
    for article in articles:
        sources[article.source] = sources.get(article.source, 0) + 1

    print("=== 来源统计 ===")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count}")


if __name__ == "__main__":
    main()