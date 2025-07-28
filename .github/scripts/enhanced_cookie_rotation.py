#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版 GitHub Actions Cookie 管理脚本
支持随机选择、自动故障切换、失效Cookie清理
"""

import json
import os
import sys
import time
import random
import subprocess
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class CookieManager:
    """增强版Cookie管理器"""
    
    def __init__(self):
        self.cookies_data = {}
        self.failed_cookies = set()
        self.usage_history = []
        self.is_github_actions = self.detect_github_actions()
        
    def detect_github_actions(self) -> bool:
        """检测是否在GitHub Actions环境中运行"""
        return (
            os.environ.get('GITHUB_ACTIONS') == 'true' or
            os.environ.get('CI') == 'true' or
            os.environ.get('GITHUB_WORKFLOW') is not None
        )
        
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
            
            analysis = {
                'key': key,
                'cookie': cookie,
                'format_valid': format_valid,
                'expiry_valid': is_valid,
                'days_left': days_left,
                'reason': reason,
                'is_failed': is_failed,
                'score': self.calculate_cookie_score(format_valid, is_valid, days_left, is_failed)
            }
            
            cookie_analysis.append(analysis)
            self.cookies_data[key] = analysis
        
        return cookie_analysis

    def calculate_cookie_score(self, format_valid: bool, expiry_valid: bool, days_left: int, is_failed: bool) -> int:
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
            print(f"  {item['key']}: {status} {item['reason']} (分数: {item['score']})")
        
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
            # 导入B站Cookie测试器
            sys.path.append(os.path.dirname(__file__))
            from bilibili_cookie_tester import BilibiliCookieTester
            
            tester = BilibiliCookieTester()
            success, message, user_info = tester.comprehensive_test(cookie_str)
            
            if success:
                username = user_info.get('username', 'Unknown')
                level = user_info.get('level', 0)
                return True, f"连接成功: {username} (Lv.{level})"
            else:
                return False, f"连接失败: {message}"
                
        except ImportError:
            # 如果无法导入测试器，回退到格式验证
            print("⚠️ 无法导入API测试器，使用格式验证")
            if self.validate_cookie_format(cookie_str):
                return True, "格式验证通过（未进行API测试）"
            else:
                return False, "格式验证失败"
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

    def record_usage(self, cookie_key: str, success: bool, message: str):
        """记录Cookie使用情况"""
        usage_record = {
            'timestamp': datetime.now().isoformat(),
            'cookie_key': cookie_key,
            'success': success,
            'message': message
        }
        self.usage_history.append(usage_record)

    def cleanup_failed_cookies(self, secrets: Dict[str, str]) -> Dict[str, str]:
        """清理失效Cookie（仅在环境变量中标记，不修改Secrets）"""
        if not self.failed_cookies:
            return secrets
        
        print(f"\n🗑️ 发现失效Cookie，建议清理: {list(self.failed_cookies)}")
        
        # 在实际环境中，这里不能直接删除GitHub Secrets
        # 只能记录失效Cookie列表供用户手动处理
        failed_cookies_list = list(self.failed_cookies)
        
        # 保存失效Cookie列表到文件
        failed_report = {
            'timestamp': datetime.now().isoformat(),
            'failed_cookies': failed_cookies_list,
            'recommendation': '建议在GitHub Secrets中更新或删除这些Cookie'
        }
        
        with open('failed_cookies_report.json', 'w', encoding='utf-8') as f:
            json.dump(failed_report, f, indent=2, ensure_ascii=False)
        
        print("📝 失效Cookie报告已保存到: failed_cookies_report.json")
        
        return secrets

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

    def save_usage_report(self):
        """保存使用报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_cookies': len(self.cookies_data),
            'failed_cookies': list(self.failed_cookies),
            'usage_history': self.usage_history,
            'cookie_analysis': self.cookies_data
        }
        
        with open('cookie_management_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("📊 Cookie管理报告已保存")

def main():
    """主函数"""
    print("🚀 增强版 GitHub Actions Cookie 轮换管理器")
    print("=" * 60)
    
    manager = CookieManager()
    
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
            manager.cleanup_failed_cookies(secrets)
            return 1
        
        # 4. 更新配置文件
        config_path = manager.update_original_config(final_cookie)
        
        # 5. 保存报告
        manager.save_usage_report()
        
        print("\n" + "=" * 60)
        print("✅ Cookie轮换管理完成")
        print(f"🎯 最终选择的Cookie已应用到配置文件")
        print(f"📊 详细报告已保存")
        
        return 0
        
    except Exception as e:
        print(f"❌ Cookie轮换管理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())