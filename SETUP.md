# Bilibili Flow 设置指南

## GitHub Secrets 配置

为了保护敏感信息，需要在 GitHub 仓库中设置以下 Secrets：

### 必需的 Secrets

1. **UP_ID** - B站UP主的用户ID
   - 值：`1140672573` (或你要监控的UP主ID)

2. **BILIBILI_COOKIES** - 主要的B站登录Cookie
   - 从浏览器开发者工具中获取完整的Cookie字符串

3. **BILIBILI_COOKIES_1** 到 **BILIBILI_COOKIES_10** - 备用Cookie池
   - 可选，用于Cookie轮换和故障转移

4. **FEISHU_WEBHOOK_URL** - 飞书通知Webhook地址
   - 可选，用于接收任务执行通知

### 如何设置 Secrets

1. 进入你的 GitHub 仓库
2. 点击 `Settings` 标签
3. 在左侧菜单中选择 `Secrets and variables` > `Actions`
4. 点击 `New repository secret`
5. 输入 Secret 名称和值
6. 点击 `Add secret`

## 数据保护

- `data/` 目录已被添加到 `.gitignore` 中
- 所有收集的数据都不会被提交到 Git 仓库
- Fork 的仓库无法获取到你的历史数据
- 只有工作流运行时才会生成和存储数据

## 本地开发

如果需要本地运行，请：

1. 创建 `.env` 文件：
```bash
UP_ID=1140672573
BILIBILI_COOKIES=你的Cookie字符串
FEISHU_WEBHOOK_URL=你的飞书Webhook地址
```

2. 修改 `daily_task_config.yaml` 中的 `up_id` 为实际值（仅用于本地测试）

## 安全建议

- 定期更新 Cookie（建议每月更新一次）
- 不要在公开场合分享你的 Cookie 或 UP_ID
- 如果怀疑 Cookie 泄露，立即更换
- 考虑使用小号的 Cookie 来降低风险