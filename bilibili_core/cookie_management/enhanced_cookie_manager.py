#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版Cookie管理器
支持原始Cookie字符串、备用Cookie文件管理等功能
"""

import json
import os
import time
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from bilibili_core.utils.logger import get_logger
from playwright.async_api import BrowserContext
from .smart_cookie_pool import SmartCookiePool

logger = get_logger()


class EnhancedCookieManager:
    """增强版Cookie管理器"""
    
    def __init__(self, config: Dict = None, raw_cookie: str = "", backup_cookies_dir: str = "data/backup_cookies",
                 check_interval_hours: int = 24):
        self.config = config or {}
        self.raw_cookie = raw_cookie.strip()
        self.backup_cookies_dir = backup_cookies_dir
        self.check_interval_hours = check_interval_hours

        self.cookies = []
        self.cookie_dict = {}
        self.last_check_time = 0
        self.current_source = ""  # 记录当前Cookie来源

        # 初始化智能Cookie池
        self.cookie_pool = SmartCookiePool(self.config) if self.config else None

        # 确保备用Cookie目录存在（仅在路径非空时创建）
        if backup_cookies_dir and backup_cookies_dir.strip():
            os.makedirs(backup_cookies_dir, exist_ok=True)
        
    def parse_raw_cookie(self, raw_cookie: str) -> List[Dict]:
        """
        解析原始Cookie字符串
        Args:
            raw_cookie: 原始Cookie字符串，格式：name1=value1; name2=value2
        Returns:
            List[Dict]: Cookie列表
        """
        cookies = []
        
        if not raw_cookie:
            return cookies
            
        try:
            # 分割Cookie字符串
            cookie_pairs = raw_cookie.split(';')
            
            for pair in cookie_pairs:
                pair = pair.strip()
                if '=' in pair:
                    name, value = pair.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    
                    # 构建Cookie对象
                    cookie = {
                        "name": name,
                        "value": value,
                        "domain": ".bilibili.com",
                        "path": "/",
                        "expires": int(time.time()) + 86400 * 30,  # 30天后过期
                        "httpOnly": False,
                        "secure": False,
                        "sameSite": "Lax"
                    }
                    cookies.append(cookie)
            
            logger.info(f"成功解析原始Cookie: {len(cookies)}个")
            return cookies
            
        except Exception as e:
            logger.error(f"解析原始Cookie失败: {e}")
            return []
    
    def validate_raw_cookie(self, raw_cookie: str) -> bool:
        """
        验证原始Cookie格式
        Args:
            raw_cookie: 原始Cookie字符串
        Returns:
            bool: 是否有效
        """
        if not raw_cookie:
            return False
            
        # 检查基本格式
        if ';' not in raw_cookie and '=' not in raw_cookie:
            return False
            
        # 检查是否包含关键Cookie
        essential_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID']
        cookie_lower = raw_cookie.lower()
        
        for essential in essential_cookies:
            if essential.lower() not in cookie_lower:
                logger.warning(f"原始Cookie缺少关键字段: {essential}")
                return False
        
        return True
    
    def get_latest_backup_cookie_file(self) -> Optional[str]:
        """
        获取最新的备用Cookie文件
        Returns:
            Optional[str]: 最新的Cookie文件路径
        """
        try:
            # 查找所有备用Cookie文件（仅在备份目录存在时）
            if not self.backup_cookies_dir or not self.backup_cookies_dir.strip():
                return []
            pattern = os.path.join(self.backup_cookies_dir, "cookies_*.json")
            cookie_files = glob.glob(pattern)
            
            if not cookie_files:
                return None
            
            # 按修改时间排序，获取最新的
            latest_file = max(cookie_files, key=os.path.getmtime)
            logger.info(f"找到最新备用Cookie文件: {latest_file}")
            return latest_file
            
        except Exception as e:
            logger.error(f"查找备用Cookie文件失败: {e}")
            return None
    
    def load_backup_cookie_file(self, file_path: str) -> bool:
        """
        加载备用Cookie文件
        Args:
            file_path: Cookie文件路径
        Returns:
            bool: 是否成功加载
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            self.cookies = cookie_data.get('cookies', [])
            self.last_check_time = cookie_data.get('last_check_time', 0)
            
            if not self.cookies:
                logger.warning(f"备用Cookie文件为空: {file_path}")
                return False
            
            # 转换为字典格式
            self.cookie_dict = {cookie['name']: cookie['value'] for cookie in self.cookies}
            self.current_source = f"backup_file:{os.path.basename(file_path)}"
            
            logger.info(f"成功加载备用Cookie文件: {len(self.cookies)}个Cookie")
            return True
            
        except Exception as e:
            logger.error(f"加载备用Cookie文件失败 {file_path}: {e}")
            return False
    
    def save_backup_cookie_file(self, cookies: List[Dict]) -> str:
        """
        保存Cookie到备用文件（GitHub Actions环境中跳过）
        Args:
            cookies: Cookie列表
        Returns:
            str: 保存的文件路径或空字符串
        """
        # 检查是否在GitHub Actions环境中
        is_github_actions = (
            os.environ.get('GITHUB_ACTIONS') == 'true' or
            os.environ.get('CI') == 'true' or
            os.environ.get('GITHUB_WORKFLOW') is not None
        )
        
        if is_github_actions:
            logger.info("🎭 GitHub Actions环境：跳过本地Cookie备份文件保存")
            return ""  # 返回空字符串表示未保存文件
        
        try:
            # 生成文件名：cookies_YYYYMMDD_HHMMSS.json
            # 仅在备份目录存在时保存
            if not self.backup_cookies_dir or not self.backup_cookies_dir.strip():
                self.logger.info("备份目录未配置，跳过Cookie备份")
                return True
                
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
    
    def load_cookies(self) -> bool:
        """
        按优先级加载Cookie
        优先级：Cookie池 > 原始Cookie > 最新备用Cookie文件
        Returns:
            bool: 是否成功加载有效的Cookie
        """
        # 1. 优先尝试Cookie池
        if self.cookie_pool and self.cookie_pool.get_available_cookies():
            selected_cookie = self.cookie_pool.select_cookie()
            if selected_cookie:
                logger.info(f"使用Cookie池中的Cookie: {selected_cookie.name}")
                self.cookies = self.parse_raw_cookie(selected_cookie.cookie)
                if self.cookies:
                    self.cookie_dict = {cookie['name']: cookie['value'] for cookie in self.cookies}
                    self.current_source = f"cookie_pool:{selected_cookie.name}"
                    self.last_check_time = time.time()
                    logger.info(f"Cookie池Cookie加载成功: {len(self.cookies)}个")
                    return True

        # 2. 尝试原始Cookie（向后兼容）
        if self.raw_cookie and self.validate_raw_cookie(self.raw_cookie):
            logger.info("使用配置文件中的原始Cookie")
            self.cookies = self.parse_raw_cookie(self.raw_cookie)
            if self.cookies:
                self.cookie_dict = {cookie['name']: cookie['value'] for cookie in self.cookies}
                self.current_source = "raw_cookie"
                self.last_check_time = time.time()
                logger.info(f"原始Cookie加载成功: {len(self.cookies)}个")
                return True

        # 3. 尝试最新的备用Cookie文件
        latest_backup = self.get_latest_backup_cookie_file()
        if latest_backup and self.load_backup_cookie_file(latest_backup):
            return True

        # 4. 都没有找到有效Cookie
        logger.info("未找到有效的Cookie，需要重新登录")
        return False
    
    def is_cookie_expired(self) -> bool:
        """
        检查Cookie是否过期
        Returns:
            bool: True表示过期或需要检查，False表示仍然有效
        """
        if not self.cookies:
            return True
        
        # 检查时间间隔
        current_time = time.time()
        time_diff_hours = (current_time - self.last_check_time) / 3600
        
        if time_diff_hours >= self.check_interval_hours:
            logger.info(f"Cookie已超过检查间隔 ({time_diff_hours:.1f}小时)，需要验证")
            return True
        
        # 检查Cookie的过期时间
        for cookie in self.cookies:
            if 'expires' in cookie and cookie['expires'] > 0:
                if cookie['expires'] < current_time:
                    logger.info(f"Cookie已过期: {cookie['name']}")
                    return True
        
        logger.info(f"Cookie仍然有效 (距离上次检查 {time_diff_hours:.1f}小时，来源: {self.current_source})")
        return False

    async def validate_cookies(self, browser_context: BrowserContext) -> bool:
        """
        验证Cookie是否仍然有效
        Args:
            browser_context: 浏览器上下文
        Returns:
            bool: Cookie是否有效
        """
        try:
            # 设置Cookie到浏览器
            await browser_context.add_cookies(self.cookies)

            # 创建页面并访问B站
            page = await browser_context.new_page()
            await page.goto("https://www.bilibili.com")

            # 等待页面加载
            await page.wait_for_timeout(3000)

            # 检查是否已登录（查找用户头像或登录状态）
            try:
                # 检查是否存在用户信息
                user_info = await page.locator(".header-avatar-wrap, .nav-user-info").first.is_visible(timeout=5000)
                if user_info:
                    logger.info("Cookie验证成功，用户已登录")
                    # 更新检查时间
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

    def get_cookie_string(self) -> str:
        """
        获取Cookie字符串
        Returns:
            str: Cookie字符串
        """
        if not self.cookies:
            return ""

        return "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in self.cookies])

    def get_cookie_dict(self) -> Dict[str, str]:
        """
        获取Cookie字典
        Returns:
            Dict[str, str]: Cookie字典
        """
        return self.cookie_dict.copy()

    def save_cookies_after_login(self, cookies: List[Dict]) -> str:
        """
        登录后保存Cookie（GitHub Actions环境中仅更新内存）
        Args:
            cookies: 从浏览器获取的Cookie列表
        Returns:
            str: 保存的文件路径或空字符串
        """
        try:
            # 尝试保存到备用文件（GitHub Actions环境中会跳过）
            filepath = self.save_backup_cookie_file(cookies)

            # 更新当前Cookie（无论是否保存文件都需要更新）
            self.cookies = cookies
            self.cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            self.last_check_time = time.time()
            
            if filepath:
                # 本地环境：文件保存成功
                self.current_source = f"backup_file:{os.path.basename(filepath)}"
                logger.info(f"登录后Cookie已保存到文件: {len(cookies)}个")
            else:
                # GitHub Actions环境：仅内存更新
                self.current_source = "github_actions_memory"
                logger.info(f"登录后Cookie已更新到内存: {len(cookies)}个（GitHub Actions环境）")
            
            return filepath

        except Exception as e:
            logger.error(f"保存登录后Cookie失败: {e}")
            raise

    def cleanup_old_backup_files(self, keep_count: int = 5):
        """
        清理旧的备用Cookie文件，只保留最新的几个（GitHub Actions环境中跳过）
        Args:
            keep_count: 保留的文件数量
        """
        # 检查是否在GitHub Actions环境中
        is_github_actions = (
            os.environ.get('GITHUB_ACTIONS') == 'true' or
            os.environ.get('CI') == 'true' or
            os.environ.get('GITHUB_WORKFLOW') is not None
        )
        
        if is_github_actions:
            logger.info("🎭 GitHub Actions环境：跳过备份文件清理")
            return
        
        try:
            # 仅在备份目录存在时清理
            if not self.backup_cookies_dir or not self.backup_cookies_dir.strip():
                return 0
            pattern = os.path.join(self.backup_cookies_dir, "cookies_*.json")
            cookie_files = glob.glob(pattern)

            if len(cookie_files) <= keep_count:
                return

            # 按修改时间排序
            cookie_files.sort(key=os.path.getmtime, reverse=True)

            # 删除多余的文件
            files_to_delete = cookie_files[keep_count:]
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    logger.info(f"已删除旧的备用Cookie文件: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {e}")

        except Exception as e:
            logger.error(f"清理备用Cookie文件失败: {e}")

    def get_status_info(self) -> Dict:
        """
        获取Cookie管理器状态信息
        Returns:
            Dict: 状态信息
        """
        return {
            "has_cookies": len(self.cookies) > 0,
            "cookie_count": len(self.cookies),
            "current_source": self.current_source,
            "last_check_time": datetime.fromtimestamp(self.last_check_time).isoformat() if self.last_check_time else None,
            "backup_files_count": len(glob.glob(os.path.join(self.backup_cookies_dir, "cookies_*.json"))) if self.backup_cookies_dir and self.backup_cookies_dir.strip() else 0,
            "has_raw_cookie": bool(self.raw_cookie)
        }
