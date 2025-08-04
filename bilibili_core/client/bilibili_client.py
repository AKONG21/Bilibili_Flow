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
# @Time    : 2023/12/2 18:44
# @Desc    : bilibili 请求客户端
import asyncio
import json
import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urlencode

import httpx
from playwright.async_api import BrowserContext, Page

try:
    from .wbi_signature import BilibiliSign
    from .exceptions import DataFetchError
    from .field import CommentOrderType, SearchOrderType
    from ..utils.logger import get_logger
except ImportError:
    # 处理相对导入失败的情况
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from bilibili_core.client.wbi_signature import BilibiliSign
    from bilibili_core.client.exceptions import DataFetchError
    from bilibili_core.client.field import CommentOrderType, SearchOrderType
    from bilibili_core.utils.logger import get_logger

logger = get_logger()


class BilibiliClient:
    def __init__(
            self,
            timeout=10,
            proxies=None,
            *,
            headers: Dict[str, str],
            playwright_page: Page,
            cookie_dict: Dict[str, str],
    ):
        self.proxies = proxies
        self.timeout = timeout
        self.headers = headers
        self._host = "https://api.bilibili.com"
        self.playwright_page = playwright_page
        self.cookie_dict = cookie_dict

    async def request(self, method, url, **kwargs) -> Any:
        # 确保请求头包含正确的Accept-Encoding，但不要br压缩
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        # 合并默认headers和传入的headers
        request_headers = {**self.headers, **kwargs.get('headers', {})}
        # 明确指定不要Brotli压缩，只要gzip
        request_headers['Accept-Encoding'] = 'gzip, deflate'
        kwargs['headers'] = request_headers
        
        # 只在有代理时传递proxies参数
        client_kwargs = {}
        if self.proxies:
            client_kwargs['proxies'] = self.proxies

        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.request(
                method, url, timeout=self.timeout,
                **kwargs
            )
        
        # 调试信息
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Response Status: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        
        try:
            data: Dict = response.json()
        except json.JSONDecodeError:
            # 如果JSON解析失败，检查响应内容
            content_type = response.headers.get('content-type', '')
            content_encoding = response.headers.get('content-encoding', '')
            logger.error(f"[BilibiliClient.request] Failed to decode JSON from response.")
            logger.error(f"Status: {response.status_code}, Content-Type: {content_type}, Content-Encoding: {content_encoding}")
            logger.error(f"Response length: {len(response.content)} bytes")
            
            # 尝试手动处理压缩
            if content_encoding == 'br':
                try:
                    import brotli
                    decompressed = brotli.decompress(response.content)
                    data = json.loads(decompressed.decode('utf-8'))
                    logger.info("Successfully decompressed Brotli response")
                except ImportError:
                    logger.error("Brotli library not available. Install with: pip install brotli")
                    raise DataFetchError(f"Brotli compression not supported")
                except Exception as e:
                    logger.error(f"Failed to decompress Brotli: {e}")
                    raise DataFetchError(f"Failed to decode compressed response")
            else:
                logger.error(f"Response text preview: {response.text[:200]}...")
                raise DataFetchError(f"Failed to decode JSON, status: {response.status_code}")
            
        if data.get("code") != 0:
            raise DataFetchError(data.get("message", "unkonw error"))
        else:
            return data.get("data", {})

    async def pre_request_data(self, req_data: Dict) -> Dict:
        """
        发送请求进行请求参数签名
        需要从 localStorage 拿 wbi_img_urls 这参数，值如下：
        https://i0.hdslb.com/bfs/wbi/7cd084941338484aae1ad9425b84077c.png-https://i0.hdslb.com/bfs/wbi/4932caff0ff746eab6f01bf08b70ac45.png
        :param req_data:
        :return:
        """
        if not req_data:
            return {}
        img_key, sub_key = await self.get_wbi_keys()
        return BilibiliSign(img_key, sub_key).sign(req_data)

    async def get_wbi_keys(self) -> Tuple[str, str]:
        """
        获取最新的 img_key 和 sub_key
        :return:
        """
        local_storage = await self.playwright_page.evaluate("() => window.localStorage")
        wbi_img_urls = local_storage.get("wbi_img_urls", "")
        if not wbi_img_urls:
            img_url_from_storage = local_storage.get("wbi_img_url")
            sub_url_from_storage = local_storage.get("wbi_sub_url")
            if img_url_from_storage and sub_url_from_storage:
                wbi_img_urls = f"{img_url_from_storage}-{sub_url_from_storage}"
        if wbi_img_urls and "-" in wbi_img_urls:
            img_url, sub_url = wbi_img_urls.split("-")
        else:
            resp = await self.request(method="GET", url=self._host + "/x/web-interface/nav")
            img_url: str = resp['wbi_img']['img_url']
            sub_url: str = resp['wbi_img']['sub_url']
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        return img_key, sub_key

    async def get(self, uri: str, params=None, enable_params_sign: bool = True) -> Dict:
        final_uri = uri
        if enable_params_sign:
            params = await self.pre_request_data(params)
        if isinstance(params, dict):
            final_uri = (f"{uri}?"
                         f"{urlencode(params)}")
        return await self.request(method="GET", url=f"{self._host}{final_uri}", headers=self.headers)

    async def post(self, uri: str, data: dict) -> Dict:
        data = await self.pre_request_data(data)
        json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        return await self.request(method="POST", url=f"{self._host}{uri}",
                                  data=json_str, headers=self.headers)

    async def pong(self) -> bool:
        """get a note to check if login state is ok"""
        logger.info("[BilibiliClient.pong] Begin pong bilibili...")
        ping_flag = False
        try:
            check_login_uri = "/x/web-interface/nav"
            response = await self.get(check_login_uri)
            if response.get("isLogin"):
                logger.info(
                    "[BilibiliClient.pong] Use cache login state get web interface successfull!")
                ping_flag = True
        except Exception as e:
            logger.error(
                f"[BilibiliClient.pong] Pong bilibili failed: {e}, and try to login again...")
            ping_flag = False
        return ping_flag

    async def update_cookies(self, browser_context: BrowserContext):
        from ..utils.cookie_utils import convert_cookies
        cookie_str, cookie_dict = convert_cookies(await browser_context.cookies())
        self.headers["Cookie"] = cookie_str
        self.cookie_dict = cookie_dict

    async def search_video_by_keyword(self, keyword: str, page: int = 1, page_size: int = 20,
                                      order: SearchOrderType = SearchOrderType.DEFAULT,
                                      pubtime_begin_s: int = 0, pubtime_end_s: int = 0) -> Dict:

        """
        KuaiShou web search api
        :param keyword: 搜索关键词
        :param page: 分页参数具体第几页
        :param page_size: 每一页参数的数量
        :param order: 搜索结果排序，默认位综合排序
        :param pubtime_begin_s: 发布时间开始时间戳
        :param pubtime_end_s: 发布时间结束时间戳
        :return:
        """
        uri = "/x/web-interface/wbi/search/type"
        post_data = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "order": order.value,
            "pubtime_begin_s": pubtime_begin_s,
            "pubtime_end_s": pubtime_end_s
        }
        return await self.get(uri, post_data)

    async def get_video_info(self, aid: Union[int, None] = None, bvid: Union[str, None] = None) -> Dict:
        """
        Bilibili web video detail api, aid 和 bvid任选一个参数
        Enhanced to extract comprehensive video information including tags
        :param aid: 稿件avid
        :param bvid: 稿件bvid
        :return: Enhanced video information with tags and category data
        """
        if not aid and not bvid:
            raise ValueError("请提供 aid 或 bvid 中的至少一个参数")

        uri = "/x/web-interface/view/detail"
        params = dict()
        if aid:
            params.update({"aid": aid})
        else:
            params.update({"bvid": bvid})
        
        try:
            # Get the original video detail response
            video_detail = await self.get(uri, params, enable_params_sign=False)
            
            # Extract and enhance with tag information
            # This method is designed to never fail and always return valid data
            enhanced_detail = await self._extract_video_tags_and_category(video_detail)
            
            return enhanced_detail
            
        except Exception as e:
            logger.error(f"[BilibiliClient.get_video_info] Failed to get video info for aid={aid}, bvid={bvid}: {e}")
            # Re-raise the exception as this is a critical failure
            # The calling code should handle this appropriately
            raise

    async def get_video_comments(self,
                                 video_id: str,
                                 order_mode: CommentOrderType = CommentOrderType.MIXED,
                                 next: int = 0
                                 ) -> Dict:
        """get video comments
        :param video_id: 视频 ID
        :param order_mode: 排序方式
        :param next: 评论页选择
        :return:
        """
        uri = "/x/v2/reply/wbi/main"
        post_data = {
            "oid": video_id,
            "mode": order_mode.value,
            "type": 1,
            "ps": 20,
            "next": next
        }
        return await self.get(uri, post_data)

    async def get_creator_videos(self, creator_id: str, pn: int, ps: int = 30, order_mode: SearchOrderType = SearchOrderType.LAST_PUBLISH) -> Dict:
        """get all videos for a creator
        :param creator_id: 创作者 ID
        :param pn: 页数
        :param ps: 一页视频数
        :param order_mode: 排序方式

        :return:
        """
        uri = "/x/space/wbi/arc/search"
        post_data = {
            "mid": creator_id,
            "pn": pn,
            "ps": ps,
            "order": order_mode,
        }
        return await self.get(uri, post_data)

    async def get_creator_info(self, creator_id: int) -> Dict:
        """
        get creator info
        :param creator_id: 作者 ID
        """
        uri = "/x/space/wbi/acc/info"
        post_data = {
            "mid": creator_id,
        }
        return await self.get(uri, post_data)

    async def _extract_video_tags_and_category(self, video_detail: Dict) -> Dict:
        """
        Extract and enhance video detail with tag and category information
        :param video_detail: Original video detail response
        :return: Enhanced video detail with tags and category info
        """
        # Initialize default enhanced data
        enhanced_detail = video_detail.copy()
        enhanced_detail["EnhancedTags"] = []
        enhanced_detail["CategoryInfo"] = {}
        
        try:
            # Extract view data with error handling
            view_data = video_detail.get("View", {})
            if not view_data:
                logger.warning("[BilibiliClient._extract_video_tags_and_category] No View data found, using empty defaults")
                return enhanced_detail
            
            video_id = view_data.get("bvid", view_data.get("aid", "unknown"))
            
            # Extract tags information with comprehensive error handling
            try:
                tags_data = video_detail.get("Tags", [])
                enhanced_tags = []
                
                if not isinstance(tags_data, list):
                    logger.warning(f"[BilibiliClient._extract_video_tags_and_category] Tags data is not a list for video {video_id}, got: {type(tags_data)}")
                    tags_data = []
                
                for i, tag in enumerate(tags_data):
                    try:
                        if not isinstance(tag, dict):
                            logger.warning(f"[BilibiliClient._extract_video_tags_and_category] Tag {i} is not a dict for video {video_id}, skipping")
                            continue
                            
                        enhanced_tag = {
                            "tag_id": tag.get("tag_id", 0),
                            "tag_name": tag.get("tag_name", ""),
                            "category": tag.get("category", ""),
                            "likes": tag.get("likes", 0),
                            "hates": tag.get("hates", 0),
                            "subscribed": tag.get("subscribed", False)
                        }
                        
                        # Validate tag data
                        if not enhanced_tag["tag_name"]:
                            logger.warning(f"[BilibiliClient._extract_video_tags_and_category] Empty tag name for video {video_id}, tag {i}")
                            continue
                            
                        enhanced_tags.append(enhanced_tag)
                        
                    except Exception as tag_error:
                        logger.error(f"[BilibiliClient._extract_video_tags_and_category] Error processing tag {i} for video {video_id}: {tag_error}")
                        continue
                
                enhanced_detail["EnhancedTags"] = enhanced_tags
                
                if enhanced_tags:
                    logger.info(f"[BilibiliClient._extract_video_tags_and_category] Successfully extracted {len(enhanced_tags)} tags for video {video_id}")
                else:
                    logger.info(f"[BilibiliClient._extract_video_tags_and_category] No valid tags found for video {video_id}")
                    
            except Exception as tags_error:
                logger.error(f"[BilibiliClient._extract_video_tags_and_category] Failed to extract tags for video {video_id}: {tags_error}")
                enhanced_detail["EnhancedTags"] = []
            
            # Extract category information with error handling
            try:
                category_info = {
                    "main_category": view_data.get("tname", ""),
                    "sub_category": view_data.get("typename", ""),
                    "tid": view_data.get("tid", 0)
                }
                
                # Validate category data
                if not category_info["main_category"] and not category_info["sub_category"]:
                    logger.warning(f"[BilibiliClient._extract_video_tags_and_category] No category information found for video {video_id}")
                
                enhanced_detail["CategoryInfo"] = category_info
                logger.debug(f"[BilibiliClient._extract_video_tags_and_category] Extracted category info for video {video_id}: {category_info}")
                
            except Exception as category_error:
                logger.error(f"[BilibiliClient._extract_video_tags_and_category] Failed to extract category info for video {video_id}: {category_error}")
                enhanced_detail["CategoryInfo"] = {}
            
            return enhanced_detail
            
        except Exception as e:
            logger.error(f"[BilibiliClient._extract_video_tags_and_category] Critical error in tag/category extraction: {e}")
            # Ensure we always return the original data with empty enhanced fields
            enhanced_detail = video_detail.copy()
            enhanced_detail["EnhancedTags"] = []
            enhanced_detail["CategoryInfo"] = {}
            return enhanced_detail