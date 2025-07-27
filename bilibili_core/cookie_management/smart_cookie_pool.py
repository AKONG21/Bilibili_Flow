#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能Cookie池管理器
支持多账号轮换、智能过期检测、自动故障切换
"""

import asyncio
import json
import random
import time
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from bilibili_core.utils.logger import get_logger

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


class SmartCookiePool:
    """智能Cookie池管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cookies: List[CookieInfo] = []
        self.current_index = 0  # 用于轮询模式
        self.last_health_check = 0
        
        # 加载Cookie配置
        self._load_cookies_from_config()
        
    def _load_cookies_from_config(self):
        """从配置加载Cookie"""
        cookies_config = self.config.get("login", {}).get("cookies", {})
        
        # 1. 检查是否启用Cookie池
        pool_config = cookies_config.get("cookie_pool", {})
        if not pool_config.get("enabled", False):
            # 使用单个Cookie（向后兼容）
            raw_cookie = cookies_config.get("raw_cookie", "")
            if raw_cookie:
                self.cookies = [CookieInfo(
                    name="default",
                    cookie=raw_cookie,
                    priority=1,
                    enabled=True
                )]
                logger.info("使用单个Cookie模式")
            return
        
        # 2. 加载Cookie池
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
                self.cookies.append(cookie_info)
        
        logger.info(f"Cookie池加载完成: {len(self.cookies)}个可用Cookie")
        
    def get_available_cookies(self) -> List[CookieInfo]:
        """获取可用的Cookie列表"""
        return [c for c in self.cookies if c.enabled and c.failure_count < c.max_failures]
    
    def select_cookie(self) -> Optional[CookieInfo]:
        """根据配置的选择模式选择Cookie"""
        available_cookies = self.get_available_cookies()
        
        if not available_cookies:
            logger.error("没有可用的Cookie")
            return None
        
        pool_config = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})
        selection_mode = pool_config.get("selection_mode", "random")
        
        if selection_mode == "random":
            return self._select_random(available_cookies)
        elif selection_mode == "round_robin":
            return self._select_round_robin(available_cookies)
        elif selection_mode == "priority":
            return self._select_priority(available_cookies)
        else:
            logger.warning(f"未知的选择模式: {selection_mode}，使用随机模式")
            return self._select_random(available_cookies)
    
    def _select_random(self, cookies: List[CookieInfo]) -> CookieInfo:
        """随机选择Cookie"""
        selected = random.choice(cookies)
        logger.info(f"随机选择Cookie: {selected.name}")
        return selected
    
    def _select_round_robin(self, cookies: List[CookieInfo]) -> CookieInfo:
        """轮询选择Cookie"""
        if self.current_index >= len(cookies):
            self.current_index = 0
        
        selected = cookies[self.current_index]
        self.current_index += 1
        logger.info(f"轮询选择Cookie: {selected.name}")
        return selected
    
    def _select_priority(self, cookies: List[CookieInfo]) -> CookieInfo:
        """按优先级选择Cookie"""
        # 按优先级排序（数字越小优先级越高）
        sorted_cookies = sorted(cookies, key=lambda x: x.priority)
        selected = sorted_cookies[0]
        logger.info(f"优先级选择Cookie: {selected.name} (优先级: {selected.priority})")
        return selected
    
    def mark_cookie_used(self, cookie_info: CookieInfo, success: bool = True):
        """标记Cookie使用结果"""
        cookie_info.last_used = datetime.now().isoformat()
        
        if success:
            # 重置失败计数
            cookie_info.failure_count = 0
            cookie_info.health_status = "healthy"
            logger.info(f"Cookie使用成功: {cookie_info.name}")
        else:
            # 增加失败计数
            cookie_info.failure_count += 1
            cookie_info.health_status = "unhealthy"
            logger.warning(f"Cookie使用失败: {cookie_info.name} (失败次数: {cookie_info.failure_count}/{cookie_info.max_failures})")
            
            # 检查是否需要禁用
            if cookie_info.failure_count >= cookie_info.max_failures:
                smart_config = self.config.get("login", {}).get("smart_expiry_detection", {})
                if smart_config.get("auto_disable_failed", True):
                    cookie_info.enabled = False
                    logger.error(f"Cookie已自动禁用: {cookie_info.name} (失败次数过多)")
    
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
                            # 检查是否登录成功
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
    
    async def batch_health_check(self) -> Dict[str, bool]:
        """批量健康检查所有Cookie"""
        smart_config = self.config.get("login", {}).get("smart_expiry_detection", {})
        if not smart_config.get("enabled", True):
            logger.info("智能过期检测已禁用")
            return {}
        
        # 检查是否需要进行健康检查
        check_interval_hours = smart_config.get("check_interval_hours", 6)
        current_time = time.time()
        
        if current_time - self.last_health_check < check_interval_hours * 3600:
            logger.info(f"距离上次健康检查不足{check_interval_hours}小时，跳过检查")
            return {}
        
        logger.info("开始批量Cookie健康检查...")
        results = {}
        
        # 并发检查所有Cookie
        tasks = []
        for cookie_info in self.cookies:
            if cookie_info.enabled:
                task = self.health_check_cookie(cookie_info)
                tasks.append((cookie_info.name, task))
        
        if tasks:
            task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (name, _), result in zip(tasks, task_results):
                if isinstance(result, Exception):
                    logger.error(f"Cookie健康检查异常: {name} - {result}")
                    results[name] = False
                else:
                    results[name] = result
        
        self.last_health_check = current_time
        
        # 统计结果
        healthy_count = sum(1 for r in results.values() if r)
        total_count = len(results)
        logger.info(f"批量健康检查完成: {healthy_count}/{total_count} 个Cookie健康")
        
        return results
    
    def get_status_summary(self) -> Dict:
        """获取Cookie池状态摘要"""
        available_cookies = self.get_available_cookies()
        
        return {
            "total_cookies": len(self.cookies),
            "available_cookies": len(available_cookies),
            "disabled_cookies": len([c for c in self.cookies if not c.enabled]),
            "failed_cookies": len([c for c in self.cookies if c.failure_count >= c.max_failures]),
            "healthy_cookies": len([c for c in self.cookies if c.health_status == "healthy"]),
            "last_health_check": datetime.fromtimestamp(self.last_health_check).isoformat() if self.last_health_check else None,
            "cookie_details": [
                {
                    "name": c.name,
                    "enabled": c.enabled,
                    "failure_count": c.failure_count,
                    "health_status": c.health_status,
                    "last_used": c.last_used
                }
                for c in self.cookies
            ]
        }
