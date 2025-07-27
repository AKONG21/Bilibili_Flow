#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
运行每日任务的脚本
按照用户要求的数据结构输出
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bilibili_core.processors.daily_task_processor import DailyTaskProcessor


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 B站每日任务数据采集器")
    print("=" * 60)

    processor = DailyTaskProcessor()

    try:
        print("正在初始化...")
        await processor.initialize()
        
        print("开始执行每日任务...")
        result = await processor.run_daily_task()
        
        print("\n" + "=" * 60)
        print("任务执行完成！")
        print("=" * 60)
        print(f"UP主: {result['up_info'].get('name', 'Unknown')}")
        print(f"处理视频数: {result['statistics']['total_videos']}")
        print(f"收集评论数: {result['statistics']['total_comments']}")
        print(f"错误次数: {result['statistics']['errors_count']}")
        print(f"重试次数: {result['statistics']['retries_count']}")
        print(f"执行时长: {result['statistics']['duration_seconds']:.2f} 秒")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n用户中断任务")
        return 1
    except Exception as e:
        print(f"\n任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await processor.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
