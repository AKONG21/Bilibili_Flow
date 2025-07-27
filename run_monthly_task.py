#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B站数据跟踪系统 - 月任务脚本
使用统一存储模式：JSON + 数据库同时保存
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bilibili_core.processors.daily_task_processor import DailyTaskProcessor


async def main():
    """月任务主函数"""
    print("============================================================")
    print("🚀 B站月任务数据采集器")
    print("============================================================")
    print("正在初始化...")
    
    # 使用统一的处理器，只是任务类型设为 monthly
    processor = DailyTaskProcessor("daily_task_config.yaml", task_type="monthly")
    
    try:
        # 初始化处理器
        await processor.initialize()
        
        print("开始执行月任务...")
        
        # 执行任务
        result = await processor.run_task()
        
        if result:
            print("\n============================================================")
            print("任务执行完成！")
            print("============================================================")
            print("月任务: 获取全量242个视频")
            print("数据库: 直接保存全量视频")
            print("JSON: 前28天拆分存储")
            print("============================================================")
        else:
            print("❌ 任务执行失败")
            
    except Exception as e:
        print(f"❌ 任务执行出错: {e}")
        return False
        
    finally:
        # 清理资源
        await processor.close()
        
    return result


if __name__ == "__main__":
    asyncio.run(main())
