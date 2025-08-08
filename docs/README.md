# 配置模板和功能说明

这个目录包含了不同使用场景的配置模板文件和功能说明文档。

## 文件说明

### daily_task_config_clean.yaml
- **用途**: 最简配置模板
- **特点**: 只包含必要的配置项，适合新用户快速上手
- **适用场景**: 单账号使用，默认功能配置

### daily_task_config_multi_cookie.yaml  
- **用途**: 多Cookie配置模板
- **特点**: 包含Cookie池配置，支持多账号轮换
- **适用场景**: 高频采集，需要Cookie故障切换

### daily_task_config.yaml.backup
- **用途**: 主配置文件的备份
- **特点**: 保留了完整的配置历史
- **适用场景**: 配置回滚和参考

## 新功能配置说明

### CSV导出功能

在 `daily_task_config.yaml` 中配置CSV导出：

```yaml
storage:
  export_format: csv  # 可选: json, csv, both
  csv_options:
    encoding: utf-8-sig  # Excel兼容编码
    delimiter: ','
    include_headers: true
    escape_special_chars: true
```

### 视频标签提取

启用视频标签提取功能：

```yaml
task_config:
  daily_task:
    video_fields:
      tags:
        enabled: true           # 启用标签提取
        include_tag_id: true    # 包含标签ID
        include_tag_name: true  # 包含标签名称
        include_category: true  # 包含分类信息
        max_tags: 20           # 最大标签数量
```

### 热评采集配置

配置热评采集参数：

```yaml
task_config:
  daily_task:
    hot_comments_json:
      enabled: true
      max_count: 10    # 每个视频最多采集10条热评
      fields:          # 采集的字段
        - message      # 评论内容
        - mid          # 用户ID
        - ctime        # 评论时间
        - like         # 点赞数
        - rcount       # 回复数
```

## 手动执行工作流

### GitHub Actions配置

工作流已简化为手动执行模式：

- **移除定时任务**: 不再自动执行，完全手动控制
- **手动触发**: 通过GitHub Actions页面手动启动
- **任务描述**: 支持添加执行描述便于追踪

### 执行步骤

1. 进入GitHub仓库的Actions页面
2. 选择对应的工作流
3. 点击"Run workflow"
4. 填写任务描述(可选)
5. 确认执行

## 使用方法

1. 复制合适的模板到根目录
2. 重命名为 `daily_task_config.yaml`
3. 根据需要启用新功能(CSV导出、标签提取、热评采集)
4. 配置GitHub Actions Secrets
5. 手动执行工作流

## 配置优先级

1. 根目录的 `daily_task_config.yaml` (主配置)
2. 环境变量 (如 UP_ID, BILIBILI_COOKIES)
3. 模板文件中的默认值

## 数据输出格式

### CSV文件结构

- `{up_id}_{timestamp}_videos.csv` - 视频数据
- `{up_id}_{timestamp}_comments.csv` - 普通评论
- `{up_id}_{timestamp}_hot_comments.csv` - 热门评论
- `{up_id}_{timestamp}_up_info.csv` - UP主信息

### 数据分析建议

- 使用pandas读取CSV进行数据分析
- Excel打开时选择UTF-8编码
- 利用标签数据进行内容分类分析
- 分析热评数据了解用户反馈