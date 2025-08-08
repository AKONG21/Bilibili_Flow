# 🚀 B站数据采集器 (Bilibili Flow)

一个功能完整的B站UP主数据采集工具，支持热评采集、视频标签提取、CSV数据导出、多账号Cookie管理、智能过期检测等功能。

> ⚠️ **免责声明**: 本项目仅供学习和研究目的使用，请遵守相关平台的使用条款，不得用于商业用途。

## ✨ 主要特性

- 🎯 **双模式采集**: 日任务(28天内+热评) + 月任务(全量视频)  
- 🔥 **热评采集**: 自动采集视频热门评论并存储到数据库
- 🏷️ **视频标签提取**: 自动提取视频标签和分类信息用于内容分析
- 📊 **CSV数据导出**: 支持CSV格式导出，兼容Excel、pandas等数据分析工具
- 🍪 **智能Cookie管理**: 多账号轮换、自动过期检测、故障切换
- 💾 **多格式存储**: SQLite + JSON + CSV三重存储，支持增量更新
- 🗂️ **智能分类**: 按时间自动分文件夹存储
- 📱 **飞书通知**: 实时推送任务执行状态
- 🔧 **手动执行**: 支持GitHub Actions手动触发，无需定时任务

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
  up_id: 23947287   # 要监控的UP主ID

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

# 数据存储配置
storage:
  export_format: csv  # 导出格式: json, csv, both
  csv_options:
    encoding: utf-8
    delimiter: ','
    include_headers: true
    escape_special_chars: true

# 数据采集配置
daily_task:
  hot_comments_json:
    enabled: true    # 启用热评采集
    max_count: 10    # 每个视频最多采集10条热评
    fields:          # 热评字段配置
      - message      # 评论内容
      - mid          # 用户ID
      - ctime        # 评论时间
      - like         # 点赞数
      - rcount       # 回复数
  video_fields:
    tags:
      enabled: true           # 启用视频标签提取
      include_tag_id: true    # 包含标签ID
      include_tag_name: true  # 包含标签名称
      include_category: true  # 包含分类信息
      max_tags: 20           # 最大标签数量
  time_range:
    days: 28        # 采集28天内的视频

monthly_task:
  hot_comments_json:
    enabled: true    # 月任务也启用热评采集
    max_count: 10    # 每个视频最多采集10条热评
  video_fields:
    tags:
      enabled: true           # 启用视频标签提取
      include_tag_id: true    # 包含标签ID
      include_tag_name: true  # 包含标签名称
      include_category: true  # 包含分类信息
      max_tags: 20           # 最大标签数量
  time_range:
    get_all_videos: true  # 获取全量视频
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
│   │   ├── bilibili_client.py    # 主客户端(含视频标签提取)
│   │   └── field.py              # 枚举类型定义
│   ├── processors/               # ⚙️ 任务处理器
│   │   └── daily_task_processor.py # 主任务处理器(含热评采集)
│   ├── cookie_management/        # 🍪 Cookie管理
│   ├── storage/                  # 💾 数据存储
│   │   ├── simple_storage.py     # 主存储类
│   │   └── csv_exporter.py       # CSV导出工具
│   └── utils/                    # 🛠️ 工具函数
│       └── data_converter.py     # 数据转换工具
│
└── data/                         # 📊 数据输出
    ├── daily/2025-W31/          # 日任务数据(按周分组)
    │   ├── {up_id}_{timestamp}_videos.csv      # 视频数据CSV
    │   ├── {up_id}_{timestamp}_comments.csv    # 评论数据CSV
    │   ├── {up_id}_{timestamp}_hot_comments.csv # 热评数据CSV
    │   └── {up_id}_{timestamp}_up_info.csv     # UP主信息CSV
    ├── monthly/                 # 月任务数据
    └── database/                # SQLite数据库
```


## 📊 数据格式说明

### CSV文件格式

系统会自动生成以下CSV文件，便于数据分析：

#### 1. 视频数据 (`{up_id}_{timestamp}_videos.csv`)

| 字段名 | 说明 | 示例 |
|--------|------|------|
| `aid` | 视频AV号 | `123456789` |
| `title` | 视频标题 | `【技术分享】如何优化代码性能` |
| `video_url` | 视频链接 | `https://www.bilibili.com/video/BV1xx411c7mD` |
| `publish_time` | 发布时间 | `2025-01-15 14:30:00` |
| `duration` | 视频时长(秒) | `1200` |
| `category` | 视频分类 | `科技` |
| `description` | 视频简介 | `本期视频介绍...` |
| `tags` | 视频标签 | `编程; 技术; 教程; Python` |
| `view` | 播放量 | `50000` |
| `like` | 点赞数 | `1500` |
| `reply` | 评论数 | `200` |
| `favorite` | 收藏数 | `800` |
| `share` | 分享数 | `100` |
| `coin` | 投币数 | `300` |
| `danmaku` | 弹幕数 | `500` |
| `hot_comments` | 热评摘要 | `太棒了; 学到了; 感谢分享` |

#### 2. 评论数据 (`{up_id}_{timestamp}_comments.csv`)

| 字段名 | 说明 | 示例 |
|--------|------|------|
| `comment_id` | 评论ID | `987654321` |
| `video_id` | 所属视频ID | `123456789` |
| `message` | 评论内容 | `这个教程太有用了！` |
| `mid` | 评论者用户ID | `456789123` |
| `ctime` | 评论时间戳 | `1705123456` |
| `like` | 点赞数 | `50` |
| `rcount` | 回复数 | `5` |
| `comment_type` | 评论类型 | `regular` |

