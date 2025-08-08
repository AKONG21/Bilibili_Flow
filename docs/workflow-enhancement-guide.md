# 工作流增强功能指南

本文档详细介绍了Bilibili Flow v3.0.0版本中新增的工作流增强功能。

## 🆕 新功能概览

### 1. CSV数据导出
- **功能**: 将采集的数据导出为CSV格式，便于数据分析
- **兼容性**: 支持Excel、pandas、R等数据分析工具
- **编码**: 使用UTF-8-sig编码，确保中文字符正确显示

### 2. 视频标签提取
- **功能**: 自动提取视频的标签和分类信息
- **用途**: 用于内容分析、标签趋势分析、分类统计
- **数据结构**: 包含标签ID、标签名称、分类信息

### 3. 热评功能增强
- **功能**: 月任务也支持热评采集
- **改进**: 提供更完整的用户反馈数据
- **分析价值**: 了解用户对不同类型内容的反应

### 4. 手动执行模式
- **改进**: 移除自动定时任务，改为完全手动执行
- **优势**: 更好的执行控制，避免不必要的资源消耗
- **灵活性**: 可根据需要随时执行数据采集

## 📊 CSV数据格式详解

### 视频数据CSV字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `aid` | 整数 | 视频AV号 | `123456789` |
| `title` | 文本 | 视频标题 | `【技术分享】Python编程技巧` |
| `video_url` | URL | 视频链接 | `https://www.bilibili.com/video/BV1xx411c7mD` |
| `cover_url` | URL | 封面图片链接 | `https://i0.hdslb.com/bfs/archive/xxx.jpg` |
| `publish_time` | 日期时间 | 发布时间 | `2025-01-15 14:30:00` |
| `duration` | 整数 | 视频时长(秒) | `1200` |
| `category` | 文本 | 视频分类 | `科技` |
| `description` | 文本 | 视频简介 | `本期视频介绍Python编程技巧...` |
| `tags` | 文本 | 视频标签(分号分隔) | `编程; 技术; 教程; Python` |
| `view` | 整数 | 播放量 | `50000` |
| `like` | 整数 | 点赞数 | `1500` |
| `reply` | 整数 | 评论数 | `200` |
| `favorite` | 整数 | 收藏数 | `800` |
| `share` | 整数 | 分享数 | `100` |
| `coin` | 整数 | 投币数 | `300` |
| `danmaku` | 整数 | 弹幕数 | `500` |
| `hot_comments` | 文本 | 热评摘要(分号分隔) | `太棒了; 学到了; 感谢分享` |

### 热评数据结构

热评数据包含以下关键信息：

```json
{
  "comment_id": "987654321",
  "message": "这个教程太有用了，感谢UP主的分享！",
  "mid": 456789123,
  "uname": "技术爱好者",
  "ctime": 1705123456,
  "like": 150,
  "rcount": 12,
  "replies": [
    {
      "message": "同感，学到很多！",
      "uname": "学习者",
      "like": 20
    }
  ]
}
```

### 视频标签数据结构

标签提取功能提供详细的标签信息：

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
    },
    {
      "tag_id": 12347,
      "tag_name": "教程",
      "category": "学习"
    }
  ]
}
```

## 🔧 配置说明

### CSV导出配置

在 `daily_task_config.yaml` 中配置CSV导出选项：

```yaml
storage:
  export_format: csv  # 选项: json, csv, both
  csv_options:
    encoding: utf-8-sig    # Excel兼容编码
    delimiter: ','         # CSV分隔符
    include_headers: true  # 包含表头
    escape_special_chars: true  # 转义特殊字符
```

### 视频标签提取配置

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
  
  monthly_task:
    hot_comments_json:
      enabled: true    # 月任务也启用热评采集
      max_count: 10
      fields:
        - message
        - mid
        - ctime
        - like
        - rcount
```

## 🚀 手动执行工作流

### GitHub Actions配置变更

**移除的功能**:
- 自动定时任务(cron调度)
- 复杂的时间判断逻辑

