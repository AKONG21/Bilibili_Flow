#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cookie池状态监控工具
用于查看和管理Cookie池状态
"""

import asyncio
import sys
import os
import yaml
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bilibili_core.cookie_management import SmartCookiePool
from bilibili_core.utils.logger import get_logger

logger = get_logger()


class CookiePoolMonitor:
    """Cookie池监控器"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml"):
        self.config_file = config_file
        self.config = None
        self.cookie_pool = None
        
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                    return True
            else:
                print(f"配置文件不存在: {self.config_file}")
                return False
        except Exception as e:
            print(f"配置加载失败: {e}")
            return False
    
    def init_cookie_pool(self):
        """初始化Cookie池"""
        if not self.config:
            return False
            
        self.cookie_pool = SmartCookiePool(self.config)
        return True
    
    def display_status(self):
        """显示Cookie池状态"""
        if not self.cookie_pool:
            print("Cookie池未初始化")
            return
            
        status = self.cookie_pool.get_status_summary()
        
        print("=" * 60)
        print("Cookie池状态监控")
        print("=" * 60)
        print(f"总Cookie数量: {status['total_cookies']}")
        print(f"可用Cookie数量: {status['available_cookies']}")
        print(f"已禁用Cookie数量: {status['disabled_cookies']}")
        print(f"失败Cookie数量: {status['failed_cookies']}")
        print(f"健康Cookie数量: {status['healthy_cookies']}")
        print(f"最后健康检查: {status['last_health_check'] or '从未检查'}")
        print()
        
        print("Cookie详细状态:")
        print("-" * 60)
        print(f"{'名称':<15} {'状态':<8} {'健康':<8} {'失败次数':<8} {'最后使用':<20}")
        print("-" * 60)
        
        for cookie_detail in status['cookie_details']:
            name = cookie_detail['name']
            enabled = "启用" if cookie_detail['enabled'] else "禁用"
            health = cookie_detail['health_status']
            failure_count = f"{cookie_detail['failure_count']}"
            last_used = cookie_detail['last_used'][:19] if cookie_detail['last_used'] else "从未使用"
            
            print(f"{name:<15} {enabled:<8} {health:<8} {failure_count:<8} {last_used:<20}")
        
        print("=" * 60)
    
    async def run_health_check(self):
        """运行健康检查"""
        if not self.cookie_pool:
            print("Cookie池未初始化")
            return
            
        print("开始执行Cookie健康检查...")
        results = await self.cookie_pool.batch_health_check()
        
        if results:
            print("\n健康检查结果:")
            print("-" * 40)
            for name, is_healthy in results.items():
                status = "✓ 健康" if is_healthy else "✗ 不健康"
                print(f"{name:<15} {status}")
            print("-" * 40)
        else:
            print("未执行健康检查（可能距离上次检查时间过短）")
    
    def test_cookie_selection(self, count: int = 5):
        """测试Cookie选择机制"""
        if not self.cookie_pool:
            print("Cookie池未初始化")
            return
            
        print(f"\n测试Cookie选择机制（{count}次）:")
        print("-" * 40)
        
        for i in range(count):
            selected = self.cookie_pool.select_cookie()
            if selected:
                print(f"第{i+1}次选择: {selected.name} (优先级: {selected.priority})")
            else:
                print(f"第{i+1}次选择: 无可用Cookie")
        print("-" * 40)


async def main():
    """主函数"""
    print("Cookie池监控工具")
    print("=" * 60)
    
    monitor = CookiePoolMonitor()
    
    # 加载配置
    if not monitor.load_config():
        return 1
    
    # 初始化Cookie池
    if not monitor.init_cookie_pool():
        print("Cookie池初始化失败")
        return 1
    
    while True:
        print("\n请选择操作:")
        print("1. 显示Cookie池状态")
        print("2. 执行健康检查")
        print("3. 测试Cookie选择")
        print("4. 退出")
        
        try:
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == "1":
                monitor.display_status()
                
            elif choice == "2":
                await monitor.run_health_check()
                
            elif choice == "3":
                try:
                    count = int(input("请输入测试次数 (默认5): ") or "5")
                    monitor.test_cookie_selection(count)
                except ValueError:
                    print("无效的数字")
                    
            elif choice == "4":
                print("退出监控工具")
                break
                
            else:
                print("无效的选项，请重新选择")
                
        except KeyboardInterrupt:
            print("\n\n用户中断，退出监控工具")
            break
        except Exception as e:
            print(f"操作失败: {e}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
