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
# @Time    : 2023/12/2 23:26
# @Desc    : bilibili 请求参数签名
# 逆向实现参考：https://socialsisteryi.github.io/bilibili-API-collect/docs/misc/sign/wbi.html#wbi%E7%AD%BE%E5%90%8D%E7%AE%97%E6%B3%95
import urllib.parse
from hashlib import md5
from typing import Dict

try:
    from ..utils.time_utils import get_unix_timestamp
except ImportError:
    # 处理相对导入失败的情况
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from bilibili_core.utils.time_utils import get_unix_timestamp


class BilibiliSign:
    def __init__(self, img_key: str, sub_key: str):
        self.img_key = img_key
        self.sub_key = sub_key
        self.map_table = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
            33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
            61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
            36, 20, 34, 44, 52
        ]

    def get_salt(self) -> str:
        """
        获取加盐的 key
        :return:
        """
        salt = ""
        mixin_key = self.img_key + self.sub_key
        for mt in self.map_table:
            salt += mixin_key[mt]
        return salt[:32]

    def sign(self, req_data: Dict) -> Dict:
        """
        请求参数中加上当前时间戳对请求参数中的key进行字典序排序
        再将请求参数进行 url 编码集合 salt 进行 md5 就可以生成w_rid参数了
        :param req_data:
        :return:
        """
        current_ts = get_unix_timestamp()
        req_data.update({"wts": current_ts})
        req_data = dict(sorted(req_data.items()))
        req_data = {
            # 过滤 value 中的 "!'()*" 字符
            k: ''.join(filter(lambda ch: ch not in "!'()*", str(v)))
            for k, v
            in req_data.items()
        }
        query = urllib.parse.urlencode(req_data)
        salt = self.get_salt()
        wbi_sign = md5((query + salt).encode()).hexdigest()  # 计算 w_rid
        req_data['w_rid'] = wbi_sign
        return req_data