**保留的功能**:
- 手动触发(workflow_dispatch)
- 完整的数据采集流程
- 飞书通知功能
- 数据提交和推送

### 手动执行步骤

1. **进入Actions页面**
   - 访问GitHub仓库
   - 点击"Actions"标签

2. **选择工作流**
   - `Daily Data Collection` - 日任务
   - `Monthly Historical Data Collection` - 月任务

3. **启动执行**
   - 点击"Run workflow"按钮
   - 选择分支(通常是`sync-current-files`)
   - 填写任务描述(可选)
   - 点击"Run workflow"确认

4. **监控执行**
   - 查看执行日志
   - 等待完成通知

### 执行结果

- **数据文件**: 自动提交到指定分支
- **CSV文件**: 生成多个CSV文件用于分析
- **通知**: 发送执行结果到飞书(如已配置)

## 📈 数据分析示例

### 使用pandas分析

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 读取视频数据
videos_df = pd.read_csv('data/daily/2025-W31/23947287_20250803_videos.csv')

# 1. 基础统计分析
print("视频数据概览:")
print(videos_df.describe())

# 2. 标签分析
# 展开标签数据
tags_series = videos_df['tags'].str.split(';').explode().str.strip()
tag_counts = tags_series.value_counts().head(20)

# 绘制标签分布图
plt.figure(figsize=(12, 6))
tag_counts.plot(kind='bar')
plt.title('热门标签分布')
plt.xlabel('标签')
plt.ylabel('频次')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 3. 视频表现分析
# 播放量与点赞数的关系
plt.figure(figsize=(10, 6))
plt.scatter(videos_df['view'], videos_df['like'], alpha=0.6)
plt.xlabel('播放量')
plt.ylabel('点赞数')
plt.title('播放量与点赞数关系')
plt.show()

# 4. 热评分析
hot_comments_df = pd.read_csv('data/daily/2025-W31/23947287_20250803_hot_comments.csv')

print(f"\n热评统计:")
print(f"总热评数: {len(hot_comments_df)}")
print(f"平均点赞数: {hot_comments_df['like'].mean():.1f}")
print(f"平均回复数: {hot_comments_df['rcount'].mean():.1f}")

# 热评点赞数分布
plt.figure(figsize=(10, 6))
plt.hist(hot_comments_df['like'], bins=30, alpha=0.7)
plt.xlabel('点赞数')
plt.ylabel('频次')
plt.title('热评点赞数分布')
plt.show()
```

### 使用Excel分析

1. **打开CSV文件**
   - 选择UTF-8编码
   - 确认分隔符为逗号

2. **创建数据透视表**
   - 分析视频分类分布
   - 统计标签使用频率
   - 计算平均互动率

3. **制作图表**
   - 播放量趋势图
   - 标签词云
   - 互动数据对比

## 🔍 故障排除

### 常见问题

1. **CSV文件乱码**
   - 确保使用UTF-8编码打开
   - Excel中选择"数据" → "从文本/CSV"

2. **标签数据为空**
   - 检查配置中tags.enabled是否为true
   - 确认视频确实有标签信息

3. **热评数据缺失**
   - 检查hot_comments_json.enabled配置
   - 确认视频有足够的热评数据

4. **手动执行失败**
   - 检查GitHub Secrets配置
   - 查看Actions执行日志
   - 确认Cookie有效性

### 性能优化建议

1. **合理设置采集参数**
   - 根据需要调整max_count
   - 避免过度采集标签数据

2. **定期清理数据**
   - 删除过期的CSV文件
   - 压缩历史数据

3. **监控资源使用**
   - 关注GitHub Actions使用时间
   - 合理安排执行频率

## 📞 技术支持

如果在使用过程中遇到问题，请：

1. 查看项目README文档
2. 检查GitHub Issues
3. 提交新的Issue描述问题
4. 包含详细的错误日志和配置信息

---

*本文档随项目更新而更新，请关注最新版本。*