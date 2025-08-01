#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cookie管理基础工具模块
提供Cookie解析、验证、配置操作等通用功能
"""

import os
import re
import time
import yaml
from typing import Dict, List, Optional
from bilibili_core.utils.logger import get_logger

logger = get_logger()


class CookieValidator:
    """Cookie验证器"""
    
    # B站必需的Cookie字段
    REQUIRED_COOKIES = ['SESSDATA', 'bili_jct', 'DedeUserID']
    # B站重要的Cookie字段
    IMPORTANT_COOKIES = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid']
    
    @classmethod
    def validate_cookie_string(cls, cookie_string: str) -> bool:
        """
        验证Cookie字符串是否有效
        Args:
            cookie_string: Cookie字符串
        Returns:
            bool: 是否有效
        """
        if not cookie_string:
            return False
        
        # 检查基本格式
        if ';' not in cookie_string and '=' not in cookie_string:
            return False
            
        # 检查必需的Cookie字段
        cookie_lower = cookie_string.lower()
        for required in cls.REQUIRED_COOKIES:
            if required.lower() not in cookie_lower:
                logger.warning(f"Cookie缺少必需字段: {required}")
                return False
        
        return True
    
    @classmethod
    def validate_raw_cookie(cls, raw_cookie: str) -> bool:
        """
        验证原始Cookie格式（增强版）
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
        cookie_lower = raw_cookie.lower()
        
        for essential in cls.REQUIRED_COOKIES:
            if essential.lower() not in cookie_lower:
                logger.warning(f"原始Cookie缺少关键字段: {essential}")
                return False
        
        return True


class CookieParser:
    """Cookie解析器"""
    
    @classmethod
    def parse_raw_cookie(cls, raw_cookie: str) -> List[Dict]:
        """
        解析原始Cookie字符串为Cookie对象列表
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
    
    @classmethod
    def extract_cookie_string_from_browser(cls, cookies: List[Dict]) -> str:
        """
        从浏览器Cookie列表提取Cookie字符串
        Args:
            cookies: 浏览器Cookie列表
        Returns:
            str: Cookie字符串
        """
        try:
            # 只提取B站相关的重要Cookie
            cookie_pairs = []
            
            for cookie in cookies:
                if (cookie.get('name') in CookieValidator.IMPORTANT_COOKIES and 
                    cookie.get('domain', '').endswith('bilibili.com')):
                    cookie_pairs.append(f"{cookie['name']}={cookie['value']}")
            
            return "; ".join(cookie_pairs)
        except Exception as e:
            logger.error(f"提取Cookie字符串失败: {e}")
            return ""
    
    @classmethod
    def cookies_to_string(cls, cookies: List[Dict]) -> str:
        """
        将Cookie列表转换为字符串
        Args:
            cookies: Cookie列表
        Returns:
            str: Cookie字符串
        """
        if not cookies:
            return ""
        
        return "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
    
    @classmethod
    def cookies_to_dict(cls, cookies: List[Dict]) -> Dict[str, str]:
        """
        将Cookie列表转换为字典
        Args:
            cookies: Cookie列表
        Returns:
            Dict[str, str]: Cookie字典
        """
        return {cookie['name']: cookie['value'] for cookie in cookies}


class ConfigUtils:
    """配置工具类"""
    
    @staticmethod
    def substitute_env_vars(obj):
        """
        递归替换配置中的环境变量
        Args:
            obj: 配置对象
        Returns:
            替换后的配置对象
        """
        if isinstance(obj, dict):
            return {key: ConfigUtils.substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [ConfigUtils.substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 替换 ${VAR_NAME} 格式的环境变量
            def replace_env_var(match):
                var_name = match.group(1)
                env_value = os.environ.get(var_name)
                if env_value is None:
                    return match.group(0)  # 保持原样
                return env_value
            
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, obj)
        else:
            return obj
    
    @staticmethod
    def load_yaml_config(config_file: str) -> Optional[Dict]:
        """
        加载YAML配置文件
        Args:
            config_file: 配置文件路径
        Returns:
            Optional[Dict]: 配置字典，失败返回None
        """
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # 替换环境变量
                    config = ConfigUtils.substitute_env_vars(config)
                return config
            else:
                logger.error(f"配置文件不存在: {config_file}")
                return None
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            return None


class CookieStatus:
    """Cookie状态管理"""
    
    @staticmethod
    def calculate_status(cookies_list: List[Dict]) -> Dict:
        """
        计算Cookie状态统计
        Args:
            cookies_list: Cookie配置列表
        Returns:
            Dict: 状态统计
        """
        total = len([c for c in cookies_list if c.get("cookie")])
        available = len([
            c for c in cookies_list 
            if (c.get("cookie") and 
                c.get("enabled", True) and 
                c.get("failure_count", 0) < c.get("max_failures", 3))
        ])
        disabled = len([c for c in cookies_list if not c.get("enabled", True)])
        expired = len([
            c for c in cookies_list 
            if c.get("failure_count", 0) >= c.get("max_failures", 3)
        ])
        
        return {
            "total": total,
            "available": available,
            "expired": expired,
            "disabled": disabled
        }
    
    @staticmethod
    def display_status_report(status: Dict, title: str = "Cookie状态报告"):
        """
        显示Cookie状态报告
        Args:
            status: 状态字典
            title: 报告标题
        """
        print("=" * 50)
        print(f"🍪 {title}")
        print("=" * 50)
        print(f"📊 总Cookie数量: {status['total']}")
        print(f"✅ 可用Cookie数量: {status['available']}")
        print(f"❌ 过期Cookie数量: {status['expired']}")
        print(f"🚫 禁用Cookie数量: {status['disabled']}")
        
        # 状态提醒
        if status['available'] < 2:
            print("\n⚠️  警告: 可用Cookie数量不足2个，建议及时补充！")
            print("💡 建议: 运行扫码登录添加新的Cookie账号")
        elif status['available'] < 3:
            print("\n💡 提示: 可用Cookie数量较少，建议适时补充")
        else:
            print("\n✨ Cookie数量充足，系统运行良好")
        
        print("=" * 50)


class EnvironmentDetector:
    """环境检测器"""
    
    @staticmethod
    def is_github_actions() -> bool:
        """检查是否在GitHub Actions环境中"""
        return (
            os.environ.get('GITHUB_ACTIONS') == 'true' or
            os.environ.get('CI') == 'true' or
            os.environ.get('GITHUB_WORKFLOW') is not None
        )
    
    @staticmethod
    def is_local_environment() -> bool:
        """检查是否在本地环境中"""
        return not EnvironmentDetector.is_github_actions()