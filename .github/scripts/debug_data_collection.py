#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试数据收集问题的脚本
用于在 GitHub Actions 中诊断数据采集失败的原因
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def debug_environment():
    """调试环境信息"""
    print("=" * 60)
    print("🔍 环境调试信息")
    print("=" * 60)
    
    # 检查Python环境
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path[:3]}...")
    
    # 检查文件结构
    print("\n📁 文件结构检查:")
    for root, dirs, files in os.walk(".", topdown=True):
        level = root.replace(".", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files[:5]:  # 只显示前5个文件
            print(f"{subindent}{file}")
        if len(files) > 5:
            print(f"{subindent}... 还有 {len(files) - 5} 个文件")
        if level > 2:  # 限制深度
            dirs.clear()
    
    # 检查配置文件
    print("\n📋 配置文件检查:")
    config_files = ["daily_task_config.yaml", "requirements.txt"]
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file} 存在")
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   大小: {len(content)} 字符")
        else:
            print(f"❌ {config_file} 不存在")
    
    # 检查环境变量
    print("\n🔐 Cookie环境变量检查:")
    cookie_vars = [f"BILIBILI_COOKIES_{i}" for i in range(1, 11)] + ["BILIBILI_COOKIES"]
    found_cookies = 0
    for var in cookie_vars:
        value = os.environ.get(var)
        if value:
            found_cookies += 1
            print(f"✅ {var}: 已设置 (长度: {len(value)})")
        else:
            print(f"❌ {var}: 未设置")
    
    print(f"\n总共找到 {found_cookies} 个Cookie配置")
    
    # 检查数据目录
    print("\n📊 数据目录检查:")
    data_dir = "data"
    if os.path.exists(data_dir):
        print(f"✅ {data_dir} 目录存在")
        for subdir in ["daily", "monthly", "database", "reports"]:
            subdir_path = os.path.join(data_dir, subdir)
            if os.path.exists(subdir_path):
                files = os.listdir(subdir_path)
                print(f"   {subdir}/: {len(files)} 个文件")
            else:
                print(f"   {subdir}/: 不存在")
    else:
        print(f"❌ {data_dir} 目录不存在")

async def test_basic_imports():
    """测试基本模块导入"""
    print("\n" + "=" * 60)
    print("📦 模块导入测试")
    print("=" * 60)
    
    modules_to_test = [
        "httpx",
        "playwright",
        "pandas", 
        "aiofiles",
        "yaml",
        "requests"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: 导入成功")
        except ImportError as e:
            print(f"❌ {module}: 导入失败 - {e}")
    
    # 测试项目模块
    print("\n🏗️ 项目模块测试:")
    try:
        from bilibili_core.processors.daily_task_processor import DailyTaskProcessor
        print("✅ DailyTaskProcessor: 导入成功")
    except Exception as e:
        print(f"❌ DailyTaskProcessor: 导入失败 - {e}")

async def test_config_loading():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("⚙️ 配置加载测试")
    print("=" * 60)
    
    try:
        import yaml
        with open("daily_task_config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("✅ 配置文件加载成功")
        print(f"   UP ID: {config.get('task_config', {}).get('up_id', 'N/A')}")
        print(f"   存储压缩: {config.get('storage', {}).get('compress', 'N/A')}")
        print(f"   日志级别: {config.get('system', {}).get('log_level', 'N/A')}")
        
        # 检查Cookie配置
        cookie_config = config.get('login', {}).get('cookies', {})
        raw_cookie = cookie_config.get('raw_cookie', '')
        if raw_cookie:
            print(f"   配置文件Cookie: 已设置 (长度: {len(raw_cookie)})")
        else:
            print("   配置文件Cookie: 未设置")
            
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")

async def create_debug_report():
    """创建调试报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "environment": "github_actions",
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "debug_status": "completed"
    }
    
    # 保存调试报告
    with open("debug_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 调试报告已保存到: debug_report.json")

async def main():
    """主函数"""
    print("🚀 开始调试数据收集问题...")
    
    await debug_environment()
    await test_basic_imports()
    await test_config_loading()
    await create_debug_report()
    
    print("\n" + "=" * 60)
    print("✅ 调试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())