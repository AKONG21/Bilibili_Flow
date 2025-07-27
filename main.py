#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B站数据采集主入口
支持日任务、月任务等不同类型的数据采集任务
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bilibili_core.processors.daily_task_processor import DailyTaskProcessor
from bilibili_core.utils.logger import get_logger

logger = get_logger()


class BilibiliDataCollector:
    """B站数据采集器主类"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml"):
        self.config_file = config_file
        self.processor = None
    
    async def run_daily_task(self):
        """运行日任务"""
        logger.info("🌅 开始执行日任务")

        try:
            self.processor = DailyTaskProcessor(self.config_file, task_type="daily")
            await self.processor.initialize()

            print("开始执行每日任务...")
            result = await self.processor.run_task()

            if result:
                print("\n" + "=" * 60)
                print("✅ 日任务执行完成！")
                print("=" * 60)
                return True
            else:
                print("\n" + "=" * 60)
                print("❌ 日任务执行失败！")
                print("=" * 60)
                return False

        except Exception as e:
            logger.error(f"日任务执行失败: {e}")
            print(f"\n❌ 任务执行失败: {e}")
            return False
        finally:
            if self.processor:
                await self.processor.cleanup()
    
    async def run_monthly_task(self):
        """运行月任务"""
        logger.info("📅 开始执行月任务")

        try:
            # 月任务：获取全量视频，筛选前28天
            self.processor = DailyTaskProcessor(self.config_file, task_type="monthly")
            await self.processor.initialize()

            print("开始执行月度任务...")
            print("📋 月任务将获取全量视频并筛选前28天的数据")
            result = await self.processor.run_task()

            if result:
                print("\n" + "=" * 60)
                print("✅ 月任务执行完成！")
                print("=" * 60)
                return True
            else:
                print("\n" + "=" * 60)
                print("❌ 月任务执行失败！")
                print("=" * 60)
                return False

        except Exception as e:
            logger.error(f"月任务执行失败: {e}")
            print(f"\n❌ 任务执行失败: {e}")
            return False
        finally:
            if self.processor:
                await self.processor.cleanup()
    
    async def run_custom_task(self, **kwargs):
        """运行自定义任务"""
        logger.info("🔧 开始执行自定义任务")
        
        try:
            self.processor = DailyTaskProcessor(self.config_file)
            await self.processor.initialize()
            
            print("开始执行自定义任务...")
            # 这里可以根据kwargs参数执行不同的逻辑
            result = await self.processor.run_daily_task()
            
            if result:
                print("\n" + "=" * 60)
                print("✅ 自定义任务执行完成！")
                print("=" * 60)
                return True
            else:
                print("\n" + "=" * 60)
                print("❌ 自定义任务执行失败！")
                print("=" * 60)
                return False
                
        except Exception as e:
            logger.error(f"自定义任务执行失败: {e}")
            print(f"\n❌ 任务执行失败: {e}")
            return False
        finally:
            if self.processor:
                await self.processor.cleanup()


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="B站数据采集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                    # 运行日任务（默认）
  python main.py --type daily       # 运行日任务
  python main.py --type monthly     # 运行月任务
  python main.py --config custom.yaml  # 使用自定义配置文件
  
GitHub Actions环境变量:
  TASK_TYPE: daily|monthly|custom   # 任务类型
  CONFIG_FILE: config.yaml          # 配置文件路径
        """
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['daily', 'monthly', 'custom'],
        default='daily',
        help='任务类型 (默认: daily)'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='daily_task_config.yaml',
        help='配置文件路径 (默认: daily_task_config.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    
    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 支持从环境变量读取配置（用于GitHub Actions）
    task_type = os.getenv('TASK_TYPE', args.type)
    config_file = os.getenv('CONFIG_FILE', args.config)
    
    print("=" * 60)
    print("🚀 B站数据采集器")
    print("=" * 60)
    print(f"📋 任务类型: {task_type}")
    print(f"⚙️  配置文件: {config_file}")
    print(f"🕐 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        return 1
    
    # 创建采集器实例
    collector = BilibiliDataCollector(config_file)
    
    try:
        # 根据任务类型执行相应任务
        if task_type == 'daily':
            success = await collector.run_daily_task()
        elif task_type == 'monthly':
            success = await collector.run_monthly_task()
        elif task_type == 'custom':
            success = await collector.run_custom_task()
        else:
            print(f"❌ 未知的任务类型: {task_type}")
            return 1
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
        return 1
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
        print(f"\n❌ 程序执行异常: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
