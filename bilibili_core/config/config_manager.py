# -*- coding: utf-8 -*-
"""
配置管理模块
支持YAML配置文件、环境变量和命令行参数的优先级管理
"""

import os
import yaml
import argparse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..utils.logger import get_logger

logger = get_logger()


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml"):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            # 1. 加载默认配置
            self.config = self._get_default_config()
            
            # 2. 加载YAML配置文件
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        self._merge_config(self.config, yaml_config)
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
            
            # 3. 加载环境变量（优先级高于配置文件）
            self._load_env_config()
            
            # 4. 处理命令行参数（最高优先级）
            self._load_cli_config()
            
            # 5. 验证配置
            self._validate_config()
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "task": {
                "up_id": "1140672573",
                "time_range": {
                    "days": 28
                }
            },
            "fields": {
                "up_info": {
                    "enabled": True,
                    "fields": ["up_mid", "up_name", "up_fans", "up_video_count", "up_sign", "up_level", "up_official_verify"]
                },
                "video_info": {
                    "enabled": True,
                    "fields": ["video_aid", "video_bvid", "video_title", "video_desc", "video_duration", 
                              "video_pubdate", "video_view", "video_danmaku", "video_reply", "video_favorite",
                              "video_coin", "video_like", "video_share", "video_tname", "video_pic"]
                },
                "comments": {
                    "enabled": True,
                    "max_comments": 10,
                    "fields": ["hot_comments_json", "hot_comments_count"]
                }
            },
            "login": {
                "cookie_file": "data/cookies.json",
                "cookie_check_interval": 24,
                "auto_login": {
                    "enabled": True,
                    "timeout": 300
                }
            },
            "storage": {
                # 存储路径已自动分类：日任务存储到data/daily/周文件夹，月任务存储到data/monthly
                # "data_dir": "data",  # 已废弃，存储路径由任务类型自动决定
                # "filename_format": "bilibili_data_{timestamp}_{up_id}.json",  # 已废弃，由任务配置决定
                "save_raw_data": False,
                "compress": False
            },
            "system": {
                "log_level": "INFO",
                "request_delay": 2,
                "browser": {
                    "headless": False,
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "stealth_script": "MediaCrawler_test/libs/stealth.min.js"
                }
            }
        }
    
    def _merge_config(self, base: Dict, override: Dict):
        """递归合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_env_config(self):
        """加载环境变量配置"""
        env_mappings = {
            "BILIBILI_UP_ID": ("task", "up_id"),
            "BILIBILI_DAYS": ("task", "time_range", "days"),
            "BILIBILI_START_DATE": ("task", "time_range", "start_date"),
            "BILIBILI_END_DATE": ("task", "time_range", "end_date"),
            "BILIBILI_COOKIE_FILE": ("login", "cookie_file"),
            "BILIBILI_DATA_DIR": ("storage", "data_dir"),
            "BILIBILI_LOG_LEVEL": ("system", "log_level"),
            "BILIBILI_HEADLESS": ("system", "browser", "headless"),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 类型转换
                if env_var in ["BILIBILI_DAYS"]:
                    value = int(value)
                elif env_var in ["BILIBILI_HEADLESS"]:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                # 设置配置值
                current = self.config
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = value
                
                logger.info(f"环境变量覆盖配置: {env_var} = {value}")
    
    def _load_cli_config(self):
        """加载命令行参数配置"""
        parser = argparse.ArgumentParser(description='Bilibili数据采集工具')
        parser.add_argument('--up-id', type=str, help='UP主ID')
        parser.add_argument('--days', type=int, help='采集天数')
        parser.add_argument('--start-date', type=str, help='开始日期 (YYYY-MM-DD)')
        parser.add_argument('--end-date', type=str, help='结束日期 (YYYY-MM-DD)')
        parser.add_argument('--cookie-file', type=str, help='Cookie文件路径')
        parser.add_argument('--data-dir', type=str, help='数据存储目录')
        parser.add_argument('--headless', action='store_true', help='无头模式')
        parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='日志级别')
        
        args, _ = parser.parse_known_args()
        
        # 应用命令行参数
        if args.up_id:
            self.config["task"]["up_id"] = args.up_id
            logger.info(f"命令行参数覆盖配置: up_id = {args.up_id}")
        
        if args.days:
            self.config["task"]["time_range"]["days"] = args.days
            logger.info(f"命令行参数覆盖配置: days = {args.days}")
        
        if args.start_date:
            self.config["task"]["time_range"]["start_date"] = args.start_date
            logger.info(f"命令行参数覆盖配置: start_date = {args.start_date}")
        
        if args.end_date:
            self.config["task"]["time_range"]["end_date"] = args.end_date
            logger.info(f"命令行参数覆盖配置: end_date = {args.end_date}")
        
        if args.cookie_file:
            self.config["login"]["cookie_file"] = args.cookie_file
            logger.info(f"命令行参数覆盖配置: cookie_file = {args.cookie_file}")
        
        if args.data_dir:
            self.config["storage"]["data_dir"] = args.data_dir
            logger.info(f"命令行参数覆盖配置: data_dir = {args.data_dir}")
        
        if args.headless:
            self.config["system"]["browser"]["headless"] = True
            logger.info(f"命令行参数覆盖配置: headless = True")
        
        if args.log_level:
            self.config["system"]["log_level"] = args.log_level
            logger.info(f"命令行参数覆盖配置: log_level = {args.log_level}")
    
    def _validate_config(self):
        """验证配置"""
        # 验证UP主ID
        if not self.config["task"]["up_id"]:
            raise ValueError("UP主ID不能为空")
        
        # 验证时间范围
        time_range = self.config["task"]["time_range"]
        if "start_date" in time_range and "end_date" in time_range:
            # 验证日期格式
            try:
                datetime.strptime(time_range["start_date"], "%Y-%m-%d")
                datetime.strptime(time_range["end_date"], "%Y-%m-%d")
            except ValueError:
                raise ValueError("日期格式错误，应为 YYYY-MM-DD")
        elif "days" not in time_range or time_range["days"] <= 0:
            raise ValueError("采集天数必须大于0")
        
        # 创建必要的目录
        data_dir = self.config["storage"]["data_dir"]
        os.makedirs(data_dir, exist_ok=True)
        
        cookie_dir = os.path.dirname(self.config["login"]["cookie_file"])
        if cookie_dir:
            os.makedirs(cookie_dir, exist_ok=True)
    
    def get(self, *keys, default=None):
        """获取配置值"""
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get_time_range(self):
        """获取时间范围"""
        time_range = self.config["task"]["time_range"]
        
        if "start_date" in time_range and "end_date" in time_range:
            return time_range["start_date"], time_range["end_date"]
        else:
            days = time_range.get("days", 28)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    
    def get_enabled_fields(self, category: str):
        """获取启用的字段列表"""
        field_config = self.config["fields"].get(category, {})
        if not field_config.get("enabled", True):
            return []
        return field_config.get("fields", [])
    
    def is_field_enabled(self, category: str, field: str):
        """检查字段是否启用"""
        enabled_fields = self.get_enabled_fields(category)
        return field in enabled_fields
    
    def print_config_summary(self):
        """打印配置摘要"""
        logger.info("=" * 50)
        logger.info("配置摘要:")
        logger.info(f"UP主ID: {self.get('task', 'up_id')}")
        
        start_date, end_date = self.get_time_range()
        logger.info(f"时间范围: {start_date} 到 {end_date}")
        
        logger.info(f"Cookie文件: {self.get('login', 'cookie_file')}")
        logger.info(f"数据目录: {self.get('storage', 'data_dir')}")
        logger.info(f"无头模式: {self.get('system', 'browser', 'headless')}")
        
        # 显示启用的字段
        for category in ["up_info", "video_info", "comments"]:
            enabled_fields = self.get_enabled_fields(category)
            logger.info(f"{category}字段 ({len(enabled_fields)}个): {', '.join(enabled_fields[:5])}{'...' if len(enabled_fields) > 5 else ''}")
        
        logger.info("=" * 50)
