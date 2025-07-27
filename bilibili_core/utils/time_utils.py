# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  

# -*- coding: utf-8 -*-
# @Time    : 2023/12/3 16:20
# @Desc    : Time utility functions for Bilibili video tracking

import time
from datetime import datetime, timedelta
from typing import Tuple
import pandas as pd


def get_unix_timestamp() -> int:
    """Get current unix timestamp"""
    return int(time.time())


def get_pubtime_datetime(start: str, end: str) -> Tuple[str, str]:
    """
    获取 bilibili 作品发布日期起始时间戳 pubtime_begin_s 与发布日期结束时间戳 pubtime_end_s
    ---
    :param start: 发布日期起始时间，YYYY-MM-DD
    :param end: 发布日期结束时间，YYYY-MM-DD

    Note
    ---
    - 搜索的时间范围为 start 至 end，包含 start 和 end
    - 若要搜索同一天的内容，为了包含 start 当天的搜索内容，则 pubtime_end_s 的值应该为 pubtime_begin_s 的值加上一天再减去一秒，即 start 当天的最后一秒
        - 如仅搜索 2024-01-05 的内容，pubtime_begin_s = 1704384000，pubtime_end_s = 1704470399
          转换为可读的 datetime 对象：pubtime_begin_s = datetime.datetime(2024, 1, 5, 0, 0)，pubtime_end_s = datetime.datetime(2024, 1, 5, 23, 59, 59)
    - 若要搜索 start 至 end 的内容，为了包含 end 当天的搜索内容，则 pubtime_end_s 的值应该为 pubtime_end_s 的值加上一天再减去一秒，即 end 当天的最后一秒
        - 如搜索 2024-01-05 - 2024-01-06 的内容，pubtime_begin_s = 1704384000，pubtime_end_s = 1704556799
          转换为可读的 datetime 对象：pubtime_begin_s = datetime.datetime(2024, 1, 5, 0, 0)，pubtime_end_s = datetime.datetime(2024, 1, 6, 23, 59, 59)
    """
    # 转换 start 与 end 为 datetime 对象
    start_day: datetime = datetime.strptime(start, "%Y-%m-%d")
    end_day: datetime = datetime.strptime(end, "%Y-%m-%d")
    if start_day > end_day:
        raise ValueError(
            "Wrong time range, please check your start and end argument, to ensure that the start cannot exceed end"
        )
    elif start_day == end_day:  # 搜索同一天的内容
        end_day = (
            start_day + timedelta(days=1) - timedelta(seconds=1)
        )  # 则将 end_day 设置为 start_day + 1 day - 1 second
    else:  # 搜索 start 至 end
        end_day = (
            end_day + timedelta(days=1) - timedelta(seconds=1)
        )  # 则将 end_day 设置为 end_day + 1 day - 1 second
    # 将其重新转换为时间戳
    return str(int(start_day.timestamp())), str(int(end_day.timestamp()))


def generate_date_range(start_date: str, end_date: str):
    """
    Generate date range for daily crawling
    :param start_date: Start date in YYYY-MM-DD format
    :param end_date: End date in YYYY-MM-DD format
    :return: pandas DatetimeIndex
    """
    return pd.date_range(start=start_date, end=end_date, freq="D")