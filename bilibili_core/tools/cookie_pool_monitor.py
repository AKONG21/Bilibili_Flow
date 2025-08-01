#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cookie池状态监控工具
用于查看和管理Cookie池状态
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bilibili_core.cookie_management import UnifiedCookieManager
from bilibili_core.utils.logger import get_logger

logger = get_logger()


class CookiePoolMonitor:
    """Cookie池监控器"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml"):
        self.config_file = config_file
        self.unified_manager = UnifiedCookieManager(config_file)
        
    def display_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 60)
        print("🍪 Cookie池监控工具")
        print("=" * 60)
        print("1. 查看Cookie池状态")
        print("2. 执行Cookie健康检查")
        print("3. 显示详细Cookie信息")
        print("4. 测试Cookie选择")
        print("5. 清理失败Cookie")
        print("6. 退出")
        print("=" * 60)
    
    def show_pool_status(self):
        """显示Cookie池状态"""
        try:
            print("\n" + "=" * 50)
            print("📊 Cookie池状态概览")
            print("=" * 50)
            
            self.unified_manager.display_status_report()
            
        except Exception as e:
            print(f"❌ 显示状态失败: {e}")
            logger.error(f"显示Cookie池状态失败: {e}")
    
    async def run_health_check(self):
        """执行Cookie健康检查"""
        try:
            print("\n" + "=" * 50)
            print("🏥 Cookie健康检查")
            print("=" * 50)
            
            available_cookies = self.unified_manager.get_available_cookies()
            if not available_cookies:
                print("❌ 没有可用的Cookie进行健康检查")
                return
            
            print(f"开始检查 {len(available_cookies)} 个Cookie...")
            
            # 执行健康检查
            for i, cookie_info in enumerate(available_cookies):
                print(f"[{i+1}/{len(available_cookies)}] 检查 {cookie_info.name}...")
                
                is_healthy = await self.unified_manager.health_check_cookie(cookie_info)
                status_emoji = "✅" if is_healthy else "❌"
                print(f"  {status_emoji} {cookie_info.name}: {cookie_info.health_status}")
            
            print("\n🏥 健康检查完成!")
            
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            logger.error(f"Cookie健康检查失败: {e}")
    
    def show_detailed_info(self):
        """显示详细Cookie信息"""
        try:
            print("\n" + "=" * 60)
            print("📋 详细Cookie池信息")
            print("=" * 60)
            
            status = self.unified_manager.get_comprehensive_status()
            pool_status = status["pool_status"]
            current_status = status["current_status"]
            
            # 池统计信息
            print("🏊 Cookie池统计:")
            print(f"  总Cookie数量: {pool_status['total_cookies']}")
            print(f"  可用Cookie数量: {pool_status['available_cookies']}")
            print(f"  健康Cookie数量: {pool_status['healthy_cookies']}")
            print(f"  禁用Cookie数量: {pool_status['disabled_cookies']}")
            print(f"  失败Cookie数量: {pool_status['failed_cookies']}")
            
            # Cookie详情
            if self.unified_manager.cookie_pool:
                print(f"\n📝 Cookie详情:")
                for i, cookie_info in enumerate(self.unified_manager.cookie_pool):
                    status_emoji = "✅" if cookie_info.enabled else "❌"
                    health_emoji = {
                        "healthy": "💚", 
                        "unhealthy": "❤️", 
                        "unknown": "💛"
                    }.get(cookie_info.health_status, "💛")
                    
                    print(f"\n{i + 1}. {status_emoji} {cookie_info.name}")
                    print(f"   优先级: {cookie_info.priority}")
                    print(f"   启用状态: {'是' if cookie_info.enabled else '否'}")
                    print(f"   健康状态: {health_emoji} {cookie_info.health_status}")
                    print(f"   失败次数: {cookie_info.failure_count}/{cookie_info.max_failures}")
                    print(f"   最后使用: {cookie_info.last_used or '从未使用'}")
                    print(f"   最后健康检查: {cookie_info.last_health_check or '从未检查'}")
            
            # 当前Cookie状态
            print(f"\n🎯 当前Cookie状态:")
            print(f"  有效Cookie: {'✅' if current_status['has_cookies'] else '❌'}")
            print(f"  Cookie数量: {current_status['cookie_count']}")
            print(f"  Cookie来源: {current_status['current_source']}")
            print(f"  运行环境: {status['environment']}")
            
        except Exception as e:
            print(f"❌ 显示详细信息失败: {e}")
            logger.error(f"显示详细Cookie信息失败: {e}")
    
    def test_cookie_selection(self):
        """测试Cookie选择"""
        try:
            print("\n" + "=" * 50)
            print("🎲 Cookie选择测试")
            print("=" * 50)
            
            available_cookies = self.unified_manager.get_available_cookies()
            if not available_cookies:
                print("❌ 没有可用的Cookie进行测试")
                return
            
            print(f"可用Cookie数量: {len(available_cookies)}")
            print("执行5次选择测试:")
            
            for i in range(5):
                selected = self.unified_manager.select_cookie()
                if selected:
                    print(f"  第{i+1}次: {selected.name} (优先级: {selected.priority})")
                else:
                    print(f"  第{i+1}次: 选择失败")
            
        except Exception as e:
            print(f"❌ Cookie选择测试失败: {e}")
            logger.error(f"Cookie选择测试失败: {e}")
    
    def cleanup_failed_cookies(self):
        """清理失败的Cookie"""
        try:
            print("\n" + "=" * 50)
            print("🧹 清理失败Cookie")
            print("=" * 50)
            
            status = self.unified_manager.get_comprehensive_status()
            failed_count = status["pool_status"]["failed_cookies"]
            
            if failed_count == 0:
                print("✅ 没有需要清理的失败Cookie")
                return
            
            print(f"发现 {failed_count} 个失败Cookie，正在清理...")
            
            # 禁用失败的Cookie
            cleaned_count = 0
            for cookie_info in self.unified_manager.cookie_pool:
                if cookie_info.failure_count >= cookie_info.max_failures and cookie_info.enabled:
                    cookie_info.enabled = False
                    cleaned_count += 1
                    print(f"  🗑️ 已禁用: {cookie_info.name} (失败 {cookie_info.failure_count} 次)")
            
            print(f"✅ 清理完成，共禁用 {cleaned_count} 个失败Cookie")
            
        except Exception as e:
            print(f"❌ 清理失败Cookie失败: {e}")
            logger.error(f"清理失败Cookie失败: {e}")
    
    async def run_async(self):
        """异步运行监控工具"""
        while True:
            try:
                self.display_menu()
                choice = input("\n请选择操作 (1-6): ").strip()
                
                if choice == "1":
                    self.show_pool_status()
                elif choice == "2":
                    await self.run_health_check()
                elif choice == "3":
                    self.show_detailed_info()
                elif choice == "4":
                    self.test_cookie_selection()
                elif choice == "5":
                    self.cleanup_failed_cookies()
                elif choice == "6":
                    print("👋 再见!")
                    break
                else:
                    print("❌ 无效的选择，请输入 1-6")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n👋 用户取消，再见!")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")
                logger.error(f"监控工具操作失败: {e}")
                input("\n按回车键继续...")
    
    def run(self):
        """运行监控工具（同步接口）"""
        asyncio.run(self.run_async())


async def main():
    """主函数"""
    monitor = CookiePoolMonitor()
    await monitor.run_async()


def main_sync():
    """同步主函数"""
    monitor = CookiePoolMonitor()
    monitor.run()


if __name__ == "__main__":
    # 支持两种运行方式
    try:
        main_sync()
    except Exception as e:
        logger.error(f"运行Cookie池监控工具失败: {e}")
        print(f"❌ 运行失败: {e}")