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
# @Desc    : Bilibili crawler configuration

from typing import List
from dataclasses import dataclass


@dataclass
class BilibiliConfig:
    """Bilibili crawler configuration"""
    
    # Search configuration
    keywords: str = "编程副业,编程兼职"  # Keywords separated by comma
    search_mode: str = "normal"  # normal | all_in_time_range | daily_limit_in_time_range
    
    # Time range configuration
    start_day: str = "2024-01-01"  # Start date YYYY-MM-DD
    end_day: str = "2024-01-01"    # End date YYYY-MM-DD
    max_notes_per_day: int = 100   # Max videos per day
    
    # Crawling limits
    max_notes_count: int = 200     # Total max videos to crawl
    max_comments_per_video: int = 10  # Max comments per video
    max_creators_count: int = 50   # Max creators to process
    
    # Concurrency and timing
    max_concurrency: int = 1       # Concurrent requests
    crawl_interval: float = 1.0    # Seconds between requests
    
    # Feature toggles
    enable_comments: bool = True   # Whether to crawl comments
    enable_creator_info: bool = True  # Whether to crawl creator info
    enable_sub_comments: bool = False  # Whether to crawl sub-comments
    
    # Storage configuration
    storage_type: str = "json"     # json | csv | db
    data_dir: str = "data/bilibili"
    
    # Browser configuration
    headless: bool = False
    timeout: int = 10
    
    # Specific video/creator lists
    specified_video_ids: List[str] = None
    specified_creator_ids: List[str] = None
    
    def __post_init__(self):
        if self.specified_video_ids is None:
            self.specified_video_ids = []
        if self.specified_creator_ids is None:
            self.specified_creator_ids = []


# Default configuration instance
default_config = BilibiliConfig()