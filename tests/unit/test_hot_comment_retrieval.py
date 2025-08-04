"""
Unit tests for hot comment retrieval functionality.

Tests hot comment collection with different video types,
verifies proper integration with existing comment system,
and tests error handling for hot comment API failures.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from bilibili_core.processors.daily_task_processor import DailyTaskProcessor
from bilibili_core.client.exceptions import DataFetchError
from bilibili_core.client.field import CommentOrderType


class TestHotCommentRetrieval(unittest.TestCase):
    """Test cases for hot comment retrieval functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create processor instance with mocked dependencies
        self.processor = DailyTaskProcessor(task_type="monthly")
        
        # Mock logger
        self.processor.logger = MagicMock()
        
        # Mock config
        self.processor.config = {
            "task_config": {
                "monthly_task": {
                    "hot_comments_json": {
                        "enabled": True,
                        "fields": ["message", "mid", "ctime", "like", "rcount"],
                        "max_count": 10
                    }
                },
                "daily_task": {
                    "hot_comments_json": {
                        "enabled": True,
                        "fields": ["message", "mid", "ctime", "like", "rcount"],
                        "max_count": 10
                    }
                }
            }
        }
        
        # Mock bilibili client
        self.processor.bili_client = MagicMock()
        
        # Mock stats
        self.processor.stats = {
            "comments_collected": 0,
            "errors": 0,
            "retries": 0
        }
        
        # Sample hot comment response
        self.sample_hot_comments_response = {
            "replies": [
                {
                    "rpid": 123456789,
                    "oid": 987654321,
                    "type": 1,
                    "mid": 111111,
                    "root": 0,
                    "parent": 0,
                    "dialog": 0,
                    "count": 5,
                    "rcount": 3,
                    "state": 0,
                    "fansgrade": 0,
                    "attr": 0,
                    "ctime": 1640995200,
                    "rpid_str": "123456789",
                    "root_str": "0",
                    "parent_str": "0",
                    "like": 100,
                    "action": 0,
                    "member": {
                        "mid": "111111",
                        "uname": "测试用户1",
                        "sex": "男",
                        "sign": "这是一个测试用户",
                        "avatar": "https://example.com/avatar1.jpg",
                        "rank": "10000",
                        "DisplayRank": "0",
                        "level_info": {
                            "current_level": 5,
                            "current_min": 10800,
                            "current_exp": 28421,
                            "next_exp": 28800
                        },
                        "pendant": {
                            "pid": 0,
                            "name": "",
                            "image": "",
                            "expire": 0,
                            "image_enhance": "",
                            "image_enhance_frame": ""
                        },
                        "nameplate": {
                            "nid": 0,
                            "name": "",
                            "image": "",
                            "image_small": "",
                            "level": "",
                            "condition": ""
                        },
                        "official_verify": {
                            "type": -1,
                            "desc": ""
                        },
                        "vip": {
                            "vipType": 1,
                            "vipDueDate": 1640995200000,
                            "dueRemark": "",
                            "accessStatus": 0,
                            "vipStatus": 0,
                            "vipStatusWarn": "",
                            "themeType": 0,
                            "label": {
                                "path": "",
                                "text": "",
                                "label_theme": "",
                                "text_color": "",
                                "bg_style": 0,
                                "bg_color": "",
                                "border_color": ""
                            },
                            "avatar_subscript": 0,
                            "nickname_color": ""
                        },
                        "fans_detail": None,
                        "following": 0,
                        "is_followed": 0,
                        "user_sailing": {
                            "pendant": None,
                            "cardbg": None,
                            "cardbg_with_focus": None
                        },
                        "is_contractor": False,
                        "contract_desc": ""
                    },
                    "content": {
                        "message": "这是一条测试热门评论！👍",
                        "plat": 2,
                        "device": "",
                        "members": [],
                        "jump_url": {},
                        "max_line": 6
                    },
                    "replies": None,
                    "assist": 0,
                    "folder": {
                        "has_folded": False,
                        "is_folded": False,
                        "rule": ""
                    },
                    "up_action": {
                        "like": False,
                        "reply": False
                    },
                    "show_follow": False,
                    "invisible": False,
                    "reply_control": {}
                },
                {
                    "rpid": 987654321,
                    "oid": 987654321,
                    "type": 1,
                    "mid": 222222,
                    "root": 0,
                    "parent": 0,
                    "dialog": 0,
                    "count": 2,
                    "rcount": 1,
                    "state": 0,
                    "fansgrade": 0,
                    "attr": 0,
                    "ctime": 1640995300,
                    "rpid_str": "987654321",
                    "root_str": "0",
                    "parent_str": "0",
                    "like": 50,
                    "action": 0,
                    "member": {
                        "mid": "222222",
                        "uname": "测试用户2",
                        "sex": "女",
                        "sign": "另一个测试用户",
                        "avatar": "https://example.com/avatar2.jpg",
                        "rank": "10000",
                        "DisplayRank": "0",
                        "level_info": {
                            "current_level": 3,
                            "current_min": 1500,
                            "current_exp": 2100,
                            "next_exp": 4500
                        }
                    },
                    "content": {
                        "message": "支持！这个视频很有意思 🎉",
                        "plat": 2,
                        "device": "",
                        "members": [],
                        "jump_url": {},
                        "max_line": 6
                    },
                    "replies": None,
                    "assist": 0,
                    "folder": {
                        "has_folded": False,
                        "is_folded": False,
                        "rule": ""
                    },
                    "up_action": {
                        "like": False,
                        "reply": False
                    },
                    "show_follow": False,
                    "invisible": False,
                    "reply_control": {}
                }
            ]
        }
        
        # Sample empty response
        self.empty_comments_response = {
            "replies": []
        }
        
        # Sample malformed response
        self.malformed_comments_response = {
            "replies": [
                {
                    "rpid": 123456789,
                    # Missing required fields
                    "content": {
                        "message": "Incomplete comment"
                    }
                },
                "invalid_comment_string",  # Not a dict
                {
                    "rpid": 987654321,
                    "content": {
                        "message": ""  # Empty message
                    },
                    "member": {
                        "uname": "Valid User"
                    },
                    "like": 10,
                    "ctime": 1640995200
                }
            ]
        }
    
    async def test_get_hot_comments_success(self):
        """Test successful hot comment retrieval."""
        # Mock the bilibili client response
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=self.sample_hot_comments_response
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Verify API call
        self.processor.bili_client.get_video_comments.assert_called_once_with(
            video_id="123456",
            order_mode=CommentOrderType.MIXED,
            next=0
        )
        
        # Verify result structure
        self.assertEqual(len(result), 2)
        
        # Check first comment
        first_comment = result[0]
        self.assertEqual(first_comment["message"], "这是一条测试热门评论！👍")
        self.assertEqual(first_comment["mid"], "111111")
        self.assertEqual(first_comment["like"], 100)
        self.assertIn("ctime", first_comment)  # Time format is converted
        self.assertEqual(first_comment["rcount"], 3)
        
        # Check second comment
        second_comment = result[1]
        self.assertEqual(second_comment["message"], "支持！这个视频很有意思 🎉")
        self.assertEqual(second_comment["mid"], "222222")
        self.assertEqual(second_comment["like"], 50)
        
        # Verify stats updated
        self.assertEqual(self.processor.stats["comments_collected"], 2)
    
    async def test_get_hot_comments_disabled(self):
        """Test hot comment retrieval when disabled in config."""
        # Disable hot comments in config
        self.processor.config["task_config"]["monthly_task"]["hot_comments_json"]["enabled"] = False
        
        result = await self.processor.get_hot_comments("123456")
        
        # Should return empty list
        self.assertEqual(result, [])
        
        # API should not be called
        self.processor.bili_client.get_video_comments.assert_not_called()
    
    async def test_get_hot_comments_empty_response(self):
        """Test hot comment retrieval with empty response."""
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=self.empty_comments_response
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Should return empty list
        self.assertEqual(result, [])
        
        # Stats should not be updated
        self.assertEqual(self.processor.stats["comments_collected"], 0)
    
    async def test_get_hot_comments_api_error(self):
        """Test hot comment retrieval with API error."""
        self.processor.bili_client.get_video_comments = AsyncMock(
            side_effect=DataFetchError("API Error")
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Should return empty list on error
        self.assertEqual(result, [])
        
        # Error should be logged
        self.processor.logger.error.assert_called()
        
        # Stats should reflect the error
        self.assertEqual(self.processor.stats["errors"], 1)
    
    async def test_get_hot_comments_malformed_data(self):
        """Test hot comment retrieval with malformed data."""
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=self.malformed_comments_response
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Should only return valid comments (filtering out malformed ones)
        self.assertEqual(len(result), 0)  # All comments are malformed in this test
        
        # Warning should be logged for malformed data
        self.processor.logger.warning.assert_called()
    
    async def test_get_hot_comments_field_filtering(self):
        """Test that only enabled fields are included in results."""
        # Set specific fields (exclude rcount and ctime)
        self.processor.config["task_config"]["monthly_task"]["hot_comments_json"]["fields"] = ["message", "mid", "like"]
        
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=self.sample_hot_comments_response
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Check that only enabled fields are included
        first_comment = result[0]
        self.assertIn("message", first_comment)
        self.assertIn("mid", first_comment)
        self.assertIn("like", first_comment)
        self.assertNotIn("rcount", first_comment)
        self.assertNotIn("ctime", first_comment)
    
    async def test_get_hot_comments_max_count_limit(self):
        """Test that max_count limit is respected."""
        # Set max_count to 1
        self.processor.config["task_config"]["monthly_task"]["hot_comments_json"]["max_count"] = 1
        
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=self.sample_hot_comments_response
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Should only return 1 comment despite 2 being available
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["message"], "这是一条测试热门评论！👍")
    
    async def test_get_hot_comments_daily_task_config(self):
        """Test hot comment retrieval with daily task configuration."""
        # Switch to daily task type
        self.processor.task_type = "daily"
        
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=self.sample_hot_comments_response
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Should work with daily task config
        self.assertEqual(len(result), 2)
        self.assertEqual(self.processor.stats["comments_collected"], 2)
    
    async def test_get_hot_comments_unicode_handling(self):
        """Test proper handling of Unicode characters in comments."""
        unicode_response = {
            "replies": [
                {
                    "rpid": 123456789,
                    "oid": 987654321,
                    "type": 1,
                    "mid": 111111,
                    "root": 0,
                    "parent": 0,
                    "dialog": 0,
                    "count": 1,
                    "rcount": 0,
                    "state": 0,
                    "fansgrade": 0,
                    "attr": 0,
                    "ctime": 1640995200,
                    "like": 50,
                    "member": {
                        "mid": "111111",
                        "uname": "中文用户名",
                        "sex": "男",
                        "sign": "测试签名",
                        "avatar": "https://example.com/avatar.jpg"
                    },
                    "content": {
                        "message": "这是中文评论 with émojis 🎉🎊 and symbols ©®™",
                        "plat": 2,
                        "device": "",
                        "members": [],
                        "jump_url": {},
                        "max_line": 6
                    }
                }
            ]
        }
        
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=unicode_response
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Verify Unicode characters are preserved
        self.assertEqual(len(result), 1)
        comment = result[0]
        self.assertEqual(comment["mid"], "111111")
        self.assertIn("中文评论", comment["message"])
        self.assertIn("🎉🎊", comment["message"])
        self.assertIn("©®™", comment["message"])
    
    async def test_get_hot_comments_retry_mechanism(self):
        """Test retry mechanism for hot comment retrieval."""
        # Mock first call to fail, second to succeed
        self.processor.bili_client.get_video_comments = AsyncMock(
            side_effect=[
                DataFetchError("Temporary error"),
                self.sample_hot_comments_response
            ]
        )
        
        result = await self.processor.get_hot_comments("123456")
        
        # Should succeed after retry
        self.assertEqual(len(result), 2)
        
        # Should have been called twice (original + retry)
        self.assertEqual(self.processor.bili_client.get_video_comments.call_count, 2)
        
        # Stats should reflect the retry
        self.assertEqual(self.processor.stats["retries"], 1)
    
    async def test_get_hot_comments_integration_with_video_processing(self):
        """Test integration of hot comments with video processing workflow."""
        # This tests the integration point where hot comments are added to video data
        video_data = {
            "aid": 123456,
            "title": "Test Video",
            "view": 1000
        }
        
        self.processor.bili_client.get_video_comments = AsyncMock(
            return_value=self.sample_hot_comments_response
        )
        
        # Simulate the integration point in video processing
        video_aid = str(video_data.get("aid", ""))
        if video_aid:
            hot_comments = await self.processor.get_hot_comments(video_aid)
            if hot_comments:
                video_data["hot_comments"] = hot_comments
        
        # Verify hot comments are properly integrated
        self.assertIn("hot_comments", video_data)
        self.assertEqual(len(video_data["hot_comments"]), 2)
        self.assertEqual(video_data["hot_comments"][0]["message"], "这是一条测试热门评论！👍")
    
    def test_serialize_hot_comments_success(self):
        """Test successful serialization of hot comments."""
        hot_comments = [
            {"message": "Test comment 1", "like": 10},
            {"message": "Test comment 2", "like": 5}
        ]
        
        result = self.processor._serialize_hot_comments(hot_comments)
        
        # Should return JSON string
        self.assertIsInstance(result, str)
        self.assertIn("Test comment 1", result)
        self.assertIn("Test comment 2", result)
    
    def test_serialize_hot_comments_empty(self):
        """Test serialization of empty hot comments."""
        result = self.processor._serialize_hot_comments([])
        
        # Should return None for empty list
        self.assertIsNone(result)
    
    def test_serialize_hot_comments_none(self):
        """Test serialization of None hot comments."""
        result = self.processor._serialize_hot_comments(None)
        
        # Should return None
        self.assertIsNone(result)
    
    def test_serialize_hot_comments_error_handling(self):
        """Test error handling in hot comments serialization."""
        # Create data that might cause JSON serialization issues
        problematic_data = [
            {"message": "Test", "circular_ref": None}
        ]
        # Add circular reference
        problematic_data[0]["circular_ref"] = problematic_data[0]
        
        with patch('json.dumps', side_effect=TypeError("Circular reference")):
            result = self.processor._serialize_hot_comments(problematic_data)
            
            # Should return None on error
            self.assertIsNone(result)
            
            # Warning should be logged
            self.processor.logger.warning.assert_called()


# Async test runner
def run_async_test(coro):
    """Helper to run async tests."""
    import asyncio
    return asyncio.run(coro)


class TestHotCommentRetrievalAsync(TestHotCommentRetrieval):
    """Async version of hot comment retrieval tests."""
    
    def test_get_hot_comments_success_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_success())
    
    def test_get_hot_comments_disabled_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_disabled())
    
    def test_get_hot_comments_empty_response_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_empty_response())
    
    def test_get_hot_comments_api_error_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_api_error())
    
    def test_get_hot_comments_malformed_data_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_malformed_data())
    
    def test_get_hot_comments_field_filtering_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_field_filtering())
    
    def test_get_hot_comments_max_count_limit_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_max_count_limit())
    
    def test_get_hot_comments_daily_task_config_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_daily_task_config())
    
    def test_get_hot_comments_unicode_handling_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_unicode_handling())
    
    def test_get_hot_comments_retry_mechanism_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_retry_mechanism())
    
    def test_get_hot_comments_integration_with_video_processing_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_hot_comments_integration_with_video_processing())


if __name__ == '__main__':
    unittest.main()