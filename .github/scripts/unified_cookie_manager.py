#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一Cookie管理器
整合enhanced_cookie_rotation.py、bilibili_cookie_tester.py、cookie_cleanup_manager.py的功能
提供完整的Cookie轮换、测试、清理和统计功能
"""

import json
import os
import sys
import time
import random
import subprocess
import urllib.parse
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Set

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

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

class UnifiedCookieManager:
    """统一Cookie管理器"""
    
    def __init__(self):
        self.cookies_data = {}
        self.failed_cookies = set()
        self.expired_cookies = set()
        self.warning_cookies = set()
        self.usage_history = []
        self.usage_statistics = {}
        self.cleanup_history = []
        
        self.is_github_actions = self.detect_github_actions()
        self.cache_file_path = os.path.expanduser("~/.cache/bilibili-cookie-usage-history.json")
        self.tester = BilibiliCookieTester()
        
        # 加载历史使用记录
        self.load_usage_history()
        
    def detect_github_actions(self) -> bool:
        """检测是否在GitHub Actions环境中运行"""
        return (
            os.environ.get('GITHUB_ACTIONS') == 'true' or
            os.environ.get('CI') == 'true' or
            os.environ.get('GITHUB_WORKFLOW') is not None
        )
    
    # === 使用历史和统计功能 ===
    
    def load_usage_history(self):
        """加载使用历史记录（支持GitHub Actions缓存）"""
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                self.usage_history = cached_data.get('usage_history', [])
                self.usage_statistics = cached_data.get('usage_statistics', {})
                self.failed_cookies = set(cached_data.get('failed_cookies', []))
                
                print(f"✅ 已加载使用历史记录: {len(self.usage_history)} 条记录")
            else:
                print("ℹ️ 未找到历史记录文件，使用全新状态")
                
        except Exception as e:
            print(f"⚠️ 加载使用历史失败: {e}")
            self.usage_history = []
            self.usage_statistics = {}
    
    def save_usage_history(self):
        """保存使用历史记录到缓存"""
        try:
            # 确保缓存目录存在
            cache_dir = os.path.dirname(self.cache_file_path)
            os.makedirs(cache_dir, exist_ok=True)
            
            # 准备保存数据
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'usage_history': self.usage_history[-1000:],  # 只保留最近1000条记录
                'usage_statistics': self.usage_statistics,
                'failed_cookies': list(self.failed_cookies),
                'cache_version': '1.0'
            }
            
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 使用历史已保存到缓存: {self.cache_file_path}")
            
        except Exception as e:
            print(f"⚠️ 保存使用历史失败: {e}")
    
    def update_usage_statistics(self, cookie_key: str, success: bool):
        """更新使用统计信息"""
        if cookie_key not in self.usage_statistics:
            self.usage_statistics[cookie_key] = {
                'total_uses': 0,
                'successful_uses': 0,
                'failed_uses': 0,
                'first_used': datetime.now().isoformat(),
                'last_used': None,
                'success_rate': 0.0
            }
        
        stats = self.usage_statistics[cookie_key]
        stats['total_uses'] += 1
        stats['last_used'] = datetime.now().isoformat()
        
        if success:
            stats['successful_uses'] += 1
        else:
            stats['failed_uses'] += 1
        
        # 计算成功率
        if stats['total_uses'] > 0:
            stats['success_rate'] = stats['successful_uses'] / stats['total_uses']
    
    def record_usage(self, cookie_key: str, success: bool, message: str):
        """记录Cookie使用情况"""
        usage_record = {
            'timestamp': datetime.now().isoformat(),
            'cookie_key': cookie_key,
            'success': success,
            'message': message
        }
        self.usage_history.append(usage_record)
        
        # 更新统计信息
        self.update_usage_statistics(cookie_key, success)
        
        # 立即保存到缓存（GitHub Actions环境）
        if self.is_github_actions:
            self.save_usage_history()
    
    # === Cookie管理核心功能 ===
    
    def get_github_secrets(self) -> Dict[str, str]:
        """获取GitHub Secrets中的所有BILIBILI_COOKIES"""
        secrets = {}
        
        # 从环境变量读取多个Cookie
        for i in range(1, 11):  # 支持最多10个Cookie
            key = f"BILIBILI_COOKIES_{i}"
            value = os.environ.get(key, "")
            if value.strip():
                secrets[key] = value.strip()
        
        # 兼容单个Cookie配置
        single_cookie = os.environ.get("BILIBILI_COOKIES", "")
        if single_cookie.strip():
            secrets["BILIBILI_COOKIES"] = single_cookie.strip()
        
        return secrets

    def validate_cookie_format(self, cookie_str: str) -> bool:
        """验证Cookie格式"""
        if not cookie_str:
            return False
        
        # 检查基本格式
        if ';' not in cookie_str and '=' not in cookie_str:
            return False
        
        # 检查关键字段
        essential_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID']
        cookie_lower = cookie_str.lower()
        
        for essential in essential_cookies:
            if essential.lower() not in cookie_lower:
                return False
        
        return True

    def check_cookie_expiry(self, cookie_str: str) -> Tuple[bool, str, int]:
        """
        检查Cookie过期状态
        Returns: (is_valid, reason, days_left)
        """
        if not cookie_str:
            return False, "空Cookie", 0
        
        try:
            if "SESSDATA=" in cookie_str:
                # 提取SESSDATA值
                sessdata_part = cookie_str.split("SESSDATA=")[1].split(";")[0]
                
                # URL解码
                decoded_sessdata = urllib.parse.unquote(sessdata_part)
                
                # 解析时间戳
                if ',' in decoded_sessdata:
                    parts = decoded_sessdata.split(',')
                    if len(parts) >= 2:
                        try:
                            expire_timestamp = int(parts[1])
                            current_timestamp = int(time.time())
                            
                            if expire_timestamp <= current_timestamp:
                                return False, "Cookie已过期", 0
                            else:
                                days_left = (expire_timestamp - current_timestamp) // 86400
                                if days_left < 7:
                                    return True, f"即将过期({days_left}天)", days_left
                                else:
                                    return True, f"有效({days_left}天)", days_left
                        except (ValueError, IndexError):
                            pass
                
                # 如果无法解析时间戳，仍然认为格式有效
                return True, "格式有效(无法检查过期)", 365
                
        except Exception as e:
            return False, f"检查失败: {str(e)}", 0
        
        return True, "格式验证通过", 365

    def analyze_all_cookies(self, secrets: Dict[str, str]) -> List[Dict]:
        """分析所有Cookie的状态"""
        cookie_analysis = []
        
        for key, cookie in secrets.items():
            if not cookie.strip():
                continue
                
            # 基础格式验证
            format_valid = self.validate_cookie_format(cookie)
            
            # 过期检查
            is_valid, reason, days_left = self.check_cookie_expiry(cookie)
            
            # 检查是否在失败列表中
            is_failed = key in self.failed_cookies
            
            # 获取使用统计
            usage_stats = self.usage_statistics.get(key, {})
            
            analysis = {
                'key': key,
                'cookie': cookie,
                'format_valid': format_valid,
                'expiry_valid': is_valid,
                'days_left': days_left,
                'reason': reason,
                'is_failed': is_failed,
                'usage_count': usage_stats.get('total_uses', 0),
                'success_rate': usage_stats.get('success_rate', 0.0),
                'first_used': usage_stats.get('first_used'),
                'last_used': usage_stats.get('last_used'),
                'score': self.calculate_cookie_score(format_valid, is_valid, days_left, is_failed, usage_stats)
            }
            
            cookie_analysis.append(analysis)
            self.cookies_data[key] = analysis
        
        return cookie_analysis

    def calculate_cookie_score(self, format_valid: bool, expiry_valid: bool, days_left: int, is_failed: bool, usage_stats: Dict) -> int:
        """计算Cookie质量分数，用于排序"""
        score = 0
        
        if not format_valid:
            return -100
        
        if is_failed:
            return -50
        
        if not expiry_valid:
            return -10
        
        # 基础分数
        score = 100
        
        # 剩余天数奖励
        if days_left > 30:
            score += 50
        elif days_left > 7:
            score += 20
        elif days_left > 1:
            score += 10
        
        # 使用统计奖励/惩罚
        if usage_stats:
            success_rate = usage_stats.get('success_rate', 0.0)
            total_uses = usage_stats.get('total_uses', 0)
            
            # 成功率奖励
            if success_rate > 0.9:
                score += 30
            elif success_rate > 0.7:
                score += 15
            elif success_rate < 0.5:
                score -= 20
            
            # 使用频率适中奖励（避免过度使用单个Cookie）
            if 5 <= total_uses <= 20:
                score += 10
            elif total_uses > 50:
                score -= 10
        
        # 随机因子（用于随机选择）
        score += random.randint(-10, 10)
        
        return score

    def select_best_cookies(self, secrets: Dict[str, str], count: int = 3) -> List[Dict]:
        """随机选择最佳的几个Cookie"""
        if not secrets:
            print("❌ 未找到任何Cookie配置")
            return []
        
        # 分析所有Cookie
        analysis = self.analyze_all_cookies(secrets)
        
        print("🔍 Cookie状态分析:")
        for item in analysis:
            status = "✅" if (item['format_valid'] and item['expiry_valid'] and not item['is_failed']) else "❌"
            usage_info = f"(使用{item['usage_count']}次,成功率{item['success_rate']*100:.1f}%)" if item['usage_count'] > 0 else "(未使用)"
            print(f"  {item['key']}: {status} {item['reason']} {usage_info} (分数: {item['score']})")
        
        # 过滤出有效的Cookie
        valid_cookies = [
            item for item in analysis 
            if item['format_valid'] and item['expiry_valid'] and not item['is_failed']
        ]
        
        if not valid_cookies:
            print("❌ 没有找到有效的Cookie")
            return []
        
        # 按分数排序并随机化
        valid_cookies.sort(key=lambda x: x['score'], reverse=True)
        
        # 从前几名中随机选择
        top_cookies = valid_cookies[:min(count * 2, len(valid_cookies))]
        selected = random.sample(top_cookies, min(count, len(top_cookies)))
        
        print(f"🎲 随机选择了 {len(selected)} 个Cookie进行轮换")
        
        return selected

    def test_cookie_connectivity(self, cookie_str: str) -> Tuple[bool, str]:
        """测试Cookie连通性（真实B站API测试）"""
        try:
            success, message, user_info = self.tester.comprehensive_test(cookie_str)
            
            if success:
                username = user_info.get('username', 'Unknown')
                level = user_info.get('level', 0)
                return True, f"连接成功: {username} (Lv.{level})"
            else:
                return False, f"连接失败: {message}"
                
        except Exception as e:
            return False, f"连接测试异常: {e}"

    def try_cookies_with_fallback(self, selected_cookies: List[Dict]) -> Optional[str]:
        """尝试Cookie并在失败时自动切换"""
        print("\n🔄 开始Cookie故障切换测试...")
        
        for i, cookie_info in enumerate(selected_cookies):
            key = cookie_info['key']
            cookie = cookie_info['cookie']
            
            print(f"\n📋 尝试Cookie {i+1}/{len(selected_cookies)}: {key}")
            
            # 测试连通性
            is_connected, result = self.test_cookie_connectivity(cookie)
            
            if is_connected:
                print(f"✅ Cookie {key} 测试成功: {result}")
                self.record_usage(key, True, result)
                return cookie
            else:
                print(f"❌ Cookie {key} 测试失败: {result}")
                self.record_usage(key, False, result)
                self.mark_cookie_failed(key)
        
        print("❌ 所有Cookie都无法使用")
        return None

    def mark_cookie_failed(self, cookie_key: str):
        """标记Cookie为失败"""
        self.failed_cookies.add(cookie_key)
        print(f"🚫 标记Cookie为失败: {cookie_key}")

    # === 清理管理功能 ===
    
    def load_failed_cookies_history(self) -> Set[str]:
        """加载历史失败记录"""
        history_files = [
            'failed_cookies_report.json',
            'cookie_management_report.json'
        ]
        
        failed_set = set()
        
        for file_path in history_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 从不同格式的报告中提取失败Cookie
                    if 'failed_cookies' in data:
                        failed_set.update(data['failed_cookies'])
                    
                    if 'usage_history' in data:
                        for record in data['usage_history']:
                            if not record.get('success', True):
                                failed_set.add(record.get('cookie_key', ''))
                    
                except Exception as e:
                    print(f"⚠️ 读取历史文件失败 {file_path}: {e}")
        
        return failed_set

    def analyze_cookies_for_cleanup(self, secrets: Dict[str, str]) -> Dict:
        """分析Cookie清理需求"""
        analysis = self.analyze_all_cookies(secrets)
        
        # 加载历史失败记录
        historical_failed = self.load_failed_cookies_history()
        
        cleanup_analysis = {
            'total_cookies': len(analysis),
            'expired_cookies': [],
            'warning_cookies': [],  # 7天内过期
            'failed_cookies': [],
            'healthy_cookies': [],
            'recommendations': []
        }
        
        for item in analysis:
            key = item['key']
            
            # 检查是否在历史失败记录中
            if key in historical_failed:
                item['historical_failure'] = True
                cleanup_analysis['failed_cookies'].append(item)
                self.failed_cookies.add(key)
                continue
            
            # 检查过期状态
            if not item['expiry_valid']:
                cleanup_analysis['expired_cookies'].append(item)
                self.expired_cookies.add(key)
            elif item['days_left'] <= 7:
                cleanup_analysis['warning_cookies'].append(item)
                self.warning_cookies.add(key)
            elif item['format_valid'] and item['expiry_valid']:
                cleanup_analysis['healthy_cookies'].append(item)
        
        # 生成清理建议
        self.generate_cleanup_recommendations(cleanup_analysis)
        
        return cleanup_analysis

    def generate_cleanup_recommendations(self, analysis: Dict):
        """生成清理建议"""
        recommendations = []
        
        # 立即删除建议
        if analysis['expired_cookies']:
            recommendations.append({
                'priority': 'high',
                'action': 'delete_immediately',
                'cookies': [item['key'] for item in analysis['expired_cookies']],
                'reason': 'Cookie已过期，无法使用'
            })
        
        if analysis['failed_cookies']:
            recommendations.append({
                'priority': 'high',
                'action': 'delete_or_replace',
                'cookies': [item['key'] for item in analysis['failed_cookies']],
                'reason': 'Cookie多次失败，建议删除或更换'
            })
        
        # 警告更新建议
        if analysis['warning_cookies']:
            recommendations.append({
                'priority': 'medium',
                'action': 'update_soon',
                'cookies': [item['key'] for item in analysis['warning_cookies']],
                'reason': 'Cookie即将过期，建议及时更新'
            })
        
        # 健康检查建议
        if len(analysis['healthy_cookies']) < 2:
            recommendations.append({
                'priority': 'medium',
                'action': 'add_backup',
                'cookies': [],
                'reason': '健康Cookie数量不足，建议添加备用Cookie'
            })
        
        analysis['recommendations'] = recommendations

    # === 配置文件更新功能 ===
    
    def update_original_config(self, selected_cookie: str) -> str:
        """更新原始配置文件中的Cookie部分"""
        original_config_path = "daily_task_config.yaml"
        backup_config_path = "daily_task_config.yaml.backup"
        
        try:
            with open(original_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 备份原始配置
            with open(backup_config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 解析并更新配置
            import yaml
            config = yaml.safe_load(content)
            
            if 'login' not in config:
                config['login'] = {}
            if 'cookies' not in config['login']:
                config['login']['cookies'] = {}
            
            # 更新Cookie配置
            config['login']['cookies']['raw_cookie'] = selected_cookie
            
            # GitHub Actions环境优化
            if self.is_github_actions:
                print("🎭 GitHub Actions环境：应用安全优化设置...")
                
                # 禁用Cookie池（避免冲突）
                if 'cookie_pool' not in config['login']['cookies']:
                    config['login']['cookies']['cookie_pool'] = {}
                config['login']['cookies']['cookie_pool']['enabled'] = False
                
                # 清空backup_cookies_dir路径（安全考虑）
                config['login']['backup_cookies_dir'] = ""
                
                print("✅ 已禁用Cookie池和备份目录")
            else:
                print("🏠 本地环境：保持原有设置")
            
            # 写回配置
            with open(original_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print(f"✅ 配置文件已更新: {original_config_path}")
            if self.is_github_actions:
                print("🚫 GitHub Actions环境：已清空backup_cookies_dir路径")
            
            return original_config_path
            
        except Exception as e:
            print(f"❌ 配置文件更新失败: {e}")
            raise

    # === 报告和统计功能 ===
    
    def get_most_used_cookie(self) -> Optional[str]:
        """获取使用次数最多的Cookie"""
        if not self.usage_statistics:
            return None
        
        most_used = max(self.usage_statistics.items(), key=lambda x: x[1]['total_uses'])
        return f"{most_used[0]} ({most_used[1]['total_uses']} 次)"
    
    def calculate_overall_success_rate(self) -> float:
        """计算总体成功率"""
        if not self.usage_statistics:
            return 0.0
        
        total_success = sum(stats['successful_uses'] for stats in self.usage_statistics.values())
        total_attempts = sum(stats['total_uses'] for stats in self.usage_statistics.values())
        
        return total_success / total_attempts if total_attempts > 0 else 0.0
    
    def print_usage_statistics(self):
        """打印使用统计信息"""
        if not self.usage_statistics:
            print("📊 暂无使用统计数据")
            return
        
        print("\n" + "=" * 60)
        print("📊 Cookie使用统计报告")
        print("=" * 60)
        
        for cookie_key, stats in self.usage_statistics.items():
            success_rate_pct = stats['success_rate'] * 100
            print(f"🍪 {cookie_key}:")
            print(f"   总使用次数: {stats['total_uses']}")
            print(f"   成功次数: {stats['successful_uses']}")
            print(f"   失败次数: {stats['failed_uses']}")
            print(f"   成功率: {success_rate_pct:.1f}%")
            print(f"   首次使用: {stats['first_used'][:19]}")
            if stats['last_used']:
                print(f"   最后使用: {stats['last_used'][:19]}")
            print()
        
        overall_rate = self.calculate_overall_success_rate() * 100
        print(f"📈 总体成功率: {overall_rate:.1f}%")
        print(f"📊 活跃Cookie数: {len(self.usage_statistics)}")
        print("=" * 60)

    def save_comprehensive_report(self):
        """保存综合报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_cookies': len(self.cookies_data),
            'failed_cookies': list(self.failed_cookies),
            'expired_cookies': list(self.expired_cookies),
            'warning_cookies': list(self.warning_cookies),
            'usage_history': self.usage_history,
            'cookie_analysis': self.cookies_data,
            'usage_statistics': self.usage_statistics,
            'summary': {
                'total_usage_records': len(self.usage_history),
                'cookies_with_history': len(self.usage_statistics),
                'most_used_cookie': self.get_most_used_cookie(),
                'overall_success_rate': self.calculate_overall_success_rate(),
                'healthy_cookie_count': len([k for k, v in self.cookies_data.items() 
                                           if v.get('format_valid') and v.get('expiry_valid') and k not in self.failed_cookies])
            }
        }
        
        with open('unified_cookie_management_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("📊 统一Cookie管理报告已保存")
        
        # 打印统计摘要
        self.print_usage_statistics()

def cookie_rotation_mode(manager: UnifiedCookieManager) -> int:
    """Cookie轮换模式"""
    print("🚀 Cookie轮换模式")
    print("=" * 50)
    
    try:
        # 1. 获取所有Cookie Secrets
        secrets = manager.get_github_secrets()
        
        if not secrets:
            print("❌ 未配置任何BILIBILI_COOKIES")
            return 1
        
        print(f"📦 发现 {len(secrets)} 个Cookie配置")
        
        # 2. 随机选择最佳Cookie
        selected_cookies = manager.select_best_cookies(secrets, count=3)
        
        if not selected_cookies:
            print("❌ 未找到有效的Cookie")
            return 1
        
        # 3. 故障切换测试
        final_cookie = manager.try_cookies_with_fallback(selected_cookies)
        
        if not final_cookie:
            print("❌ 所有Cookie都无法使用")
            return 1
        
        # 4. 更新配置文件
        config_path = manager.update_original_config(final_cookie)
        
        # 5. 保存报告
        manager.save_comprehensive_report()
        
        # 确保最终保存使用历史到缓存
        if not manager.is_github_actions:
            manager.save_usage_history()
        
        print("\n" + "=" * 50)
        print("✅ Cookie轮换管理完成")
        
        return 0
        
    except Exception as e:
        print(f"❌ Cookie轮换管理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

def cleanup_mode(manager: UnifiedCookieManager) -> int:
    """清理模式"""
    print("🗑️ Cookie清理模式")
    print("=" * 50)
    
    try:
        # 获取环境变量中的Cookie
        secrets = manager.get_github_secrets()
        
        if not secrets:
            print("❌ 未找到任何Cookie配置")
            return 1
        
        # 分析清理需求
        analysis = manager.analyze_cookies_for_cleanup(secrets)
        
        # 保存报告
        manager.save_comprehensive_report()
        
        # 打印摘要
        print(f"📊 总Cookie数量: {analysis['total_cookies']}")
        print(f"❌ 已过期Cookie: {len(analysis['expired_cookies'])}")
        print(f"🚫 失败Cookie: {len(analysis['failed_cookies'])}")
        print(f"⚠️ 即将过期Cookie: {len(analysis['warning_cookies'])}")
        print(f"✅ 健康Cookie: {len(analysis['healthy_cookies'])}")
        
        # 返回状态码
        if analysis['expired_cookies'] or analysis['failed_cookies']:
            return 2  # 需要清理
        elif analysis['warning_cookies']:
            return 1  # 需要关注
        else:
            return 0  # 一切正常
        
    except Exception as e:
        print(f"❌ 清理分析失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """主函数"""
    mode = sys.argv[1] if len(sys.argv) > 1 else "rotation"
    
    manager = UnifiedCookieManager()
    
    if mode == "rotation":
        return cookie_rotation_mode(manager)
    elif mode == "cleanup":
        return cleanup_mode(manager)
    else:
        print("用法: python unified_cookie_manager.py [rotation|cleanup]")
        return 1

if __name__ == "__main__":
    sys.exit(main())