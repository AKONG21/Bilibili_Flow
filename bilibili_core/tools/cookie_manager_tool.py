#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cookie管理工具
提供Cookie的查看、添加、删除、清理等功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bilibili_core.cookie_management import UnifiedCookieManager, CookieValidator


class CookieManagerTool:
    """Cookie管理工具"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml"):
        self.unified_manager = UnifiedCookieManager(config_file)
        
    def display_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 60)
        print("🍪 Cookie管理工具")
        print("=" * 60)
        print("1. 查看Cookie状态")
        print("2. 手动添加Cookie")
        print("3. 删除指定Cookie")
        print("4. 清理过期Cookie")
        print("5. 清理备份文件")
        print("6. 显示详细Cookie信息")
        print("7. 退出")
        print("=" * 60)
    
    def show_cookie_status(self):
        """显示Cookie状态"""
        self.unified_manager.display_status_report()
    
    def add_cookie_manually(self):
        """手动添加Cookie"""
        try:
            print("\n" + "=" * 50)
            print("🍪 手动添加Cookie")
            print("=" * 50)
            
            # 输入Cookie字符串
            cookie_string = input("请输入Cookie字符串（格式：name1=value1; name2=value2）: ").strip()
            
            if not cookie_string:
                print("❌ Cookie字符串不能为空")
                return
            
            # 验证Cookie格式
            if not CookieValidator.validate_cookie_string(cookie_string):
                print("❌ Cookie格式无效或缺少必需字段")
                return
            
            # 输入账号名称
            account_name = input("请输入账号名称（可选，回车使用默认名称）: ").strip()
            if not account_name:
                account_name = f"manual_account_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"✅ Cookie添加成功: {account_name}")
            print("💡 提示: Cookie已添加到统一管理器中")
            
        except Exception as e:
            print(f"❌ 添加Cookie失败: {e}")
    
    def delete_cookie(self):
        """删除指定Cookie"""
        try:
            status = self.unified_manager.get_comprehensive_status()
            pool_status = status["pool_status"]
            
            if pool_status["total_cookies"] == 0:
                print("❌ 没有可删除的Cookie")
                return
            
            print("\n" + "=" * 50)
            print("🗑️ 删除Cookie")
            print("=" * 50)
            
            # 显示当前Cookie列表
            available_cookies = self.unified_manager.get_available_cookies()
            if not available_cookies:
                print("❌ 没有可删除的Cookie")
                return
            
            print("当前可用Cookie:")
            for i, cookie_info in enumerate(available_cookies):
                print(f"{i + 1}. {cookie_info.name} (优先级: {cookie_info.priority})")
            
            # 选择要删除的Cookie
            try:
                choice = int(input("\n请选择要删除的Cookie编号: ")) - 1
                if 0 <= choice < len(available_cookies):
                    selected_cookie = available_cookies[choice]
                    # 标记为禁用
                    selected_cookie.enabled = False
                    print(f"✅ Cookie已禁用: {selected_cookie.name}")
                else:
                    print("❌ 无效的选择")
            except ValueError:
                print("❌ 请输入有效数字")
                
        except Exception as e:
            print(f"❌ 删除Cookie失败: {e}")
    
    def cleanup_expired_cookies(self):
        """清理过期Cookie"""
        try:
            print("\n" + "=" * 50)
            print("🧹 清理过期Cookie")
            print("=" * 50)
            
            # 获取失败的Cookie数量
            status = self.unified_manager.get_comprehensive_status()
            failed_count = status["pool_status"]["failed_cookies"]
            
            if failed_count == 0:
                print("✅ 没有需要清理的过期Cookie")
                return
            
            # 禁用失败的Cookie
            removed_count = 0
            for cookie_info in self.unified_manager.cookie_pool:
                if cookie_info.failure_count >= cookie_info.max_failures:
                    cookie_info.enabled = False
                    removed_count += 1
                    print(f"🗑️ 已禁用过期Cookie: {cookie_info.name}")
            
            print(f"✅ 清理完成，共禁用 {removed_count} 个过期Cookie")
            
        except Exception as e:
            print(f"❌ 清理过期Cookie失败: {e}")
    
    def cleanup_backup_files(self):
        """清理备份文件"""
        try:
            print("\n" + "=" * 50)
            print("🧹 清理备份文件")
            print("=" * 50)
            
            days = input("请输入保留天数（默认30天）: ").strip()
            try:
                keep_days = int(days) if days else 30
            except ValueError:
                keep_days = 30
            
            # 使用统一管理器清理备份文件
            self.unified_manager.cleanup_old_backup_files(keep_count=keep_days)
            print(f"✅ 备份文件清理完成，保留最新 {keep_days} 个文件")
            
        except Exception as e:
            print(f"❌ 清理备份文件失败: {e}")
    
    def show_detailed_info(self):
        """显示详细Cookie信息"""
        try:
            print("\n" + "=" * 60)
            print("📊 详细Cookie信息")
            print("=" * 60)
            
            status = self.unified_manager.get_comprehensive_status()
            
            # 显示Cookie池详情
            if self.unified_manager.cookie_pool:
                print("Cookie池详情:")
                for i, cookie_info in enumerate(self.unified_manager.cookie_pool):
                    status_emoji = "✅" if cookie_info.enabled else "❌"
                    health_emoji = {"healthy": "💚", "unhealthy": "❤️", "unknown": "💛"}.get(cookie_info.health_status, "💛")
                    
                    print(f"{i + 1}. {status_emoji} {cookie_info.name}")
                    print(f"   优先级: {cookie_info.priority}")
                    print(f"   健康状态: {health_emoji} {cookie_info.health_status}")
                    print(f"   失败次数: {cookie_info.failure_count}/{cookie_info.max_failures}")
                    print(f"   最后使用: {cookie_info.last_used or '从未使用'}")
                    print(f"   最后健康检查: {cookie_info.last_health_check or '从未检查'}")
                    print()
            else:
                print("❌ 没有找到Cookie池配置")
            
            # 显示当前Cookie状态
            current_status = status["current_status"]
            print("当前Cookie状态:")
            print(f"  有效Cookie: {'✅' if current_status['has_cookies'] else '❌'}")
            print(f"  Cookie数量: {current_status['cookie_count']}")
            print(f"  Cookie来源: {current_status['current_source']}")
            print(f"  备份文件数量: {current_status['backup_files_count']}")
            print(f"  运行环境: {status['environment']}")
            
        except Exception as e:
            print(f"❌ 显示详细信息失败: {e}")
    
    def run(self):
        """运行Cookie管理工具"""
        while True:
            try:
                self.display_menu()
                choice = input("\n请选择操作 (1-7): ").strip()
                
                if choice == "1":
                    self.show_cookie_status()
                elif choice == "2":
                    self.add_cookie_manually()
                elif choice == "3":
                    self.delete_cookie()
                elif choice == "4":
                    self.cleanup_expired_cookies()
                elif choice == "5":
                    self.cleanup_backup_files()
                elif choice == "6":
                    self.show_detailed_info()
                elif choice == "7":
                    print("👋 再见!")
                    break
                else:
                    print("❌ 无效的选择，请输入 1-7")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n👋 用户取消，再见!")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")
                input("\n按回车键继续...")


def main():
    """主函数"""
    tool = CookieManagerTool()
    tool.run()


if __name__ == "__main__":
    main()