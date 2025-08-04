"""
Integration tests for complete workflow.

Tests end-to-end daily task execution with CSV export,
tests monthly task execution with hot comment collection,
and verifies data consistency between JSON and CSV formats.
"""

import unittest
import tempfile
import shutil
import os
import json
import csv
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from bilibili_core.processors.daily_task_processor import DailyTaskProcessor
from bilibili_core.storage.csv_exporter import CSVExporter
from bilibili_core.storage.simple_storage import SimpleStorage


class TestWorkflowIntegration(unittest.TestCase):
    """Integration test cases for complete workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample complete workflow data
        self.sample_up_info = {
            "mid": 1140672573,
            "name": "测试UP主",
            "fans": 50000,
            "up_video_count": 100,
            "sign": "测试签名",
            "level": 5
        }
        
        self.sample_videos_data = [
            {
                "aid": 123456,
                "bvid": "BV1234567890",
                "title": "测试视频1",
                "description": "测试描述1",
                "cover_url": "https://example.com/cover1.jpg",
                "video_url": "https://www.bilibili.com/video/BV1234567890",
                "duration": "5:30",
                "category": "科技",
                "publish_time": "2025-01-01T12:00:00+08:00",
                "view": 10000,
                "like": 500,
                "coin": 100,
                "favorite": 200,
                "share": 50,
                "reply": 25,
                "danmaku": 300,
                "tags": [
                    {
                        "tag_id": 1,
                        "tag_name": "测试标签1",
                        "category": "科技",
                        "likes": 10,
                        "hates": 0,
                        "subscribed": False
                    }
                ],
                "category_info": {
                    "main_category": "科技",
                    "sub_category": "数码",
                    "tid": 188
                },
                "hot_comments": [
                    {
                        "message": "很棒的视频！",
                        "mid": "111111",
                        "ctime": "2025-01-01T13:00:00+08:00",
                        "like": 50,
                        "rcount": 2
                    },
                    {
                        "message": "学到了很多",
                        "mid": "222222",
                        "ctime": "2025-01-01T14:00:00+08:00",
                        "like": 30,
                        "rcount": 1
                    }
                ]
            },
            {
                "aid": 789012,
                "bvid": "BV0987654321",
                "title": "测试视频2",
                "description": "测试描述2",
                "cover_url": "https://example.com/cover2.jpg",
                "video_url": "https://www.bilibili.com/video/BV0987654321",
                "duration": "10:15",
                "category": "娱乐",
                "publish_time": "2025-01-02T15:00:00+08:00",
                "view": 20000,
                "like": 800,
                "coin": 150,
                "favorite": 300,
                "share": 75,
                "reply": 40,
                "danmaku": 500,
                "tags": [
                    {
                        "tag_id": 2,
                        "tag_name": "测试标签2",
                        "category": "娱乐",
                        "likes": 15,
                        "hates": 1,
                        "subscribed": True
                    }
                ],
                "category_info": {
                    "main_category": "娱乐",
                    "sub_category": "综艺",
                    "tid": 71
                },
                "hot_comments": [
                    {
                        "message": "太有趣了！",
                        "mid": "333333",
                        "ctime": "2025-01-02T16:00:00+08:00",
                        "like": 80,
                        "rcount": 3
                    }
                ]
            }
        ]
        
        # Complete workflow data structure
        self.complete_workflow_data = {
            "up_info": self.sample_up_info,
            "videos": self.sample_videos_data,
            "task_info": {
                "task_type": "daily",
                "execution_time": "2025-01-01T10:00:00+08:00",
                "up_id": 1140672573,
                "total_videos": 2,
                "total_comments": 3
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_daily_task_end_to_end_with_csv_export(self):
        """Test complete daily task execution with CSV export."""
        # Create storage instances
        json_storage = SimpleStorage(
            data_dir=os.path.join(self.temp_dir, "json"),
            filename_format="daily_task_{timestamp}_{up_id}.json",
            timestamp_format="%Y%m%d_%H%M",
            task_type="daily"
        )
        
        csv_exporter = CSVExporter(
            data_dir=os.path.join(self.temp_dir, "csv"),
            encoding="utf-8-sig"
        )
        
        # Step 1: Store data in JSON format
        up_id = str(self.sample_up_info["mid"])
        
        # Initialize task
        json_storage.init_task(
            up_id=up_id,
            time_range={"start_date": "2025-01-01", "end_date": "2025-01-02"},
            config={"fields": {"up_info": {"enabled": True}}}
        )
        
        # Store UP info
        json_storage.store_up_info(self.sample_up_info)
        
        # Store videos
        for video in self.sample_videos_data:
            json_storage.store_video(video)
        
        # Finalize and get file path
        json_file_path = json_storage.finalize_task()
        
        # Verify JSON file was created
        self.assertIsNotNone(json_file_path)
        self.assertTrue(os.path.exists(json_file_path))
        
        # Step 2: Read and verify JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)
        
        self.assertEqual(stored_data["up_info"]["name"], "测试UP主")
        self.assertEqual(len(stored_data["videos"]), 2)
        self.assertEqual(stored_data["task_info"]["up_id"], up_id)
        
        # Step 3: Export to CSV format
        base_path = os.path.join(self.temp_dir, "csv", "daily_export")
        csv_results = csv_exporter.export_combined_data_to_csv(stored_data, base_path)
        
        # Verify CSV files were created
        self.assertIn("videos", csv_results)
        self.assertIn("up_info", csv_results)
        self.assertIsNotNone(csv_results["videos"])
        self.assertIsNotNone(csv_results["up_info"])
        
        # Step 4: Verify CSV content consistency
        # Check videos CSV
        videos_csv_path = csv_results["videos"]
        with open(videos_csv_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.DictReader(f)
            csv_videos = list(csv_reader)
        
        self.assertEqual(len(csv_videos), 2)
        
        # Verify video data consistency
        first_video_csv = csv_videos[0]
        first_video_json = stored_data["videos"][0]
        
        self.assertEqual(first_video_csv["title"], first_video_json["title"])
        self.assertEqual(first_video_csv["aid"], str(first_video_json["aid"]))
        self.assertEqual(first_video_csv["view"], str(first_video_json["view"]))
        
        # Verify hot comments are properly flattened in CSV
        self.assertIn("hot_comments", first_video_csv)
        self.assertIn("很棒的视频", first_video_csv["hot_comments"])
        
        # Check UP info CSV
        up_info_csv_path = csv_results["up_info"]
        with open(up_info_csv_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.DictReader(f)
            csv_up_info = list(csv_reader)
        
        self.assertEqual(len(csv_up_info), 1)
        up_info_csv = csv_up_info[0]
        
        self.assertEqual(up_info_csv["name"], self.sample_up_info["name"])
        self.assertEqual(up_info_csv["mid"], str(self.sample_up_info["mid"]))
        self.assertEqual(up_info_csv["fans"], str(self.sample_up_info["fans"]))
    
    def test_monthly_task_with_hot_comments_integration(self):
        """Test monthly task execution with hot comment collection."""
        # Create storage for monthly task
        monthly_storage = SimpleStorage(
            data_dir=os.path.join(self.temp_dir, "monthly"),
            filename_format="monthly_task_{timestamp}_{up_id}.json",
            timestamp_format="%Y%m%d",
            task_type="monthly"
        )
        
        # Modify task info for monthly task
        monthly_task_info = self.complete_workflow_data["task_info"].copy()
        monthly_task_info["task_type"] = "monthly"
        monthly_task_info["time_range_days"] = 30
        
        # Store monthly data
        up_id = str(self.sample_up_info["mid"])
        
        # Initialize monthly task
        monthly_storage.init_task(
            up_id=up_id,
            time_range={"start_date": "2024-12-01", "end_date": "2024-12-31"},
            config={"fields": {"up_info": {"enabled": True}}}
        )
        
        # Store UP info and videos
        monthly_storage.store_up_info(self.sample_up_info)
        for video in self.sample_videos_data:
            monthly_storage.store_video(video)
        
        # Finalize and get file path
        json_file_path = monthly_storage.finalize_task()
        
        # Verify monthly data structure
        with open(json_file_path, 'r', encoding='utf-8') as f:
            monthly_data = json.load(f)
        
        self.assertEqual(monthly_data["task_info"]["up_id"], up_id)
        
        # Verify hot comments are included
        for video in monthly_data["videos"]:
            self.assertIn("hot_comments", video)
            if video["aid"] == 123456:
                self.assertEqual(len(video["hot_comments"]), 2)
                self.assertEqual(video["hot_comments"][0]["message"], "很棒的视频！")
            elif video["aid"] == 789012:
                self.assertEqual(len(video["hot_comments"]), 1)
                self.assertEqual(video["hot_comments"][0]["message"], "太有趣了！")
        
        # Test CSV export for monthly data
        csv_exporter = CSVExporter(
            data_dir=os.path.join(self.temp_dir, "monthly_csv"),
            encoding="utf-8-sig"
        )
        
        base_path = os.path.join(self.temp_dir, "monthly_csv", "monthly_export")
        csv_results = csv_exporter.export_combined_data_to_csv(monthly_data, base_path)
        
        # Verify hot comments are properly exported in CSV
        videos_csv_path = csv_results["videos"]
        with open(videos_csv_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.DictReader(f)
            csv_videos = list(csv_reader)
        
        # Check that hot comments are serialized in CSV
        for csv_video in csv_videos:
            self.assertIn("hot_comments", csv_video)
            if csv_video["aid"] == "123456":
                self.assertIn("很棒的视频", csv_video["hot_comments"])
                self.assertIn("学到了很多", csv_video["hot_comments"])
    
    def test_data_consistency_between_json_and_csv(self):
        """Test data consistency between JSON and CSV formats."""
        # Store data in JSON
        json_storage = SimpleStorage(
            data_dir=os.path.join(self.temp_dir, "consistency_test"),
            filename_format="test_{timestamp}_{up_id}.json",
            timestamp_format="%Y%m%d_%H%M",
            task_type="daily"
        )
        
        up_id = str(self.sample_up_info["mid"])
        
        # Initialize task
        json_storage.init_task(
            up_id=up_id,
            time_range={"start_date": "2025-01-01", "end_date": "2025-01-02"},
            config={"fields": {"up_info": {"enabled": True}}}
        )
        
        # Store data
        json_storage.store_up_info(self.sample_up_info)
        for video in self.sample_videos_data:
            json_storage.store_video(video)
        
        # Finalize and get file path
        json_file_path = json_storage.finalize_task()
        
        # Read JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Export to CSV
        csv_exporter = CSVExporter(
            data_dir=os.path.join(self.temp_dir, "consistency_test"),
            encoding="utf-8-sig"
        )
        
        base_path = os.path.join(self.temp_dir, "consistency_test", "consistency_export")
        csv_results = csv_exporter.export_combined_data_to_csv(json_data, base_path)
        
        # Read CSV data
        videos_csv_path = csv_results["videos"]
        with open(videos_csv_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.DictReader(f)
            csv_videos = list(csv_reader)
        
        up_info_csv_path = csv_results["up_info"]
        with open(up_info_csv_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.DictReader(f)
            csv_up_info = list(csv_reader)[0]
        
        # Verify data consistency
        # Check video count
        self.assertEqual(len(json_data["videos"]), len(csv_videos))
        
        # Check specific video data consistency
        for i, json_video in enumerate(json_data["videos"]):
            csv_video = csv_videos[i]
            
            # Basic fields
            self.assertEqual(str(json_video["aid"]), csv_video["aid"])
            self.assertEqual(json_video["title"], csv_video["title"])
            self.assertEqual(str(json_video["view"]), csv_video["view"])
            self.assertEqual(str(json_video["like"]), csv_video["like"])
            
            # Complex fields (tags and category_info should be flattened)
            if json_video.get("tags"):
                self.assertIn("tags", csv_video)
                # Tags should be serialized as string in CSV
                for tag in json_video["tags"]:
                    self.assertIn(tag["tag_name"], csv_video["tags"])
            
            if json_video.get("category_info"):
                self.assertIn("category_info_main_category", csv_video)
                self.assertEqual(
                    json_video["category_info"]["main_category"],
                    csv_video["category_info_main_category"]
                )
            
            # Hot comments should be serialized
            if json_video.get("hot_comments"):
                self.assertIn("hot_comments", csv_video)
                for comment in json_video["hot_comments"]:
                    self.assertIn(comment["message"], csv_video["hot_comments"])
        
        # Check UP info consistency
        self.assertEqual(str(json_data["up_info"]["mid"]), csv_up_info["mid"])
        self.assertEqual(json_data["up_info"]["name"], csv_up_info["name"])
        self.assertEqual(str(json_data["up_info"]["fans"]), csv_up_info["fans"])
    
    def test_workflow_error_handling_and_recovery(self):
        """Test workflow error handling and recovery mechanisms."""
        # Test normal workflow first
        json_storage = SimpleStorage(
            data_dir=os.path.join(self.temp_dir, "error_test"),
            filename_format="test_{timestamp}_{up_id}.json",
            timestamp_format="%Y%m%d_%H%M",
            task_type="daily"
        )
        
        up_id = str(self.sample_up_info["mid"])
        
        # Test normal workflow
        json_storage.init_task(
            up_id=up_id,
            time_range={"start_date": "2025-01-01", "end_date": "2025-01-02"},
            config={"fields": {"up_info": {"enabled": True}}}
        )
        
        json_storage.store_up_info(self.sample_up_info)
        json_file_path = json_storage.finalize_task()
        
        # Should succeed
        self.assertIsNotNone(json_file_path)
        self.assertTrue(os.path.exists(json_file_path))
        
        # Test CSV export with invalid data structure
        csv_exporter = CSVExporter(
            data_dir=self.temp_dir,
            encoding="utf-8-sig"
        )
        
        # Test with invalid data structure
        invalid_data = {"invalid": "structure"}
        base_path = os.path.join(self.temp_dir, "error_test")
        csv_results = csv_exporter.export_combined_data_to_csv(invalid_data, base_path)
        
        # Should return empty results for invalid data
        self.assertEqual(csv_results, {})
        
        # Test CSV export with partially valid data
        partial_data = {
            "up_info": self.sample_up_info,
            "videos": [],  # Empty videos list
            "invalid_key": "should_be_ignored"
        }
        
        csv_results = csv_exporter.export_combined_data_to_csv(partial_data, base_path)
        
        # Should export UP info but not videos (empty list)
        self.assertIn("up_info", csv_results)
        self.assertNotIn("videos", csv_results)
    
    def test_large_dataset_workflow_performance(self):
        """Test workflow performance with large datasets."""
        # Create a large dataset
        large_videos_data = []
        for i in range(100):  # 100 videos
            video = self.sample_videos_data[0].copy()
            video["aid"] = 123456 + i
            video["bvid"] = f"BV{123456 + i:010d}"
            video["title"] = f"测试视频{i + 1}"
            
            # Add multiple hot comments
            video["hot_comments"] = []
            for j in range(5):  # 5 comments per video
                comment = {
                    "message": f"评论{j + 1} for video {i + 1}",
                    "mid": f"{111111 + j}",
                    "ctime": "2025-01-01T13:00:00+08:00",
                    "like": 10 + j,
                    "rcount": j
                }
                video["hot_comments"].append(comment)
            
            large_videos_data.append(video)
        
        # Test JSON storage with large dataset
        json_storage = SimpleStorage(
            data_dir=os.path.join(self.temp_dir, "large_test"),
            filename_format="large_test_{timestamp}_{up_id}.json",
            timestamp_format="%Y%m%d_%H%M",
            task_type="daily"
        )
        
        up_id = str(self.sample_up_info["mid"])
        
        # Initialize task
        json_storage.init_task(
            up_id=up_id,
            time_range={"start_date": "2025-01-01", "end_date": "2025-01-02"},
            config={"fields": {"up_info": {"enabled": True}}}
        )
        
        # Store data
        json_storage.store_up_info(self.sample_up_info)
        for video in large_videos_data:
            json_storage.store_video(video)
        
        # Finalize and get file path
        json_file_path = json_storage.finalize_task()
        
        # Verify large dataset was stored
        self.assertIsNotNone(json_file_path)
        self.assertTrue(os.path.exists(json_file_path))
        
        # Verify file size is reasonable (should be > 0)
        file_size = os.path.getsize(json_file_path)
        self.assertGreater(file_size, 1000)  # Should be at least 1KB
        
        # Test CSV export with large dataset
        with open(json_file_path, 'r', encoding='utf-8') as f:
            large_data = json.load(f)
        
        csv_exporter = CSVExporter(
            data_dir=os.path.join(self.temp_dir, "large_csv"),
            encoding="utf-8-sig"
        )
        
        base_path = os.path.join(self.temp_dir, "large_csv", "large_export")
        csv_results = csv_exporter.export_combined_data_to_csv(large_data, base_path)
        
        # Verify CSV export succeeded
        self.assertIn("videos", csv_results)
        self.assertIsNotNone(csv_results["videos"])
        
        # Verify CSV content
        videos_csv_path = csv_results["videos"]
        with open(videos_csv_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.DictReader(f)
            csv_videos = list(csv_reader)
        
        # Should have all 100 videos
        self.assertEqual(len(csv_videos), 100)
        
        # Verify hot comments are properly serialized
        first_video = csv_videos[0]
        self.assertIn("hot_comments", first_video)
        self.assertIn("评论1 for video 1", first_video["hot_comments"])
    
    def test_unicode_and_special_characters_workflow(self):
        """Test workflow with Unicode and special characters."""
        # Create data with various Unicode characters
        unicode_up_info = {
            "mid": 1140672573,
            "name": "测试UP主 with émojis 🎉🎊",
            "fans": 50000,
            "sign": "签名包含特殊字符: ©®™ and newlines\nand tabs\t"
        }
        
        unicode_video = {
            "aid": 123456,
            "bvid": "BV1234567890",
            "title": "中文标题 with émojis 🎥📺 and symbols ©®™",
            "description": "描述包含换行\n和制表符\t以及引号\"test\"",
            "category": "科技分类",
            "view": 10000,
            "like": 500,
            "hot_comments": [
                {
                    "message": "中文评论 with émojis 🎉 and quotes \"amazing\"",
                    "mid": "111111",
                    "ctime": "2025-01-01T13:00:00+08:00",
                    "like": 50,
                    "rcount": 2
                }
            ]
        }
        
        # Test JSON storage
        json_storage = SimpleStorage(
            data_dir=os.path.join(self.temp_dir, "unicode_test"),
            filename_format="unicode_test_{timestamp}_{up_id}.json",
            timestamp_format="%Y%m%d_%H%M",
            task_type="daily"
        )
        
        up_id = str(unicode_up_info["mid"])
        
        # Initialize task
        json_storage.init_task(
            up_id=up_id,
            time_range={"start_date": "2025-01-01", "end_date": "2025-01-02"},
            config={"fields": {"up_info": {"enabled": True}}}
        )
        
        # Store data
        json_storage.store_up_info(unicode_up_info)
        json_storage.store_video(unicode_video)
        
        # Finalize and get file path
        json_file_path = json_storage.finalize_task()
        
        # Verify JSON storage preserves Unicode
        with open(json_file_path, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)
        
        self.assertIn("🎉🎊", stored_data["up_info"]["name"])
        self.assertIn("🎥📺", stored_data["videos"][0]["title"])
        self.assertIn("🎉", stored_data["videos"][0]["hot_comments"][0]["message"])
        
        # Test CSV export preserves Unicode
        csv_exporter = CSVExporter(
            data_dir=os.path.join(self.temp_dir, "unicode_csv"),
            encoding="utf-8-sig"
        )
        
        base_path = os.path.join(self.temp_dir, "unicode_csv", "unicode_export")
        csv_results = csv_exporter.export_combined_data_to_csv(stored_data, base_path)
        
        # Verify CSV preserves Unicode
        videos_csv_path = csv_results["videos"]
        with open(videos_csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertIn("🎥📺", content)
            self.assertIn("🎉", content)
            self.assertIn("中文标题", content)
        
        up_info_csv_path = csv_results["up_info"]
        with open(up_info_csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertIn("🎉🎊", content)
            self.assertIn("测试UP主", content)


if __name__ == '__main__':
    unittest.main()