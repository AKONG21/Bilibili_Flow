# GitHub Actions 配置说明

## 概述
本项目使用 GitHub Actions 实现 B 站视频数据跟踪系统的自动化执行，包含三个主要工作流程：

## 工作流程

### 1. 每日早晨数据采集 (daily-morning.yml)
- **执行时间**: 每日 8:00 (北京时间)
- **目标**: 采集前一天 10 点上传视频的 10 小时后数据
- **功能**: 初始互动数据采集
- **文件**: `.github/workflows/daily-morning.yml`

### 2. 每日晚间数据采集 (daily-evening.yml)
- **执行时间**: 每日 20:00 (北京时间)
- **目标**: 采集同一视频的 22 小时后数据
- **功能**: 计算 12 小时增长率
- **文件**: `.github/workflows/daily-evening.yml`

### 3. 每周历史数据处理 (weekly-historical.yml)
- **执行时间**: 每周五 8:00 (北京时间)
- **目标**: 全量历史数据 + 28 天分段
- **功能**: 历史数据基准建立
- **文件**: `.github/workflows/weekly-historical.yml`

## 必需的 Secrets 配置

在 GitHub 仓库设置中，需要配置以下 Secrets：

### 多账号 Cookie 配置（推荐）
为了解决 Cookie 频繁过期问题，支持配置多个 B 站账号 Cookie：

```
BILIBILI_COOKIES_1=your_first_bilibili_cookies_here
BILIBILI_COOKIES_2=your_second_bilibili_cookies_here  
BILIBILI_COOKIES_3=your_third_bilibili_cookies_here
BILIBILI_COOKIES_4=your_fourth_bilibili_cookies_here
BILIBILI_COOKIES_5=your_fifth_bilibili_cookies_here
```

### 单账号 Cookie 配置（向后兼容）
```
BILIBILI_COOKIES=your_bilibili_cookies_here
```

### 飞书通知配置（推荐）
为了实时跟踪工作流程执行状态，支持飞书Webhook通知：

```
FEISHU_WEBHOOK_URL=your_feishu_webhook_url_here
```

### 可选Telegram通知配置（已废弃）
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## 通知功能

### 飞书Webhook通知
系统支持飞书群机器人通知，在工作流程开始和结束时发送状态更新：

- ✅ **成功通知**: 任务成功完成后发送绿色状态卡片
- ❌ **失败通知**: 任务失败时发送红色警告卡片
- ℹ️ **开始通知**: 任务开始时发送蓝色信息卡片
- 📊 **详细信息**: 包含执行时间、分支信息和运行编号

### 飞书Webhook配置步骤
1. 在飞书群中添加自定义机器人
2. 获取Webhook URL
3. 在GitHub Secrets中配置 `FEISHU_WEBHOOK_URL`

## Cookie 轮换机制

系统会自动选择最佳可用的 Cookie：

1. **智能检测**: 自动验证每个 Cookie 的有效性
2. **优先级选择**: 优先使用编号最小的有效 Cookie
3. **故障切换**: 当前 Cookie 失效时自动切换到下一个
4. **格式验证**: 确保 Cookie 包含必需字段（SESSDATA、bili_jct、DedeUserID）

## Cookie 管理最佳实践

1. **多账号准备**: 建议配置 2-3 个备用账号
2. **定期更新**: 每周检查并更新即将过期的 Cookie
3. **格式正确**: 确保 Cookie 格式为 `name1=value1; name2=value2`
4. **及时替换**: 发现 Cookie 失效时及时替换对应的 Secret

## 配置步骤

1. **进入仓库设置**
   - 在 GitHub 仓库页面，点击 Settings
   - 在左侧菜单中找到 Secrets and variables → Actions

2. **添加 Repository secrets**
   - 点击 "New repository secret"
   - 分别添加上述必需的 secrets

3. **启用 Actions**
   - 在 Actions 页面确保工作流程已启用
   - 可以手动触发工作流程进行测试

## 工作流程特性

- **自动依赖缓存**: 使用 pip 缓存加速构建
- **浏览器自动安装**: 自动安装 Playwright Chromium
- **自动提交**: 自动提交数据和日志到仓库
- **日志上传**: 上传执行日志作为 artifacts
- **错误处理**: 包含完整的错误处理和报告
- **增强Cookie管理**: 随机选择、故障切换、失效Cookie清理
- **实时通知**: 飞书Webhook实时状态通知

## 手动执行

所有工作流程都支持手动触发：
1. 进入 Actions 页面
2. 选择对应的工作流程
3. 点击 "Run workflow"

## 注意事项

- 确保 `run_daily_task.py` 和 `run_monthly_task.py` 脚本能正常执行
- 工作流程使用 UTC 时间，已转换为北京时间
- 日志文件会自动上传，保留期为 7-30 天
- 数据变更会自动提交到仓库的 `data/` 和 `logs/` 目录