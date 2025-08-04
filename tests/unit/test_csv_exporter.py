"""
Unit tests for CSV export functionality.

Tests CSVExporter with various data types and edge cases,
verifies proper UTF-8 encoding and special character handling,
and tests error handling for file operations and data conversion.
"""

import unittest
import tempfile
import os
import csv
import shutil
from unittest.mock import patch, mock_open
from typing import Dict, List, Any

from bilibili_core.storage.csv_exporter import CSVExporter


class TestCSVExporter(unittest.TestCase):
    """Test cases for CSVExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = CSVExporter(data_dir=self.temp_dir)
        
        # Sample test data
        self.sample_video_data = [
            {
                "video_id": "BV1234567890",
                "title": "Test Video 1",
                "description": "Test description with\nnewlines and\ttabs",
                "duration": 300,
                "view_count": 1000,
                "tags": [
                    {"tag_id": 1, "tag_name": "测试"},
                    {"tag_id": 2, "tag_name": "Test"}
                ],
                "category_info": {
                    "main_category": "科技",
                    "sub_category": "数码"
                }
            },
            {
                "video_id": "BV0987654321",
                "title": "Test Video 2 with special chars: 中文, émojis 🎉",
                "description": None,
                "duration": 600,
                "view_count": 2000,
                "tags": [],
                "category_info": {
                    "main_category": "娱乐",
                    "sub_category": None
                }
            }
        ]
        
        self.sample_comment_data = [
            {
                "comment_id": "123456",
                "content": "Great video! 👍\nVery helpful",
                "author": "TestUser",
                "like_count": 10,
                "reply_count": 2,
                "timestamp": "2025-01-01T12:00:00"
            },
            {
                "comment_id": "789012",
                "content": "Another comment with special chars: 中文评论",
                "author": "用户名",
                "like_count": 5,
                "reply_count": 0,
                "timestamp": "2025-01-01T13:00:00"
            }
        ]
        
        self.sample_up_data = {
            "up_id": "12345",
            "name": "Test UP主",
            "follower_count": 10000,
            "video_count": 50,
            "description": "Test UP description\nwith newlines",
            "avatar_url": "https://example.com/avatar.jpg"
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_default_values(self):
        """Test CSVExporter initialization with default values."""
        exporter = CSVExporter()
        self.assertEqual(exporter.data_dir, "data")
        self.assertEqual(exporter.encoding, "utf-8-sig")
        self.assertEqual(exporter.delimiter, ',')
    
    def test_init_custom_values(self):
        """Test CSVExporter initialization with custom values."""
        custom_dir = "/custom/path"
        custom_encoding = "utf-8"
        exporter = CSVExporter(data_dir=custom_dir, encoding=custom_encoding)
        self.assertEqual(exporter.data_dir, custom_dir)
        self.assertEqual(exporter.encoding, custom_encoding)
    
    def test_sanitize_value_none(self):
        """Test sanitizing None values."""
        result = self.exporter._sanitize_value(None)
        self.assertEqual(result, "")
    
    def test_sanitize_value_newlines_and_tabs(self):
        """Test sanitizing values with newlines and tabs."""
        test_value = "Text with\nnewlines and\ttabs\r\nand carriage returns"
        result = self.exporter._sanitize_value(test_value)
        expected = "Text with newlines and tabs  and carriage returns"
        self.assertEqual(result, expected)
    
    def test_sanitize_value_unicode(self):
        """Test sanitizing Unicode characters."""
        test_value = "中文测试 with émojis 🎉"
        result = self.exporter._sanitize_value(test_value)
        self.assertEqual(result, test_value)
    
    def test_sanitize_value_numbers(self):
        """Test sanitizing numeric values."""
        self.assertEqual(self.exporter._sanitize_value(123), "123")
        self.assertEqual(self.exporter._sanitize_value(123.45), "123.45")
    
    def test_flatten_dict_simple(self):
        """Test flattening simple dictionary."""
        data = {"key1": "value1", "key2": "value2"}
        result = self.exporter._flatten_dict(data)
        expected = {"key1": "value1", "key2": "value2"}
        self.assertEqual(result, expected)
    
    def test_flatten_dict_nested(self):
        """Test flattening nested dictionary."""
        data = {
            "level1": {
                "level2": {
                    "key": "value"
                }
            }
        }
        result = self.exporter._flatten_dict(data)
        expected = {"level1_level2_key": "value"}
        self.assertEqual(result, expected)
    
    def test_flatten_dict_with_list_of_dicts(self):
        """Test flattening dictionary with list of dictionaries."""
        data = {
            "tags": [
                {"id": 1, "name": "tag1"},
                {"id": 2, "name": "tag2"}
            ]
        }
        result = self.exporter._flatten_dict(data)
        self.assertIn("tags", result)
        self.assertIn("id:1, name:tag1", result["tags"])
        self.assertIn("id:2, name:tag2", result["tags"])
    
    def test_flatten_dict_with_simple_list(self):
        """Test flattening dictionary with simple list."""
        data = {"categories": ["cat1", "cat2", "cat3"]}
        result = self.exporter._flatten_dict(data)
        expected = {"categories": "cat1, cat2, cat3"}
        self.assertEqual(result, expected)
    
    def test_export_videos_to_csv_success(self):
        """Test successful video export to CSV."""
        file_path = os.path.join(self.temp_dir, "test_videos.csv")
        result = self.exporter.export_videos_to_csv(self.sample_video_data, file_path)
        
        self.assertEqual(result, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify CSV content
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            
            # Check first row
            first_row = rows[0]
            self.assertEqual(first_row['video_id'], 'BV1234567890')
            self.assertEqual(first_row['title'], 'Test Video 1')
            self.assertIn('测试', first_row['tags'])
    
    def test_export_videos_to_csv_empty_data(self):
        """Test video export with empty data."""
        file_path = os.path.join(self.temp_dir, "empty_videos.csv")
        result = self.exporter.export_videos_to_csv([], file_path)
        
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(file_path))
    
    def test_export_videos_to_csv_directory_creation(self):
        """Test that directories are created when they don't exist."""
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "videos.csv")
        result = self.exporter.export_videos_to_csv(self.sample_video_data, nested_path)
        
        self.assertEqual(result, nested_path)
        self.assertTrue(os.path.exists(nested_path))
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_export_videos_to_csv_permission_error(self, mock_file):
        """Test handling of permission errors during video export."""
        file_path = os.path.join(self.temp_dir, "permission_test.csv")
        result = self.exporter.export_videos_to_csv(self.sample_video_data, file_path)
        
        self.assertIsNone(result)
    
    def test_export_comments_to_csv_success(self):
        """Test successful comment export to CSV."""
        file_path = os.path.join(self.temp_dir, "test_comments.csv")
        result = self.exporter.export_comments_to_csv(
            self.sample_comment_data, file_path, "regular"
        )
        
        self.assertEqual(result, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify CSV content
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            
            # Check comment type is added
            for row in rows:
                self.assertEqual(row['comment_type'], 'regular')
    
    def test_export_comments_to_csv_hot_comments(self):
        """Test export of hot comments with proper type labeling."""
        file_path = os.path.join(self.temp_dir, "hot_comments.csv")
        result = self.exporter.export_comments_to_csv(
            self.sample_comment_data, file_path, "hot"
        )
        
        self.assertEqual(result, file_path)
        
        # Verify hot comment type
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            for row in rows:
                self.assertEqual(row['comment_type'], 'hot')
    
    def test_export_comments_to_csv_empty_data(self):
        """Test comment export with empty data."""
        file_path = os.path.join(self.temp_dir, "empty_comments.csv")
        result = self.exporter.export_comments_to_csv([], file_path, "regular")
        
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(file_path))
    
    @patch('builtins.open', side_effect=IOError("IO Error"))
    def test_export_comments_to_csv_io_error(self, mock_file):
        """Test handling of IO errors during comment export."""
        file_path = os.path.join(self.temp_dir, "io_error_test.csv")
        result = self.exporter.export_comments_to_csv(
            self.sample_comment_data, file_path, "regular"
        )
        
        self.assertIsNone(result)
    
    def test_export_up_info_to_csv_success(self):
        """Test successful UP info export to CSV."""
        file_path = os.path.join(self.temp_dir, "test_up_info.csv")
        result = self.exporter.export_up_info_to_csv(self.sample_up_data, file_path)
        
        self.assertEqual(result, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify CSV content
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            
            row = rows[0]
            self.assertEqual(row['up_id'], '12345')
            self.assertEqual(row['name'], 'Test UP主')
            self.assertIn('export_timestamp', row)
    
    def test_export_up_info_to_csv_empty_data(self):
        """Test UP info export with empty data."""
        file_path = os.path.join(self.temp_dir, "empty_up_info.csv")
        result = self.exporter.export_up_info_to_csv({}, file_path)
        
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(file_path))
    
    def test_export_up_info_to_csv_none_data(self):
        """Test UP info export with None data."""
        file_path = os.path.join(self.temp_dir, "none_up_info.csv")
        result = self.exporter.export_up_info_to_csv(None, file_path)
        
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(file_path))
    
    def test_export_combined_data_to_csv_success(self):
        """Test successful combined data export."""
        combined_data = {
            "videos": self.sample_video_data,
            "comments": self.sample_comment_data,
            "hot_comments": self.sample_comment_data,
            "up_info": self.sample_up_data
        }
        
        base_path = os.path.join(self.temp_dir, "combined_test")
        results = self.exporter.export_combined_data_to_csv(combined_data, base_path)
        
        # Check all expected files were created
        expected_files = ['videos', 'comments', 'hot_comments', 'up_info']
        for file_type in expected_files:
            self.assertIn(file_type, results)
            self.assertIsNotNone(results[file_type])
            self.assertTrue(os.path.exists(results[file_type]))
    
    def test_export_combined_data_to_csv_partial_data(self):
        """Test combined data export with only some data types."""
        combined_data = {
            "videos": self.sample_video_data,
            "up_info": self.sample_up_data
        }
        
        base_path = os.path.join(self.temp_dir, "partial_test")
        results = self.exporter.export_combined_data_to_csv(combined_data, base_path)
        
        # Check only expected files were created
        self.assertIn('videos', results)
        self.assertIn('up_info', results)
        self.assertNotIn('comments', results)
        self.assertNotIn('hot_comments', results)
    
    def test_export_combined_data_to_csv_empty_data(self):
        """Test combined data export with empty data."""
        combined_data = {}
        
        base_path = os.path.join(self.temp_dir, "empty_test")
        results = self.exporter.export_combined_data_to_csv(combined_data, base_path)
        
        self.assertEqual(results, {})
    
    def test_utf8_encoding_with_special_characters(self):
        """Test UTF-8 encoding with various special characters."""
        special_data = [
            {
                "title": "测试视频 with émojis 🎉🎊 and symbols ©®™",
                "description": "Description with quotes \"test\" and apostrophes 'test'",
                "content": "Content with commas, semicolons; and newlines\ntest"
            }
        ]
        
        file_path = os.path.join(self.temp_dir, "special_chars.csv")
        result = self.exporter.export_videos_to_csv(special_data, file_path)
        
        self.assertIsNotNone(result)
        
        # Verify content can be read back correctly
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertIn("测试视频", content)
            self.assertIn("🎉🎊", content)
            self.assertIn("©®™", content)
    
    def test_large_data_handling(self):
        """Test handling of large datasets."""
        # Create a large dataset
        large_data = []
        for i in range(1000):
            large_data.append({
                "id": f"video_{i}",
                "title": f"Video {i} with some content",
                "description": f"Description for video {i}" * 10,  # Make it longer
                "tags": [{"id": j, "name": f"tag_{j}"} for j in range(5)]
            })
        
        file_path = os.path.join(self.temp_dir, "large_data.csv")
        result = self.exporter.export_videos_to_csv(large_data, file_path)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify all data was written
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1000)


if __name__ == '__main__':
    unittest.main()