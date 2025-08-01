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
# @Time    : 2023/12/3 16:20
# @Desc    :

from enum import Enum


class SearchOrderType(Enum):
    # 综合排序
    DEFAULT = ""

    # 最多点击
    MOST_CLICK = "click"

    # 最新发布
    LAST_PUBLISH = "pubdate"

    # 最多弹幕
    MOST_DANMU = "dm"

    # 最多收藏
    MOST_MARK = "stow"


class CommentOrderType(Enum):
    # 仅按热度
    DEFAULT = 0

    # 按热度+按时间
    MIXED = 1

    # 按时间
    TIME = 2