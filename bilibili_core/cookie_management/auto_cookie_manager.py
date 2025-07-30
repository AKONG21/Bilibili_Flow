#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动Cookie管理器
支持扫码后自动填写配置文件、过期Cookie自动删除、状态提醒等功能
"""

import os
import yaml
import json
import glob
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from bilibili_core.utils.logger import get_logger

logger = get_logger()


class AutoCookieManager:
    """自动Cookie管理器"""
    
    def __init__(self, config_file: str = "daily_task_config.yaml"):
        self.config_file = config_file
        self.config = None
        
    def _substitute_env_vars(self, obj):
        """递归替换配置中的环境变量"""
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 替换 ${VAR_NAME} 格式的环境变量
            import re
            def replace_env_var(match):
                var_name = match.group(1)
                env_value = os.environ.get(var_name)
                if env_value is None:
                    return match.group(0)  # 保持原样
                return env_value
            
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, obj)
        else:
            return obj

    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                    # 替换环境变量
                    self.config = self._substitute_env_vars(self.config)
                return True
            else:
                logger.error(f"配置文件不存在: {self.config_file}")
                return False
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            return False
    
    def save_config(self) -> bool:
        """保存配置文件（保留注释和格式）"""
        try:
            # 读取原始文件内容
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用正则表达式精确更新Cookie池部分
            updated_content = self._update_cookie_pool_in_content(content)

            # 写回文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            return True

        except Exception as e:
            logger.error(f"配置保存失败: {e}")
            return False

    def _update_cookie_pool_in_content(self, content: str) -> str:
        """在内容中更新Cookie池部分，保留注释"""
        try:
            cookie_pool_config = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})

            # 生成新的Cookie池YAML内容
            new_cookie_pool_yaml = self._generate_cookie_pool_yaml_string()

            # 查找cookie_pool部分的模式
            # 匹配从 "cookie_pool:" 开始到下一个同级配置项或文件结束
            pattern = r'(\s*cookie_pool:\s*\n)(.*?)(?=\n\s*[a-zA-Z_][a-zA-Z0-9_]*:\s*|$)'

            # 如果找到了cookie_pool部分，替换它
            if re.search(r'\s*cookie_pool:', content):
                # 替换现有的cookie_pool部分
                updated_content = re.sub(
                    pattern,
                    r'\1' + new_cookie_pool_yaml,
                    content,
                    flags=re.DOTALL
                )
                return updated_content
            else:
                # 如果没有找到cookie_pool，在cookies部分添加
                return self._add_cookie_pool_to_content(content, new_cookie_pool_yaml)

        except Exception as e:
            logger.error(f"更新Cookie池内容失败: {e}")
            return content

    def _generate_cookie_pool_yaml_string(self) -> str:
        """生成Cookie池的YAML字符串"""
        cookie_pool = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})

        lines = []
        lines.append(f"      enabled: {str(cookie_pool.get('enabled', False)).lower()}")
        lines.append(f"      selection_mode: {cookie_pool.get('selection_mode', 'random')}")
        lines.append("      cookies:")

        cookies_list = cookie_pool.get("cookies", [])
        for cookie_config in cookies_list:
            if cookie_config.get("cookie"):  # 只保存有效的Cookie
                lines.append(f"        - name: {cookie_config.get('name', 'unknown')}")

                # 处理长Cookie字符串
                cookie_str = cookie_config.get('cookie', '')
                lines.append(f"          cookie: {cookie_str}")
                lines.append(f"          priority: {cookie_config.get('priority', 1)}")
                lines.append(f"          enabled: {str(cookie_config.get('enabled', True)).lower()}")
                lines.append(f"          last_used: '{cookie_config.get('last_used', '')}'")
                lines.append(f"          failure_count: {cookie_config.get('failure_count', 0)}")
                lines.append(f"          max_failures: {cookie_config.get('max_failures', 3)}")

        return '\n'.join(lines)

    def _add_cookie_pool_to_content(self, content: str, cookie_pool_yaml: str) -> str:
        """在内容中添加Cookie池配置"""
        # 查找cookies部分，在其中添加cookie_pool
        cookies_pattern = r'(\s*cookies:\s*\n)(.*?)(?=\n\s*[a-zA-Z_][a-zA-Z0-9_]*:\s*|$)'

        if re.search(r'\s*cookies:', content):
            # 在cookies部分添加cookie_pool
            replacement = r'\1\2    cookie_pool:\n' + cookie_pool_yaml + '\n'
            return re.sub(cookies_pattern, replacement, content, flags=re.DOTALL)
        else:
            # 如果没有cookies部分，添加整个cookies配置
            login_pattern = r'(\s*login:\s*\n)'
            if re.search(r'\s*login:', content):
                replacement = r'\1  cookies:\n    cookie_pool:\n' + cookie_pool_yaml + '\n'
                return re.sub(login_pattern, replacement, content)

        return content

    def _update_config_preserving_comments(self, original_lines: list) -> bool:
        """智能更新配置文件，保留注释和格式"""
        try:
            # 找到cookie_pool部分的开始和结束位置
            cookie_pool_start = -1
            cookie_pool_end = -1
            indent_level = 0

            for i, line in enumerate(original_lines):
                stripped = line.strip()
                if 'cookie_pool:' in stripped:
                    cookie_pool_start = i
                    # 计算缩进级别
                    indent_level = len(line) - len(line.lstrip())
                    continue

                if cookie_pool_start != -1:
                    # 找到cookie_pool部分的结束位置
                    current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 2

                    # 如果遇到同级别或更低级别的配置项，说明cookie_pool部分结束
                    if line.strip() and current_indent <= indent_level:
                        cookie_pool_end = i
                        break

            # 如果没有找到结束位置，说明cookie_pool是最后一部分
            if cookie_pool_start != -1 and cookie_pool_end == -1:
                cookie_pool_end = len(original_lines)

            # 生成新的cookie_pool配置
            new_cookie_pool_lines = self._generate_cookie_pool_yaml(indent_level)

            # 构建新的文件内容
            new_lines = []

            if cookie_pool_start == -1:
                # 如果没有找到cookie_pool，添加到login部分
                new_lines = self._add_cookie_pool_to_login_section(original_lines)
            else:
                # 替换cookie_pool部分
                new_lines.extend(original_lines[:cookie_pool_start])
                new_lines.extend(new_cookie_pool_lines)
                new_lines.extend(original_lines[cookie_pool_end:])

            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return True

        except Exception as e:
            logger.error(f"智能更新配置失败: {e}")
            # 回退到原始方法
            return self._fallback_save_config()

    def _generate_cookie_pool_yaml(self, indent_level: int) -> list:
        """生成cookie_pool的YAML配置行"""
        lines = []
        base_indent = ' ' * indent_level
        item_indent = ' ' * (indent_level + 2)
        cookie_indent = ' ' * (indent_level + 4)

        cookie_pool = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})

        lines.append(f"{base_indent}cookie_pool:\n")
        lines.append(f"{item_indent}enabled: {str(cookie_pool.get('enabled', False)).lower()}\n")
        lines.append(f"{item_indent}selection_mode: {cookie_pool.get('selection_mode', 'random')}\n")
        lines.append(f"{item_indent}cookies:\n")

        cookies_list = cookie_pool.get("cookies", [])
        for cookie_config in cookies_list:
            if cookie_config.get("cookie"):  # 只保存有效的Cookie
                lines.append(f"{cookie_indent}- name: {cookie_config.get('name', 'unknown')}\n")

                # 处理长Cookie字符串，进行换行
                cookie_str = cookie_config.get('cookie', '')
                if len(cookie_str) > 80:
                    lines.append(f"{cookie_indent}  cookie: >\n")
                    lines.append(f"{cookie_indent}    {cookie_str}\n")
                else:
                    lines.append(f"{cookie_indent}  cookie: {cookie_str}\n")

                lines.append(f"{cookie_indent}  priority: {cookie_config.get('priority', 1)}\n")
                lines.append(f"{cookie_indent}  enabled: {str(cookie_config.get('enabled', True)).lower()}\n")
                lines.append(f"{cookie_indent}  last_used: '{cookie_config.get('last_used', '')}'\n")
                lines.append(f"{cookie_indent}  failure_count: {cookie_config.get('failure_count', 0)}\n")
                lines.append(f"{cookie_indent}  max_failures: {cookie_config.get('max_failures', 3)}\n")

        return lines

    def _add_cookie_pool_to_login_section(self, original_lines: list) -> list:
        """在login部分添加cookie_pool配置"""
        # 这是一个简化版本，如果需要可以进一步完善
        # 目前直接使用回退方法
        return self._fallback_save_config_lines(original_lines)

    def _fallback_save_config(self) -> bool:
        """回退保存方法"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, indent=2)
            logger.warning("使用回退方法保存配置，注释可能丢失")
            return True
        except Exception as e:
            logger.error(f"回退保存失败: {e}")
            return False

    def _fallback_save_config_lines(self, original_lines: list) -> list:
        """回退方法生成配置行"""
        # 简单返回原始行，实际应该添加cookie_pool
        return original_lines
    
    def extract_cookie_string_from_browser(self, cookies: List[Dict]) -> str:
        """从浏览器Cookie列表提取Cookie字符串"""
        try:
            # 只提取B站相关的重要Cookie
            important_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid']
            cookie_pairs = []
            
            for cookie in cookies:
                if cookie.get('name') in important_cookies and cookie.get('domain', '').endswith('bilibili.com'):
                    cookie_pairs.append(f"{cookie['name']}={cookie['value']}")
            
            return "; ".join(cookie_pairs)
        except Exception as e:
            logger.error(f"提取Cookie字符串失败: {e}")
            return ""
    
    def find_next_available_slot(self) -> Optional[int]:
        """查找下一个可用的Cookie槽位"""
        if not self.config:
            return None
            
        cookie_pool = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})
        cookies_list = cookie_pool.get("cookies", [])
        
        # 查找空槽位或禁用的槽位
        for i, cookie_config in enumerate(cookies_list):
            if not cookie_config.get("cookie") or not cookie_config.get("enabled", True):
                return i
        
        # 如果没有空槽位，检查是否可以添加新槽位（最多支持5个）
        if len(cookies_list) < 5:
            return len(cookies_list)
        
        return None
    
    def add_cookie_to_config(self, cookie_string: str, account_name: str = None) -> bool:
        """将新Cookie添加到配置文件"""
        try:
            if not self.config:
                logger.error("配置未加载")
                return False
            
            # 确保配置结构存在
            if "login" not in self.config:
                self.config["login"] = {}
            if "cookies" not in self.config["login"]:
                self.config["login"]["cookies"] = {}
            if "cookie_pool" not in self.config["login"]["cookies"]:
                self.config["login"]["cookies"]["cookie_pool"] = {
                    "enabled": True,
                    "selection_mode": "random",
                    "cookies": []
                }
            
            # 查找可用槽位
            slot_index = self.find_next_available_slot()
            if slot_index is None:
                logger.warning("没有可用的Cookie槽位")
                return False
            
            # 生成账号名称
            if not account_name:
                account_name = f"account{slot_index + 1}"
            
            # 创建Cookie配置
            cookie_config = {
                "name": account_name,
                "cookie": cookie_string,
                "priority": slot_index + 1,
                "enabled": True,
                "last_used": "",
                "failure_count": 0,
                "max_failures": 3
            }
            
            # 添加或更新Cookie
            cookies_list = self.config["login"]["cookies"]["cookie_pool"]["cookies"]
            if slot_index < len(cookies_list):
                cookies_list[slot_index] = cookie_config
                logger.info(f"更新Cookie槽位 {slot_index + 1}: {account_name}")
            else:
                cookies_list.append(cookie_config)
                logger.info(f"添加新Cookie槽位 {slot_index + 1}: {account_name}")
            
            # 启用Cookie池
            self.config["login"]["cookies"]["cookie_pool"]["enabled"] = True
            
            # 保存配置
            return self.save_config()
            
        except Exception as e:
            logger.error(f"添加Cookie到配置失败: {e}")
            return False
    
    def validate_cookie_string(self, cookie_string: str) -> bool:
        """验证Cookie字符串是否有效"""
        if not cookie_string:
            return False
        
        # 检查必需的Cookie字段
        required_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID']
        for required in required_cookies:
            if required not in cookie_string:
                logger.warning(f"Cookie缺少必需字段: {required}")
                return False
        
        return True
    
    def get_cookie_status(self) -> Dict:
        """获取Cookie状态信息"""
        if not self.config:
            return {"total": 0, "available": 0, "expired": 0, "disabled": 0}
        
        cookie_pool = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})
        cookies_list = cookie_pool.get("cookies", [])
        
        total = len([c for c in cookies_list if c.get("cookie")])
        available = len([c for c in cookies_list if c.get("cookie") and c.get("enabled", True) and c.get("failure_count", 0) < c.get("max_failures", 3)])
        disabled = len([c for c in cookies_list if not c.get("enabled", True)])
        expired = len([c for c in cookies_list if c.get("failure_count", 0) >= c.get("max_failures", 3)])
        
        return {
            "total": total,
            "available": available,
            "expired": expired,
            "disabled": disabled
        }
    
    def remove_expired_cookies(self) -> int:
        """删除过期的Cookie"""
        if not self.config:
            return 0
        
        removed_count = 0
        cookie_pool = self.config.get("login", {}).get("cookies", {}).get("cookie_pool", {})
        cookies_list = cookie_pool.get("cookies", [])
        
        # 标记过期Cookie为禁用并清空cookie字段
        for cookie_config in cookies_list:
            if cookie_config.get("failure_count", 0) >= cookie_config.get("max_failures", 3):
                if cookie_config.get("cookie"):
                    logger.info(f"删除过期Cookie: {cookie_config.get('name', 'unknown')}")
                    cookie_config["cookie"] = ""
                    cookie_config["enabled"] = False
                    cookie_config["last_used"] = ""
                    removed_count += 1
        
        if removed_count > 0:
            self.save_config()
            logger.info(f"已删除 {removed_count} 个过期Cookie")
        
        return removed_count
    
    def remove_expired_backup_files(self, backup_dir: str = "cookies/backup_cookies", max_age_days: int = 30) -> int:
        """删除过期的备份Cookie文件"""
        try:
            if not os.path.exists(backup_dir):
                return 0
            
            removed_count = 0
            cutoff_time = time.time() - (max_age_days * 24 * 3600)
            
            pattern = os.path.join(backup_dir, "cookies_*.json")
            cookie_files = glob.glob(pattern)
            
            for file_path in cookie_files:
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        removed_count += 1
                        logger.info(f"删除过期备份文件: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {file_path}: {e}")
            
            if removed_count > 0:
                logger.info(f"已删除 {removed_count} 个过期备份文件")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"清理备份文件失败: {e}")
            return 0
    
    def display_cookie_status(self):
        """显示Cookie状态"""
        status = self.get_cookie_status()
        
        print("=" * 50)
        print("🍪 Cookie状态报告")
        print("=" * 50)
        print(f"📊 总Cookie数量: {status['total']}")
        print(f"✅ 可用Cookie数量: {status['available']}")
        print(f"❌ 过期Cookie数量: {status['expired']}")
        print(f"🚫 禁用Cookie数量: {status['disabled']}")
        
        # 状态提醒
        if status['available'] < 2:
            print("\n⚠️  警告: 可用Cookie数量不足2个，建议及时补充！")
            print("💡 建议: 运行扫码登录添加新的Cookie账号")
        elif status['available'] < 3:
            print("\n💡 提示: 可用Cookie数量较少，建议适时补充")
        else:
            print("\n✨ Cookie数量充足，系统运行良好")
        
        print("=" * 50)
        
        return status
    
    def cleanup_all_expired(self) -> Dict[str, int]:
        """清理所有过期内容"""
        results = {
            "config_cookies": 0,
            "backup_files": 0
        }
        
        logger.info("开始清理过期Cookie...")
        
        # 清理配置文件中的过期Cookie
        results["config_cookies"] = self.remove_expired_cookies()
        
        # 清理过期备份文件
        backup_dir = self.config.get("login", {}).get("backup_cookies_dir", "cookies/backup_cookies")
        results["backup_files"] = self.remove_expired_backup_files(backup_dir)
        
        logger.info(f"清理完成: 配置Cookie {results['config_cookies']}个, 备份文件 {results['backup_files']}个")
        
        return results
