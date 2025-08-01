#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一Cookie管理器
整合自动管理、增强管理、智能池等功能的统一接口
"""

import os
import json
import glob
import time
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from playwright.async_api import BrowserContext

from bilibili_core.utils.logger import get_logger
from .cookie_utils import (
    CookieValidator, CookieParser, ConfigUtils, 
    CookieStatus, EnvironmentDetector
)

logger = get_logger()


@dataclass
class CookieInfo:
    """Cookie信息数据类"""
    name: str
    cookie: str
    priority: int = 1
    enabled: bool = True
    last_used: str = ""
    failure_count: int = 0
    max_failures: int = 3
    last_health_check: str = ""
    health_status: str = "unknown"  # unknown, healthy, unhealthy


class UnifiedCookieManager:
    """统一Cookie管理器"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml", 
                 raw_cookie: str = "", backup_cookies_dir: str = "data/backup_cookies"):
        self.config_file = config_file
        self.raw_cookie = raw_cookie.strip()
        self.backup_cookies_dir = backup_cookies_dir
        self.config = None
        
        # Cookie池相关
        self.cookie_pool: List[CookieInfo] = []
        self.current_index = 0  # 用于轮询模式
        self.last_health_check = 0
        
        # 当前使用的Cookie
        self.current_cookies: List[Dict] = []
        self.current_cookie_dict: Dict[str, str] = {}
        self.current_source = ""
        self.last_check_time = 0
        
        # 确保备用Cookie目录存在（本地环境）
        if (backup_cookies_dir and backup_cookies_dir.strip() and 
            EnvironmentDetector.is_local_environment()):
            os.makedirs(backup_cookies_dir, exist_ok=True)
        
        # 初始化
        self.load_config()
        self._initialize_cookie_pool()
    
    def load_config(self) -> bool:
        """加载配置文件"""
        self.config = ConfigUtils.load_yaml_config(self.config_file)
        
        # 在GitHub Actions环境中，检查是否需要从环境变量加载Cookie
        if EnvironmentDetector.is_github_actions() and self.config:
            self._load_cookies_from_env()
            
        return self.config is not None
    
    def _load_cookies_from_env(self):
        """从环境变量加载Cookie（GitHub Actions环境）"""
        try:
            # 确保配置结构存在
            if "login" not in self.config:
                self.config["login"] = {}
            if "cookies" not in self.config["login"]:
                self.config["login"]["cookies"] = {}
            if "cookie_pool" not in self.config["login"]["cookies"]:
                self.config["login"]["cookies"]["cookie_pool"] = {
                    "enabled": True,
                    "selection_mode": "random",
                    "cookies": []
                }
            
            pool_config = self.config["login"]["cookies"]["cookie_pool"]
            
            # 检查环境变量中的Cookie
            env_cookies = []
            
            # 主Cookie
            main_cookie = os.environ.get("BILIBILI_COOKIES")
            if main_cookie:
                env_cookies.append({
                    "name": "main",
                    "cookie": main_cookie,
                    "priority": 1,
                    "enabled": True,
                    "last_used": "",
                    "failure_count": 0,
                    "max_failures": 3
                })
            
            # 备用Cookie池 (BILIBILI_COOKIES_1 到 BILIBILI_COOKIES_10)
            for i in range(1, 11):
                env_key = f"BILIBILI_COOKIES_{i}"
                cookie_value = os.environ.get(env_key)
                if cookie_value:
                    env_cookies.append({
                        "name": f"env_cookie_{i}",
                        "cookie": cookie_value,
                        "priority": i + 1,
                        "enabled": True,
                        "last_used": "",
                        "failure_count": 0,
                        "max_failures": 3
                    })
            
            if env_cookies:
                # 启用Cookie池并设置从环境变量加载的Cookie
                pool_config["enabled"] = True
                pool_config["cookies"] = env_cookies
                logger.info(f"从环境变量加载了 {len(env_cookies)} 个Cookie")
            else:
                logger.warning("GitHub Actions环境中未找到Cookie环境变量")
                
        except Exception as e:
            logger.error(f"从环境变量加载Cookie失败: {e}")
    
    def _initialize_cookie_pool(self):
        """初始化Cookie池"""
        if not self.config:
            return
        
        cookies_config = self.config.get("login", {}).get("cookies", {})
        pool_config = cookies_config.get("cookie_pool", {})
        
        if not pool_config.get("enabled", False):
            # 使用单个Cookie（向后兼容）
            raw_cookie = cookies_config.get("raw_cookie", "") or self.raw_cookie
            if raw_cookie:
                self.cookie_pool = [CookieInfo(
                    name="default",
                    cookie=raw_cookie,
                    priority=1,
                    enabled=True
                )]
                logger.info("使用单个Cookie模式")
            return
        
        # 加载Cookie池
        pool_cookies = pool_config.get("cookies", [])
        for cookie_data in pool_cookies:
            if cookie_data.get("enabled", True) and cookie_data.get("cookie"):
                cookie_info = CookieInfo(
                    name=cookie_data.get("name", "unknown"),
                    cookie=cookie_data["cookie"],
                    priority=cookie_data.get("priority", 1),
                    enabled=cookie_data.get("enabled", True),
                    last_used=cookie_data.get("last_used", ""),
                    failure_count=cookie_data.get("failure_count", 0),
                    max_failures=cookie_data.get("max_failures", 3)
                )
                self.cookie_pool.append(cookie_info)
        
        logger.info(f"Cookie池初始化完成: {len(self.cookie_pool)}个可用Cookie")
    
    def get_available_cookies(self) -> List[CookieInfo]:
        """获取可用的Cookie列表"""
        return [c for c in self.cookie_pool if c.enabled and c.failure_count < c.max_failures]
    
    def select_cookie(self) -> Optional[CookieInfo]:
        """根据配置的选择模式选择Cookie"""
        available_cookies = self.get_available_cookies()
        
        if not available_cookies:
            logger.error("没有可用的Cookie")
            return None
        
        pool_config = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})
        selection_mode = pool_config.get("selection_mode", "random")
        
        if selection_mode == "random":
            import random
            selected = random.choice(available_cookies)
            logger.info(f"随机选择Cookie: {selected.name}")
        elif selection_mode == "round_robin":
            if self.current_index >= len(available_cookies):
                self.current_index = 0
            selected = available_cookies[self.current_index]
            self.current_index += 1
            logger.info(f"轮询选择Cookie: {selected.name}")
        elif selection_mode == "priority":
            sorted_cookies = sorted(available_cookies, key=lambda x: x.priority)
            selected = sorted_cookies[0]
            logger.info(f"优先级选择Cookie: {selected.name} (优先级: {selected.priority})")
        else:
            logger.warning(f"未知的选择模式: {selection_mode}，使用随机模式")
            import random
            selected = random.choice(available_cookies)
        
        return selected
    
    def load_cookies(self) -> bool:
        """
        按优先级加载Cookie
        优先级：Cookie池 > 原始Cookie > 最新备用Cookie文件
        """
        # 1. 优先尝试Cookie池
        if self.cookie_pool:
            selected_cookie = self.select_cookie()
            if selected_cookie:
                logger.info(f"使用Cookie池中的Cookie: {selected_cookie.name}")
                self.current_cookies = CookieParser.parse_raw_cookie(selected_cookie.cookie)
                if self.current_cookies:
                    self.current_cookie_dict = CookieParser.cookies_to_dict(self.current_cookies)
                    self.current_source = f"cookie_pool:{selected_cookie.name}"
                    self.last_check_time = time.time()
                    logger.info(f"Cookie池Cookie加载成功: {len(self.current_cookies)}个")
                    return True

        # 2. 尝试原始Cookie（向后兼容）
        if self.raw_cookie and CookieValidator.validate_raw_cookie(self.raw_cookie):
            logger.info("使用配置文件中的原始Cookie")
            self.current_cookies = CookieParser.parse_raw_cookie(self.raw_cookie)
            if self.current_cookies:
                self.current_cookie_dict = CookieParser.cookies_to_dict(self.current_cookies)
                self.current_source = "raw_cookie"
                self.last_check_time = time.time()
                logger.info(f"原始Cookie加载成功: {len(self.current_cookies)}个")
                return True

        # 3. 尝试最新的备用Cookie文件
        latest_backup = self._get_latest_backup_cookie_file()
        if latest_backup and self._load_backup_cookie_file(latest_backup):
            return True

        # 4. 都没有找到有效Cookie
        logger.info("未找到有效的Cookie，需要重新登录")
        return False
    
    def _get_latest_backup_cookie_file(self) -> Optional[str]:
        """获取最新的备用Cookie文件"""
        try:
            if not self.backup_cookies_dir or not self.backup_cookies_dir.strip():
                return None
            
            pattern = os.path.join(self.backup_cookies_dir, "cookies_*.json")
            cookie_files = glob.glob(pattern)
            
            if not cookie_files:
                return None
            
            latest_file = max(cookie_files, key=os.path.getmtime)
            logger.info(f"找到最新备用Cookie文件: {latest_file}")
            return latest_file
            
        except Exception as e:
            logger.error(f"查找备用Cookie文件失败: {e}")
            return None
    
    def _load_backup_cookie_file(self, file_path: str) -> bool:
        """加载备用Cookie文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            self.current_cookies = cookie_data.get('cookies', [])
            self.last_check_time = cookie_data.get('last_check_time', 0)
            
            if not self.current_cookies:
                logger.warning(f"备用Cookie文件为空: {file_path}")
                return False
            
            self.current_cookie_dict = CookieParser.cookies_to_dict(self.current_cookies)
            self.current_source = f"backup_file:{os.path.basename(file_path)}"
            
            logger.info(f"成功加载备用Cookie文件: {len(self.current_cookies)}个Cookie")
            return True
            
        except Exception as e:
            logger.error(f"加载备用Cookie文件失败 {file_path}: {e}")
            return False
    
    def save_backup_cookie_file(self, cookies: List[Dict]) -> str:
        """保存Cookie到备用文件（GitHub Actions环境中跳过）"""
        if EnvironmentDetector.is_github_actions():
            logger.info("🎭 GitHub Actions环境：跳过本地Cookie备份文件保存")
            return ""
        
        try:
            if not self.backup_cookies_dir or not self.backup_cookies_dir.strip():
                logger.info("备份目录未配置，跳过Cookie备份")
                return ""
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cookies_{timestamp}.json"
            filepath = os.path.join(self.backup_cookies_dir, filename)
            
            cookie_data = {
                "cookies": cookies,
                "last_check_time": time.time(),
                "created_time": datetime.now().isoformat(),
                "source": "login_scan"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功保存备用Cookie文件: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存备用Cookie文件失败: {e}")
            raise
    
    def save_cookies_after_login(self, cookies: List[Dict]) -> str:
        """登录后保存Cookie"""
        try:
            # 尝试保存到备用文件
            filepath = self.save_backup_cookie_file(cookies)

            # 更新当前Cookie
            self.current_cookies = cookies
            self.current_cookie_dict = CookieParser.cookies_to_dict(cookies)
            self.last_check_time = time.time()
            
            if filepath:
                self.current_source = f"backup_file:{os.path.basename(filepath)}"
                logger.info(f"登录后Cookie已保存到文件: {len(cookies)}个")
            else:
                self.current_source = "github_actions_memory"
                logger.info(f"登录后Cookie已更新到内存: {len(cookies)}个（GitHub Actions环境）")
            
            return filepath

        except Exception as e:
            logger.error(f"保存登录后Cookie失败: {e}")
            raise
    
    def is_cookie_expired(self, check_interval_hours: int = 24) -> bool:
        """检查Cookie是否过期"""
        if not self.current_cookies:
            return True
        
        current_time = time.time()
        time_diff_hours = (current_time - self.last_check_time) / 3600
        
        if time_diff_hours >= check_interval_hours:
            logger.info(f"Cookie已超过检查间隔 ({time_diff_hours:.1f}小时)，需要验证")
            return True
        
        # 检查Cookie的过期时间
        for cookie in self.current_cookies:
            if 'expires' in cookie and cookie['expires'] > 0:
                if cookie['expires'] < current_time:
                    logger.info(f"Cookie已过期: {cookie['name']}")
                    return True
        
        logger.info(f"Cookie仍然有效 (距离上次检查 {time_diff_hours:.1f}小时，来源: {self.current_source})")
        return False
    
    async def validate_cookies(self, browser_context: BrowserContext) -> bool:
        """验证Cookie是否仍然有效"""
        try:
            await browser_context.add_cookies(self.current_cookies)
            page = await browser_context.new_page()
            await page.goto("https://www.bilibili.com")
            await page.wait_for_timeout(3000)

            try:
                user_info = await page.locator(".header-avatar-wrap, .nav-user-info").first.is_visible(timeout=5000)
                if user_info:
                    logger.info("Cookie验证成功，用户已登录")
                    self.last_check_time = time.time()
                    await page.close()
                    return True
                else:
                    logger.warning("Cookie验证失败，未检测到登录状态")
                    await page.close()
                    return False

            except Exception as e:
                logger.warning(f"Cookie验证过程中检查登录状态失败: {e}")
                await page.close()
                return False

        except Exception as e:
            logger.error(f"Cookie验证过程出错: {e}")
            return False
    
    async def health_check_cookie(self, cookie_info: CookieInfo) -> bool:
        """对单个Cookie进行健康检查"""
        smart_config = self.config.get("login", {}).get("smart_expiry_detection", {})
        endpoints = smart_config.get("health_check_endpoints", [
            "https://api.bilibili.com/x/web-interface/nav"
        ])
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": cookie_info.cookie,
            "Referer": "https://www.bilibili.com"
        }
        
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("code") == 0 and data.get("data", {}).get("isLogin"):
                                cookie_info.health_status = "healthy"
                                cookie_info.last_health_check = datetime.now().isoformat()
                                logger.info(f"Cookie健康检查通过: {cookie_info.name}")
                                return True
                        else:
                            logger.warning(f"Cookie健康检查失败: {cookie_info.name} (HTTP {response.status})")
                            
            except Exception as e:
                logger.warning(f"Cookie健康检查异常: {cookie_info.name} - {e}")
        
        cookie_info.health_status = "unhealthy"
        cookie_info.last_health_check = datetime.now().isoformat()
        return False
    
    def mark_cookie_used(self, cookie_info: CookieInfo, success: bool = True):
        """标记Cookie使用结果"""
        cookie_info.last_used = datetime.now().isoformat()
        
        if success:
            cookie_info.failure_count = 0
            cookie_info.health_status = "healthy"
            logger.info(f"Cookie使用成功: {cookie_info.name}")
        else:
            cookie_info.failure_count += 1
            cookie_info.health_status = "unhealthy"
            logger.warning(f"Cookie使用失败: {cookie_info.name} (失败次数: {cookie_info.failure_count}/{cookie_info.max_failures})")
            
            if cookie_info.failure_count >= cookie_info.max_failures:
                smart_config = self.config.get("login", {}).get("smart_expiry_detection", {})
                if smart_config.get("auto_disable_failed", True):
                    cookie_info.enabled = False
                    logger.error(f"Cookie已自动禁用: {cookie_info.name} (失败次数过多)")
    
    @property
    def cookies(self) -> List[Dict]:
        """向后兼容的cookies属性"""
        return self.current_cookies
    
    def get_cookie_string(self) -> str:
        """获取当前Cookie字符串"""
        return CookieParser.cookies_to_string(self.current_cookies)
    
    def get_cookie_dict(self) -> Dict[str, str]:
        """获取当前Cookie字典"""
        return self.current_cookie_dict.copy()
    
    def get_comprehensive_status(self) -> Dict:
        """获取综合状态信息"""
        # Cookie池状态
        pool_status = {
            "total_cookies": len(self.cookie_pool),
            "available_cookies": len(self.get_available_cookies()),
            "disabled_cookies": len([c for c in self.cookie_pool if not c.enabled]),
            "failed_cookies": len([c for c in self.cookie_pool if c.failure_count >= c.max_failures]),
            "healthy_cookies": len([c for c in self.cookie_pool if c.health_status == "healthy"]),
        }
        
        # 当前Cookie状态
        current_status = {
            "has_cookies": len(self.current_cookies) > 0,
            "cookie_count": len(self.current_cookies),
            "current_source": self.current_source,
            "last_check_time": datetime.fromtimestamp(self.last_check_time).isoformat() if self.last_check_time else None,
            "backup_files_count": 0
        }
        
        # 备份文件统计
        if self.backup_cookies_dir and self.backup_cookies_dir.strip():
            pattern = os.path.join(self.backup_cookies_dir, "cookies_*.json")
            current_status["backup_files_count"] = len(glob.glob(pattern))
        
        return {
            "pool_status": pool_status,
            "current_status": current_status,
            "environment": "github_actions" if EnvironmentDetector.is_github_actions() else "local"
        }
    
    def display_status_report(self):
        """显示综合状态报告"""
        status = self.get_comprehensive_status()
        pool_status = status["pool_status"]
        current_status = status["current_status"]
        
        print("=" * 60)
        print("🍪 统一Cookie管理器状态报告")
        print("=" * 60)
        
        # Cookie池状态
        print("📊 Cookie池状态:")
        print(f"   总Cookie数量: {pool_status['total_cookies']}")
        print(f"   可用Cookie数量: {pool_status['available_cookies']}")
        print(f"   健康Cookie数量: {pool_status['healthy_cookies']}")
        print(f"   禁用Cookie数量: {pool_status['disabled_cookies']}")
        print(f"   失败Cookie数量: {pool_status['failed_cookies']}")
        
        # 当前Cookie状态
        print(f"\n🎯 当前Cookie状态:")
        print(f"   是否有Cookie: {'✅' if current_status['has_cookies'] else '❌'}")
        print(f"   Cookie数量: {current_status['cookie_count']}")
        print(f"   Cookie源: {current_status['current_source']}")
        print(f"   备份文件数量: {current_status['backup_files_count']}")
        
        # 环境信息
        print(f"\n🌍 运行环境: {status['environment']}")
        
        # 状态提醒
        if pool_status['available_cookies'] < 2:
            print("\n⚠️  警告: 可用Cookie数量不足2个，建议及时补充！")
        elif not current_status['has_cookies']:
            print("\n⚠️  警告: 当前没有加载任何Cookie，需要重新登录！")
        else:
            print("\n✨ Cookie状态良好，系统运行正常")
        
        print("=" * 60)
    
    def cleanup_old_backup_files(self, keep_count: int = 5):
        """清理旧的备用Cookie文件"""
        if EnvironmentDetector.is_github_actions():
            logger.info("🎭 GitHub Actions环境：跳过备份文件清理")
            return
        
        try:
            if not self.backup_cookies_dir or not self.backup_cookies_dir.strip():
                return
            
            pattern = os.path.join(self.backup_cookies_dir, "cookies_*.json")
            cookie_files = glob.glob(pattern)

            if len(cookie_files) <= keep_count:
                return

            cookie_files.sort(key=os.path.getmtime, reverse=True)
            files_to_delete = cookie_files[keep_count:]
            
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    logger.info(f"已删除旧的备用Cookie文件: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {e}")

        except Exception as e:
            logger.error(f"清理备用Cookie文件失败: {e}")