# 飞书Webhook通知配置指南

## 📋 概述

B站数据跟踪系统支持飞书群机器人实时通知，能够自动从终端输出中提取关键信息并推送到飞书群，包括：
- 🍪 Cookie状态和轮换信息
- 📊 任务执行统计数据
- ⏱️ 执行时间和性能指标
- ❌ 错误信息和异常提醒

## 🔧 飞书侧配置步骤

### 1. 创建飞书群机器人

1. **打开飞书群聊**
   - 在需要接收通知的飞书群中操作

2. **添加机器人**
   - 点击群聊右上角设置按钮
   - 选择"机器人" → "添加机器人"
   - 选择"自定义机器人"

3. **配置机器人**
   - **机器人名称**: B站数据跟踪系统 (或自定义名称)
   - **描述**: GitHub Actions自动通知机器人
   - **头像**: 可选择系统默认或上传自定义头像

4. **获取Webhook URL**
   - 创建完成后，复制机器人的Webhook URL
   - URL格式类似: `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 2. 安全设置（推荐）

1. **IP白名单设置**
   - 在机器人设置中配置GitHub Actions的IP范围
   - 或选择"不限制IP"（简化配置）

2. **签名验证**
   - 如需要额外安全性，可启用签名验证
   - 本项目暂未实现签名验证，建议通过IP限制保证安全

## 🎯 GitHub侧配置步骤

### 1. 配置Repository Secrets

在GitHub仓库中配置以下Secret：

1. **进入仓库设置**
   ```
   仓库页面 → Settings → Secrets and variables → Actions
   ```

2. **添加FEISHU_WEBHOOK_URL**
   ```
   Name: FEISHU_WEBHOOK_URL
   Value: https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url-here
   ```

### 2. 验证配置

可以通过手动触发GitHub Actions工作流来验证配置：
1. 进入Actions页面
2. 选择任意工作流
3. 点击"Run workflow"进行测试

## 📊 通知内容字段说明

### Cookie状态信息
| 字段名 | 描述 | 示例值 |
|--------|------|--------|
| total_cookies | 总Cookie数量 | 5 |
| selected_cookies | 已选择Cookie数量 | 3 |
| active_cookie | 当前使用的Cookie名称 | BILIBILI_COOKIES_1 |
| cookie_info | Cookie详细信息 | 连接成功: 用户名 (Lv.6) |

### 任务执行统计  
| 字段名 | 描述 | 示例值 |
|--------|------|--------|
| up_name | UP主名称 | 某UP主 |
| total_videos | 处理视频数量 | 25 |
| total_comments | 收集评论数量 | 150 |
| errors_count | 错误次数 | 2 |
| retries_count | 重试次数 | 1 |
| duration_seconds | 任务执行时长（秒） | 45.67 |

### 执行环境信息
| 字段名 | 描述 | 示例值 |
|--------|------|--------|
| total_duration | 总执行时间（分钟） | 15.3 |
| return_code | 进程退出码 | 0 |
| workflow_name | 工作流名称 | Daily Data Collection - Morning |
| run_number | 运行编号 | #123 |
| branch | 分支名称 | main |

## 🎨 通知卡片样式

### 成功通知（绿色卡片）
```
✅ 🌅 晨间数据采集 - SUCCESS

📦 仓库: Bilibili_Flow
🔄 工作流: Daily Data Collection - Morning  
📅 时间: 2025-07-28 12:34:56
🏷️ 运行: #123
🌿 分支: main

🔐 Cookie状态
🍪 总Cookie数: 5
🎲 已选择: 3 个
✅ 当前Cookie: BILIBILI_COOKIES_1
ℹ️ Cookie信息: 连接成功: 用户名 (Lv.6)

📊 任务统计  
👤 UP主: 某UP主
🎬 处理视频: 25 个
💬 收集评论: 150 条
❌ 错误次数: 0
🔄 重试次数: 0
⏱️ 执行时长: 2.3 分钟

