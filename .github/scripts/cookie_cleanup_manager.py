#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
失效Cookie自动清理和管理脚本
支持批量检测、自动标记失效、生成更新建议
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set

class CookieCleanupManager:
    """Cookie清理管理器"""
    
    def __init__(self):
        self.failed_cookies = set()
        self.expired_cookies = set()
        self.warning_cookies = set()  # 即将过期的Cookie
        self.cleanup_history = []
        
    def load_failed_cookies_history(self) -> Set[str]:
        """加载历史失败记录（GitHub Actions环境中仅检查当前运行生成的报告）"""
        # 检查是否在GitHub Actions环境中
        is_github_actions = (
            os.environ.get('GITHUB_ACTIONS') == 'true' or
            os.environ.get('CI') == 'true' or
            os.environ.get('GITHUB_WORKFLOW') is not None
        )
        
        if is_github_actions:
            # 在GitHub Actions中只检查当前运行的报告文件
            history_files = [
                'failed_cookies_report.json',
                'cookie_management_report.json'
            ]
        else:
            # 本地环境可以检查更多历史文件
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
        from enhanced_cookie_rotation import CookieManager
        
        manager = CookieManager()
        analysis = manager.analyze_all_cookies(secrets)
        
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
    
    def create_cleanup_script(self, analysis: Dict) -> str:
        """创建清理脚本"""
        script_content = f"""#!/bin/bash

# Cookie清理脚本 - 生成时间: {datetime.now().isoformat()}
# 此脚本需要手动执行，用于清理GitHub Secrets中的失效Cookie

echo "🗑️ Cookie清理脚本"
echo "================="

"""
        
        # 添加删除命令
        for rec in analysis['recommendations']:
            if rec['action'] in ['delete_immediately', 'delete_or_replace']:
                script_content += f"""
# {rec['reason']}
echo "🚫 需要删除的Cookie ({rec['priority']} 优先级):"
"""
                for cookie_key in rec['cookies']:
                    script_content += f'echo "  - {cookie_key}"\n'
                
                script_content += f"""
echo "⚠️ 请在GitHub仓库Settings > Secrets中手动删除上述Cookie"
echo ""
"""
        
        # 添加更新提醒
        for rec in analysis['recommendations']:
            if rec['action'] == 'update_soon':
                script_content += f"""
# {rec['reason']}
echo "⏰ 需要更新的Cookie ({rec['priority']} 优先级):"
"""
                for cookie_key in rec['cookies']:
                    script_content += f'echo "  - {cookie_key}"\n'
                
                script_content += f"""
echo "💡 建议重新获取这些账号的Cookie并更新Secrets"
echo ""
"""
        
        script_content += """
echo "✅ 清理检查完成"
echo "📝 详细报告请查看: cookie_cleanup_report.json"
"""
        
        # 保存脚本
        script_path = "cleanup_cookies.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(script_path, 0o755)
        
        return script_path
    
    def save_cleanup_report(self, analysis: Dict):
        """保存清理报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_cookies': analysis['total_cookies'],
                'expired_count': len(analysis['expired_cookies']),
                'failed_count': len(analysis['failed_cookies']),
                'warning_count': len(analysis['warning_cookies']),
                'healthy_count': len(analysis['healthy_cookies'])
            },
            'details': analysis,
            'next_check_recommended': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        with open('cookie_cleanup_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("📊 清理报告已保存: cookie_cleanup_report.json")
    
    def print_cleanup_summary(self, analysis: Dict):
        """打印清理摘要"""
        print("\n" + "=" * 60)
        print("🗑️ Cookie清理分析报告")
        print("=" * 60)
        
        print(f"📊 总Cookie数量: {analysis['total_cookies']}")
        print(f"❌ 已过期Cookie: {len(analysis['expired_cookies'])}")
        print(f"🚫 失败Cookie: {len(analysis['failed_cookies'])}")
        print(f"⚠️ 即将过期Cookie: {len(analysis['warning_cookies'])}")
        print(f"✅ 健康Cookie: {len(analysis['healthy_cookies'])}")
        
        print("\n📋 清理建议:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            priority_icon = "🔥" if rec['priority'] == 'high' else "⚠️"
            print(f"{i}. {priority_icon} {rec['action']}: {rec['reason']}")
            if rec['cookies']:
                for cookie in rec['cookies']:
                    print(f"   - {cookie}")
        
        if analysis['expired_cookies'] or analysis['failed_cookies']:
            print("\n🚨 立即行动建议:")
            print("1. 运行生成的清理脚本: ./cleanup_cookies.sh")
            print("2. 在GitHub Secrets中删除失效Cookie")
            print("3. 添加新的有效Cookie替换")
        
        print("=" * 60)

def main():
    """主函数"""
    print("🗑️ Cookie自动清理管理器")
    print("=" * 50)
    
    manager = CookieCleanupManager()
    
    try:
        # 获取环境变量中的Cookie
        secrets = {}
        for i in range(1, 11):
            key = f"BILIBILI_COOKIES_{i}"
            value = os.environ.get(key, "")
            if value.strip():
                secrets[key] = value.strip()
        
        single_cookie = os.environ.get("BILIBILI_COOKIES", "")
        if single_cookie.strip():
            secrets["BILIBILI_COOKIES"] = single_cookie.strip()
        
        if not secrets:
            print("❌ 未找到任何Cookie配置")
            return 1
        
        # 分析清理需求
        analysis = manager.analyze_cookies_for_cleanup(secrets)
        
        # 生成清理脚本
        script_path = manager.create_cleanup_script(analysis)
        print(f"✅ 清理脚本已生成: {script_path}")
        
        # 保存报告
        manager.save_cleanup_report(analysis)
        
        # 打印摘要
        manager.print_cleanup_summary(analysis)
        
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

if __name__ == "__main__":
    sys.exit(main())