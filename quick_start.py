#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B站数据跟踪系统 - 快速启动脚本
一键初始化数据库并运行月任务试运行
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    missing_deps = []
    
    # 检查Python模块
    required_modules = [
        ('aiofiles', 'aiofiles'),
        ('aiohttp', 'aiohttp'),
        ('playwright', 'playwright'),
        ('yaml', 'pyyaml'),
        ('requests', 'requests')
    ]

    for import_name, display_name in required_modules:
        try:
            __import__(import_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name}")
            missing_deps.append(display_name)
    
    # 检查增强存储模块
    try:
        from bilibili_core.storage.database_schema import DatabaseSchema
        print(f"   ✅ bilibili_core.storage")
    except ImportError as e:
        print(f"   ❌ bilibili_core.storage: {e}")
        missing_deps.append('bilibili_core.storage')
    
    if missing_deps:
        print(f"\n❌ 缺少依赖项: {', '.join(missing_deps)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖项检查通过")
    return True


def check_config_files():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")
    
    config_files = [
        'daily_task_config.yaml',
        'config.template.yaml'
    ]
    
    found_config = None
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   ✅ {config_file}")
            if found_config is None:
                found_config = config_file
        else:
            print(f"   ❌ {config_file}")
    
    if found_config:
        print(f"✅ 将使用配置文件: {found_config}")
        return found_config
    else:
        print("❌ 未找到配置文件")
        print("请确保存在 daily_task_config.yaml 或 config.template.yaml")
        return None


def check_directories():
    """检查并创建必要的目录"""
    print("\n🔍 检查目录结构...")
    
    required_dirs = [
        'data',
        'data/daily',
        'data/monthly',
        'data/cache',
        'logs',
        'cookies'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"   ✅ {dir_path} (已创建)")
            except Exception as e:
                print(f"   ❌ {dir_path}: {e}")
                return False
    
    print("✅ 目录结构检查完成")
    return True


def run_database_init():
    """运行数据库初始化"""
    print("\n🏗️ 初始化数据库...")
    
    try:
        # 运行数据库初始化脚本
        result = subprocess.run([
            sys.executable, 'init_database.py', '--force', '--test'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 数据库初始化成功")
            print(result.stdout)
            return True
        else:
            print("❌ 数据库初始化失败")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 数据库初始化异常: {e}")
        return False


async def run_monthly_task_trial(config_file):
    """运行月任务试运行"""
    print("\n🚀 运行月任务试运行...")
    
    try:
        # 导入并运行增强月任务
        from run_monthly_task_enhanced import EnhancedMonthlyTaskRunner
        
        runner = EnhancedMonthlyTaskRunner(
            config_file=config_file,
            dry_run=True  # 试运行模式
        )
        
        success = await runner.run()
        
        if success:
            print("✅ 月任务试运行成功")
            return True
        else:
            print("❌ 月任务试运行失败")
            return False
            
    except Exception as e:
        print(f"❌ 月任务试运行异常: {e}")
        return False


def display_next_steps():
    """显示后续步骤"""
    print("\n" + "=" * 80)
    print("🎉 快速启动完成！")
    print("=" * 80)
    
    print("\n💡 接下来可以执行:")
    print("   1. 正式运行月任务:")
    print("      python run_monthly_task_enhanced.py")
    print()
    print("   2. 运行日任务:")
    print("      python main.py --type daily")
    print()
    print("   3. 查看数据库内容:")
    print("      sqlite3 data/bilibili_tracking.db")
    print("      .tables")
    print("      SELECT COUNT(*) FROM video_records;")
    print()
    print("   4. 查看生成的文件:")
    print("      ls -la data/")
    print()
    print("   5. 配置多维表格同步 (可选):")
    print("      export MULTITABLE_API_KEY='your_api_key'")
    print("      export MULTITABLE_BASE_URL='https://open.feishu.cn/open-apis/bitable/v1'")
    print()
    print("   6. 运行测试:")
    print("      python tests/test_storage_architecture.py")
    
    print("\n📚 更多信息请查看:")
    print("   - bilibili_core/storage/README.md")
    print("   - .github/workflows/bilibili-tracking.yml")
    
    print("\n" + "=" * 80)


async def main():
    """主函数"""
    print("🚀 B站数据跟踪系统 - 快速启动")
    print("=" * 80)
    print("这个脚本将帮助您:")
    print("1. 检查依赖项和配置")
    print("2. 初始化数据库")
    print("3. 运行月任务试运行")
    print("=" * 80)
    
    # 询问用户是否继续
    response = input("\n是否继续？(Y/n): ")
    if response.lower() == 'n':
        print("❌ 用户取消操作")
        return 1
    
    try:
        # 1. 检查依赖项
        if not check_dependencies():
            return 1
        
        # 2. 检查配置文件
        config_file = check_config_files()
        if not config_file:
            return 1
        
        # 3. 检查目录结构
        if not check_directories():
            return 1
        
        # 4. 初始化数据库
        if not run_database_init():
            print("\n⚠️ 数据库初始化失败，但可以继续试运行")
            response = input("是否继续试运行？(y/N): ")
            if response.lower() != 'y':
                return 1
        
        # 5. 运行月任务试运行
        success = await run_monthly_task_trial(config_file)
        if not success:
            print("\n⚠️ 月任务试运行失败")
            return 1
        
        # 6. 显示后续步骤
        display_next_steps()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
        return 1
    except Exception as e:
        print(f"\n❌ 快速启动异常: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
