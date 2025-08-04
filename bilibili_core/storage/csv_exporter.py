"""
CSV Export utility for Bilibili data.

This module provides functionality to export video, comment, and UP information
data to CSV format with proper UTF-8 encoding and special character handling.
"""

import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVExporter:
    """Utility class for exporting Bilibili data to CSV format."""
    
    def __init__(self, data_dir: str = "data", encoding: str = "utf-8-sig"):
        """
        Initialize CSV exporter.
        
        Args:
            data_dir: Directory to store CSV files
            encoding: File encoding (utf-8-sig for Excel compatibility)
        """
        self.data_dir = data_dir
        self.encoding = encoding
        self.delimiter = ','
        
    def _ensure_directory(self, file_path: str) -> None:
        """Ensure the directory for the file path exists."""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _sanitize_value(self, value: Any) -> str:
        """
        Sanitize value for CSV export.
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized string value
        """
        if value is None:
            return ""
        
        # Convert to string
        str_value = str(value)
        
        # Handle newlines and special characters
        str_value = str_value.replace('\n', ' ').replace('\r', ' ')
        str_value = str_value.replace('\t', ' ')
        
        return str_value.strip()
    
    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flatten nested dictionary for CSV export.
        
        Args:
            data: Dictionary to flatten
            prefix: Prefix for keys
            
        Returns:
            Flattened dictionary
        """
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, new_key))
            elif isinstance(value, list):
                # Special handling for tags and hot_comments
                if key == "tags" and value and isinstance(value[0], dict):
                    # For tags, only extract tag_name and join with semicolon
                    tag_names = [item.get("tag_name", "") for item in value if item.get("tag_name")]
                    flattened[new_key] = self._sanitize_value("; ".join(tag_names))
                elif key == "hot_comments" and value and isinstance(value[0], dict):
                    # For hot comments, extract message and join with semicolon
                    messages = [item.get("message", "") for item in value if item.get("message")]
                    flattened[new_key] = self._sanitize_value("; ".join(messages))
                elif value and isinstance(value[0], dict):
                    # For other list of dicts, create a simplified representation
                    list_str = "; ".join([
                        ", ".join([f"{k}:{v}" for k, v in item.items() if v is not None])
                        for item in value[:10]  # Limit to first 10 items
                    ])
                    flattened[new_key] = self._sanitize_value(list_str)
                else:
                    # For simple lists
                    flattened[new_key] = self._sanitize_value(", ".join(map(str, value)))
            else:
                flattened[new_key] = self._sanitize_value(value)
        
        return flattened 
   
    def export_videos_to_csv(self, videos_data: List[Dict[str, Any]], 
                           file_path: str) -> Optional[str]:
        """
        Export video data to CSV file.
        
        Args:
            videos_data: List of video data dictionaries
            file_path: Path to save CSV file
            
        Returns:
            Path to created CSV file or None if failed
        """
        if not videos_data:
            logger.warning("No video data to export")
            return None
            
        try:
            self._ensure_directory(file_path)
            
            # Flatten all video data and collect all possible fields
            flattened_videos = []
            all_fields = set()
            
            for video in videos_data:
                flattened = self._flatten_dict(video)
                flattened_videos.append(flattened)
                all_fields.update(flattened.keys())
            
            # Define custom field order for videos
            desired_order = [
                'aid', 'title', 'video_url', 'cover_url', 'publish_time', 'duration', 
                'category', 'description', 'tags', 'view', 'like', 'reply', 'favorite', 
                'share', 'coin', 'danmaku', 'hot_comments'
            ]
            
            # Sort fields with custom order, putting desired fields first
            fieldnames = []
            for field in desired_order:
                if field in all_fields:
                    fieldnames.append(field)
            
            # Add any remaining fields not in the desired order
            for field in sorted(all_fields):
                if field not in fieldnames:
                    fieldnames.append(field)
            
            with open(file_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, 
                                      delimiter=self.delimiter)
                writer.writeheader()
                
                for video in flattened_videos:
                    # Ensure all fields are present
                    row = {field: video.get(field, "") for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Successfully exported {len(videos_data)} videos to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to export videos to CSV: {e}")
            return None
    
    def export_comments_to_csv(self, comments_data: List[Dict[str, Any]], 
                             file_path: str, comment_type: str = "regular") -> Optional[str]:
        """
        Export comment data to CSV file.
        
        Args:
            comments_data: List of comment data dictionaries
            file_path: Path to save CSV file
            comment_type: Type of comments (regular, hot)
            
        Returns:
            Path to created CSV file or None if failed
        """
        if not comments_data:
            logger.warning(f"No {comment_type} comment data to export")
            return None
            
        try:
            self._ensure_directory(file_path)
            
            # Flatten all comment data
            flattened_comments = []
            all_fields = set()
            
            for comment in comments_data:
                flattened = self._flatten_dict(comment)
                # Add comment type for identification
                flattened['comment_type'] = comment_type
                flattened_comments.append(flattened)
                all_fields.update(flattened.keys())
            
            # Sort fields for consistent column order
            fieldnames = sorted(all_fields)
            
            with open(file_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, 
                                      delimiter=self.delimiter)
                writer.writeheader()
                
                for comment in flattened_comments:
                    # Ensure all fields are present
                    row = {field: comment.get(field, "") for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Successfully exported {len(comments_data)} {comment_type} comments to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to export {comment_type} comments to CSV: {e}")
            return None
    
    def export_up_info_to_csv(self, up_data: Dict[str, Any], 
                            file_path: str) -> Optional[str]:
        """
        Export UP information to CSV file.
        
        Args:
            up_data: UP information dictionary
            file_path: Path to save CSV file
            
        Returns:
            Path to created CSV file or None if failed
        """
        if not up_data:
            logger.warning("No UP data to export")
            return None
            
        try:
            self._ensure_directory(file_path)
            
            # Flatten UP data
            flattened_up = self._flatten_dict(up_data)
            
            # Add timestamp
            flattened_up['export_timestamp'] = datetime.now().isoformat()
            
            fieldnames = sorted(flattened_up.keys())
            
            with open(file_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, 
                                      delimiter=self.delimiter)
                writer.writeheader()
                writer.writerow(flattened_up)
            
            logger.info(f"Successfully exported UP info to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to export UP info to CSV: {e}")
            return None
    
    def export_combined_data_to_csv(self, data: Dict[str, Any], 
                                  base_path: str) -> Dict[str, Optional[str]]:
        """
        Export all data types to separate CSV files.
        
        Args:
            data: Combined data dictionary containing videos, comments, and UP info
            base_path: Base path for CSV files (without extension)
            
        Returns:
            Dictionary mapping data type to file path
        """
        results = {}
        
        # Export videos
        if 'videos' in data and data['videos']:
            video_path = f"{base_path}_videos.csv"
            results['videos'] = self.export_videos_to_csv(data['videos'], video_path)
        
        # Export regular comments
        if 'comments' in data and data['comments']:
            comments_path = f"{base_path}_comments.csv"
            results['comments'] = self.export_comments_to_csv(
                data['comments'], comments_path, "regular"
            )
        
        # Export hot comments
        if 'hot_comments' in data and data['hot_comments']:
            hot_comments_path = f"{base_path}_hot_comments.csv"
            results['hot_comments'] = self.export_comments_to_csv(
                data['hot_comments'], hot_comments_path, "hot"
            )
        
        # Export UP info
        if 'up_info' in data and data['up_info']:
            up_path = f"{base_path}_up_info.csv"
            results['up_info'] = self.export_up_info_to_csv(data['up_info'], up_path)
        
        return results