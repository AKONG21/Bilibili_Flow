# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  

# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/4/6 15:30
# @Desc    : Bilibili database storage implementation

from typing import Dict, List, Union
from abc import ABC, abstractmethod
import time


class AbstractStorage(ABC):
    @abstractmethod
    async def store_content(self, content_item: Dict):
        pass

    @abstractmethod
    async def store_comment(self, comment_item: Dict):
        pass

    @abstractmethod
    async def store_creator(self, creator_item: Dict):
        pass


class BilibiliStorage(AbstractStorage):
    """Simple storage implementation with deduplication logic"""
    
    def __init__(self, db_connection=None):
        self.db_connection = db_connection
        self._stored_videos = set()  # Simple in-memory deduplication
        self._stored_comments = set()
        self._stored_creators = set()

    def get_current_timestamp(self) -> int:
        """Get current timestamp"""
        return int(time.time())

    async def store_content(self, content_item: Dict):
        """
        Store video content with deduplication
        Args:
            content_item: video content dictionary
        """
        video_id = content_item.get("video_id") or content_item.get("aid")
        if not video_id:
            return
            
        # Simple deduplication check
        if video_id in self._stored_videos:
            print(f"Video {video_id} already stored, skipping...")
            return
            
        # Add timestamp
        content_item["add_ts"] = self.get_current_timestamp()
        
        # Store in database or print (for demo)
        if self.db_connection:
            await self._store_to_db("bilibili_video", content_item)
        else:
            print(f"Storing video: {video_id} - {content_item.get('title', 'No title')}")
            
        self._stored_videos.add(video_id)

    async def store_comment(self, comment_item: Dict):
        """
        Store comment with deduplication
        Args:
            comment_item: comment dictionary
        """
        comment_id = comment_item.get("comment_id") or comment_item.get("rpid")
        if not comment_id:
            return
            
        if comment_id in self._stored_comments:
            print(f"Comment {comment_id} already stored, skipping...")
            return
            
        comment_item["add_ts"] = self.get_current_timestamp()
        
        if self.db_connection:
            await self._store_to_db("bilibili_comment", comment_item)
        else:
            print(f"Storing comment: {comment_id}")
            
        self._stored_comments.add(comment_id)

    async def store_creator(self, creator_item: Dict):
        """
        Store creator with deduplication
        Args:
            creator_item: creator dictionary
        """
        creator_id = creator_item.get("user_id") or creator_item.get("mid")
        if not creator_id:
            return
            
        if creator_id in self._stored_creators:
            print(f"Creator {creator_id} already stored, skipping...")
            return
            
        creator_item["add_ts"] = self.get_current_timestamp()
        
        if self.db_connection:
            await self._store_to_db("bilibili_creator", creator_item)
        else:
            print(f"Storing creator: {creator_id} - {creator_item.get('name', 'No name')}")
            
        self._stored_creators.add(creator_id)

    async def _store_to_db(self, table_name: str, item: Dict):
        """Store item to database (placeholder for actual DB implementation)"""
        # This would be implemented with actual database connection
        # For now, just print what would be stored
        print(f"Would store to {table_name}: {item}")

    def get_stored_count(self) -> Dict[str, int]:
        """Get count of stored items"""
        return {
            "videos": len(self._stored_videos),
            "comments": len(self._stored_comments),
            "creators": len(self._stored_creators)
        }