"""
Data conversion utilities for converting JSON data structures to CSV format.

This module provides utilities to handle nested data structures like tags and 
comments arrays, implementing proper data flattening for CSV compatibility.
"""

import json
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataConverter:
    """Utility class for converting complex data structures to CSV-compatible format."""
    
    @staticmethod
    def flatten_video_data(video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten video data structure for CSV export.
        
        Args:
            video_data: Video data dictionary
            
        Returns:
            Flattened video data dictionary
        """
        flattened = {}
        
        for key, value in video_data.items():
            if key == "tags" and isinstance(value, list):
                # Handle tags array
                flattened.update(DataConverter._flatten_tags(value))
            elif key == "stats_fields" and isinstance(value, dict):
                # Handle stats fields
                for stat_key, stat_value in value.items():
                    flattened[f"stats_{stat_key}"] = stat_value
            elif key == "hot_comments_json":
                # Handle comments JSON string or list
                flattened.update(DataConverter._flatten_comments(value, "hot_comments"))
            elif key == "comments" and isinstance(value, list):
                # Handle comments list
                flattened.update(DataConverter._flatten_comments(value, "comments"))
            elif isinstance(value, dict):
                # Handle nested dictionaries
                for nested_key, nested_value in value.items():
                    flattened[f"{key}_{nested_key}"] = nested_value
            elif isinstance(value, list) and value:
                # Handle other lists by joining as string
                if isinstance(value[0], (str, int, float)):
                    flattened[key] = ", ".join(map(str, value))
                else:
                    # Complex objects in list - convert to JSON string
                    flattened[key] = json.dumps(value, ensure_ascii=False)
            else:
                # Simple values
                flattened[key] = value
        
        return flattened
    
    @staticmethod
    def _flatten_tags(tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Flatten tags array into CSV-compatible format.
        
        Args:
            tags: List of tag dictionaries
            
        Returns:
            Flattened tags data
        """
        if not tags:
            return {
                "tags_count": 0,
                "tags_names": "",
                "tags_ids": "",
                "tags_categories": ""
            }
        
        tag_names = []
        tag_ids = []
        tag_categories = []
        
        for tag in tags[:20]:  # Limit to first 20 tags
            if isinstance(tag, dict):
                tag_names.append(str(tag.get("tag_name", "")))
                tag_ids.append(str(tag.get("tag_id", "")))
                tag_categories.append(str(tag.get("category", "")))
            elif isinstance(tag, str):
                tag_names.append(tag)
        
        return {
            "tags_count": len(tags),
            "tags_names": "; ".join(filter(None, tag_names)),
            "tags_ids": "; ".join(filter(None, tag_ids)),
            "tags_categories": "; ".join(filter(None, tag_categories))
        }
    
    @staticmethod
    def _flatten_comments(comments: Union[str, List[Dict[str, Any]]], prefix: str) -> Dict[str, Any]:
        """
        Flatten comments data into CSV-compatible format.
        
        Args:
            comments: Comments data (JSON string or list)
            prefix: Prefix for field names
            
        Returns:
            Flattened comments data
        """
        # Parse JSON string if needed
        if isinstance(comments, str):
            try:
                comments = json.loads(comments) if comments else []
            except json.JSONDecodeError:
                comments = []
        
        if not comments or not isinstance(comments, list):
            return {
                f"{prefix}_count": 0,
                f"{prefix}_summary": ""
            }
        
        # Extract key information from comments
        comment_summaries = []
        total_likes = 0
        total_replies = 0
        
        for comment in comments[:10]:  # Limit to first 10 comments for summary
            if isinstance(comment, dict):
                message = comment.get("message", "")
                likes = comment.get("like", 0)
                replies = comment.get("rcount", 0)
                author = comment.get("mid", "")
                
                # Clean message for CSV
                clean_message = str(message).replace('\n', ' ').replace('\r', ' ')[:100]
                if len(clean_message) == 100:
                    clean_message += "..."
                
                comment_summaries.append(f"[{author}] {clean_message} (👍{likes} 💬{replies})")
                total_likes += likes if isinstance(likes, int) else 0
                total_replies += replies if isinstance(replies, int) else 0
        
        return {
            f"{prefix}_count": len(comments),
            f"{prefix}_total_likes": total_likes,
            f"{prefix}_total_replies": total_replies,
            f"{prefix}_summary": " | ".join(comment_summaries)
        }
    
    @staticmethod
    def flatten_up_info(up_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten UP info data structure for CSV export.
        
        Args:
            up_data: UP info data dictionary
            
        Returns:
            Flattened UP info data dictionary
        """
        flattened = {}
        
        for key, value in up_data.items():
            if isinstance(value, dict):
                # Handle nested dictionaries
                for nested_key, nested_value in value.items():
                    flattened[f"{key}_{nested_key}"] = nested_value
            elif isinstance(value, list):
                # Handle lists by joining as string
                if value and isinstance(value[0], (str, int, float)):
                    flattened[key] = ", ".join(map(str, value))
                else:
                    flattened[key] = json.dumps(value, ensure_ascii=False)
            else:
                # Simple values
                flattened[key] = value
        
        return flattened
    
    @staticmethod
    def convert_json_to_csv_data(json_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert complete JSON data structure to CSV-compatible format.
        
        Args:
            json_data: Complete JSON data structure
            
        Returns:
            Dictionary with CSV-compatible data for each type
        """
        csv_data = {}
        
        # Convert videos data
        if "videos" in json_data and json_data["videos"]:
            csv_data["videos"] = [
                DataConverter.flatten_video_data(video) 
                for video in json_data["videos"]
            ]
        
        # Convert UP info
        if "up_info" in json_data and json_data["up_info"]:
            csv_data["up_info"] = [DataConverter.flatten_up_info(json_data["up_info"])]
        
        # Convert hot comments if they exist separately
        if "hot_comments" in json_data and json_data["hot_comments"]:
            csv_data["hot_comments"] = json_data["hot_comments"]
        
        # Extract regular comments from videos
        all_comments = []
        if "videos" in json_data:
            for video in json_data["videos"]:
                video_id = video.get("video_aid", video.get("aid", "unknown"))
                
                # Extract comments from hot_comments_json field
                comments_json = video.get("hot_comments_json", "[]")
                try:
                    comments = json.loads(comments_json) if isinstance(comments_json, str) else comments_json
                    if isinstance(comments, list):
                        for comment in comments:
                            if isinstance(comment, dict):
                                comment["video_id"] = video_id
                                comment["comment_type"] = "regular"
                                all_comments.append(comment)
                except json.JSONDecodeError:
                    pass
        
        if all_comments:
            csv_data["comments"] = all_comments
        
        return csv_data
    
    @staticmethod
    def sanitize_for_csv(value: Any) -> str:
        """
        Sanitize a value for CSV export.
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized string value
        """
        if value is None:
            return ""
        
        # Convert to string
        str_value = str(value)
        
        # Handle special characters
        str_value = str_value.replace('\n', ' ').replace('\r', ' ')
        str_value = str_value.replace('\t', ' ')
        
        # Remove excessive whitespace
        str_value = ' '.join(str_value.split())
        
        return str_value.strip()
    
    @staticmethod
    def batch_convert_json_files(json_files: List[str], output_dir: str) -> Dict[str, List[str]]:
        """
        Batch convert multiple JSON files to CSV format.
        
        Args:
            json_files: List of JSON file paths
            output_dir: Output directory for CSV files
            
        Returns:
            Dictionary mapping data type to list of created CSV files
        """
        from ..storage.csv_exporter import CSVExporter
        
        csv_exporter = CSVExporter(data_dir=output_dir)
        results = {"videos": [], "comments": [], "hot_comments": [], "up_info": []}
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Convert to CSV data
                csv_data = DataConverter.convert_json_to_csv_data(json_data)
                
                # Generate base filename
                base_name = os.path.splitext(os.path.basename(json_file))[0]
                base_path = os.path.join(output_dir, base_name)
                
                # Export each data type
                export_results = csv_exporter.export_combined_data_to_csv(csv_data, base_path)
                
                # Track successful exports
                for data_type, csv_path in export_results.items():
                    if csv_path and data_type in results:
                        results[data_type].append(csv_path)
                
                logger.info(f"Successfully converted {json_file} to CSV")
                
            except Exception as e:
                logger.error(f"Failed to convert {json_file}: {e}")
        
        return results