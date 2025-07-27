# -*- coding: utf-8 -*-
"""
Cookie管理模块
支持Cookie的持久化存储、过期检查和自动刷新
"""

import json
import os
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from playwright.async_api import BrowserContext, Page
from .logger import get_logger

logger = get_logger()


class CookieManager:
    """Cookie管理器"""
    
    def __init__(self, cookie_file: str, check_interval_hours: int = 24):
        self.cookie_file = cookie_file
        self.check_interval_hours = check_interval_hours
        self.cookies = []
        self.cookie_dict = {}
        self.last_check_time = 0
        
        # 确保目录存在
        cookie_dir = os.path.dirname(cookie_file)
        if cookie_dir:
            os.makedirs(cookie_dir, exist_ok=True)
    
    def load_cookies(self) -> bool:
        """
        加载Cookie文件
        Returns:
            bool: 是否成功加载有效的Cookie
        """
        try:
            if not os.path.exists(self.cookie_file):
                logger.info("Cookie文件不存在，需要重新登录")
                return False
            
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            self.cookies = cookie_data.get('cookies', [])
            self.last_check_time = cookie_data.get('last_check_time', 0)
            
            if not self.cookies:
                logger.info("Cookie文件为空，需要重新登录")
                return False
            
            # 转换为字典格式
            self.cookie_dict = {cookie['name']: cookie['value'] for cookie in self.cookies}
            
            logger.info(f"成功加载 {len(self.cookies)} 个Cookie")
            return True
            
        except Exception as e:
            logger.error(f"加载Cookie文件失败: {e}")
            return False
    
    def save_cookies(self, cookies: List[Dict]):
        """
        保存Cookie到文件
        Args:
            cookies: Cookie列表
        """
        try:
            self.cookies = cookies
            self.cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            self.last_check_time = time.time()
            
            cookie_data = {
                'cookies': self.cookies,
                'last_check_time': self.last_check_time,
                'save_time': datetime.now().isoformat(),
                'domain': 'bilibili.com'
            }
            
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功保存 {len(cookies)} 个Cookie到文件: {self.cookie_file}")
            
        except Exception as e:
            logger.error(f"保存Cookie文件失败: {e}")
            raise
    
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
        
        logger.info(f"Cookie仍然有效 (距离上次检查 {time_diff_hours:.1f}小时)")
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
            
            # 检查是否已登录（查找用户头像或用户名）
            user_indicators = [
                ".nav-user-info .user-con",
                ".bili-avatar",
                ".header-avatar-wrap"
            ]
            
            for selector in user_indicators:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=2000):
                        logger.info("Cookie验证成功，用户已登录")
                        await page.close()
                        
                        # 更新检查时间
                        self.last_check_time = time.time()
                        self.save_cookies(self.cookies)
                        
                        return True
                except:
                    continue
            
            logger.warning("Cookie验证失败，用户未登录")
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
    
    def clear_cookies(self):
        """清除Cookie"""
        self.cookies = []
        self.cookie_dict = {}
        self.last_check_time = 0
        
        if os.path.exists(self.cookie_file):
            try:
                os.remove(self.cookie_file)
                logger.info("已清除Cookie文件")
            except Exception as e:
                logger.error(f"清除Cookie文件失败: {e}")
    
    def get_cookie_info(self) -> Dict:
        """
        获取Cookie信息摘要
        Returns:
            Dict: Cookie信息
        """
        if not self.cookies:
            return {
                "status": "empty",
                "count": 0,
                "last_check": None,
                "next_check": None
            }
        
        last_check = datetime.fromtimestamp(self.last_check_time) if self.last_check_time > 0 else None
        next_check = last_check + timedelta(hours=self.check_interval_hours) if last_check else None
        
        return {
            "status": "loaded",
            "count": len(self.cookies),
            "last_check": last_check.isoformat() if last_check else None,
            "next_check": next_check.isoformat() if next_check else None,
            "file_path": self.cookie_file,
            "domains": list(set(cookie.get('domain', 'unknown') for cookie in self.cookies))
        }
    
    def print_cookie_status(self):
        """打印Cookie状态"""
        info = self.get_cookie_info()
        
        logger.info("=" * 30)
        logger.info("Cookie状态:")
        logger.info(f"状态: {info['status']}")
        logger.info(f"数量: {info['count']}")
        
        if info['last_check']:
            logger.info(f"上次检查: {info['last_check']}")
        
        if info['next_check']:
            logger.info(f"下次检查: {info['next_check']}")
        
        logger.info(f"文件路径: {info['file_path']}")
        logger.info("=" * 30)
