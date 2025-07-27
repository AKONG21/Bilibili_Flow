# 🚀 B站数据采集器 (Bilibili Data Collector)

一个功能完整的B站UP主数据采集工具，支持多账号Cookie管理、智能过期检测、自动故障切换等高级功能。

> ⚠️ **免责声明**: 本项目仅供学习和研究目的使用，请遵守相关平台的使用条款和robots.txt规则，不得用于商业用途或大规模爬取。

## ✨ 主要特性

- 🎯 **智能数据采集**: 支持日任务和月任务，自动分类存储
- 🍪 **多账号管理**: 支持多个Cookie账号轮换使用
- 🔄 **增量更新**: 智能识别新视频和数据更新
- 📊 **数据库存储**: 使用SQLite存储，支持数字时间戳
- 🗂️ **分类存储**: 日任务按周分文件夹，月任务独立存储
- 🛡️ **故障切换**: Cookie失效时自动切换到其他可用账号

## 📁 项目结构

```
Bilibili_Flow/
├── main.py                     # 🎯 主执行入口（推荐使用）
├── run_daily_task.py          # 📅 日任务执行入口（兼容性保留）
├── daily_task_processor.py    # 🔧 核心任务处理器
├── daily_task_config.yaml     # ⚙️ 主配置文件
├── requirements.txt           # 📦 依赖包列表
│
├── bilibili_core/            # 🏗️ 核心功能模块
│   ├── cookie_management/    # 🍪 Cookie管理模块
│   │   ├── auto_cookie_manager.py      # 自动Cookie管理
│   │   ├── enhanced_cookie_manager.py  # 增强Cookie管理
│   │   └── smart_cookie_pool.py        # 智能Cookie池
│   ├── client/              # 🌐 API客户端
│   ├── storage/             # 💾 数据存储
│   └── utils/               # 🛠️ 工具函数
│
├── tools/                   # 🔧 管理工具
│   ├── cookie_manager_tool.py    # Cookie管理工具
│   └── cookie_pool_monitor.py    # Cookie池监控工具
│
├── data/                    # 📊 数据输出目录
├── cookies/                 # 🍪 Cookie备份目录
└── venv/                    # 🐍 Python虚拟环境
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 2. 基本使用

#### 方式一：使用新的主入口（推荐）
```bash
# 运行日任务（默认）
python main.py

# 运行月任务
python main.py --type monthly

# 使用自定义配置文件
python main.py --config custom_config.yaml

# 查看帮助
python main.py --help
```

#### 方式二：使用原有入口（兼容性）
```bash
# 运行日任务
python run_daily_task.py
```

### 3. Cookie管理工具
```bash
# Cookie管理工具
python tools/cookie_manager_tool.py

# Cookie池监控
python tools/cookie_pool_monitor.py
```

## 🔧 配置说明

### 主配置文件：`daily_task_config.yaml`

```yaml
# 🎯 UP主配置
daily_task:
  up_id: "1140672573"  # UP主ID
  time_range:
    days: 28           # 采集天数

# 🍪 Cookie管理
login:
  cookies:
    cookie_pool:
      enabled: true    # 启用Cookie池
      selection_mode: "random"  # 随机选择
      cookies: []      # Cookie列表（扫码后自动添加）
```

## 🤖 GitHub Actions部署

### 环境变量配置
- `TASK_TYPE`: 任务类型（daily/monthly/custom）
- `CONFIG_FILE`: 配置文件路径

### Workflow示例
```yaml
name: Bilibili Data Collection
on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Run collection
        env:
          TASK_TYPE: daily
        run: python main.py
```

## 🍪 Cookie管理功能

### 自动Cookie管理
- ✅ 扫码后自动保存到配置文件
- ✅ 支持多账号轮换使用
- ✅ 智能过期检测和自动切换
- ✅ 失效Cookie自动禁用

### Cookie池特性
- 🎲 **随机选择**：避免检测
- 🔄 **轮询选择**：均匀使用
- 📊 **优先级选择**：按重要性使用
- 🧠 **智能故障切换**：自动处理失效

### 状态监控
```
🍪 Cookie状态报告
📊 总Cookie数量: 3
✅ 可用Cookie数量: 3
❌ 过期Cookie数量: 0
🚫 禁用Cookie数量: 0
✨ Cookie数量充足，系统运行良好
```

## 📊 数据输出

### 输出格式
- JSON格式数据文件
- 包含UP主信息、视频数据、热门评论
- 自动时间戳命名：`daily_task_20250726_053000_1140672573.json`

### 数据字段
- UP主信息：昵称、粉丝数、视频总数
- 视频信息：标题、描述、播放量、点赞数等
- 热门评论：评论内容、用户ID、点赞数等

## 🛠️ 开发说明

### 核心模块
- `DailyTaskProcessor`: 主要任务处理器
- `AutoCookieManager`: 自动Cookie管理
- `SmartCookiePool`: 智能Cookie池
- `EnhancedCookieManager`: 增强Cookie管理

### 扩展开发
1. 在`bilibili_core`中添加新功能模块
2. 在`main.py`中添加新的任务类型
3. 更新配置文件支持新功能

## 📝 更新日志

### v2.0.0 (2025-07-26)
- ✅ 重构项目结构，模块化设计
- ✅ 新增统一主入口`main.py`
- ✅ 完善Cookie自动管理系统
- ✅ 支持多任务类型（日任务/月任务）
- ✅ 优化GitHub Actions支持
- ✅ 清理无用脚本，保留核心功能

### v1.x.x
- 基础数据采集功能
- Cookie管理功能
- 配置文件支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交Issue和Pull Request！请确保：

1. 遵守代码规范
2. 添加适当的测试
3. 更新相关文档
4. 遵守免责声明中的使用原则

## ⚠️ 注意事项

- 请合理控制请求频率，避免给目标平台带来负担
- 仅用于学习和研究目的，不得用于商业用途
- 使用时请遵守相关法律法规和平台规则
- 本项目不承担任何使用风险和法律责任

## 📞 联系方式

如有问题或建议，请通过GitHub Issues联系。
