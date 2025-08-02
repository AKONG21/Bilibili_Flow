# 🚀 B站数据采集器 (Bilibili Flow)

一个功能完整的B站UP主数据采集工具，支持热评采集、多账号Cookie管理、智能过期检测等功能。

> ⚠️ **免责声明**: 本项目仅供学习和研究目的使用，请遵守相关平台的使用条款，不得用于商业用途。

## ✨ 主要特性

- 🎯 **双模式采集**: 日任务(28天内+热评) + 月任务(全量视频)  
- 🔥 **热评采集**: 自动采集视频热门评论并存储到数据库
- 🍪 **智能Cookie管理**: 多账号轮换、自动过期检测、故障切换
- 📊 **数据库存储**: SQLite + JSON双重存储，支持增量更新
- 🗂️ **智能分类**: 按时间自动分文件夹存储
- 📱 **飞书通知**: 实时推送任务执行状态

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd Bilibili_Flow

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

编辑 `daily_task_config.yaml`：

```yaml
# 基本配置
task_config:
  up_id:   # 要监控的UP主ID

# Cookie配置 (三选一)
login:
  cookies:
    # 方式1: 单Cookie
    raw_cookie: "你的完整Cookie字符串"
    
    # 方式2: Cookie池 (推荐)
    cookie_pool:
      enabled: true
      cookies:
        - name: "账号1"
          cookie: "Cookie字符串1"
        - name: "账号2" 
          cookie: "Cookie字符串2"

# 数据采集配置
daily_task:
  hot_comments_json:
    enabled: true    # 启用热评采集
    max_count: 10    # 每个视频最多采集10条热评
  time_range:
    days: 28        # 采集28天内的视频

monthly_task:
  hot_comments_json:
    enabled: false   # 月任务不采集热评(性能考虑)
  time_range:
    get_all_videos: true  # 获取全量视频
```

### 3. 执行任务

```bash
# 日任务 (推荐用于日常监控)
python run_daily_task.py

# 月任务 (推荐用于初始化数据库)
python run_monthly_task.py

# 通用入口
python main.py --task daily
python main.py --task monthly
```

## 📁 项目结构

```
Bilibili_Flow/
├── run_daily_task.py              # 📅 日任务入口
├── run_monthly_task.py             # 📆 月任务入口  
├── daily_task_config.yaml         # ⚙️ 主配置文件
├── requirements.txt               # 📦 依赖包
│
├── bilibili_core/                # 🏗️ 核心模块
│   ├── client/                   # 🔗 API客户端
│   ├── processors/               # ⚙️ 任务处理器
│   ├── cookie_management/        # 🍪 Cookie管理
│   ├── storage/                  # 💾 数据存储
│   └── utils/                    # 🛠️ 工具函数
│
└── data/                         # 📊 数据输出
    ├── daily/2025-W31/          # 日任务数据(按周分组)
    ├── monthly/                 # 月任务数据
    └── database/                # SQLite数据库
```

## 📊 数据输出格式

### 文件命名规则
- JSON: `{up_id}_{timestamp}_{类型}.json`
- 数据库: `{up_id}_{timestamp}_数据库.db`
- 示例: `1140672573_20250802_daily.json`

### 数据结构
```json
{
  "task_info": {
    "up_id": "1140672573",
    "collection_time": "2025-08-02T15:30:00",
    "time_range": {"start_date": "2025-07-05", "end_date": "2025-08-02"}
  },
  "up_info": {
    "name": "UP主名称",
    "fans": 150000,
    "up_video_count": 242
  },
  "videos": [
    {
      "aid": 1234567,
      "title": "视频标题",
      "view": 50000,
      "like": 2000,
      "hot_comments": [
        {
          "message": "评论内容",
          "like": 100,
          "ctime": "2025-08-01T10:30:00"
        }
      ]
    }
  ]
}
```

## 🍪 Cookie 获取方法

1. **登录B站**: 在浏览器中正常登录
2. **打开开发者工具**: F12 → Network
3. **刷新页面**: 找到任意请求
4. **复制Cookie**: Request Headers → Cookie字段的完整值

## 🔧 GitHub Actions 配置

### 设置 Secrets

在 GitHub 仓库的 Settings → Secrets and variables → Actions 中添加：

| Secret名称 | 说明 | 示例 |
|------------|------|------|
| `UP_ID` | UP主ID | `1140672573` |
| `BILIBILI_COOKIES` | 主Cookie | `完整Cookie字符串` |
| `BILIBILI_COOKIES_1~10` | 备用Cookie池 | `备用Cookie字符串` |
| `FEISHU_WEBHOOK_URL` | 飞书通知地址(可选) | `https://open.feishu.cn/...` |

### 工作流说明

- **月任务**: 每月1号执行，初始化数据库
- **日任务**: 每天定时执行，采集最新数据
- **手动触发**: 支持手动运行任务

## 📱 飞书通知配置

### 1. 创建飞书群机器人
1. 飞书群 → 设置 → 机器人 → 添加机器人
2. 选择"自定义机器人" → 添加
3. 复制 Webhook 地址

### 2. 配置通知内容
系统会自动推送：
- 🍪 Cookie状态和切换信息
- 📊 采集统计(视频数、评论数等)
- ⏱️ 执行时间和性能指标
- ❌ 错误信息和异常提醒

## 🛠️ 高级功能

### Cookie池管理
- **自动轮换**: 按配置策略切换账号
- **健康检查**: 定期验证Cookie有效性
- **故障切换**: Cookie失效时自动使用备用账号
- **过期检测**: 智能识别Cookie过期并发出警告

### 数据增量更新
- **智能识别**: 自动区分新视频和已知视频
- **数据版本**: 支持同一视频的多次数据快照
- **时间戳**: 精确记录每次采集的时间点

### 任务模式对比

| 特性 | 日任务 | 月任务 |
|------|--------|--------|
| 视频范围 | 28天内 | 全量视频 |
| 热评采集 | ✅ 启用 | ❌ 禁用 |
| 执行频率 | 每日 | 每月 |
| 适用场景 | 日常监控 | 数据初始化 |
| 性能消耗 | 低 | 高 |

## 🚨 注意事项

1. **请求频率**: 已内置延时机制，避免频繁请求
2. **Cookie安全**: 不要在公开场所暴露Cookie信息
3. **数据合规**: 仅用于学习研究，请遵守平台规定
4. **资源消耗**: 月任务会消耗更多时间和网络资源

## 📝 更新日志

### v2.0.0 (2025-08-02)
- ✅ 新增热评采集功能
- ✅ 优化数据库结构(添加hot_comments_json字段)
- ✅ 统一文件命名格式({up_id}_{timestamp}_{类型})
- ✅ 精简项目结构，清理无用文件

### v1.0.0 
- ✅ 基础数据采集功能
- ✅ Cookie管理系统
- ✅ 双重存储机制

## 📄 许可证

本项目基于学习研究目的开发，使用时请遵守相关法律法规和平台服务条款。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！