#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞书Webhook通知脚本 - 增强版
用于发送GitHub Actions执行结果通知到飞书群
支持从终端输出中提取Cookie状态、任务统计和执行时间信息
"""

import requests
import json
import os
import sys
import re
import subprocess
from datetime import datetime
from typing import Dict, Optional, List, Tuple

class EnhancedFeishuNotifier:
    """增强版飞书通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def parse_terminal_output(self, output: str) -> Dict:
        """解析终端输出，提取关键信息"""
        extracted_data = {
            'cookie_status': {},
            'task_statistics': {},
            'execution_info': {},
            'errors': []
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Cookie状态解析
            if '发现' in line and '个Cookie配置' in line:
                match = re.search(r'发现 (\d+) 个Cookie配置', line)
                if match:
                    extracted_data['cookie_status']['total_cookies'] = int(match.group(1))
            
            if '随机选择了' in line and '个Cookie进行轮换' in line:
                match = re.search(r'随机选择了 (\d+) 个Cookie进行轮换', line)
                if match:
                    extracted_data['cookie_status']['selected_cookies'] = int(match.group(1))
            
            if 'Cookie' in line and '测试成功' in line:
                match = re.search(r'Cookie ([^\s]+) 测试成功: (.+)', line)
                if match:
                    extracted_data['cookie_status']['active_cookie'] = match.group(1)
                    extracted_data['cookie_status']['cookie_info'] = match.group(2)
            
            if 'Cookie' in line and '测试失败' in line:
                match = re.search(r'Cookie ([^\s]+) 测试失败: (.+)', line)
                if match:
                    extracted_data['errors'].append(f"Cookie {match.group(1)} 失败: {match.group(2)}")
            
            # 任务统计解析
            if 'UP主:' in line:
                match = re.search(r'UP主: (.+)', line)
                if match:
                    extracted_data['task_statistics']['up_name'] = match.group(1)
            
            if '处理视频数:' in line:
                match = re.search(r'处理视频数: (\d+)', line)
                if match:
                    extracted_data['task_statistics']['total_videos'] = int(match.group(1))
            
            if '收集评论数:' in line:
                match = re.search(r'收集评论数: (\d+)', line)
                if match:
                    extracted_data['task_statistics']['total_comments'] = int(match.group(1))
            
            if '错误次数:' in line:
                match = re.search(r'错误次数: (\d+)', line)
                if match:
                    extracted_data['task_statistics']['errors_count'] = int(match.group(1))
            
            if '重试次数:' in line:
                match = re.search(r'重试次数: (\d+)', line)
                if match:
                    extracted_data['task_statistics']['retries_count'] = int(match.group(1))
            
            if '执行时长:' in line:
                match = re.search(r'执行时长: ([\d.]+) 秒', line)
                if match:
                    extracted_data['task_statistics']['duration_seconds'] = float(match.group(1))
            
            # 执行信息解析
            if '任务执行完成' in line:
                extracted_data['execution_info']['status'] = 'completed'
            
            if '任务执行失败' in line:
                extracted_data['execution_info']['status'] = 'failed'
                
            # 错误信息收集
            if '❌' in line or 'ERROR' in line or '失败' in line:
                if line not in extracted_data['errors']:
                    extracted_data['errors'].append(line)
        
        return extracted_data
    
    def capture_workflow_output(self, command: List[str]) -> Tuple[str, int, Dict]:
        """捕获工作流命令输出并解析"""
        try:
            start_time = datetime.now()
            
            # 执行命令并捕获输出
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 合并stdout和stderr
            full_output = result.stdout + "\n" + result.stderr
            
            # 解析输出
            parsed_data = self.parse_terminal_output(full_output)
            parsed_data['execution_info']['total_duration'] = duration
            parsed_data['execution_info']['return_code'] = result.returncode
            
            return full_output, result.returncode, parsed_data
            
        except subprocess.TimeoutExpired:
            return "命令执行超时", 1, {'execution_info': {'status': 'timeout'}}
        except Exception as e:
            return f"命令执行异常: {e}", 1, {'execution_info': {'status': 'error'}}
    
    def format_extracted_data(self, data: Dict) -> str:
        """格式化提取的数据为markdown"""
        sections = []
        
        # Cookie状态部分
        if data.get('cookie_status'):
            cookie_info = []
            cs = data['cookie_status']
            
            if cs.get('total_cookies'):
                cookie_info.append(f"🍪 **总Cookie数**: {cs['total_cookies']}")
            if cs.get('selected_cookies'):
                cookie_info.append(f"🎲 **已选择**: {cs['selected_cookies']} 个")
            if cs.get('active_cookie'):
                cookie_info.append(f"✅ **当前Cookie**: {cs['active_cookie']}")
            if cs.get('cookie_info'):
                cookie_info.append(f"ℹ️ **Cookie信息**: {cs['cookie_info']}")
            
            if cookie_info:
                sections.append("**🔐 Cookie状态**\n" + "\n".join(cookie_info))
        
        # 任务统计部分
        if data.get('task_statistics'):
            task_info = []
            ts = data['task_statistics']
            
            if ts.get('up_name'):
                task_info.append(f"👤 **UP主**: {ts['up_name']}")
            if ts.get('total_videos') is not None:
                task_info.append(f"🎬 **处理视频**: {ts['total_videos']} 个")
            if ts.get('total_comments') is not None:
                task_info.append(f"💬 **收集评论**: {ts['total_comments']} 条")
            if ts.get('errors_count') is not None:
                task_info.append(f"❌ **错误次数**: {ts['errors_count']}")
            if ts.get('retries_count') is not None:
                task_info.append(f"🔄 **重试次数**: {ts['retries_count']}")
            if ts.get('duration_seconds') is not None:
                duration_min = ts['duration_seconds'] / 60
                task_info.append(f"⏱️ **执行时长**: {duration_min:.1f} 分钟")
            
            if task_info:
                sections.append("**📊 任务统计**\n" + "\n".join(task_info))
        
        # 执行信息部分
        if data.get('execution_info'):
            exec_info = []
            ei = data['execution_info']
            
            if ei.get('total_duration'):
                total_min = ei['total_duration'] / 60
                exec_info.append(f"⏰ **总执行时间**: {total_min:.1f} 分钟")
            
            if ei.get('return_code') is not None:
                status_icon = "✅" if ei['return_code'] == 0 else "❌"
                exec_info.append(f"{status_icon} **退出码**: {ei['return_code']}")
            
            if exec_info:
                sections.append("**🚀 执行信息**\n" + "\n".join(exec_info))
        
        # 错误信息部分
        if data.get('errors'):
            error_list = data['errors'][:5]  # 只显示前5个错误
            if error_list:
                sections.append("**⚠️ 错误信息**\n" + "\n".join([f"- {err}" for err in error_list]))
        
        return "\n\n".join(sections) if sections else "无详细信息可显示"
    
    def send_enhanced_notification(self, 
                                 workflow_name: str,
                                 status: str,
                                 extracted_data: Dict,
                                 repository: str = "B站数据跟踪系统") -> bool:
        """发送增强版GitHub Actions通知"""
        # 状态配置
        status_config = {
            "success": {"icon": "✅", "template": "green"},
            "failure": {"icon": "❌", "template": "red"},
            "warning": {"icon": "⚠️", "template": "orange"},
            "info": {"icon": "ℹ️", "template": "blue"}
        }
        
        config = status_config.get(status, status_config["info"])
        
        # 构建标题
        title = f"{config['icon']} {workflow_name} - {status.upper()}"
        
        # 构建基本信息
        basic_info = [
            f"**📦 仓库**: {repository}",
            f"**🔄 工作流**: {workflow_name}", 
            f"**📅 时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**🏷️ 运行**: #{os.environ.get('GITHUB_RUN_NUMBER', 'N/A')}",
            f"**🌿 分支**: {os.environ.get('GITHUB_REF_NAME', 'main')}"
        ]
        
        # 格式化提取的数据
        detailed_info = self.format_extracted_data(extracted_data)
        
        # 组合内容
        content_parts = basic_info + ["", detailed_info] if detailed_info != "无详细信息可显示" else basic_info
        content = "\n".join(content_parts)
        
        # 构建消息
        payload = {
            "msg_type": "interactive",
            "card": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": content,
                            "tag": "lark_md"
                        }
                    }
                ],
                "header": {
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    },
                    "template": config["template"]
                }
            }
        }
        
        try:
            response = self.session.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"✅ 飞书增强通知发送成功")
                    return True
                else:
                    print(f"❌ 飞书通知发送失败: {result.get('msg', 'Unknown error')}")
                    return False
            else:
                print(f"❌ 飞书通知HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 飞书通知异常: {e}")
            return False