#### 3. 热评数据 (`{up_id}_{timestamp}_hot_comments.csv`)

热评数据结构与普通评论相同，但 `comment_type` 字段为 `hot`：

```csv
comment_id,video_id,message,mid,ctime,like,rcount,comment_type
987654321,123456789,"太棒了，学到很多！",456789123,1705123456,150,12,hot
987654322,123456789,"感谢UP主的分享",456789124,1705123457,120,8,hot
```

#### 4. UP主信息 (`{up_id}_{timestamp}_up_info.csv`)

| 字段名 | 说明 | 示例 |
|--------|------|------|
| `mid` | UP主用户ID | `23947287` |
| `name` | UP主昵称 | `技术分享者` |
| `fans` | 粉丝数 | `100000` |
| `up_video_count` | 视频总数 | `500` |
| `export_timestamp` | 导出时间 | `2025-01-15T14:30:00` |

### 热评数据结构

热评采集功能会收集每个视频的热门评论，数据结构如下：

```json
{
  "comment_id": "987654321",
  "message": "这个教程太有用了，感谢UP主！",
  "mid": 456789123,
  "uname": "用户昵称",
  "ctime": 1705123456,
  "like": 150,
  "rcount": 12,
  "replies": [
    {
      "message": "同感！",
      "uname": "回复者",
      "like": 20
    }
  ]
}
```

### 视频标签数据结构

视频标签提取功能会获取详细的标签信息：

```json
{
  "tags": [
    {
      "tag_id": 12345,
      "tag_name": "编程",
      "category": "科技"
    },
    {
      "tag_id": 12346,
      "tag_name": "Python",
      "category": "编程语言"
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

- **手动日任务**: 通过GitHub Actions页面手动触发日任务
- **手动月任务**: 通过GitHub Actions页面手动触发月任务
- **自动触发**: 已移除定时任务，改为完全手动执行模式
- **任务描述**: 手动执行时可添加任务描述便于追踪

### 手动执行步骤

1. 进入GitHub仓库的 **Actions** 页面
2. 选择 **Daily Data Collection** 或 **Monthly Historical Data Collection**
3. 点击 **Run workflow** 按钮
4. 可选填写任务描述(如"测试新功能"、"补充数据"等)
5. 点击 **Run workflow** 开始执行

### 执行结果

- **数据文件**: 自动提交到 `sync-current-files` 分支
- **CSV导出**: 生成视频、评论、热评、UP主信息的CSV文件
- **飞书通知**: 执行完成后发送结果通知(如已配置)

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
| 热评采集 | ✅ 启用 | ✅ 启用 |
| 视频标签提取 | ✅ 启用 | ✅ 启用 |
| CSV导出 | ✅ 支持 | ✅ 支持 |
| 执行方式 | 手动触发 | 手动触发 |
| 适用场景 | 日常监控 | 数据初始化/全量分析 |
| 性能消耗 | 低 | 高 |
| 数据完整性 | 增量更新 | 全量数据 |

## 📈 数据分析示例

### 使用pandas分析CSV数据

```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取视频数据
videos_df = pd.read_csv('data/daily/2025-W31/23947287_20250803_videos.csv')

# 分析视频表现
print("视频播放量统计:")
print(videos_df['view'].describe())

# 分析标签分布
tags_series = videos_df['tags'].str.split(';').explode().str.strip()
tag_counts = tags_series.value_counts().head(10)
print("\n热门标签TOP10:")
print(tag_counts)

# 读取热评数据
hot_comments_df = pd.read_csv('data/daily/2025-W31/23947287_20250803_hot_comments.csv')

# 分析热评特征
print(f"\n热评总数: {len(hot_comments_df)}")
print(f"平均点赞数: {hot_comments_df['like'].mean():.1f}")
print(f"平均回复数: {hot_comments_df['rcount'].mean():.1f}")
```

### 使用Excel分析

1. 打开生成的CSV文件
2. 使用数据透视表分析视频分类分布
3. 创建图表展示播放量趋势
4. 分析热评关键词频率

### 数据可视化建议

- **播放量趋势**: 时间序列图展示视频表现
- **标签云**: 展示热门标签分布
- **互动分析**: 点赞、评论、收藏的相关性分析
- **热评情感**: 基于热评内容进行情感分析

## 🚨 注意事项

1. **请求频率**: 已内置延时机制，避免频繁请求
2. **Cookie安全**: 不要在公开场所暴露Cookie信息
3. **数据合规**: 仅用于学习研究，请遵守平台规定
4. **资源消耗**: 月任务会消耗更多时间和网络资源
5. **CSV编码**: 使用UTF-8编码，Excel打开时选择正确编码格式
6. **数据备份**: 建议定期备份重要的数据文件

## 📝 更新日志

### v3.0.0 (2025-08-03) - 工作流增强版
- ✅ **CSV数据导出**: 新增CSV格式导出，兼容Excel和数据分析工具
- ✅ **视频标签提取**: 自动提取视频标签和分类信息用于内容分析
- ✅ **热评功能增强**: 月任务也支持热评采集，提供完整数据分析
- ✅ **手动执行模式**: 移除定时任务，改为完全手动执行，提供更好的控制
- ✅ **工作流简化**: 简化GitHub Actions配置，移除复杂的定时调度
- ✅ **数据格式优化**: 统一数据结构，提供详细的字段说明和示例

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