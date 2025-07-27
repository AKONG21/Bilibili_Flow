# 存储分类功能说明

## 概述

本次更新实现了JSON文件的自动分类存储功能，将日任务和月任务的JSON文件保存到不同的文件夹中，并为日任务添加了以周命名的子文件夹。

## 存储结构

### 新的存储结构
```
data/
├── daily/                    # 日任务存储目录
│   ├── 2025-W30/            # 按周分组的子文件夹
│   │   ├── 2025-07-27_15-32_1140672573.json
│   │   └── ...
│   ├── 2025-W31/            # 下一周的文件夹
│   └── ...
├── monthly/                  # 月任务存储目录
│   ├── 2025-07-27_1140672573.json
│   └── ...
└── bilibili_tracking.db     # 数据库文件（位置不变）
```

### 旧的存储结构（已清理）
```
data/
├── daily_task_20250727_1533_1140672573.json  # ❌ 已移除
├── daily_task_20250727_1543_1140672573.json  # ❌ 已移除
├── monthly_task_20250727_1140672573.json     # ❌ 已移除
└── ...
```

## 主要更改

### 1. 代码更改

#### `bilibili_core/processors/daily_task_processor.py`
- 修改了存储初始化逻辑，根据任务类型设置不同的存储目录
- 日任务使用 `data/daily` 目录
- 月任务使用 `data/monthly` 目录
- 传递 `task_type` 参数给 `SimpleStorage`

#### `bilibili_core/storage/simple_storage.py`
- 添加了 `task_type` 参数支持
- 修改了 `finalize_task` 方法，实现分类存储逻辑：
  - 日任务：保存到 `data/daily/{年}-W{周数}/` 目录
  - 月任务：保存到 `data/monthly/` 目录

### 2. 配置文件更改

#### 已清理的配置项
以下配置文件中的存储设置已被注释或标记为废弃：
- `daily_task_config.yaml`
- `bilibili_core/config/config_manager.py`

#### 已移除的配置文件
以下重复的配置文件已移除或移动到模板目录：
- `config.yaml` - 已删除（重复且未被使用）
- `daily_task_config_clean.yaml` - 已移动到 `docs/config_templates/`
- `daily_task_config_multi_cookie.yaml` - 已移动到 `docs/config_templates/`

#### 废弃的配置项
```yaml
storage:
  # data_dir: "data"  # 已废弃，存储路径由任务类型自动决定
  # filename_format: "..."  # 已废弃，由任务配置决定
```

## 功能特点

### 1. 自动分类存储
- **日任务**：自动保存到 `data/daily/{年}-W{周数}/` 目录
- **月任务**：自动保存到 `data/monthly/` 目录
- 无需手动配置存储路径

### 2. 周文件夹命名
- 日任务按照 ISO 8601 标准的周数命名：`{年}-W{周数}`
- 例如：`2025-W30` 表示2025年第30周
- 自动创建目录，无需手动管理

### 3. 向后兼容
- 现有的数据库存储功能保持不变
- 现有的API和接口保持兼容
- 只是改变了JSON文件的存储位置

### 4. 文件命名保持一致
- 日任务：`daily_task_{timestamp}_{up_id}.json`
- 月任务：`monthly_task_{timestamp}_{up_id}.json`
- 时间戳格式保持不变

## 测试验证

已通过测试验证以下功能：
- ✅ 日任务文件正确保存到周文件夹
- ✅ 月任务文件正确保存到月任务文件夹
- ✅ 目录自动创建
- ✅ 文件命名格式正确
- ✅ 不再在根目录生成文件

## 使用说明

### 运行任务
正常运行日任务或月任务，文件会自动保存到正确的位置：

```bash
# 运行日任务
python run_daily_task.py

# 运行月任务
python run_monthly_task.py
```

### 查找文件
- **日任务文件**：在 `data/daily/{年}-W{周数}/` 目录中查找
- **月任务文件**：在 `data/monthly/` 目录中查找

### 清理旧文件
如果需要清理根目录下的旧文件：
```bash
# 手动删除根目录下的旧任务文件
rm data/daily_task_*.json
rm data/monthly_task_*.json
```

## 注意事项

1. **配置文件**：存储相关的配置项已被废弃，无需再配置 `data_dir` 和 `filename_format`
2. **目录权限**：确保程序有权限在 `data/` 目录下创建子目录
3. **磁盘空间**：分类存储不会增加额外的磁盘使用，只是改变了文件组织方式
4. **备份策略**：如果有自动备份脚本，需要更新路径配置

## 故障排除

### 问题：文件仍然保存在根目录
**解决方案**：检查是否使用了最新的代码，确保 `SimpleStorage` 接收到了正确的 `task_type` 参数

### 问题：周文件夹命名错误
**解决方案**：检查系统时间设置，周数计算基于 ISO 8601 标准

### 问题：权限错误
**解决方案**：确保程序有权限在 `data/` 目录下创建子目录和文件
