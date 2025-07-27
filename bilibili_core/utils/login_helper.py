# -*- coding: utf-8 -*-
"""
Bilibili自动登录辅助模块
提供自动点击登录按钮和弹出二维码的功能
"""

import asyncio
from typing import Optional
from playwright.async_api import Page
from .logger import get_logger

logger = get_logger()


class BilibiliLoginHelper:
    """Bilibili登录辅助类"""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def auto_login_process(self) -> bool:
        """
        自动化登录流程
        Returns:
            bool: 是否成功触发登录流程
        """
        try:
            logger.info("开始自动化登录流程...")
            
            # 等待页面加载
            await asyncio.sleep(2)
            
            # 步骤1: 点击登录按钮
            if not await self._click_login_button():
                logger.warning("未找到登录按钮，可能已经登录或页面结构发生变化")
                return False
            
            # 等待登录弹窗出现
            await asyncio.sleep(2)
            
            # 步骤2: 点击二维码登录
            if await self._click_qrcode_login():
                logger.info("二维码登录界面已打开，请使用B站APP扫码登录")
                return True
            else:
                logger.info("未找到二维码登录选项，请手动选择登录方式")
                return True  # 仍然算成功，因为登录弹窗已打开
                
        except Exception as e:
            logger.error(f"自动化登录流程出错: {e}")
            logger.info("请手动完成登录")
            return False
    
    async def _click_login_button(self) -> bool:
        """
        点击登录按钮
        Returns:
            bool: 是否成功点击
        """
        login_selectors = [
            ".header-login-entry",  # 主要登录按钮
            ".login-btn",           # 备用登录按钮
            "text=登录",             # 文本匹配
            "[data-v-*='登录']",     # 属性匹配
            ".nav-user-info .default-entry",  # 用户信息区域的登录入口
            ".bili-header .right-entry .default-entry"  # 头部右侧登录入口
        ]
        
        for selector in login_selectors:
            try:
                login_btn = self.page.locator(selector).first
                if await login_btn.is_visible(timeout=3000):
                    await login_btn.click()
                    logger.info(f"成功点击登录按钮: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"尝试选择器 {selector} 失败: {e}")
                continue
        
        return False
    
    async def _click_qrcode_login(self) -> bool:
        """
        点击二维码登录选项
        Returns:
            bool: 是否成功点击
        """
        qr_selectors = [
            ".login-scan-box",      # 二维码登录区域
            ".qrcode-login",        # 二维码登录按钮
            "text=扫码登录",         # 文本匹配
            ".scan-login-btn",      # 扫码按钮
            ".login-scan",          # 扫码登录
            "[data-v-*='扫码登录']"  # 属性匹配
        ]
        
        for selector in qr_selectors:
            try:
                qr_btn = self.page.locator(selector).first
                if await qr_btn.is_visible(timeout=3000):
                    await qr_btn.click()
                    logger.info(f"成功点击二维码登录: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"尝试二维码选择器 {selector} 失败: {e}")
                continue
        
        return False
    
    async def wait_for_login_completion(self, timeout: int = 300) -> bool:
        """
        等待登录完成
        Args:
            timeout: 超时时间（秒）
        Returns:
            bool: 是否登录成功
        """
        logger.info(f"等待登录完成，超时时间: {timeout}秒")
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                # 检查是否有用户头像或用户名出现
                user_indicators = [
                    ".nav-user-info .user-con",  # 用户信息容器
                    ".bili-avatar",              # 用户头像
                    ".header-avatar-wrap",       # 头像包装器
                    ".user-info"                 # 用户信息
                ]
                
                for selector in user_indicators:
                    try:
                        element = self.page.locator(selector).first
                        if await element.is_visible(timeout=1000):
                            logger.info("检测到登录成功标识")
                            return True
                    except:
                        continue
                
                # 检查超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning("等待登录超时")
                    return False
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"检查登录状态时出错: {e}")
                return False
    
    async def check_login_status(self) -> bool:
        """
        检查当前登录状态
        Returns:
            bool: 是否已登录
        """
        try:
            # 检查页面上是否有登录用户的标识
            user_indicators = [
                ".nav-user-info .user-con",
                ".bili-avatar",
                ".header-avatar-wrap"
            ]
            
            for selector in user_indicators:
                try:
                    element = self.page.locator(selector).first
                    if await element.is_visible(timeout=2000):
                        logger.info("检测到已登录状态")
                        return True
                except:
                    continue
            
            logger.info("未检测到登录状态")
            return False
            
        except Exception as e:
            logger.error(f"检查登录状态时出错: {e}")
            return False
