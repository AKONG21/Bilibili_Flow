# 项目结构说明

## 📁 项目目录结构

```
Bilibili_Flow/
├── 📄 主脚本 (根目录)
│   ├── main.py                          # 主入口脚本
│   ├── quick_start.py                   # 快速启动脚本
│   ├── run_daily_task.py               # 日任务主脚本
│   ├── run_monthly_task_enhanced.py    # 月任务主脚本
│   └── init_database.py                # 数据库初始化脚本
│
├── 📁 bilibili_core/                   # 核心模块目录
│   ├── 📁 processors/                  # 任务处理器
│   │   └── daily_task_processor.py     # 日任务处理器
│   │
│   ├── 📁 scripts/                     # 辅助脚本
│   │   ├── debug_monthly_task.py       # 月任务调试脚本
│   │   └── test_network.py             # 网络测试脚本
│   │
│   ├── 📁 storage/                     # 存储模块
│   │   ├── enhanced_storage.py         # 增强存储架构
│   │   ├── parent_child_storage.py     # 父子关系存储
│   │   ├── database_manager.py         # 数据库管理器
│   │   ├── database_schema.py          # 数据库架构
│   │   ├── bilibili_store_impl.py      # 存储实现
│   │   └── bilibili_store_sql.py       # SQL存储
│   │
│   ├── 📁 client/                      # B站客户端
│   │   ├── bilibili_client.py          # B站API客户端
│   │   ├── wbi_signature.py            # WBI签名
│   │   └── exceptions.py               # 异常定义
│   │
│   ├── 📁 cookie_management/           # Cookie管理
│   │   ├── enhanced_cookie_manager.py  # 增强Cookie管理器
│   │   ├── smart_cookie_pool.py        # 智能Cookie池
│   │   └── auto_cookie_manager.py      # 自动Cookie管理
│   │
│   ├── 📁 config/                      # 配置管理
│   │   ├── config_manager.py           # 配置管理器
│   │   └── bilibili_config.py          # B站配置
│   │
│   ├── 📁 utils/                       # 工具模块
│   │   ├── logger.py                   # 日志工具
│   │   ├── time_utils.py               # 时间工具
│   │   ├── cookie_utils.py             # Cookie工具
│   │   └── login_helper.py             # 登录助手
│   │
│   └── 📁 tools/                       # 管理工具
│       ├── cookie_manager_tool.py      # Cookie管理工具
│       └── cookie_pool_monitor.py      # Cookie池监控
│
├── 📁 data/                            # 数据目录
│   ├── database/                       # 数据库文件
│   ├── daily/                          # 日任务数据
│   ├── monthly/                        # 月任务数据
│   └── cache/                          # 缓存数据
│
├── 📁 cookies/                         # Cookie存储
│   └── backup_cookies/                 # Cookie备份
│
├── 📁 logs/                            # 日志文件
└── 📁 tests/                           # 测试文件
```

## 🎯 主要改进

### ✅ 已完成的重组：
1. **清理冗余文件** - 删除了重复的说明文档
2. **模块化组织** - 将非主脚本移动到 bilibili_core 目录
3. **路径更新** - 双向更新了所有调用路径
4. **结构优化** - 按功能模块组织代码

### 📋 文件分类：

#### **主脚本（根目录）：**
- 用户直接运行的脚本
- 项目入口点
- 数据库初始化

#### **核心模块（bilibili_core）：**
- **processors/** - 任务处理逻辑
- **storage/** - 数据存储架构
- **client/** - B站API客户端
- **cookie_management/** - Cookie管理
- **config/** - 配置管理
- **utils/** - 通用工具
- **tools/** - 管理工具
- **scripts/** - 辅助脚本

## 🚀 使用方式

### 运行主脚本：
```bash
# 日任务
python run_daily_task.py

# 月任务
python run_monthly_task_enhanced.py

# 快速启动
python quick_start.py

# 数据库初始化
python init_database.py
```

### 使用核心模块：
```python
from bilibili_core.processors.daily_task_processor import DailyTaskProcessor
from bilibili_core.storage.enhanced_storage import EnhancedStorage
```

## 📊 项目特点

- **模块化设计** - 清晰的功能分离
- **路径一致性** - 统一的导入路径
- **易于维护** - 结构化的代码组织
- **功能完整** - 保留所有核心功能