🚀 执行信息
⏰ 总执行时间: 15.3 分钟
✅ 退出码: 0
```

### 失败通知（红色卡片）
```
❌ 🌙 晚间数据采集 - FAILURE  

📦 仓库: Bilibili_Flow
🔄 工作流: Daily Data Collection - Evening
📅 时间: 2025-07-28 20:34:56
🏷️ 运行: #124
🌿 分支: main

⚠️ 错误信息
- ❌ Cookie BILIBILI_COOKIES_2 测试失败: HTTP 403
- ❌ 所有Cookie都无法使用
- ❌ 任务执行失败

🚀 执行信息
⏰ 总执行时间: 5.2 分钟  
❌ 退出码: 1
```

## 🔍 信息提取原理

系统通过正则表达式从终端输出中提取关键信息：

### Cookie相关模式
```python
# Cookie配置数量
r'发现 (\d+) 个Cookie配置'

# Cookie选择结果  
r'随机选择了 (\d+) 个Cookie进行轮换'

# Cookie测试结果
r'Cookie ([^\s]+) 测试成功: (.+)'
r'Cookie ([^\s]+) 测试失败: (.+)'
```

### 任务统计模式
```python  
# 基本统计
r'UP主: (.+)'
r'处理视频数: (\d+)'  
r'收集评论数: (\d+)'
r'错误次数: (\d+)'
r'重试次数: (\d+)'
r'执行时长: ([\d.]+) 秒'
```

### 错误信息模式
```python
# 错误标识
r'❌.*'
r'ERROR.*'  
r'失败.*'
```

## 🎛️ 高级配置选项

### 1. 自定义通知模板

可以修改 `feishu_notifier.py` 中的模板来自定义通知样式：

```python
# 状态配置
status_config = {
    "success": {"icon": "✅", "template": "green"},
    "failure": {"icon": "❌", "template": "red"}, 
    "warning": {"icon": "⚠️", "template": "orange"},
    "info": {"icon": "ℹ️", "template": "blue"}
}
```

### 2. 信息过滤

可以在 `format_extracted_data` 函数中调整显示的信息：

```python
# 只显示前5个错误
error_list = data['errors'][:5]

# 自定义时间格式
duration_min = ts['duration_seconds'] / 60
```

### 3. 通知频率控制

可以根据需要调整通知的触发条件：
- 只在失败时通知  
- 每日汇总通知
- 重要指标阈值告警

## 🚨 故障排除

### 1. Webhook URL无效
```
❌ 飞书通知HTTP错误: 404
```
**解决方案**: 检查FEISHU_WEBHOOK_URL是否正确配置

### 2. 机器人被禁用
```  
❌ 飞书通知发送失败: robot is disabled
```
**解决方案**: 检查飞书群中机器人状态，重新启用

### 3. 消息格式错误
```
❌ 飞书通知发送失败: invalid card format
```
**解决方案**: 检查Markdown格式，确保符合飞书卡片规范

### 4. IP限制
```
❌ 飞书通知HTTP错误: 403  
```
**解决方案**: 检查机器人IP白名单设置

## 📈 最佳实践

1. **监控告警分级**
   - 🔴 严重: Cookie全部失效、任务完全失败
   - 🟡 警告: 部分Cookie失效、重试次数高
   - 🟢 正常: 任务成功完成

2. **信息精简**
   - 成功通知：关键指标 + 简要统计
   - 失败通知：详细错误信息 + 诊断建议

3. **时间优化**
   - 避免深夜发送成功通知
   - 失败通知立即发送
   - 周报汇总推送

4. **群管理**
   - 建议使用专门的运维群
   - 设置群消息免打扰时间
   - 定期清理机器人消息

通过以上配置，您的B站数据跟踪系统将具备完善的飞书实时通知能力，确保系统运行状态的及时感知和问题快速处理。