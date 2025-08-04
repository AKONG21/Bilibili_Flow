"""
Unit tests for enhanced video info extraction functionality.

Tests get_video_info method with tag extraction,
verifies proper handling of missing or malformed tag data,
and tests category information extraction.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from bilibili_core.client.bilibili_client import BilibiliClient
from bilibili_core.client.exceptions import DataFetchError


class TestVideoInfoExtraction(unittest.TestCase):
    """Test cases for enhanced video info extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_page = MagicMock()
        self.mock_headers = {"User-Agent": "test"}
        self.mock_cookies = {"test": "cookie"}
        
        # Create client instance
        self.client = BilibiliClient(
            timeout=10,
            headers=self.mock_headers,
            playwright_page=self.mock_page,
            cookie_dict=self.mock_cookies
        )
        
        # Sample video detail response with complete data
        self.complete_video_detail = {
            "View": {
                "aid": 123456,
                "bvid": "BV1234567890",
                "title": "Test Video",
                "desc": "Test description",
                "duration": 300,
                "pubdate": 1640995200,
                "stat": {
                    "view": 1000,
                    "like": 100,
                    "coin": 50,
                    "favorite": 25,
                    "share": 10,
                    "reply": 5
                },
                "tname": "科技",
                "typename": "数码",
                "tid": 188
            },
            "Tags": [
                {
                    "tag_id": 1,
                    "tag_name": "测试标签",
                    "category": "科技",
                    "likes": 10,
                    "hates": 1,
                    "subscribed": False
                },
                {
                    "tag_id": 2,
                    "tag_name": "Python",
                    "category": "编程",
                    "likes": 20,
                    "hates": 0,
                    "subscribed": True
                }
            ]
        }
        
        # Sample video detail with missing tags
        self.video_detail_no_tags = {
            "View": {
                "aid": 789012,
                "bvid": "BV0987654321",
                "title": "Video Without Tags",
                "tname": "娱乐",
                "typename": "综艺",
                "tid": 71
            },
            "Tags": []
        }
        
        # Sample video detail with malformed tags
        self.video_detail_malformed_tags = {
            "View": {
                "aid": 345678,
                "bvid": "BV3456789012",
                "title": "Video With Malformed Tags",
                "tname": "生活",
                "tid": 160
            },
            "Tags": [
                {
                    "tag_id": 1,
                    "tag_name": "Valid Tag",
                    "category": "生活"
                },
                {
                    # Missing tag_name
                    "tag_id": 2,
                    "category": "生活"
                },
                "invalid_tag_string",  # Not a dict
                {
                    "tag_id": 3,
                    "tag_name": "",  # Empty name
                    "category": "生活"
                }
            ]
        }
        
        # Sample video detail with no View data
        self.video_detail_no_view = {
            "Tags": [
                {
                    "tag_id": 1,
                    "tag_name": "Orphaned Tag"
                }
            ]
        }
    
    async def test_get_video_info_with_aid_success(self):
        """Test successful video info retrieval with aid parameter."""
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = self.complete_video_detail
            
            result = await self.client.get_video_info(aid=123456)
            
            # Verify API call
            mock_get.assert_called_once_with(
                "/x/web-interface/view/detail",
                {"aid": 123456},
                enable_params_sign=False
            )
            
            # Verify enhanced data structure
            self.assertIn("EnhancedTags", result)
            self.assertIn("CategoryInfo", result)
            
            # Verify tags extraction
            enhanced_tags = result["EnhancedTags"]
            self.assertEqual(len(enhanced_tags), 2)
            
            first_tag = enhanced_tags[0]
            self.assertEqual(first_tag["tag_id"], 1)
            self.assertEqual(first_tag["tag_name"], "测试标签")
            self.assertEqual(first_tag["category"], "科技")
            self.assertEqual(first_tag["likes"], 10)
            self.assertEqual(first_tag["hates"], 1)
            self.assertFalse(first_tag["subscribed"])
            
            # Verify category info
            category_info = result["CategoryInfo"]
            self.assertEqual(category_info["main_category"], "科技")
            self.assertEqual(category_info["sub_category"], "数码")
            self.assertEqual(category_info["tid"], 188)
    
    async def test_get_video_info_with_bvid_success(self):
        """Test successful video info retrieval with bvid parameter."""
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = self.complete_video_detail
            
            result = await self.client.get_video_info(bvid="BV1234567890")
            
            # Verify API call
            mock_get.assert_called_once_with(
                "/x/web-interface/view/detail",
                {"bvid": "BV1234567890"},
                enable_params_sign=False
            )
            
            # Verify result contains enhanced data
            self.assertIn("EnhancedTags", result)
            self.assertIn("CategoryInfo", result)
    
    async def test_get_video_info_no_parameters_error(self):
        """Test error when neither aid nor bvid is provided."""
        with self.assertRaises(ValueError) as context:
            await self.client.get_video_info()
        
        self.assertIn("请提供 aid 或 bvid 中的至少一个参数", str(context.exception))
    
    async def test_get_video_info_api_error(self):
        """Test handling of API errors during video info retrieval."""
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = DataFetchError("API Error")
            
            with self.assertRaises(DataFetchError):
                await self.client.get_video_info(aid=123456)
    
    async def test_extract_video_tags_empty_tags(self):
        """Test tag extraction with empty tags list."""
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = self.video_detail_no_tags
            
            result = await self.client.get_video_info(aid=789012)
            
            # Verify empty tags are handled correctly
            enhanced_tags = result["EnhancedTags"]
            self.assertEqual(len(enhanced_tags), 0)
            
            # Verify category info is still extracted
            category_info = result["CategoryInfo"]
            self.assertEqual(category_info["main_category"], "娱乐")
            self.assertEqual(category_info["sub_category"], "综艺")
    
    async def test_extract_video_tags_malformed_data(self):
        """Test tag extraction with malformed tag data."""
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = self.video_detail_malformed_tags
            
            result = await self.client.get_video_info(aid=345678)
            
            # Verify only valid tags are extracted
            enhanced_tags = result["EnhancedTags"]
            self.assertEqual(len(enhanced_tags), 1)  # Only one valid tag
            
            valid_tag = enhanced_tags[0]
            self.assertEqual(valid_tag["tag_name"], "Valid Tag")
            self.assertEqual(valid_tag["category"], "生活")
    
    async def test_extract_video_tags_non_list_tags(self):
        """Test tag extraction when Tags is not a list."""
        malformed_data = self.complete_video_detail.copy()
        malformed_data["Tags"] = "not_a_list"
        
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = malformed_data
            
            result = await self.client.get_video_info(aid=123456)
            
            # Verify empty tags when data is malformed
            enhanced_tags = result["EnhancedTags"]
            self.assertEqual(len(enhanced_tags), 0)
    
    async def test_extract_category_info_missing_data(self):
        """Test category extraction with missing category data."""
        incomplete_data = {
            "View": {
                "aid": 123456,
                "bvid": "BV1234567890",
                "title": "Test Video"
                # Missing tname, typename, tid
            },
            "Tags": []
        }
        
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = incomplete_data
            
            result = await self.client.get_video_info(aid=123456)
            
            # Verify category info with empty values
            category_info = result["CategoryInfo"]
            self.assertEqual(category_info["main_category"], "")
            self.assertEqual(category_info["sub_category"], "")
            self.assertEqual(category_info["tid"], 0)
    
    async def test_extract_video_info_no_view_data(self):
        """Test handling when View data is missing."""
        with patch.object(self.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = self.video_detail_no_view
            
            result = await self.client.get_video_info(aid=123456)
            
            # Verify defaults are used when View data is missing
            self.assertIn("EnhancedTags", result)
            self.assertIn("CategoryInfo", result)
            self.assertEqual(len(result["EnhancedTags"]), 0)
            self.assertEqual(result["CategoryInfo"], {})
    
    async def test_extract_video_tags_and_category_direct(self):
        """Test the _extract_video_tags_and_category method directly."""
        result = await self.client._extract_video_tags_and_category(self.complete_video_detail)
        
        # Verify original data is preserved
        self.assertIn("View", result)
        self.assertIn("Tags", result)
        
        # Verify enhanced data is added
        self.assertIn("EnhancedTags", result)
        self.assertIn("CategoryInfo", result)
        
        # Verify tag processing
        enhanced_tags = result["EnhancedTags"]
        self.assertEqual(len(enhanced_tags), 2)
        
        # Verify all tag fields are present
        for tag in enhanced_tags:
            self.assertIn("tag_id", tag)
            self.assertIn("tag_name", tag)
            self.assertIn("category", tag)
            self.assertIn("likes", tag)
            self.assertIn("hates", tag)
            self.assertIn("subscribed", tag)
    
    async def test_extract_video_tags_exception_handling(self):
        """Test exception handling during tag extraction."""
        # Create data that will cause an exception during processing
        problematic_data = {
            "View": {
                "aid": 123456,
                "bvid": "BV1234567890"
            },
            "Tags": [
                {
                    "tag_id": None,  # This might cause issues
                    "tag_name": "Test"
                }
            ]
        }
        
        result = await self.client._extract_video_tags_and_category(problematic_data)
        
        # Verify graceful handling - should not crash
        self.assertIn("EnhancedTags", result)
        self.assertIn("CategoryInfo", result)
        
        # Tags might be empty due to processing errors, but structure should be intact
        self.assertIsInstance(result["EnhancedTags"], list)
        self.assertIsInstance(result["CategoryInfo"], dict)
    
    async def test_extract_video_tags_unicode_handling(self):
        """Test proper handling of Unicode characters in tags."""
        unicode_data = {
            "View": {
                "aid": 123456,
                "bvid": "BV1234567890",
                "tname": "科技",
                "typename": "数码",
                "tid": 188
            },
            "Tags": [
                {
                    "tag_id": 1,
                    "tag_name": "中文标签",
                    "category": "科技分类",
                    "likes": 10,
                    "hates": 0,
                    "subscribed": False
                },
                {
                    "tag_id": 2,
                    "tag_name": "émojis 🎉🎊",
                    "category": "特殊字符",
                    "likes": 5,
                    "hates": 0,
                    "subscribed": True
                }
            ]
        }
        
        result = await self.client._extract_video_tags_and_category(unicode_data)
        
        # Verify Unicode characters are preserved
        enhanced_tags = result["EnhancedTags"]
        self.assertEqual(len(enhanced_tags), 2)
        
        self.assertEqual(enhanced_tags[0]["tag_name"], "中文标签")
        self.assertEqual(enhanced_tags[0]["category"], "科技分类")
        self.assertEqual(enhanced_tags[1]["tag_name"], "émojis 🎉🎊")
        
        # Verify category info with Unicode
        category_info = result["CategoryInfo"]
        self.assertEqual(category_info["main_category"], "科技")
        self.assertEqual(category_info["sub_category"], "数码")


# Async test runner using asyncio.run for Python 3.7+
def run_async_test(coro):
    """Helper to run async tests."""
    import asyncio
    return asyncio.run(coro)


class TestVideoInfoExtractionAsync(TestVideoInfoExtraction):
    """Async version of video info extraction tests."""
    
    def test_get_video_info_with_aid_success_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_video_info_with_aid_success())
    
    def test_get_video_info_with_bvid_success_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_video_info_with_bvid_success())
    
    def test_get_video_info_no_parameters_error_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_video_info_no_parameters_error())
    
    def test_get_video_info_api_error_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_get_video_info_api_error())
    
    def test_extract_video_tags_empty_tags_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_video_tags_empty_tags())
    
    def test_extract_video_tags_malformed_data_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_video_tags_malformed_data())
    
    def test_extract_video_tags_non_list_tags_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_video_tags_non_list_tags())
    
    def test_extract_category_info_missing_data_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_category_info_missing_data())
    
    def test_extract_video_info_no_view_data_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_video_info_no_view_data())
    
    def test_extract_video_tags_and_category_direct_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_video_tags_and_category_direct())
    
    def test_extract_video_tags_exception_handling_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_video_tags_exception_handling())
    
    def test_extract_video_tags_unicode_handling_sync(self):
        """Sync wrapper for async test."""
        run_async_test(self.test_extract_video_tags_unicode_handling())


if __name__ == '__main__':
    unittest.main()