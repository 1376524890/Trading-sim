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


class EnhancedDataFetcher:
    """
    增强版数据获取类
    
    支持多种数据源自动切换和降级
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化数据获取器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.cache_dir = self.config.get("data", {}).get("cache_dir", "data")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 连接宝狮数据
        self.bs_login = bs.login()
        
        logger.info(f"增强版数据获取器初始化完成")
        logger.info(f"可用数据源：东方财富 > 新浪财经 > 腾讯源 > AkShare > 网易 > Baostock > Tushare > yfinance")
    
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
        # 设置默认日期
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
        
        logger.info(f"正在获取 {symbol} 的数据，时间范围：{start_date} ~ {end_date}")
        
        # 尝试从缓存加载
        cached = self.load_from_cache(symbol)
        if cached is not None:
            logger.info(f"从缓存加载数据")
            return cached
        
        # 尝试多个数据源
        data_sources = [
            ("东方财富接口", self._fetch_from_eastmoney),
            ("新浪财经接口", self._fetch_from_sina),
            ("腾讯源 (akshare_tencent)", self._fetch_from_tencent),
            ("AkShare 默认源", self._fetch_from_akshare),
            ("网易财经接口", self._fetch_from_netease),
            ("Baostock 宝狮数据", self._fetch_from_baostock),
            ("Tushare", self._fetch_from_tushare),
            ("yfinance", self._fetch_from_yfinance),
        ]

        for source_name, fetch_func in data_sources:
            try:
                logger.info(f"尝试 {source_name}...")
                df = fetch_func(symbol, start_date, end_date)

                if not df.empty:
                    logger.info(f"{source_name} 获取成功，共 {len(df)} 条数据")
                    self._save_to_cache(symbol, df)
                    return df
                else:
                    logger.warning(f"{source_name} 返回空数据")

            except Exception as e:
                logger.error(f"{source_name} 获取失败：{str(e)}")
                continue

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
        """从腾讯源获取数据 (最快、最稳定)"""
        # 提取股票代码
        stock_code = symbol.replace(".SS", "").replace(".SZ", "")
        
        # 腾讯数据格式
        if symbol.endswith(".SS"):
            # 沪市股票 - 需要加 6
            tencent_code = "sh" + stock_code
        else:
            # 深市股票 - 需要加 0
            tencent_code = "sz" + stock_code
        
        # 使用 AkShare 的腾讯源
        df = ak.stock_zh_a_hist(
            symbol=tencent_code,
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust="qfq"  # 前复权
        )
        
        if df.empty:
            raise Exception("腾讯源返回空数据")
        
        return self._normalize_df(df)
    
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
    
    def load_from_cache(self, symbol: str, max_age_days: int = 1) -> Optional[pd.DataFrame]:
        """从缓存加载数据

        Args:
            symbol: 股票符号
            max_age_days: 缓存最大有效期（天），默认1天

        Returns:
            DataFrame 或 None（如果缓存过期或不存在）
        """
        safe_symbol = symbol.replace(".", "_").replace("/", "_")
        cache_file = os.path.join(self.cache_dir, f"{safe_symbol}.csv")

        if not os.path.exists(cache_file):
            return None

        try:
            # 检查文件修改时间
            file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            file_age = (datetime.now() - file_mtime).days

            if file_age > max_age_days:
                logger.info(f"缓存文件已过期 ({file_age}天 > {max_age_days}天)，跳过")
                return None

            df = pd.read_csv(cache_file)

            # 检查数据中最新日期是否过旧
            date_col = None
            for col in ['date', 'Date', 'datetime', 'Datetime']:
                if col in df.columns:
                    date_col = col
                    break

            if date_col:
                # 获取最后一条数据的日期
                last_date_str = str(df[date_col].iloc[-1])
                try:
                    last_date = pd.to_datetime(last_date_str)
                    data_age = (datetime.now() - last_date).days

                    if data_age > 7:  # 数据超过7天认为是旧数据
                        logger.info(f"缓存数据过旧 (最新数据: {last_date_str}，距今{data_age}天)，跳过")
                        return None
                except:
                    pass

            logger.info(f"从缓存加载 {len(df)} 条数据 (缓存时间: {file_mtime.strftime('%Y-%m-%d %H:%M')})")
            return df
        except Exception as e:
            logger.error(f"读取缓存文件失败：{str(e)}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        Args:
            symbol: 股票符号
            
        Returns:
            float: 当前价格，获取失败返回 None
        """
        stock_code = symbol.replace(".SS", "").replace(".SZ", "")
        
        # 尝试从腾讯源获取
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=1)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                adjust="qfq"
            )
            
            if not df.empty:
                return float(df['收盘'].iloc[-1])
        except:
            pass
        
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
        start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d')
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
