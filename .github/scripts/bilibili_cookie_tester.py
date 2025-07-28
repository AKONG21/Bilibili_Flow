#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B站Cookie连通性测试器
用于实际验证Cookie是否有效
"""

import requests
import json
import time
from typing import Tuple, Dict

class BilibiliCookieTester:
    """B站Cookie测试器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*'
        })
    
    def parse_cookie_string(self, cookie_str: str) -> Dict[str, str]:
        """解析Cookie字符串为字典"""
        cookies = {}
        if not cookie_str:
            return cookies
        
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        return cookies
    
    def test_cookie_login_status(self, cookie_str: str) -> Tuple[bool, str, Dict]:
        """测试Cookie登录状态"""
        try:
            cookies = self.parse_cookie_string(cookie_str)
            
            # 测试登录状态API
            url = "https://api.bilibili.com/x/web-interface/nav"
            
            response = self.session.get(url, cookies=cookies, timeout=10)
            
            if response.status_code != 200:
                return False, f"HTTP状态码错误: {response.status_code}", {}
            
            data = response.json()
            
            if data.get('code') == 0:
                # 登录成功
                user_data = data.get('data', {})
                user_info = {
                    'uid': user_data.get('mid', 0),
                    'username': user_data.get('uname', 'Unknown'),
                    'level': user_data.get('level_info', {}).get('current_level', 0),
                    'vip_status': user_data.get('vipStatus', 0)
                }
                return True, f"登录成功: {user_info['username']} (Lv.{user_info['level']})", user_info
            else:
                # 登录失败
                message = data.get('message', '未知错误')
                return False, f"登录失败: {message}", {}
        
        except requests.exceptions.RequestException as e:
            return False, f"网络请求失败: {e}", {}
        except json.JSONDecodeError as e:
            return False, f"JSON解析失败: {e}", {}
        except Exception as e:
            return False, f"测试异常: {e}", {}
    
    def test_cookie_permissions(self, cookie_str: str) -> Tuple[bool, str]:
        """测试Cookie权限（获取用户空间信息）"""
        try:
            cookies = self.parse_cookie_string(cookie_str)
            
            # 测试获取用户空间信息
            url = "https://api.bilibili.com/x/space/myinfo"
            
            response = self.session.get(url, cookies=cookies, timeout=10)
            
            if response.status_code != 200:
                return False, f"权限测试失败: HTTP {response.status_code}"
            
            data = response.json()
            
            if data.get('code') == 0:
                return True, "权限测试通过"
            else:
                message = data.get('message', '权限不足')
                return False, f"权限测试失败: {message}"
        
        except Exception as e:
            return False, f"权限测试异常: {e}"
    
    def comprehensive_test(self, cookie_str: str) -> Tuple[bool, str, Dict]:
        """综合测试Cookie"""
        print(f"🔍 开始Cookie综合测试...")
        
        # 1. 登录状态测试
        login_success, login_message, user_info = self.test_cookie_login_status(cookie_str)
        print(f"  登录测试: {'✅' if login_success else '❌'} {login_message}")
        
        if not login_success:
            return False, login_message, {}
        
        # 2. 权限测试
        perm_success, perm_message = self.test_cookie_permissions(cookie_str)
        print(f"  权限测试: {'✅' if perm_success else '❌'} {perm_message}")
        
        if not perm_success:
            return False, f"登录成功但{perm_message}", user_info
        
        # 3. 等待避免频率限制
        time.sleep(1)
        
        return True, f"Cookie验证通过: {user_info.get('username', 'Unknown')}", user_info