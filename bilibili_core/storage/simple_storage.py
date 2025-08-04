# -*- coding: utf-8 -*-
"""
简化数据存储系统
每次任务生成一个独立的JSON文件，包含完整的采集数据
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..utils.logger import get_logger
from .csv_exporter import CSVExporter

logger = get_logger()


class SimpleStorage:
    """简化存储系统"""

    def __init__(self, data_dir: str = "data", filename_format: str = "bilibili_data_{timestamp}_{up_id}.json",
                 timestamp_format: str = "%Y%m%d_%H%M%S", task_type: str = "daily", 
                 export_format: str = "json", csv_options: Optional[Dict[str, Any]] = None):
        self.data_dir = data_dir
        self.filename_format = filename_format
        self.timestamp_format = timestamp_format  # 新增：时间戳格式
        self.task_type = task_type  # 新增：任务类型
        self.export_format = export_format  # 新增：导出格式 (json, csv, both)
        self.csv_options = csv_options or {}  # 新增：CSV选项
        
        # 初始化CSV导出器
        if export_format in ["csv", "both"]:
            csv_encoding = self.csv_options.get("encoding", "utf-8-sig")
            self.csv_exporter = CSVExporter(data_dir=data_dir, encoding=csv_encoding)
        else:
            self.csv_exporter = None
        self.current_task_data = {
            "task_info": {},
            "up_info": {},
            "videos": [],
            "hot_comments": [],  # 新增：热门评论数据
            "statistics": {
                "total_videos": 0,
                "total_comments": 0,
                "collection_time": None,
                "time_range": {},
                "errors": []
            }
        }

        # 确保基础目录存在
        os.makedirs(data_dir, exist_ok=True)
    
    def init_task(self, up_id: str, time_range: Dict[str, str], config: Dict[str, Any]):
        """
        初始化任务
        Args:
            up_id: UP主ID
            time_range: 时间范围
            config: 配置信息
        """
        self.current_task_data = {
            "task_info": {
                "up_id": up_id,
                "collection_time": datetime.now().isoformat(),
                "time_range": time_range,
                "config": {
                    "enabled_fields": {
                        "up_info": config.get("fields", {}).get("up_info", {}).get("enabled", True),
                        "video_info": config.get("fields", {}).get("video_info", {}).get("enabled", True),
                        "comments": config.get("fields", {}).get("comments", {}).get("enabled", True),
                    },
                    "max_comments": config.get("fields", {}).get("comments", {}).get("max_comments", 10),
                    "request_delay": config.get("system", {}).get("request_delay", 2)
                }
            },
            "up_info": {},
            "videos": [],
            "statistics": {
                "total_videos": 0,
                "total_comments": 0,
                "collection_start_time": datetime.now().isoformat(),
                "collection_end_time": None,
                "time_range": time_range,
                "errors": []
            }
        }
        
        logger.info(f"任务初始化完成: UP主ID={up_id}, 时间范围={time_range}")
    
    def store_up_info(self, up_data: Dict[str, Any]):
        """
        存储UP主信息
        Args:
            up_data: UP主数据
        """
        self.current_task_data["up_info"] = up_data
        logger.info(f"UP主信息已存储: {up_data.get('up_name', 'Unknown')}")
    
    def store_video(self, video_data: Dict[str, Any]):
        """
        存储视频数据
        Args:
            video_data: 视频数据
        """
        # 提取评论数据
        hot_comments_json = video_data.get("hot_comments_json", "[]")
        try:
            hot_comments = json.loads(hot_comments_json) if isinstance(hot_comments_json, str) else hot_comments_json
            comment_count = len(hot_comments) if isinstance(hot_comments, list) else 0
        except:
            comment_count = 0
        
        # 存储视频数据
        self.current_task_data["videos"].append(video_data)
        
        # 更新统计
        self.current_task_data["statistics"]["total_videos"] += 1
        self.current_task_data["statistics"]["total_comments"] += comment_count
        
        logger.info(f"视频数据已存储: {video_data.get('video_title', 'Unknown')} (评论数: {comment_count})")
    
    def store_hot_comments(self, hot_comments_data: List[Dict[str, Any]]):
        """
        存储热门评论数据
        Args:
            hot_comments_data: 热门评论数据列表
        """
        if hot_comments_data:
            self.current_task_data["hot_comments"].extend(hot_comments_data)
            logger.info(f"热门评论数据已存储: {len(hot_comments_data)}条")
    
    def add_error(self, error_msg: str, error_type: str = "general"):
        """
        添加错误记录
        Args:
            error_msg: 错误消息
            error_type: 错误类型
        """
        error_record = {
            "type": error_type,
            "message": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_task_data["statistics"]["errors"].append(error_record)
        logger.error(f"错误记录已添加: {error_type} - {error_msg}")
    
    def finalize_task(self) -> str:
        """
        完成任务并保存数据
        Returns:
            str: 保存的文件路径
        """
        # 更新结束时间
        self.current_task_data["statistics"]["collection_end_time"] = datetime.now().isoformat()

        # 计算持续时间
        start_time = datetime.fromisoformat(self.current_task_data["statistics"]["collection_start_time"])
        end_time = datetime.fromisoformat(self.current_task_data["statistics"]["collection_end_time"])
        duration = (end_time - start_time).total_seconds()
        self.current_task_data["statistics"]["duration_seconds"] = duration

        # 生成文件名（使用配置的时间戳格式，使用北京时间）
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        beijing_now = datetime.now(beijing_tz)
        timestamp = beijing_now.strftime(self.timestamp_format)
        up_id = self.current_task_data["task_info"]["up_id"]
        filename = self.filename_format.format(timestamp=timestamp, up_id=up_id)

        # 根据任务类型确定最终存储路径
        if self.task_type == "daily":
            # 日任务：按周分文件夹存储（使用北京时间计算周数）
            year, week_num, _ = beijing_now.isocalendar()
            weekly_dir = f"{self.data_dir}/{year}-W{week_num:02d}"
            os.makedirs(weekly_dir, exist_ok=True)
            filepath = os.path.join(weekly_dir, filename)
        else:
            # 月任务：直接使用配置的目录，避免重复添加 monthly 路径
            os.makedirs(self.data_dir, exist_ok=True)
            filepath = os.path.join(self.data_dir, filename)
        
        # 保存数据
        try:
            saved_files = {}
            
            # 保存JSON格式（如果需要）
            if self.export_format in ["json", "both"]:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_task_data, f, indent=2, ensure_ascii=False)
                saved_files["json"] = filepath
                logger.info(f"JSON数据已保存: {filepath}")
            
            # 保存CSV格式（如果需要）
            if self.export_format in ["csv", "both"] and self.csv_exporter:
                # 生成CSV文件的基础路径（去掉.json扩展名）
                csv_base_path = filepath.replace('.json', '')
                
                # 导出各种数据类型到CSV
                csv_results = self.csv_exporter.export_combined_data_to_csv(
                    self.current_task_data, csv_base_path
                )
                
                # 记录成功导出的CSV文件
                for data_type, csv_path in csv_results.items():
                    if csv_path:
                        saved_files[f"csv_{data_type}"] = csv_path
                        logger.info(f"CSV数据已保存 ({data_type}): {csv_path}")
            
            self.print_task_summary()
            
            # 返回主要文件路径（JSON优先，否则返回第一个CSV文件）
            if "json" in saved_files:
                return saved_files["json"]
            elif saved_files:
                return list(saved_files.values())[0]
            else:
                return filepath
            
        except Exception as e:
            logger.error(f"保存任务数据失败: {e}")
            raise
    
    def print_task_summary(self):
        """打印任务摘要"""
        stats = self.current_task_data["statistics"]
        task_info = self.current_task_data["task_info"]
        up_info = self.current_task_data["up_info"]
        
        logger.info("=" * 60)
        logger.info("任务完成摘要:")
        logger.info(f"UP主: {up_info.get('up_name', 'Unknown')} (ID: {task_info['up_id']})")
        logger.info(f"粉丝数: {up_info.get('up_fans', 'Unknown'):,}" if up_info.get('up_fans') else "粉丝数: Unknown")
        logger.info(f"视频总数: {up_info.get('up_video_count', 'Unknown')}" if up_info.get('up_video_count') else "视频总数: Unknown")
        logger.info(f"时间范围: {stats['time_range'].get('start_date', 'Unknown')} 到 {stats['time_range'].get('end_date', 'Unknown')}")
        logger.info(f"采集视频数: {stats['total_videos']}")
        logger.info(f"采集评论数: {stats['total_comments']}")
        logger.info(f"错误次数: {len(stats['errors'])}")
        logger.info(f"执行时长: {stats.get('duration_seconds', 0):.1f}秒")
        
        # 显示字段完整性
        if self.current_task_data["videos"]:
            sample_video = self.current_task_data["videos"][0]
            field_count = len([k for k in sample_video.keys() if not k.startswith('_')])
            logger.info(f"字段完整性: {field_count}个字段/视频")
        
        logger.info("=" * 60)
    
    def get_field_coverage_report(self) -> Dict[str, Any]:
        """
        生成字段覆盖率报告
        Returns:
            Dict: 字段覆盖率报告
        """
        if not self.current_task_data["videos"]:
            return {"error": "没有视频数据"}
        
        # 统计所有字段
        all_fields = set()
        field_counts = {}
        
        for video in self.current_task_data["videos"]:
            for field in video.keys():
                all_fields.add(field)
                if field not in field_counts:
                    field_counts[field] = 0
                if video[field] is not None and video[field] != "":
                    field_counts[field] += 1
        
        total_videos = len(self.current_task_data["videos"])
        
        # 计算覆盖率
        field_coverage = {}
        for field in all_fields:
            coverage = (field_counts.get(field, 0) / total_videos) * 100
            field_coverage[field] = {
                "count": field_counts.get(field, 0),
                "total": total_videos,
                "coverage": round(coverage, 1)
            }
        
        # 按类别分组
        up_fields = {k: v for k, v in field_coverage.items() if k.startswith('up_')}
        video_fields = {k: v for k, v in field_coverage.items() if k.startswith('video_')}
        comment_fields = {k: v for k, v in field_coverage.items() if 'comment' in k}
        other_fields = {k: v for k, v in field_coverage.items() 
                       if not k.startswith('up_') and not k.startswith('video_') and 'comment' not in k}
        
        return {
            "total_videos": total_videos,
            "total_fields": len(all_fields),
            "categories": {
                "up_info": up_fields,
                "video_info": video_fields,
                "comments": comment_fields,
                "other": other_fields
            },
            "summary": {
                "up_fields_count": len(up_fields),
                "video_fields_count": len(video_fields),
                "comment_fields_count": len(comment_fields),
                "avg_coverage": round(sum(v["coverage"] for v in field_coverage.values()) / len(field_coverage), 1)
            }
        }
    
    def print_field_coverage_report(self):
        """打印字段覆盖率报告"""
        report = self.get_field_coverage_report()
        
        if "error" in report:
            logger.warning(f"字段覆盖率报告生成失败: {report['error']}")
            return
        
        logger.info("=" * 60)
        logger.info("字段覆盖率报告:")
        logger.info(f"总视频数: {report['total_videos']}")
        logger.info(f"总字段数: {report['total_fields']}")
        logger.info(f"平均覆盖率: {report['summary']['avg_coverage']}%")
        
        for category, fields in report["categories"].items():
            if fields:
                logger.info(f"\n{category} ({len(fields)}个字段):")
                for field, stats in sorted(fields.items()):
                    logger.info(f"  {field}: {stats['count']}/{stats['total']} ({stats['coverage']}%)")
        
        logger.info("=" * 60)
    
    def list_data_files(self) -> List[str]:
        """
        列出所有数据文件
        Returns:
            List[str]: 数据文件列表
        """
        try:
            files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
            files.sort(reverse=True)  # 按时间倒序
            return files
        except Exception as e:
            logger.error(f"列出数据文件失败: {e}")
            return []
    
    def load_data_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        加载指定的数据文件
        Args:
            filename: 文件名
        Returns:
            Dict: 数据内容
        """
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据文件失败 {filename}: {e}")
            return None
