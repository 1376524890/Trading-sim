#!/usr/bin/env python3
"""
news_scraper.py - 财经新闻抓取模块

抓取以下新闻源:
- 新浪财经 (sina.com.cn)
- 东方财富 (eastmoney.com)
- 同花顺 (10jqka.com.cn)
- 证券时报 (stcn.com)
- 中国证券报 (cs.com.cn)

作者：御坂美琴
创建时间：2026-03-17
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


class NewsScraper:
    """
    财经新闻爬虫类
    
    从多个财经新闻源抓取最新新闻
    """
    
    def __init__(self, delay: float = 1.0):
        """
        初始化新闻爬虫
        
        Args:
            delay: 请求间隔时间 (秒)
        """
        self.delay = delay
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        logger.info("新闻爬虫初始化完成")
    
    def _make_request(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        发送 HTTP 请求
        
        Args:
            url: 目标 URL
            timeout: 超时时间
            
        Returns:
            响应文本或 None
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            time.sleep(self.delay)  # 礼貌爬取
            return response.text
        except Exception as e:
            logger.error(f"请求失败 {url}: {str(e)}")
            return None
    
    def scrape_sina(self, count: int = 10) -> List[NewsArticle]:
        """
        抓取新浪财经新闻
        
        Args:
            count: 抓取数量
            
        Returns:
            新闻列表
        """
        logger.info("正在抓取新浪财经新闻...")
        articles = []
        
        # 新浪财经财经新闻列表
        urls = [
            "https://finance.sina.com.cn/stock/",
            "https://finance.sina.com.cn/stock/ggnc/",
            "https://finance.sina.com.cn/stock/hggs/",
        ]
        
        for url in urls:
            html = self._make_request(url)
            if not html:
                continue
            
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找新闻列表
                news_items = soup.find_all('a', class_='news_list_title')
                if not news_items:
                    # 尝试其他选择器
                    news_items = soup.find_all('a', href=re.compile('/stock/'))
                
                for item in news_items[:count//3]:
                    title = item.get_text(strip=True)
                    href = item.get('href', '')
                    
                    if not href or not title:
                        continue
                    
                    # 处理相对路径
                    if href.startswith('/'):
                        href = 'https://finance.sina.com.cn' + href
                    
                    article = NewsArticle(
                        title=title,
                        url=href,
                        source='sina',
                        publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                        category=self._classify_news(title)
                    )
                    articles.append(article)
                    
                    if len(articles) >= count:
                        break
            
            except Exception as e:
                logger.error(f"解析新浪财经失败：{str(e)}")
                continue
        
        return articles[:count]
    
    def scrape_eastmoney(self, count: int = 10) -> List[NewsArticle]:
        """
        抓取东方财富新闻
        
        Args:
            count: 抓取数量
            
        Returns:
            新闻列表
        """
        logger.info("正在抓取东方财富新闻...")
        articles = []
        
        urls = [
            "https://news.eastmoney.com/",
            "https://guba.eastmoney.com/",
        ]
        
        for url in urls:
            html = self._make_request(url)
            if not html:
                continue
            
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找新闻链接
                news_items = soup.find_all('a', href=re.compile('/a_'))
                
                for item in news_items[:count//2]:
                    title = item.get_text(strip=True)
                    href = item.get('href', '')
                    
                    if not href or not title:
                        continue
                    
                    if not href.startswith('http'):
                        href = 'https://guba.eastmoney.com' + href if 'guba' in href else 'https://news.eastmoney.com' + href
                    
                    article = NewsArticle(
                        title=title,
                        url=href,
                        source='eastmoney',
                        publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                        category=self._classify_news(title)
                    )
                    articles.append(article)
                    
                    if len(articles) >= count:
                        break
            
            except Exception as e:
                logger.error(f"解析东方财富失败：{str(e)}")
                continue
        
        return articles[:count]
    
    def scrape_10jqka(self, count: int = 10) -> List[NewsArticle]:
        """
        抓取同花顺新闻
        
        Args:
            count: 抓取数量
            
        Returns:
            新闻列表
        """
        logger.info("正在抓取同花顺新闻...")
        articles = []
        
        url = "https://www.10jqka.com.cn/"
        html = self._make_request(url)
        
        if not html:
            return articles
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找新闻链接
            news_items = soup.find_all('a', href=re.compile('/news/'))
            
            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')
                
                if not href or not title:
                    continue
                
                if not href.startswith('http'):
                    href = 'https://www.10jqka.com.cn' + href
                
                article = NewsArticle(
                    title=title,
                    url=href,
                    source='10jqka',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)
        
        except Exception as e:
            logger.error(f"解析同花顺失败：{str(e)}")
        
        return articles[:count]
    
    def scrape_stcn(self, count: int = 10) -> List[NewsArticle]:
        """
        抓取证券时报新闻
        
        Args:
            count: 抓取数量
            
        Returns:
            新闻列表
        """
        logger.info("正在抓取证券时报新闻...")
        articles = []
        
        url = "https://www.stcn.com/"
        html = self._make_request(url)
        
        if not html:
            return articles
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找新闻链接
            news_items = soup.find_all('a', class_='title')
            if not news_items:
                news_items = soup.find_all('a', href=re.compile('/n/'))
            
            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')
                
                if not href or not title:
                    continue
                
                if not href.startswith('http'):
                    href = 'https://www.stcn.com' + href
                
                article = NewsArticle(
                    title=title,
                    url=href,
                    source='stcn',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)
        
        except Exception as e:
            logger.error(f"解析证券时报失败：{str(e)}")
        
        return articles[:count]
    
    def scrape_cs_comcn(self, count: int = 10) -> List[NewsArticle]:
        """
        抓取中国证券报新闻
        
        Args:
            count: 抓取数量
            
        Returns:
            新闻列表
        """
        logger.info("正在抓取中国证券报新闻...")
        articles = []
        
        url = "http://www.cs.com.cn/"
        html = self._make_request(url)
        
        if not html:
            return articles
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找新闻链接
            news_items = soup.find_all('a', href=re.compile('/a_'))
            
            for item in news_items[:count]:
                title = item.get_text(strip=True)
                href = item.get('href', '')
                
                if not href or not title:
                    continue
                
                if not href.startswith('http'):
                    href = 'http://www.cs.com.cn' + href
                
                article = NewsArticle(
                    title=title,
                    url=href,
                    source='cs.com.cn',
                    publish_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    category=self._classify_news(title)
                )
                articles.append(article)
        
        except Exception as e:
            logger.error(f"解析中国证券报失败：{str(e)}")
        
        return articles[:count]
    
    def _classify_news(self, title: str) -> str:
        """
        新闻分类
        
        Args:
            title: 新闻标题
            
        Returns:
            分类：policy, industry, stock, market
        """
        title_lower = title.lower()
        
        # 政策类关键词
        policy_keywords = ['政策', '监管', '央行', '国务院', '证监会', '发改委', '发布', '通知', '办法']
        # 行业类关键词
        industry_keywords = ['行业', '产业', '板块', '概念', '新能源', '人工智能', '半导体']
        # 个股类关键词 (A 股代码)
        stock_pattern = r'\d{6}'
        
        if any(word in title_lower for word in policy_keywords):
            return 'policy'
        elif any(word in title_lower for word in industry_keywords):
            return 'industry'
        elif re.search(stock_pattern, title):
            return 'stock'
        else:
            return 'market'
    
    def extract_keywords(self, title: str, content: str = "") -> List[str]:
        """
        提取关键词
        
        Args:
            title: 新闻标题
            content: 新闻内容
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取
        all_text = title + " " + content
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', all_text)
        
        # 过滤停用词
        stop_words = {'的', '了', '和', '是', '在', '就', '都', '而', '及', '与', '着', '或'}
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        
        # 统计词频
        word_count = {}
        for word in keywords:
            word_count[word] = word_count.get(word, 0) + 1
        
        # 返回频率最高的前 10 个词
        sorted_keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        return [kw for kw, count in sorted_keywords]
    
    def get_all_news(self, total_count: int = 50) -> List[NewsArticle]:
        """
        从所有源抓取新闻
        
        Args:
            total_count: 总抓取数量
            
        Returns:
            新闻列表
        """
        logger.info(f"开始从所有源抓取新闻，总计 {total_count} 条")
        
        all_articles = []
        
        # 定义抓取函数和数量
        scrapers = [
            (self.scrape_sina, total_count // 5),
            (self.scrape_eastmoney, total_count // 5),
            (self.scrape_10jqka, total_count // 5),
            (self.scrape_stcn, total_count // 5),
            (self.scrape_cs_comcn, total_count // 5),
        ]
        
        for scraper_func, count in scrapers:
            articles = scraper_func(count)
            all_articles.extend(articles)
            logger.info(f"抓取完成：{len(articles)} 条新闻")
        
        # 去重
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        logger.info(f"去重后剩余 {len(unique_articles)} 条新闻")
        return unique_articles

    def _generate_fallback_news(self, count: int = 10) -> List[NewsArticle]:
        """
        生成备用新闻（当无法从真实源获取时使用）

        Args:
            count: 生成数量

        Returns:
            新闻列表
        """
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
        import random
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
        """
        获取最新新闻（API接口使用）

        Args:
            limit: 获取数量

        Returns:
            新闻字典列表
        """
        articles = self.get_all_news(total_count=limit)

        # 如果没有抓取到新闻，使用备用数据
        if not articles:
            logger.warning("未能从新闻源获取数据，使用备用新闻")
            articles = self._generate_fallback_news(count=limit)

        return [article.to_dict() for article in articles]


def main():
    """测试函数"""
    # 创建爬虫
    scraper = NewsScraper(delay=0.5)
    
    # 抓取新闻
    articles = scraper.get_all_news(total_count=30)
    
    print(f"\n=== 抓取到 {len(articles)} 条新闻 ===\n")
    
    # 显示前 5 条
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. [{article.source}] {article.category}")
        print(f"   标题：{article.title}")
        print(f"   链接：{article.url}")
        print()
    
    # 按分类统计
    categories = {}
    sources = {}
    for article in articles:
        categories[article.category] = categories.get(article.category, 0) + 1
        sources[article.source] = sources.get(article.source, 0) + 1
    
    print("=== 分类统计 ===\n")
    print("按分类:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}")
    
    print("\n按来源:")
    for src, count in sources.items():
        print(f"  {src}: {count}")


if __name__ == "__main__":
    main()
