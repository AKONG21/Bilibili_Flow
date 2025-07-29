#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
每日任务数据处理器
按照用户要求的数据结构重新设计
"""

import asyncio
import json
import logging
import os
import sys
import time
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
from bilibili_core.client.bilibili_client import BilibiliClient
from bilibili_core.config.config_manager import ConfigManager
from bilibili_core.storage.simple_storage import SimpleStorage

# 统一存储模式：JSON + 数据库同时保存
from bilibili_core.utils.logger import get_logger
from bilibili_core.utils.time_utils import get_pubtime_datetime
from bilibili_core.utils.login_helper import BilibiliLoginHelper
from bilibili_core.cookie_management import EnhancedCookieManager, AutoCookieManager
from bilibili_core.client.field import SearchOrderType, CommentOrderType


class DailyTaskProcessor:
    """每日任务数据处理器"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml", task_type: str = "daily"):
        self.config_file = config_file
        self.task_type = task_type  # 新增：任务类型 ("daily" 或 "monthly")
        self.config = None
        self.logger = None
        self.bili_client = None
        self.storage = None

        # 浏览器相关
        self.browser_context = None
        self.context_page = None
        self.login_helper = None
        self.cookie_manager = None
        self.auto_cookie_manager = None

        self.stats = {
            "videos_processed": 0,
            "comments_collected": 0,
            "errors": 0,
            "retries": 0
        }
        
    async def initialize(self):
        """初始化处理器"""
        # 加载配置
        self.config = self._load_config()

        # 设置日志
        self.logger = get_logger()

        # 初始化自动Cookie管理器
        self.auto_cookie_manager = AutoCookieManager(self.config_file)
        self.auto_cookie_manager.load_config()

        # 显示Cookie状态并清理过期Cookie
        self._display_cookie_status_and_cleanup()

        # 统一存储模式：JSON + 数据库同时保存
        storage_config = self.config.get("storage", {})
        task_config = self.config.get("task_config", {})

        # 初始化JSON存储 - 使用分类存储路径
        if self.task_type == "monthly":
            monthly_config = task_config.get("monthly_task", {})
            filename_config = monthly_config.get("filename", {})
            filename_format = filename_config.get("format", "monthly_task_{timestamp}_{up_id}.json")
            timestamp_format = filename_config.get("timestamp_format", "%Y%m%d")
            # 月任务存储到 data/monthly 目录
            data_dir = "data/monthly"
        else:  # daily task
            daily_config = task_config.get("daily_task", {})
            filename_config = daily_config.get("filename", {})
            filename_format = filename_config.get("format", "daily_task_{timestamp}_{up_id}.json")
            timestamp_format = filename_config.get("timestamp_format", "%Y%m%d_%H%M")
            # 日任务存储到 data/daily 目录（会在finalize_task中进一步细分到周文件夹）
            data_dir = "data/daily"

        self.storage = SimpleStorage(
            data_dir=data_dir,
            filename_format=filename_format,
            timestamp_format=timestamp_format,
            task_type=self.task_type  # 传递任务类型用于路径处理
        )

        # 初始化数据库存储
        self.db_path = "data/database/bilibili_tracking.db"
        self._init_database()

        self.logger.info("统一存储模式初始化完成：JSON + 数据库")

        # 初始化增强版Cookie管理器
        login_config = self.config.get("login", {})
        self.cookie_manager = EnhancedCookieManager(
            config=self.config,  # 传递完整配置
            raw_cookie=login_config.get("cookies", {}).get("raw_cookie", ""),
            backup_cookies_dir=login_config.get("backup_cookies_dir", "data/backup_cookies"),
            check_interval_hours=login_config.get("cookie_check_interval", 24)
        )

        # 加载Cookie（按优先级：原始Cookie > 备用文件）
        self.cookie_manager.load_cookies()

        # 显示Cookie状态
        status = self.cookie_manager.get_status_info()
        self.logger.info(f"Cookie状态: {status}")

        # 初始化浏览器
        await self.init_browser()

        # 处理登录
        await self.handle_login()

        # 创建B站客户端
        await self.create_bilibili_client()

        # 检查登录状态
        if not await self.check_login_status():
            raise Exception("登录状态检查失败")

        self.logger.info("每日任务处理器初始化完成")

    def _init_database(self):
        """初始化数据库"""
        import sqlite3

        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # 创建数据库连接
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建UP主信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS up_master_records (
                mid INTEGER NOT NULL,
                up_name TEXT NOT NULL,
                fans_count INTEGER DEFAULT 0,
                video_count INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                friend_count INTEGER DEFAULT 0,
                collection_time INTEGER NOT NULL,
                task_type TEXT DEFAULT 'unknown',
                PRIMARY KEY (mid, collection_time)
            )
        ''')

        # 创建视频记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_records (
                aid INTEGER NOT NULL,
                bvid TEXT,
                title TEXT,
                description TEXT,
                cover_url TEXT,
                publish_time INTEGER,
                duration INTEGER,
                category TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                coin_count INTEGER DEFAULT 0,
                favorite_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                danmaku_count INTEGER DEFAULT 0,
                up_id INTEGER,
                collection_time INTEGER NOT NULL,
                task_type TEXT DEFAULT 'unknown',
                parent_aid INTEGER,
                PRIMARY KEY (aid, collection_time)
            )
        ''')

        # 创建索引（复合主键已经自动创建索引，这里创建额外的查询索引）
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_aid ON video_records(aid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_up_id ON video_records(up_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_task_type ON video_records(task_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_up_mid ON up_master_records(mid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_up_collection_time ON up_master_records(collection_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_collection_time ON video_records(collection_time)')

        conn.commit()
        conn.close()

        self.logger.info(f"数据库初始化完成: {self.db_path}")

    def _display_cookie_status_and_cleanup(self):
        """显示Cookie状态并清理过期Cookie"""
        try:
            # 清理过期Cookie
            cleanup_results = self.auto_cookie_manager.cleanup_all_expired()

            # 显示Cookie状态
            status = self.auto_cookie_manager.display_cookie_status()

            # 记录清理结果
            if cleanup_results["config_cookies"] > 0 or cleanup_results["backup_files"] > 0:
                self.logger.info(f"清理完成: 配置Cookie {cleanup_results['config_cookies']}个, 备份文件 {cleanup_results['backup_files']}个")

            # 检查Cookie数量并提醒
            if status['available'] < 2:
                self.logger.warning("⚠️ 可用Cookie数量不足2个，建议及时补充！")

        except Exception as e:
            self.logger.error(f"Cookie状态检查失败: {e}")
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config
            else:
                raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        except Exception as e:
            print(f"配置加载失败: {e}")
            raise

    async def init_browser(self):
        """初始化浏览器"""
        # 智能选择浏览器模式
        has_valid_cookies = self.cookie_manager.cookies and not self.cookie_manager.is_cookie_expired()
        browser_config = self.config.get("system", {}).get("browser", {})

        # 如果有有效Cookie，使用无头模式；否则使用有头模式进行登录
        if has_valid_cookies:
            headless_mode = True
            self.logger.info("检测到有效Cookie，使用无头模式启动浏览器...")
        else:
            headless_mode = browser_config.get("headless", False)
            self.logger.info("未检测到有效Cookie，使用有头模式启动浏览器进行登录...")

        playwright = await async_playwright().start()
        chromium = playwright.chromium

        # 启动浏览器
        browser = await chromium.launch(
            headless=headless_mode,
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        self.browser_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=browser_config.get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        )

        # 添加stealth脚本防检测
        stealth_script = browser_config.get("stealth_script")
        if stealth_script and os.path.exists(stealth_script):
            await self.browser_context.add_init_script(path=stealth_script)

        self.context_page = await self.browser_context.new_page()
        await self.context_page.goto("https://www.bilibili.com")

        # 创建登录辅助器
        self.login_helper = BilibiliLoginHelper(self.context_page)

        if headless_mode:
            self.logger.info("浏览器已在无头模式下启动完成")
        else:
            self.logger.info("浏览器已在有头模式下启动完成")

    async def handle_login(self):
        """处理登录"""
        self.logger.info("开始处理登录...")

        # 检查是否有有效的Cookie
        if not self.cookie_manager.is_cookie_expired():
            self.logger.info("发现有效Cookie，尝试使用Cookie登录")

            # 验证Cookie是否真的有效
            if await self.cookie_manager.validate_cookies(self.browser_context):
                self.logger.info("Cookie登录成功")
                return True
            else:
                self.logger.warning("Cookie已失效，需要重新登录")

        # 自动登录流程
        login_config = self.config.get("login", {}).get("auto_login", {})
        if login_config.get("enabled", True):
            self.logger.info("开始自动登录流程...")

            success = await self.login_helper.auto_login_process()
            if success:
                self.logger.info("登录界面已打开，请完成登录...")
                input("完成登录后按回车继续...")

                # 获取新的Cookie
                cookies = await self.browser_context.cookies()

                # 1. 保存到备用文件
                filepath = self.cookie_manager.save_cookies_after_login(cookies)
                self.logger.info(f"登录完成，Cookie已保存到备用文件: {filepath}")

                # 2. 自动添加到配置文件
                cookie_string = self.auto_cookie_manager.extract_cookie_string_from_browser(cookies)
                if cookie_string and self.auto_cookie_manager.validate_cookie_string(cookie_string):
                    # 生成账号名称
                    timestamp = datetime.now().strftime("%m%d_%H%M")
                    account_name = f"scan_{timestamp}"

                    if self.auto_cookie_manager.add_cookie_to_config(cookie_string, account_name):
                        self.logger.info(f"✅ Cookie已自动添加到配置文件: {account_name}")

                        # 重新加载配置以使用新Cookie
                        self.auto_cookie_manager.load_config()
                        self.config = self.auto_cookie_manager.config
                    else:
                        self.logger.warning("❌ Cookie添加到配置文件失败")
                else:
                    self.logger.warning("❌ 提取的Cookie无效，未添加到配置文件")

                # 3. 清理旧的备用文件
                self.cookie_manager.cleanup_old_backup_files()
                return True
            else:
                self.logger.error("打开登录界面失败")
                return False
        else:
            self.logger.info("请手动完成登录...")
            input("完成登录后按回车继续...")

            # 获取新的Cookie
            cookies = await self.browser_context.cookies()

            # 1. 保存到备用文件
            filepath = self.cookie_manager.save_cookies_after_login(cookies)
            self.logger.info(f"手动登录完成，Cookie已保存到备用文件: {filepath}")

            # 2. 自动添加到配置文件
            cookie_string = self.auto_cookie_manager.extract_cookie_string_from_browser(cookies)
            if cookie_string and self.auto_cookie_manager.validate_cookie_string(cookie_string):
                # 生成账号名称
                timestamp = datetime.now().strftime("%m%d_%H%M")
                account_name = f"manual_{timestamp}"

                if self.auto_cookie_manager.add_cookie_to_config(cookie_string, account_name):
                    self.logger.info(f"✅ Cookie已自动添加到配置文件: {account_name}")

                    # 重新加载配置以使用新Cookie
                    self.auto_cookie_manager.load_config()
                    self.config = self.auto_cookie_manager.config
                else:
                    self.logger.warning("❌ Cookie添加到配置文件失败")
            else:
                self.logger.warning("❌ 提取的Cookie无效，未添加到配置文件")

            # 3. 清理旧的备用文件
            self.cookie_manager.cleanup_old_backup_files()
            return True

    async def create_bilibili_client(self):
        """创建Bilibili客户端"""
        self.logger.info("正在创建Bilibili客户端...")

        # 获取Cookie
        cookie_str = self.cookie_manager.get_cookie_string()
        cookie_dict = self.cookie_manager.get_cookie_dict()

        browser_config = self.config.get("system", {}).get("browser", {})

        # 创建客户端
        self.bili_client = BilibiliClient(
            timeout=30,
            headers={
                "User-Agent": browser_config.get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                "Cookie": cookie_str,
                "Origin": "https://www.bilibili.com",
                "Referer": "https://www.bilibili.com",
                "Content-Type": "application/json;charset=UTF-8",
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
        )

        self.logger.info("Bilibili客户端创建完成")

    async def close(self):
        """关闭资源"""
        if self.browser_context:
            await self.browser_context.close()
            self.logger.info("浏览器已关闭")

    async def create_bilibili_client(self):
        """创建Bilibili客户端"""
        self.logger.info("正在创建Bilibili客户端...")

        # 从浏览器上下文获取最新的Cookie
        cookies = await self.browser_context.cookies()
        cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

        browser_config = self.config.get("system", {}).get("browser", {})

        # 创建客户端
        self.bili_client = BilibiliClient(
            timeout=30,
            headers={
                "User-Agent": browser_config.get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                "Cookie": cookie_str,
                "Origin": "https://www.bilibili.com",
                "Referer": "https://www.bilibili.com",
                "Content-Type": "application/json;charset=UTF-8",
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
        )

        self.logger.info("Bilibili客户端创建完成")

    async def check_login_status(self):
        """检查登录状态"""
        self.logger.info("正在检查登录状态...")

        if not await self.bili_client.pong():
            self.logger.error("登录状态检查失败")
            return False

        self.logger.info("登录状态检查通过")
        return True

    async def cleanup(self):
        """清理资源"""
        try:
            if self.browser_context:
                await self.browser_context.close()
                self.logger.info("浏览器已关闭")
        except Exception as e:
            self.logger.warning(f"清理资源时出错: {e}")

    async def close(self):
        """关闭资源"""
        if self.browser_context:
            await self.browser_context.close()
            self.logger.info("浏览器已关闭")

    async def _store_up_info_to_db(self, up_id: int, up_info: Dict):
        """存储UP主信息到数据库"""
        import sqlite3
        import time

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取当前时间戳
            current_timestamp = int(time.time())

            # 插入UP主信息
            cursor.execute('''
                INSERT INTO up_master_records
                (mid, up_name, fans_count, video_count, total_views, friend_count, collection_time, task_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                up_id,
                up_info.get('name', ''),
                up_info.get('fans', 0),
                up_info.get('up_video_count', 0),
                up_info.get('total_views', 0),
                up_info.get('following', 0),
                current_timestamp,
                self.task_type
            ))

            conn.commit()
            conn.close()

            self.logger.info(f"UP主信息已存储: {up_info.get('name', 'Unknown')}")

        except Exception as e:
            self.logger.error(f"UP主信息存储失败: {e}")
            raise

    async def _store_videos_to_db(self, up_id: int, videos: List[Dict]):
        """存储视频信息到数据库（支持增量更新）"""
        import sqlite3
        import time

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取已知的视频AID列表
            cursor.execute('SELECT DISTINCT aid FROM video_records WHERE parent_aid IS NULL')
            known_aids = {row[0] for row in cursor.fetchall()}

            # 获取当前时间戳
            current_timestamp = int(time.time())

            for video in videos:
                aid = video.get('aid')
                if not aid:
                    continue

                # 判断是新视频还是已知视频的增量记录
                parent_aid = None if aid not in known_aids else aid

                # 解析发布时间
                publish_time = self._parse_publish_time(video.get('publish_time'))

                # 插入视频记录
                cursor.execute('''
                    INSERT INTO video_records
                    (aid, bvid, title, description, cover_url, publish_time, duration, category,
                     view_count, like_count, coin_count, favorite_count, share_count, reply_count, danmaku_count,
                     up_id, collection_time, task_type, parent_aid)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    aid,
                    video.get('bvid', ''),
                    video.get('title', ''),
                    video.get('description', ''),
                    video.get('cover_url', ''),
                    publish_time,
                    self._parse_duration(video.get('duration', '0:00')),
                    video.get('category', ''),
                    video.get('view', 0),
                    video.get('like', 0),
                    video.get('coin', 0),
                    video.get('favorite', 0),
                    video.get('share', 0),
                    video.get('reply', 0),
                    video.get('danmaku', 0),
                    up_id,
                    current_timestamp,
                    self.task_type,
                    parent_aid
                ))

            conn.commit()
            conn.close()

            new_videos = len([v for v in videos if v.get('aid') not in known_aids])
            incremental_videos = len(videos) - new_videos

            self.logger.info(f"视频数据已存储到数据库：{new_videos}个新视频，{incremental_videos}个增量记录")

        except Exception as e:
            self.logger.error(f"视频数据存储失败: {e}")
            raise

    async def _store_data_unified(self, up_id: int, up_info: Dict, videos: List[Dict]):
        """统一存储方法：JSON + 数据库同时保存"""
        try:
            # 1. 存储UP主信息到数据库
            await self._store_up_info_to_db(up_id, up_info)

            # 2. 存储视频信息到数据库（支持增量更新）
            await self._store_videos_to_db(up_id, videos)

            # 3. 存储到JSON文件（使用现有的SimpleStorage）
            await self._store_data_simple(up_id, up_info, videos)

            self.logger.info(f"统一存储完成：UP主信息和{len(videos)}个视频已保存到数据库和JSON")

        except Exception as e:
            self.logger.error(f"统一存储失败: {e}")
            raise

    async def get_up_info(self, up_id: str) -> Dict:
        """获取UP主信息"""
        # 根据任务类型获取配置
        if self.task_type == "monthly":
            task_config = self.config.get("task_config", {}).get("monthly_task", {})
        else:
            task_config = self.config.get("task_config", {}).get("daily_task", {})

        # 检查是否启用UP主信息收集
        up_fields_config = task_config.get("up_fields", {})
        if not up_fields_config.get("enabled", True):
            self.logger.info("UP主信息收集已禁用")
            return {}

        try:
            # 获取UP主基础信息
            creator_info = await self.bili_client.get_creator_info(int(up_id))

            if not creator_info:
                raise Exception("获取UP主信息失败")

            # 获取粉丝数（通过关系接口）
            up_fans = None
            try:
                relation_response = await self.bili_client.get(f"/x/relation/stat?vmid={up_id}", enable_params_sign=False)
                up_fans = relation_response.get("follower")
            except Exception as e:
                self.logger.warning(f"获取粉丝数失败，尝试备用方法: {e}")
                # 备用方法：使用卡片接口
                try:
                    card_response = await self.bili_client.get(f"/x/web-interface/card?mid={up_id}", enable_params_sign=False)
                    up_fans = card_response.get("card", {}).get("fans")
                except Exception as e2:
                    self.logger.warning(f"备用方法也失败: {e2}")

            # 获取视频总数（通过视频列表接口）
            up_video_count = None
            videos_response = await self.bili_client.get_creator_videos(
                creator_id=up_id, pn=1, ps=1
            )
            if videos_response and videos_response.get("page"):
                up_video_count = videos_response["page"].get("count")

            # 字段映射
            field_mapping = {
                "mid": creator_info.get("mid"),
                "name": creator_info.get("name"),
                "fans": up_fans,
                "up_video_count": up_video_count,
                "sign": creator_info.get("sign", ""),
                "level": creator_info.get("level"),
                "official_verify": creator_info.get("official", {}),
            }

            # 只包含启用的字段（排除enabled字段本身）
            up_data = {}
            for field, enabled in up_fields_config.items():
                if field != "enabled" and enabled and field in field_mapping:
                    up_data[field] = field_mapping[field]

            self.logger.info(f"UP主信息获取成功: {up_data.get('name', 'Unknown')} (粉丝: {up_data.get('fans', 'Unknown')})")
            return up_data

        except Exception as e:
            self.logger.error(f"获取UP主信息失败: {e}")
            self.stats["errors"] += 1
            return {}
            
    async def get_video_info(self, video_basic: Dict) -> Dict:
        """获取视频详细信息"""
        # 根据任务类型获取配置
        if self.task_type == "monthly":
            task_config = self.config.get("task_config", {}).get("monthly_task", {})
        else:
            task_config = self.config.get("task_config", {}).get("daily_task", {})

        # 检查是否启用视频信息收集
        video_fields_config = task_config.get("video_fields", {})
        if not video_fields_config.get("enabled", True):
            self.logger.info("视频信息收集已禁用")
            return {}

        aid = video_basic.get("aid")
        bvid = video_basic.get("bvid", "")

        try:
            # 获取视频详细信息
            video_detail = await self.bili_client.get_video_info(aid=aid, bvid=bvid)

            if not video_detail or "View" not in video_detail:
                self.logger.warning(f"视频详细信息获取失败: AV{aid}")
                return self._extract_basic_video_fields(video_basic)

            view_data = video_detail["View"]
            stat_data = view_data.get("stat", {})

            stats_fields_config = video_fields_config.get("stats_fields", {})

            # 字段映射
            field_mapping = {
                "aid": view_data.get("aid"),
                "bvid": view_data.get("bvid"),
                "title": view_data.get("title"),
                "description": view_data.get("desc", ""),
                "cover_url": view_data.get("pic", ""),
                "video_url": f"https://www.bilibili.com/video/{view_data.get('bvid', '')}",
                "duration": self._format_duration(view_data.get("duration", 0)),
                "category": view_data.get("tname", ""),
                "publish_time": self._format_timestamp(view_data.get("pubdate", 0)),
                # 统计数据
                "view": stat_data.get("view", 0),
                "like": stat_data.get("like", 0),
                "coin": stat_data.get("coin", 0),
                "favorite": stat_data.get("favorite", 0),
                "share": stat_data.get("share", 0),
                "reply": stat_data.get("reply", 0),
                "danmaku": stat_data.get("danmaku", 0),
            }

            # 构建视频数据
            video_data = {}

            # 添加基础字段（排除enabled和stats_fields）
            for field, enabled in video_fields_config.items():
                if field not in ["enabled", "stats_fields"] and enabled and field in field_mapping:
                    video_data[field] = field_mapping[field]

            # 添加统计字段（如果启用）
            if stats_fields_config.get("enabled", True):
                for field, enabled in stats_fields_config.items():
                    if field != "enabled" and enabled and field in field_mapping:
                        video_data[field] = field_mapping[field]

            self.logger.info(f"视频信息获取成功: {video_data.get('title', 'Unknown')} (播放量: {video_data.get('view', 'Unknown')})")
            return video_data

        except Exception as e:
            self.logger.error(f"获取视频详细信息失败 AV{aid}: {e}")
            self.stats["errors"] += 1
            return self._extract_basic_video_fields(video_basic)
            
    def _extract_basic_video_fields(self, video_basic: Dict) -> Dict:
        """从基础视频信息中提取字段"""
        # 根据任务类型获取配置
        if self.task_type == "monthly":
            task_config = self.config.get("task_config", {}).get("monthly_task", {})
        else:
            task_config = self.config.get("task_config", {}).get("daily_task", {})

        video_fields_config = task_config.get("video_fields", {})

        # 检查是否启用视频信息收集
        if not video_fields_config.get("enabled", True):
            return {}

        stats_fields_config = video_fields_config.get("stats_fields", {})

        field_mapping = {
            "aid": video_basic.get("aid"),
            "bvid": video_basic.get("bvid"),
            "title": video_basic.get("title"),
            "description": video_basic.get("description", ""),
            "duration": self._format_duration(video_basic.get("length", 0)),
            "publish_time": self._format_timestamp(video_basic.get("created", 0)),
            "view": video_basic.get("play", 0),
            "danmaku": video_basic.get("video_review", 0),
        }

        video_data = {}

        # 添加基础字段（排除enabled和stats_fields）
        for field, enabled in video_fields_config.items():
            if field not in ["enabled", "stats_fields"] and enabled and field in field_mapping:
                video_data[field] = field_mapping[field]

        # 添加统计字段（如果启用）
        if stats_fields_config.get("enabled", True):
            for field, enabled in stats_fields_config.items():
                if field != "enabled" and enabled and field in field_mapping:
                    video_data[field] = field_mapping[field]

        return video_data

    def _format_duration(self, seconds: int) -> str:
        """
        将秒数转换为可读的时长格式
        Args:
            seconds: 秒数
        Returns:
            str: 格式化的时长，如 "1:23:45" 或 "12:34"
        """
        if not seconds or seconds <= 0:
            return "00:00"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def _format_timestamp(self, timestamp: int) -> str:
        """
        将时间戳转换为可读的时间格式
        Args:
            timestamp: Unix时间戳
        Returns:
            str: ISO格式的时间字符串
        """
        if not timestamp or timestamp <= 0:
            return ""

        try:
            return datetime.fromtimestamp(timestamp).isoformat()
        except Exception as e:
            self.logger.warning(f"时间戳转换失败 {timestamp}: {e}")
            return ""
        
    async def get_hot_comments(self, video_aid: str) -> List[Dict]:
        """获取视频的热门评论（带重试机制）"""
        # 根据任务类型获取配置
        if self.task_type == "monthly":
            task_config = self.config.get("task_config", {}).get("monthly_task", {})
        else:
            task_config = self.config.get("task_config", {}).get("daily_task", {})

        comments_config = task_config.get("hot_comments_json", {})

        if not comments_config.get("enabled", False):
            return []
        
        max_comments = comments_config.get("max_count", 10)
        comment_fields = comments_config.get("fields", ["message", "mid", "uname", "ctime", "like", "rcount"])
        
        max_attempts = self.config.get("system", {}).get("retry", {}).get("max_attempts", 3)
        retry_delay = self.config.get("system", {}).get("retry", {}).get("delay_between_retries", 5)
        
        for attempt in range(max_attempts):
            try:
                comments_response = await self.bili_client.get_video_comments(
                    video_id=video_aid,
                    order_mode=CommentOrderType.DEFAULT,
                    next=0
                )
                
                if not comments_response or "replies" not in comments_response:
                    return []
                
                hot_comments = []
                replies = comments_response.get("replies", [])
                
                for reply in replies[:max_comments]:
                    comment_data = {}

                    # 根据配置的字段提取数据
                    if "message" in comment_fields:
                        comment_data["message"] = reply.get("content", {}).get("message", "")
                    if "mid" in comment_fields:
                        comment_data["mid"] = reply.get("member", {}).get("mid", "")
                    if "ctime" in comment_fields:
                        # 转换时间戳为可读格式
                        ctime_timestamp = reply.get("ctime", 0)
                        if ctime_timestamp:
                            comment_data["ctime"] = datetime.fromtimestamp(ctime_timestamp).isoformat()
                        else:
                            comment_data["ctime"] = ""
                    if "like" in comment_fields:
                        comment_data["like"] = reply.get("like", 0)
                    if "rcount" in comment_fields:
                        comment_data["rcount"] = reply.get("rcount", 0)

                    hot_comments.append(comment_data)
                
                self.logger.info(f"获取热门评论成功: AV{video_aid} ({len(hot_comments)}条)")
                self.stats["comments_collected"] += len(hot_comments)
                return hot_comments
                
            except Exception as e:
                self.logger.warning(f"获取热门评论失败 AV{video_aid} (尝试 {attempt + 1}/{max_attempts}): {e}")
                self.stats["retries"] += 1
                
                if attempt < max_attempts - 1:
                    self.logger.info(f"等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                else:
                    self.logger.error(f"获取热门评论最终失败 AV{video_aid}")
                    self.stats["errors"] += 1
        
        return []

    async def process_videos_for_timerange(self, up_id: str, up_info: Dict) -> List[Dict]:
        """处理指定时间范围内的视频"""
        # 根据任务类型获取时间范围配置
        if self.task_type == "monthly":
            time_config = self.config.get("task_config", {}).get("monthly_task", {}).get("time_range", {})
        else:
            time_config = self.config.get("task_config", {}).get("daily_task", {}).get("time_range", {})

        if "start_date" in time_config and "end_date" in time_config:
            start_date = time_config["start_date"]
            end_date = time_config["end_date"]
        else:
            days = time_config.get("days", 28)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        pubtime_begin_s, pubtime_end_s = get_pubtime_datetime(start_date, end_date)

        self.logger.info(f"开始处理时间范围: {start_date} 到 {end_date}")

        all_videos = []
        page = 1

        while True:
            try:
                # 获取UP主视频列表
                response = await self.bili_client.get_creator_videos(
                    creator_id=up_id,
                    pn=page,
                    ps=30,
                    order_mode=SearchOrderType.LAST_PUBLISH
                )

                if not response or not response.get("list", {}).get("vlist"):
                    self.logger.info(f"第{page}页无更多视频数据")
                    break

                videos = response["list"]["vlist"]

                # 过滤时间范围内的视频
                time_range_videos = []
                for video in videos:
                    video_time = video.get("created", 0)

                    # 检查视频是否在时间范围内
                    if int(pubtime_begin_s) <= video_time <= int(pubtime_end_s):
                        time_range_videos.append(video)
                    elif video_time < int(pubtime_begin_s):
                        # 视频时间早于范围，停止处理
                        break

                if not time_range_videos:
                    break

                # 处理每个视频
                for video_basic in time_range_videos:
                    try:
                        # 获取视频详细信息
                        video_data = await self.get_video_info(video_basic)

                        # 获取热门评论
                        video_aid = str(video_data.get("aid", ""))
                        if video_aid:
                            hot_comments = await self.get_hot_comments(video_aid)

                            # 添加评论数据
                            if hot_comments:
                                video_data["hot_comments"] = hot_comments

                        all_videos.append(video_data)
                        self.stats["videos_processed"] += 1

                        # 请求延时
                        request_delay = self.config.get("system", {}).get("request_delay", 2)
                        await asyncio.sleep(request_delay)

                    except Exception as e:
                        self.logger.error(f"处理视频失败: {e}")
                        self.stats["errors"] += 1
                        continue

                page += 1

            except Exception as e:
                self.logger.error(f"获取第{page}页视频时出错: {e}")
                self.stats["errors"] += 1
                break

        self.logger.info(f"视频处理完成，共处理 {len(all_videos)} 个视频")
        return all_videos

    async def process_videos_for_monthly_task(self, up_id: str, up_info: Dict) -> List[Dict]:
        """
        月任务视频处理：获取全量视频数据（不限制时间范围）
        Args:
            up_id: UP主ID
            up_info: UP主信息
        Returns:
            List[Dict]: 全量视频列表
        """
        from datetime import datetime, timedelta

        self.logger.info("月任务：开始获取全量视频数据（不限制时间范围）")

        # 获取月任务配置
        monthly_config = self.config.get("task_config", {}).get("monthly_task", {})
        time_range_config = monthly_config.get("time_range", {})

        # 检查是否配置为全量获取
        get_all_videos = time_range_config.get("get_all_videos", False)
        filter_days = time_range_config.get("filter_days", 28)

        if get_all_videos:
            self.logger.info("月任务：按配置获取全量视频数据（不限制时间范围）")
            filter_timestamp = None  # 不进行时间筛选
        else:
            # 如果配置为非全量，则按天数筛选
            now = datetime.now()
            filter_date = now - timedelta(days=filter_days)
            filter_timestamp = int(filter_date.timestamp())
            self.logger.info(f"月任务：按配置筛选 {filter_days} 天内的视频（{filter_date.strftime('%Y-%m-%d')} 之后）")

        # 获取全量视频（不限制时间范围）
        all_videos = []
        page = 1

        while True:
            try:
                self.logger.info(f"正在获取第 {page} 页视频...")

                # 使用BilibiliClient的get_creator_videos方法
                # 这个方法已经正确处理了WBI签名
                response = await self.bili_client.get_creator_videos(
                    creator_id=up_id,
                    pn=page,
                    ps=50
                )
                # get_creator_videos返回的是data部分，不包含code字段
                data = response

                # 检查是否有数据
                if not data:
                    self.logger.error("API请求失败: 返回数据为空")
                    break

                videos_data = data.get("list", {}).get("vlist", [])

                if not videos_data:
                    self.logger.info("没有更多视频数据")
                    break

                # 处理当前页的视频
                for video_basic in videos_data:
                    # 如果配置了时间筛选，则检查视频发布时间
                    if filter_timestamp is not None:
                        video_pubdate = video_basic.get("created", 0)
                        if video_pubdate < filter_timestamp:
                            self.logger.info(f"视频 {video_basic.get('title', 'Unknown')} 发布时间超出范围，停止获取")
                            return all_videos  # 由于视频是按时间倒序的，可以直接返回

                    # 获取视频详细信息
                    video_info = await self.get_video_info(video_basic)
                    if video_info:
                        all_videos.append(video_info)
                        self.stats["videos_processed"] += 1

                page += 1

                # 添加延时避免请求过频
                delay = self.config.get("system", {}).get("request_delay", 2)
                await asyncio.sleep(delay)

            except Exception as e:
                self.logger.error(f"获取第{page}页视频时出错: {e}")
                self.stats["errors"] += 1
                break

        if filter_timestamp is None:
            self.logger.info(f"月任务视频处理完成，共处理 {len(all_videos)} 个视频（全量）")
        else:
            self.logger.info(f"月任务视频处理完成，共处理 {len(all_videos)} 个视频（{filter_days}天内）")
        return all_videos

    async def run_task(self) -> Dict:
        """运行任务（支持日任务和月任务）"""
        start_time = datetime.now()

        try:
            # 获取UP主ID（从task_config中获取）
            up_id = self.config.get("task_config", {}).get("up_id")
            if not up_id:
                raise ValueError("未配置UP主ID")

            task_name = "月任务" if self.task_type == "monthly" else "日任务"
            self.logger.info(f"开始执行{task_name}，UP主ID: {up_id}")

            # 1. 获取UP主信息
            up_info = await self.get_up_info(up_id)
            if not up_info:
                raise Exception("获取UP主信息失败")

            # 2. 处理视频数据（根据任务类型）
            if self.task_type == "monthly":
                videos = await self.process_videos_for_monthly_task(up_id, up_info)
            else:
                videos = await self.process_videos_for_timerange(up_id, up_info)

            # 3. 构建最终数据结构
            result_data = {
                "task_info": {
                    "up_id": up_id,
                    "collection_time": start_time.isoformat(),
                    "time_range": self._get_time_range_info(),
                    "config": self._get_config_summary()
                },
                "up_info": up_info,  # UP主信息只在开头出现一次
                "videos": videos,    # 视频列表，每个视频不重复UP主信息
                "statistics": {
                    "total_videos": len(videos),
                    "total_comments": self.stats["comments_collected"],
                    "collection_start_time": start_time.isoformat(),
                    "collection_end_time": datetime.now().isoformat(),
                    "time_range": self._get_time_range_info(),
                    "errors_count": self.stats["errors"],
                    "retries_count": self.stats["retries"],
                    "duration_seconds": (datetime.now() - start_time).total_seconds()
                }
            }

            # 4. 统一存储：JSON + 数据库同时保存
            await self._store_data_unified(up_id, up_info, videos)

            # 5. 月任务后处理：提取前28天数据作为日任务存储
            if self.task_type == "monthly":
                await self._post_process_monthly_task(up_id, up_info, videos)

            return result_data

        except Exception as e:
            task_name = "月任务" if self.task_type == "monthly" else "日任务"
            self.logger.error(f"{task_name}执行失败: {e}")
            raise
        finally:
            await self.close()

    async def run_daily_task(self) -> Dict:
        """运行日任务（兼容方法）"""
        return await self.run_task()

    def _get_time_range_info(self) -> Dict:
        """获取时间范围信息"""
        # 根据任务类型获取配置
        if self.task_type == "monthly":
            time_config = self.config.get("task_config", {}).get("monthly_task", {}).get("time_range", {})
        else:
            time_config = self.config.get("task_config", {}).get("daily_task", {}).get("time_range", {})

        if "start_date" in time_config and "end_date" in time_config:
            return {
                "start_date": time_config["start_date"],
                "end_date": time_config["end_date"]
            }
        else:
            days = time_config.get("days", 28)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            return {
                "start_date": start_date,
                "end_date": end_date
            }

    def _get_config_summary(self) -> Dict:
        """获取配置摘要"""
        # 根据任务类型获取配置
        if self.task_type == "monthly":
            task_config = self.config.get("task_config", {}).get("monthly_task", {})
        else:
            task_config = self.config.get("task_config", {}).get("daily_task", {})

        up_fields_config = task_config.get("up_fields", {})
        video_fields_config = task_config.get("video_fields", {})
        stats_fields_config = video_fields_config.get("stats_fields", {})
        comments_config = task_config.get("hot_comments_json", {})

        return {
            "enabled_fields": {
                "up_info": up_fields_config.get("enabled", True),
                "video_info": video_fields_config.get("enabled", True),
                "stats_info": stats_fields_config.get("enabled", True),
                "comments": comments_config.get("enabled", False)
            },
            "field_counts": {
                "up_fields": sum(1 for k, v in up_fields_config.items() if k != "enabled" and v),
                "video_fields": sum(1 for k, v in video_fields_config.items() if k not in ["enabled", "stats_fields"] and v),
                "stats_fields": sum(1 for k, v in stats_fields_config.items() if k != "enabled" and v),
                "comment_fields": len(comments_config.get("fields", []))
            },
            "max_comments": comments_config.get("max_count", 10),
            "request_delay": self.config.get("system", {}).get("request_delay", 2)
        }



    async def _store_data_simple(self, up_id: str, up_info: Dict, videos: List[Dict]):
        """使用简单存储架构存储数据（备用方案）"""
        try:
            # 4. 初始化存储任务
            time_range_info = self._get_time_range_info()
            self.storage.init_task(up_id, time_range_info, self.config)

            # 5. 存储UP主信息
            self.storage.store_up_info(up_info)

            # 6. 存储视频数据
            for video in videos:
                self.storage.store_video(video)

            # 7. 完成任务并保存
            filename = self.storage.finalize_task()
            self.logger.info(f"数据保存成功: {filename}")

        except Exception as e:
            self.logger.error(f"简单存储过程中出错: {e}")
            raise

    def _parse_duration(self, duration_str: str) -> int:
        """解析时长字符串为秒数"""
        try:
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 2:  # MM:SS
                    return int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:  # HH:MM:SS
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return int(duration_str)
        except (ValueError, IndexError):
            return 0

    def _parse_publish_time(self, publish_time_str: str) -> Optional[int]:
        """解析发布时间字符串为时间戳"""
        try:
            if publish_time_str:
                # 处理ISO格式时间字符串
                dt = datetime.fromisoformat(publish_time_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
            return None
        except (ValueError, TypeError):
            return None

    def _get_unique_filename(self, base_filename: str) -> str:
        """
        获取唯一的文件名，如果文件已存在则添加序号

        Args:
            base_filename: 基础文件名

        Returns:
            唯一的文件名
        """
        if not os.path.exists(base_filename):
            return base_filename

        # 分离文件名和扩展名
        name, ext = os.path.splitext(base_filename)
        counter = 1

        while True:
            new_filename = f"{name}({counter}){ext}"
            if not os.path.exists(new_filename):
                return new_filename
            counter += 1



    async def _post_process_monthly_task(self, up_id: str, up_info: Dict, all_videos: List[Dict]):
        """
        月任务后处理：从全量数据中提取前28天的数据，作为当天的日任务存储

        Args:
            up_id: UP主ID
            up_info: UP主信息
            all_videos: 全量视频数据
        """
        try:
            self.logger.info("开始月任务后处理：提取前28天数据作为日任务存储")

            # 获取配置
            monthly_config = self.config.get("task_config", {}).get("monthly_task", {})
            filter_days = monthly_config.get("time_range", {}).get("filter_days", 28)

            # 计算28天前的时间戳
            now = datetime.now()
            filter_date = now - timedelta(days=filter_days)
            filter_timestamp = int(filter_date.timestamp())

            # 从全量数据中筛选前28天的视频
            recent_videos = []
            for video in all_videos:
                # 解析视频发布时间
                publish_time_str = video.get('publish_time', '')
                if publish_time_str:
                    try:
                        # 假设publish_time是ISO格式字符串
                        publish_time = datetime.fromisoformat(publish_time_str.replace('Z', '+00:00'))
                        publish_timestamp = int(publish_time.timestamp())

                        if publish_timestamp >= filter_timestamp:
                            recent_videos.append(video)
                    except (ValueError, TypeError):
                        # 如果时间解析失败，跳过这个视频
                        continue

            self.logger.info(f"从 {len(all_videos)} 个全量视频中筛选出 {len(recent_videos)} 个前{filter_days}天的视频")

            if recent_videos:
                # 创建日任务格式的数据
                daily_task_data = {
                    "task_info": {
                        "task_type": "daily_extracted_from_monthly",
                        "task_id": f"daily_extracted_{now.strftime('%Y%m%d_%H%M%S')}",
                        "up_id": up_id,
                        "collection_time": now.isoformat(),
                        "extracted_from_monthly": True,
                        "filter_days": filter_days,
                        "config": self._get_config_summary()
                    },
                    "up_info": up_info,
                    "videos": recent_videos,
                    "statistics": {
                        "total_videos": len(recent_videos),
                        "total_comments": sum(len(video.get('comments', [])) for video in recent_videos),
                        "extraction_time": now.isoformat(),
                        "source_total_videos": len(all_videos),
                        "filter_days": filter_days,
                        "time_range": {
                            "start_date": filter_date.strftime("%Y-%m-%d"),
                            "end_date": now.strftime("%Y-%m-%d"),
                            "days": filter_days
                        }
                    }
                }

                self.logger.info(f"月任务后处理完成：已提取并筛选出 {len(recent_videos)} 个前{filter_days}天的视频")
            else:
                self.logger.info(f"前{filter_days}天内没有新视频，跳过日任务数据提取")

        except Exception as e:
            self.logger.error(f"月任务后处理失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    processor = DailyTaskProcessor()

    try:
        await processor.initialize()
        result = await processor.run_daily_task()
        print(f"任务完成！处理了 {result['statistics']['total_videos']} 个视频")

    except Exception as e:
        print(f"任务执行失败: {e}")
        return 1

    return 0





if __name__ == "__main__":
    exit_code = asyncio.run(main())
