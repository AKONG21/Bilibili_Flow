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

from bilibili_core.cookie_management import AutoCookieManager


class CookieManagerTool:
    """Cookie管理工具"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml"):
        self.auto_manager = AutoCookieManager(config_file)
        
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
        if not self.auto_manager.load_config():
            print("❌ 配置文件加载失败")
            return
            
        self.auto_manager.display_cookie_status()
    
    def add_cookie_manually(self):
        """手动添加Cookie"""
        if not self.auto_manager.load_config():
            print("❌ 配置文件加载失败")
            return
        
        print("\n📝 手动添加Cookie")
        print("-" * 40)
        
        # 输入账号名称
        account_name = input("请输入账号名称 (留空自动生成): ").strip()
        if not account_name:
            timestamp = datetime.now().strftime("%m%d_%H%M")
            account_name = f"manual_{timestamp}"
        
        # 输入Cookie字符串
        print("\n请输入完整的Cookie字符串:")
        print("格式: SESSDATA=xxx; bili_jct=xxx; DedeUserID=xxx; ...")
        cookie_string = input("Cookie: ").strip()
        
        if not cookie_string:
            print("❌ Cookie字符串不能为空")
            return
        
        # 验证Cookie
        if not self.auto_manager.validate_cookie_string(cookie_string):
            print("❌ Cookie格式无效或缺少必需字段")
            return
        
        # 添加Cookie
        if self.auto_manager.add_cookie_to_config(cookie_string, account_name):
            print(f"✅ Cookie添加成功: {account_name}")
        else:
            print("❌ Cookie添加失败")
    
    def remove_cookie(self):
        """删除指定Cookie"""
        if not self.auto_manager.load_config():
            print("❌ 配置文件加载失败")
            return
        
        # 显示当前Cookie列表
        self.show_detailed_cookies()
        
        print("\n🗑️ 删除Cookie")
        print("-" * 40)
        
        account_name = input("请输入要删除的账号名称: ").strip()
        if not account_name:
            print("❌ 账号名称不能为空")
            return
        
        # 查找并删除Cookie
        cookie_pool = self.auto_manager.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})
        cookies_list = cookie_pool.get("cookies", [])
        
        found = False
        for cookie_config in cookies_list:
            if cookie_config.get("name") == account_name:
                cookie_config["cookie"] = ""
                cookie_config["enabled"] = False
                cookie_config["last_used"] = ""
                found = True
                break
        
        if found:
            if self.auto_manager.save_config():
                print(f"✅ Cookie删除成功: {account_name}")
            else:
                print("❌ 保存配置失败")
        else:
            print(f"❌ 未找到账号: {account_name}")
    
    def cleanup_expired(self):
        """清理过期Cookie"""
        if not self.auto_manager.load_config():
            print("❌ 配置文件加载失败")
            return
        
        print("\n🧹 清理过期Cookie")
        print("-" * 40)
        
        results = self.auto_manager.cleanup_all_expired()
        
        print(f"✅ 清理完成:")
        print(f"   - 配置文件Cookie: {results['config_cookies']} 个")
        print(f"   - 备份文件: {results['backup_files']} 个")
    
    def cleanup_backup_files(self):
        """清理备份文件"""
        if not self.auto_manager.load_config():
            print("❌ 配置文件加载失败")
            return
        
        print("\n🧹 清理备份文件")
        print("-" * 40)
        
        try:
            days = int(input("请输入保留天数 (默认30天): ") or "30")
        except ValueError:
            print("❌ 无效的天数")
            return
        
        backup_dir = self.auto_manager.config.get("login", {}).get("backup_cookies_dir", "cookies/backup_cookies")
        removed = self.auto_manager.remove_expired_backup_files(backup_dir, days)
        
        print(f"✅ 清理完成: 删除了 {removed} 个备份文件")
    
    def show_detailed_cookies(self):
        """显示详细Cookie信息"""
        if not self.auto_manager.load_config():
            print("❌ 配置文件加载失败")
            return
        
        print("\n📋 详细Cookie信息")
        print("-" * 80)
        
        cookie_pool = self.auto_manager.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})
        cookies_list = cookie_pool.get("cookies", [])
        
        if not cookies_list:
            print("📭 没有配置任何Cookie")
            return
        
        print(f"{'序号':<4} {'账号名称':<15} {'状态':<8} {'失败次数':<8} {'最后使用':<20} {'Cookie预览':<30}")
        print("-" * 80)
        
        for i, cookie_config in enumerate(cookies_list, 1):
            name = cookie_config.get("name", "unknown")
            enabled = "启用" if cookie_config.get("enabled", True) else "禁用"
            failure_count = cookie_config.get("failure_count", 0)
            last_used = cookie_config.get("last_used", "从未使用")
            if last_used and len(last_used) > 19:
                last_used = last_used[:19]
            
            cookie_preview = cookie_config.get("cookie", "")
            if cookie_preview:
                # 只显示前30个字符
                cookie_preview = cookie_preview[:30] + "..." if len(cookie_preview) > 30 else cookie_preview
            else:
                cookie_preview = "(空)"
            
            print(f"{i:<4} {name:<15} {enabled:<8} {failure_count:<8} {last_used:<20} {cookie_preview:<30}")
        
        print("-" * 80)
    
    def run(self):
        """运行工具"""
        while True:
            try:
                self.display_menu()
                choice = input("\n请选择操作 (1-7): ").strip()
                
                if choice == "1":
                    self.show_cookie_status()
                elif choice == "2":
                    self.add_cookie_manually()
                elif choice == "3":
                    self.remove_cookie()
                elif choice == "4":
                    self.cleanup_expired()
                elif choice == "5":
                    self.cleanup_backup_files()
                elif choice == "6":
                    self.show_detailed_cookies()
                elif choice == "7":
                    print("👋 退出Cookie管理工具")
                    break
                else:
                    print("❌ 无效的选项，请重新选择")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，退出工具")
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
