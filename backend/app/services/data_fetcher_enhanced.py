#!/usr/bin/env python3
"""
增强版数据获取模块
⚡ 由御坂网络第一代打造 ⚡

支持的数据源 (按优先级):
1. 东方财富接口 - 免费、稳定
2. 新浪财经接口 - 免费、稳定
3. 腾讯源 (akshare_tencent)
4. AkShare 默认源
5. 网易财经接口
6. Baostock (宝狮数据)
7. Tushare (需 API Key)
8. yfinance (备用)

作者：御坂美琴
创建时间：2026-03-17
更新时间：2026-03-21
"""

import akshare as ak
import baostock as bs
import pandas as pd
import yfinance as yf
import requests
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union
from loguru import logger
import time
import pytz

# 中国时区 (北京时间)
CHINA_TZ = pytz.timezone('Asia/Shanghai')

def get_china_now() -> datetime:
    """获取中国时间（北京时间）"""
    return datetime.now(CHINA_TZ)

def get_china_date_str(fmt: str = "%Y-%m-%d") -> str:
    """获取中国日期字符串"""
    return get_china_now().strftime(fmt)


class EnhancedDataFetcher:
    """
    增强版数据获取类

    支持多种数据源自动切换和降级
    """

    _instance = None  # 单例实例
    _initialized = False

    def __new__(cls, config_path: str = "config.json"):
        """单例模式 - 避免重复创建实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config.json"):
        """初始化数据获取器"""
        # 只初始化一次
        if EnhancedDataFetcher._initialized:
            return

        self.config = self._load_config(config_path)
        self.cache_dir = self.config.get("data", {}).get("cache_dir", "data")
        os.makedirs(self.cache_dir, exist_ok=True)

        # 连接宝狮数据
        try:
            self.bs_login = bs.login()
            if self.bs_login.error_code == '0':
                logger.info("Baostock 宝狮数据连接成功")
            else:
                logger.warning(f"Baostock 连接失败: {self.bs_login.error_msg}")
        except Exception as e:
            logger.warning(f"Baostock 初始化失败: {e}")

        logger.info(f"增强版数据获取器初始化完成")
        logger.info(f"投资系统模式: 禁用缓存，实时数据获取")

        EnhancedDataFetcher._initialized = True
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
            return {"data": {"source": "yfinance"}}
    
    def fetch_stock_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "max",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        获取股票历史数据 (多数据源自动切换)
        
        Args:
            symbol: 股票符号 (例如：601398.SS 为建设银行)
            start_date: 开始日期 (格式：YYYY-MM-DD)
            end_date: 结束日期 (格式：YYYY-MM-DD)
            period: 获取周期
            interval: 数据间隔
            
        Returns:
            pd.DataFrame: 包含 OHLCV 数据的数据框
        """
        # 设置默认日期 (使用北京时间)
        if end_date is None:
            end_date = get_china_date_str("%Y-%m-%d")
        if start_date is None:
            start_date = (get_china_now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
        
        logger.info(f"正在获取 {symbol} 的数据，时间范围：{start_date} ~ {end_date}")

        # ⚠ 投资系统模式：禁用缓存，始终获取实时数据
        # 历史备份数据没有用，必须使用最新实时数据

        # 尝试多个数据源（按可靠性排序，已测试可用）
        # 优先级: Baostock(已验证可用) > 腾讯财经(实时报价) > 其他
        data_sources = [
            ("Baostock 宝狮数据", self._fetch_from_baostock),
            ("腾讯财经", self._fetch_from_tencent),
            ("东方财富接口", self._fetch_from_eastmoney),
            ("新浪财经接口", self._fetch_from_sina),
            ("AkShare 默认源", self._fetch_from_akshare),
            ("网易财经接口", self._fetch_from_netease),
            ("yfinance", self._fetch_from_yfinance),
        ]

        max_retries = 3  # 每个数据源最多重试3次

        for source_name, fetch_func in data_sources:
            for attempt in range(max_retries):
                try:
                    logger.info(f"尝试 {source_name} (第{attempt + 1}次)...")
                    df = fetch_func(symbol, start_date, end_date)

                    if not df.empty:
                        logger.info(f"{source_name} 获取成功，共 {len(df)} 条数据 (实时数据)")
                        # 投资系统禁用缓存，不保存数据
                        return df
                    else:
                        logger.warning(f"{source_name} 返回空数据")
                        break  # 空数据不重试，直接尝试下一个源

                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                        logger.warning(f"{source_name} 获取失败，{wait_time}秒后重试: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{source_name} 获取失败（第{max_retries}次）：{str(e)}")


        # 所有外部源都失败 - 拒绝生成模拟数据
        logger.error(f"所有数据源获取失败，拒绝生成模拟数据")
        logger.error(f"请检查网络连接或稍后重试")

        # 返回空DataFrame，不生成任何假数据
        return pd.DataFrame()

    def _fetch_from_eastmoney(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从东方财富获取数据"""
        import requests

        # 提取股票代码
        stock_code = symbol.replace(".SS", "").replace(".SZ", "")

        # 东方财富市场代码
        if symbol.endswith(".SS"):
            secid = f"1.{stock_code}"
        else:
            secid = f"0.{stock_code}"

        # 转换日期
        start_ts = int(pd.Timestamp(start_date).timestamp())
        end_ts = int(pd.Timestamp(end_date).timestamp())

        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57",
            "klt": "101",  # 日K
            "fqt": "1",    # 前复权
            "beg": start_date.replace("-", ""),
            "end": end_date.replace("-", ""),
            "ut": "fa5fd1943c7b386f172d6893dbfba10b"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "http://quote.eastmoney.com/"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if data.get("data") and data["data"].get("klines"):
            klines = data["data"]["klines"]
            rows = []
            for kline in klines:
                parts = kline.split(",")
                rows.append({
                    "date": pd.to_datetime(parts[0]),
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": float(parts[5]),
                })

            df = pd.DataFrame(rows)
            logger.info(f"东方财富获取 {len(df)} 条数据")
            return df

        raise Exception("东方财富返回空数据")

    def _fetch_from_sina(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从新浪财经获取数据"""
        import requests

        stock_code = symbol.replace(".SS", "").replace(".SZ", "")

        # 新浪市场代码
        if symbol.endswith(".SS"):
            market = "sh"
        else:
            market = "sz"

        url = f"http://finance.sina.com.cn/realstock/company/{market}{stock_code}/hisdata.shtml"
        params = {
            "fromdate": start_date,
            "todate": end_date
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.encoding = "gbk"

            # 解析HTML表格
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            tables = soup.find_all("table")
            if not tables:
                raise Exception("新浪财经未找到数据表格")

            # 尝试解析表格数据
            rows = []
            for table in tables:
                trs = table.find_all("tr")
                for tr in trs[1:]:  # 跳过表头
                    tds = tr.find_all("td")
                    if len(tds) >= 6:
                        try:
                            rows.append({
                                "date": pd.to_datetime(tds[0].text.strip()),
                                "open": float(tds[1].text.strip()),
                                "high": float(tds[2].text.strip()),
                                "close": float(tds[3].text.strip()),
                                "low": float(tds[4].text.strip()),
                                "volume": float(tds[5].text.strip().replace(",", "")),
                            })
                        except:
                            continue

            if rows:
                df = pd.DataFrame(rows)
                logger.info(f"新浪财经获取 {len(df)} 条数据")
                return df

            raise Exception("新浪财经返回空数据")
        except Exception as e:
            raise Exception(f"新浪财经请求失败: {str(e)}")

    def _fetch_from_netease(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从网易财经获取数据"""
        import requests

        stock_code = symbol.replace(".SS", "").replace(".SZ", "")

        # 网易市场代码
        if symbol.endswith(".SS"):
            market = "0"
        else:
            market = "1"

        url = f"http://quotes.money.163.com/service/chddata.html"
        params = {
            "code": f"{market}{stock_code}",
            "start": start_date.replace("-", ""),
            "end": end_date.replace("-", ""),
            "fields": "TCLOSE;HIGH;LOW;TOPEN;VOTURNOVER"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = "gbk"

        # 解析CSV数据
        lines = response.text.strip().split("\n")
        if len(lines) < 2:
            raise Exception("网易财经返回数据不足")

        rows = []
        for line in lines[1:]:  # 跳过表头
            parts = line.split(",")
            if len(parts) >= 7:
                try:
                    rows.append({
                        "date": pd.to_datetime(parts[0]),
                        "open": float(parts[5]) if parts[5] else 0,
                        "high": float(parts[4]) if parts[4] else 0,
                        "low": float(parts[3]) if parts[3] else 0,
                        "close": float(parts[2]) if parts[2] else 0,
                        "volume": float(parts[6]) if parts[6] else 0,
                    })
                except:
                    continue

        if rows:
            df = pd.DataFrame(rows)
            logger.info(f"网易财经获取 {len(df)} 条数据")
            return df

        raise Exception("网易财经返回空数据")

    def _fetch_from_tushare(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从 Tushare 获取数据 (需要 API Key)"""
        try:
            import tushare as ts

            # 尝试从环境变量或配置获取 token
            token = os.environ.get("TUSHARE_TOKEN", "")
            if not token:
                # 尝试从配置文件获取
                token = self.config.get("tushare_token", "")

            if not token:
                raise Exception("Tushare 需要 API Token，请在配置中设置 tushare_token")

            ts.set_token(token)
            pro = ts.pro_api()

            stock_code = symbol.replace(".SS", "").replace(".SZ", "")

            # Tushare 市场代码
            if symbol.endswith(".SS"):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"

            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", "")
            )

            if df.empty:
                raise Exception("Tushare 返回空数据")

            # 重命名列
            df = df.rename(columns={
                "trade_date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume"
            })
            df["date"] = pd.to_datetime(df["date"])

            logger.info(f"Tushare 获取 {len(df)} 条数据")
            return df[["date", "open", "high", "low", "close", "volume"]]

        except ImportError:
            raise Exception("Tushare 未安装，请运行: pip install tushare")
        except Exception as e:
            raise Exception(f"Tushare 请求失败: {str(e)}")

    # ⚠ 已移除模拟数据生成方法 _get_default_data
    # 数据真实性优先，拒绝生成任何假数据

    def _fetch_from_tencent(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从腾讯财经获取数据 (原生API，无需AkShare)"""
        import requests

        # 提取股票代码
        stock_code = symbol.replace(".SS", "").replace(".SZ", "")

        # 腾讯数据格式
        if symbol.endswith(".SS"):
            tencent_code = "sh" + stock_code
        else:
            tencent_code = "sz" + stock_code

        # 直接使用腾讯财经原生API
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {
            'param': f'{tencent_code},day,{start_date},{end_date},320,qfq'
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if data.get("code") != 0:
            raise Exception(f"腾讯API错误: {data.get('msg', 'Unknown error')}")

        # 解析数据
        klines = data.get("data", {}).get(tencent_code, {}).get("qfqday", [])
        if not klines:
            raise Exception("腾讯返回空数据")

        # 转换为DataFrame
        rows = []
        for kline in klines:
            if len(kline) >= 6:
                rows.append({
                    "date": pd.to_datetime(kline[0]),
                    "open": float(kline[1]),
                    "close": float(kline[2]),
                    "high": float(kline[3]),
                    "low": float(kline[4]),
                    "volume": float(kline[5]),
                })

        df = pd.DataFrame(rows)
        logger.info(f"腾讯财经获取 {len(df)} 条数据")
        return df
    
    def _fetch_from_akshare(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从 AkShare 默认源获取数据"""
        stock_code = symbol.replace(".SS", "").replace(".SZ", "")
        
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust="qfq"
        )
        
        if df.empty:
            raise Exception("AkShare 返回空数据")
        
        return self._normalize_df(df)
    
    def _fetch_from_baostock(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从 Baostock 宝狮数据获取数据"""
        # 检查并重新登录
        try:
            login_result = bs.login()
            if login_result is None:
                raise Exception("Baostock 登录返回None")
            if login_result.error_code != '0':
                # 尝试重新登录一次
                bs.logout()
                login_result = bs.login()
                if login_result.error_code != '0':
                    raise Exception(f"Baostock 登录失败: {login_result.error_msg}")
        except Exception as e:
            raise Exception(f"Baostock 连接失败: {e}")

        # Baostock 需要格式: sh.600000 或 sz.000001
        stock_code = symbol.replace(".SS", "").replace(".SZ", "")

        # 添加市场前缀
        if symbol.endswith(".SS"):
            bs_code = f"sh.{stock_code}"
        else:
            bs_code = f"sz.{stock_code}"

        # 转换日期格式为 YYYYMMDD
        start_date_bs = start_date.replace("-", "")
        end_date_bs = end_date.replace("-", "")

        # 获取历史数据 (参数名小写)
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,open,high,low,close,preclose,volume,amount",
            start_date=start_date_bs,
            end_date=end_date_bs,
            adjustflag="3"  # 前复权 (小写参数名)
        )
        
        if rs.error_code != "0":
            raise Exception(f"BaoStock 错误：{rs.error_msg}")
        
        data = []
        while rs.error_code == "0" and rs.next():
            data.append(rs.get_row_data())
        
        if not data:
            raise Exception("Baostock 返回空数据")
        
        df = pd.DataFrame(data, columns=rs.fields)
        df['date'] = pd.to_datetime(df['date'])
        
        # 转换列名
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'preclose': 'PreClose'
        })
        
        return self._normalize_df(df)
    
    def _fetch_from_yfinance(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从 yfinance 获取数据 (备用)"""
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval="1d")
        
        if df.empty:
            raise Exception("yfinance 返回空数据")
        
        # 重置索引，将日期作为列
        df = df.reset_index()
        
        return df
    
    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化数据框格式

        Args:
            df: 原始数据框

        Returns:
            pd.DataFrame: 标准化后的数据框
        """
        # 重命名列 - 中文到小写英文
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change',
            '换手': 'turnover'
        })

        # 大写列名转小写
        df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]

        # 确保日期列存在
        if 'date' not in df.columns:
            if 'Date' in df.columns:
                df['date'] = pd.to_datetime(df['Date'])
            elif df.index.name == 'date' or hasattr(df.index, 'name'):
                df = df.reset_index()
                if 'index' in df.columns:
                    df = df.rename(columns={'index': 'date'})

        # 转换为 float
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 确保列顺序
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        available_cols = [col for col in required_cols if col in df.columns]

        return df[available_cols].copy()
    
    def _save_to_cache(self, symbol: str, df: pd.DataFrame):
        """保存数据到缓存"""
        safe_symbol = symbol.replace(".", "_").replace("/", "_")
        cache_file = os.path.join(self.cache_dir, f"{safe_symbol}.csv")
        
        df.to_csv(cache_file, index=False)
        logger.debug(f"数据已缓存到 {cache_file}")
    
    def load_from_cache(self, symbol: str, max_age_days: int = 0) -> Optional[pd.DataFrame]:
        """从缓存加载数据

        ⚠ 投资系统禁用缓存，始终获取实时数据
        Args:
            symbol: 股票符号
            max_age_days: 已废弃，固定返回None（不缓存）

        Returns:
            始终返回 None，强制获取实时数据
        """
        # 投资系统禁用缓存，确保数据时效性
        logger.debug(f"投资系统模式：跳过缓存，直接获取实时数据")
        return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格 - 优先使用实时报价API

        Args:
            symbol: 股票符号

        Returns:
            float: 当前价格，获取失败返回 None
        """
        # 优先尝试实时报价API (毫秒级响应)
        price = self._get_realtime_quote(symbol)
        if price:
            return price

        # 降级方案：使用历史数据最后收盘价
        return self._get_historical_price(symbol)

    def _get_realtime_quote(self, symbol: str) -> Optional[float]:
        """
        从免费实时API获取实时报价
        按优先级尝试多个源
        """
        # 标准化股票代码
        stock_code = symbol.replace(".SH", "").replace(".SZ", "").replace(".SS", "")

        # 新浪财经实时报价API
        try:
            if symbol.endswith(".SH") or symbol.endswith(".SS"):
                sina_code = f"sh{stock_code}"
            else:
                sina_code = f"sz{stock_code}"

            url = f"https://hq.sinajs.cn/list={sina_code}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://finance.sina.com.cn"
            }
            response = requests.get(url, headers=headers, timeout=3)
            content = response.text

            if content and "=" in content:
                data = content.split("=")[1].strip('"')
                fields = data.split(",")
                if len(fields) > 3:
                    price = float(fields[3])  # 当前价格
                    if price > 0:
                        logger.debug(f"新浪实时报价: {symbol} = ¥{price}")
                        return price
        except Exception as e:
            logger.debug(f"新浪报价失败: {e}")

        # 腾讯财经实时报价API
        try:
            if symbol.endswith(".SH") or symbol.endswith(".SS"):
                tencent_code = f"sh{stock_code}"
            else:
                tencent_code = f"sz{stock_code}"

            url = f"https://qt.gtimg.cn/q={tencent_code}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=3)
            content = response.text

            if content and "~" in content:
                fields = content.split("~")
                if len(fields) > 3:
                    price = float(fields[3])  # 腾讯财经格式
                    if price > 0:
                        logger.debug(f"腾讯实时报价: {symbol} = ¥{price}")
                        return price
        except Exception as e:
            logger.debug(f"腾讯报价失败: {e}")

        # 东方财富实时报价API
        try:
            if symbol.endswith(".SH") or symbol.endswith(".SS"):
                em_code = f"{stock_code}.SH"
            else:
                em_code = f"{stock_code}.SZ"

            url = f"https://push2.eastmoney.com/api/qt/stock/get?secids={em_code}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f57,f58,f60,f169,f170,f171"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=3)
            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                stock_data = data["data"][0]
                price = stock_data.get("f43") / 1000  # 最新价(分->元)
                if price and price > 0:
                    logger.debug(f"东方财富实时报价: {symbol} = ¥{price}")
                    return price
        except Exception as e:
            logger.debug(f"东方财富报价失败: {e}")

        return None

    def _get_historical_price(self, symbol: str) -> Optional[float]:
        """
        降级方案：获取历史数据最后收盘价
        """
        try:
            stock_code = symbol.replace(".SH", "").replace(".SZ", "").replace(".SS", "")

            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=(get_china_now() - timedelta(days=5)).strftime('%Y%m%d'),
                end_date=get_china_date_str('%Y%m%d'),
                adjust="qfq"
            )

            if not df.empty:
                return float(df['收盘'].iloc[-1])
        except Exception as e:
            logger.warning(f"历史数据获取失败: {e}")

        return None
    
    def close(self):
        """关闭连接"""
        bs.logout()


def main():
    """测试函数"""
    fetcher = EnhancedDataFetcher()
    
    # 测试获取建设银行数据
    stock = "601398.SS"
    print(f"\n正在获取 {stock} 的数据...")
    
    df = fetcher.fetch_stock_data(
        stock,
        start_date=(get_china_now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        end_date=get_china_date_str('%Y-%m-%d')
    )
    
    if not df.empty:
        print(f"\n✅ 获取成功!")
        print(f"数据行数：{len(df)}")
        print("\n最近 5 天数据:")
        print(df.tail())
        print(f"\n最新价格：¥{df['Close'].iloc[-1]:.2f}")
    else:
        print("\n❌ 获取失败")
    
    fetcher.close()


if __name__ == "__main__":
    main()