def send_enhanced_workflow_notification(workflow_name: str, 
                                      command: List[str], 
                                      repository: str = None) -> bool:
    """发送增强版工作流通知的便捷函数"""
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL')
    
    if not webhook_url:
        print("⚠️ FEISHU_WEBHOOK_URL环境变量未设置，跳过飞书通知")
        return False
    
    if not repository:
        repository = os.environ.get('GITHUB_REPOSITORY', 'B站数据跟踪系统')
        if '/' in repository:
            repository = repository.split('/')[-1]
    
    notifier = EnhancedFeishuNotifier(webhook_url)
    
    # 发送开始通知
    notifier.send_enhanced_notification(
        workflow_name=workflow_name,
        status="info",
        extracted_data={'execution_info': {'status': 'starting'}},
        repository=repository
    )
    
    # 执行命令并捕获输出
    output, return_code, extracted_data = notifier.capture_workflow_output(command)
    
    # 确定状态
    if return_code == 0:
        status = "success"
    else:
        status = "failure"
    
    # 发送结果通知
    return notifier.send_enhanced_notification(
        workflow_name=workflow_name,
        status=status,
        extracted_data=extracted_data,
        repository=repository
    )

def main():
    """主函数 - 用于命令行调用"""
    if len(sys.argv) < 3:
        print("用法: python enhanced_feishu_notifier.py <workflow_name> <command> [args...]")
        print("示例: python enhanced_feishu_notifier.py '每日数据采集' python run_daily_task.py")
        sys.exit(1)
    
    workflow_name = sys.argv[1]
    command = sys.argv[2:]
    
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL')
    if not webhook_url:
        print("❌ 错误: FEISHU_WEBHOOK_URL环境变量未设置")
        sys.exit(1)
    
    success = send_enhanced_workflow_notification(workflow_name, command)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()