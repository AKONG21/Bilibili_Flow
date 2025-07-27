# 配置文件说明

## 配置文件结构

项目现在使用单一的主配置文件，简化了配置管理：

```
Bilibili_Flow/
├── daily_task_config.yaml     # 🎯 主配置文件（唯一配置文件）
└── docs/
    └── config_templates/       # 📄 配置模板目录
        ├── daily_task_config_clean.yaml      # 清洁版配置模板
        └── daily_task_config_multi_cookie.yaml # 多Cookie配置模板
```

## 主配置文件：`daily_task_config.yaml`

这是项目的唯一配置文件，包含所有必要的配置项：

### 1. 任务配置
```yaml
daily_task:
  up_id: "1140672573"          # UP主ID（必填）
  time_range:
    days: 28                   # 采集天数（从今天往前推算）
```

### 2. 字段控制
```yaml
  up_fields:                   # UP主信息字段
    enabled: true
    mid: true                  # UP主ID
    name: true                 # UP主昵称
    fans: true                 # 粉丝数
    
  video_fields:                # 视频信息字段
    enabled: true
    title: true                # 视频标题
    stats_fields:
      enabled: true
      view: true               # 播放量
      like: true               # 点赞数
```

### 3. 存储配置
```yaml
storage:
  # 存储路径已自动分类：
  # - 日任务：data/daily/{年}-W{周数}/
  # - 月任务：data/monthly/
  compress: false
```

### 4. Cookie管理
```yaml
login:
  cookies:
    raw_cookie: ""             # 单个Cookie（向后兼容）
    cookie_pool:               # Cookie池（推荐）
      enabled: true
      selection_mode: random
      cookies: []              # 扫码登录后自动添加
```

## 配置模板

### 清洁版模板：`docs/config_templates/daily_task_config_clean.yaml`
- 适合新用户
- 包含详细的中文注释
- 所有Cookie配置为空，需要扫码登录

### 多Cookie模板：`docs/config_templates/daily_task_config_multi_cookie.yaml`
- 适合高级用户
- 展示多账号Cookie配置示例
- 包含完整的Cookie池配置

## 使用方法

### 1. 首次使用
```bash
# 直接运行，程序会使用默认配置文件
python main.py

# 或使用原有入口
python run_daily_task.py
```

### 2. 使用模板
```bash
# 复制清洁版模板作为新配置
cp docs/config_templates/daily_task_config_clean.yaml my_config.yaml

# 使用自定义配置文件
python main.py --config my_config.yaml
```

### 3. Cookie管理
```bash
# 使用Cookie管理工具
python tools/cookie_manager_tool.py

# 监控Cookie池状态
python tools/cookie_pool_monitor.py
```

## 配置优先级

1. **命令行参数**（最高优先级）
2. **环境变量**
3. **配置文件**
4. **默认值**（最低优先级）

## 常见问题

### Q: 为什么只有一个配置文件？
A: 为了简化配置管理，避免用户困惑。所有功能都集中在 `daily_task_config.yaml` 中。

### Q: 如何使用不同的配置？
A: 可以复制模板文件创建新的配置文件，然后使用 `--config` 参数指定。

### Q: Cookie配置在哪里？
A: Cookie配置在主配置文件的 `login` 部分，支持单个Cookie和Cookie池两种方式。

### Q: 存储路径如何配置？
A: 存储路径已自动分类，无需手动配置：
- 日任务：`data/daily/{年}-W{周数}/`
- 月任务：`data/monthly/`

## 迁移指南

如果您之前使用了多个配置文件，现在只需要：

1. **保留** `daily_task_config.yaml` 作为主配置文件
2. **删除** 其他重复的配置文件
3. **参考** `docs/config_templates/` 中的模板进行配置

所有功能都已整合到单一配置文件中，使用更加简单！
