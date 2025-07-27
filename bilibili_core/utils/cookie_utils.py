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
# @Time    : 2023/12/3 16:20
# @Desc    : Cookie utilities

from typing import Dict, List, Tuple


def convert_cookies(cookies: List[Dict]) -> Tuple[str, Dict[str, str]]:
    """
    Convert playwright cookies to cookie string and dictionary
    
    Args:
        cookies: List of cookie dictionaries from playwright
        
    Returns:
        Tuple of (cookie_string, cookie_dict)
    """
    cookie_str = ""
    cookie_dict = {}
    
    for cookie in cookies:
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        if name and value:
            cookie_str += f"{name}={value}; "
            cookie_dict[name] = value
    
    return cookie_str.rstrip('; '), cookie_dict