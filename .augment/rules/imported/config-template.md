---
type: "manual"
---

# 简化配置文件模板

## 概述

简单的配置文件，主要用于手动执行时的参数设置。平时自动化执行只跟踪一个UP主，重点是视频范围选择的灵活性。

## 配置文件结构

### 主配置文件 (`config/tracking_config.yaml`)

```yaml
# B站视频数据跟踪系统 - 简化配置文件
# 使用说明：
# 1. 平时自动执行只跟踪default_target中的UP主
# 2. 手动执行时可以通过GitHub Actions界面选择不同配置
# 3. 敏感信息(API密钥)通过GitHub Secrets管理
# 4. 重点是视频时间范围的灵活配置

# 配置规则说明：
# - up_id留空 = 跳过整个任务
# - 其他字段留空 (null/~) = 跳过该功能模块
# - 填0 = 不限制数量
# - 填具体数值 = 按数值限制

# 默认跟踪目标 (自动化任务使用)
default_target:
  up_id: 20813884                    # UP主ID [留空=跳过整个任务]
  nickname: "老师好我叫何同学"        # UP主昵称 (仅用于日志显示)
  
  # 视频范围配置 (留空=跳过视频采集，只采集UP主信息)
  video_scope:
    daily_range_days: 28              # 日任务视频时间范围 (天) [留空=跳过所有日任务(8点+20点), 有值=8点和20点都执行]
    monthly_range_days: 180           # 月任务视频时间范围 (天) [留空=跳过月任务视频采集]
    min_view_count: 1000              # 最小播放量过滤 [0=不限制, 留空=跳过视频采集]
    max_videos_per_task: 100          # 单次任务最大视频数量 [0=不限制, 留空=跳过视频采集]
    include_live_videos: false        # 是否包含直播回放
    
  # 评论采集配置 (留空=跳过评论采集)
  comments:
    max_comments_per_video: 10        # 每个视频最大评论数 [0=不限制, 留空=跳过评论采集]
    include_hot_comments_only: true   # 只采集热门评论 [留空=跳过评论采集]
  
  # 任务类型特定的数据字段配置
  task_specific_fields:
    # 日任务字段配置 (T1/T2 - 8点和20点执行)
    daily_task:
      # UP主信息 - 日任务只采集核心字段
      up_fields:
        - "mid"                       # A列 - UP主ID (必需)
        - "name"                      # B列 - UP主昵称 (必需)
        - "fans"                      # C列 - 粉丝数 ⭐ 重要
        - "video"                     # D列 - 视频总数 ⭐ 重要
      
      # 视频信息 - 日任务重点关注互动数据
      video_fields:
        - "aid"                       # E列 - 视频AV号 ⭐ 必需
        - "bvid"                      # F列 - 视频BV号 ⭐ 必需
        - "title"                     # G列 - 视频标题 ⭐ 重要
        - "pubdate"                   # J列 - 发布时间 ⭐ 重要
        - "view"                      # K列 - 播放量 ⭐ 重要
        - "reply"                     # M列 - 评论数 ⭐ 重要
        - "favorite"                  # N列 - 收藏数 ⭐ 重要
        - "coin"                      # O列 - 投币数 ⭐ 重要
        - "like"                      # P列 - 点赞数 ⭐ 重要
        - "share"                     # Q列 - 分享数 ⭐ 重要
      
      # 特殊字段 - 日任务包含热门评论
      special_fields:
        - "hot_comments_json"         # R列 - 热门评论JSON ⭐ 重要
        - "update_time"               # S列 - 更新时间
    
    # 月任务字段配置 (每四周周五执行)
    monthly_task:
      # UP主信息 - 月任务采集完整信息
      up_fields:
        - "mid"                       # A列 - UP主ID (必需)
        - "name"                      # B列 - UP主昵称 (必需)
        - "fans"                      # C列 - 粉丝数 ⭐ 重要
        - "video"                     # D列 - 视频总数 ⭐ 重要
        - "friend"                    # 关注数 (月任务额外采集)
        - "sign"                      # 个人签名 (月任务额外采集)
        - "level"                     # 等级 (月任务额外采集)
        - "official_verify"           # 认证信息 (月任务额外采集)
      
      # 视频信息 - 月任务采集完整视频数据
      video_fields:
        - "aid"                       # E列 - 视频AV号 ⭐ 必需
        - "bvid"                      # F列 - 视频BV号 ⭐ 必需
        - "title"                     # G列 - 视频标题 ⭐ 重要
        - "desc"                      # H列 - 视频描述 (月任务额外采集)
        - "duration"                  # I列 - 视频时长 (月任务额外采集)
        - "pubdate"                   # J列 - 发布时间 ⭐ 重要
        - "view"                      # K列 - 播放量 ⭐ 重要
        - "danmaku"                   # L列 - 弹幕数 (月任务额外采集)
        - "reply"                     # M列 - 评论数 ⭐ 重要
        - "favorite"                  # N列 - 收藏数 ⭐ 重要
        - "coin"                      # O列 - 投币数 ⭐ 重要
        - "like"                      # P列 - 点赞数 ⭐ 重要
        - "share"                     # Q列 - 分享数 ⭐ 重要
        - "tname"                     # 分区名称 (月任务额外采集)
      
      # 特殊字段 - 月任务包含热门评论
      special_fields:
        - "hot_comments_json"         # R列 - 热门评论JSON ⭐ 重要
        - "update_time"               # S列 - 更新时间
  
  # 通用数据字段配置 (兼容旧版本)
  data_fields:
    # UP主信息字段 (基于MediaCrawler的get_creator_info)
    up_fields:
      - "mid"                         # UP主ID
      - "name"                        # UP主昵称
      - "fans"                        # 粉丝数 ⭐
      - "friend"                      # 关注数
      - "video"                       # 视频总数 ⭐
      - "sign"                        # 个人签名
      - "level"                       # 等级
      - "official_verify"             # 认证信息
      # 留空某个字段 = 不采集该字段
    
    # 视频信息字段 (基于MediaCrawler的get_video_info)
    video_fields:
      - "aid"                         # 视频AV号 ⭐
      - "bvid"                        # 视频BV号 ⭐
      - "title"                       # 视频标题 ⭐
      - "desc"                        # 视频描述
      - "pubdate"                     # 发布时间 ⭐
      - "duration"                    # 视频时长
      - "view"                        # 播放量 ⭐
      - "danmaku"                     # 弹幕数
      - "reply"                       # 评论数 ⭐
      - "favorite"                    # 收藏数 ⭐
      - "coin"                        # 投币数 ⭐
      - "share"                       # 分享数 ⭐
      - "like"                        # 点赞数 ⭐
      - "tname"                       # 分区名称
      # 留空某个字段 = 不采集该字段
    
    # 特殊字段配置
    special_fields:
      - "hot_comments_json"           # 热门评论JSON ⭐
      - "update_time"                 # 更新时间

# 手动执行可选配置 (通过GitHub Actions选择)
manual_targets:
  # 配置1：只采集UP主信息 (跳过视频和评论)
  up_only:
    up_id: 20813884
    nickname: "何同学-UP主信息"
    video_scope:
      daily_range_days: ~              # 留空 = 跳过日任务视频采集
      monthly_range_days: ~            # 留空 = 跳过月任务视频采集
      min_view_count: ~                # 留空 = 跳过视频采集
      max_videos_per_task: ~           # 留空 = 跳过视频采集
      include_live_videos: false
    comments:
      max_comments_per_video: ~        # 留空 = 跳过评论采集
      include_hot_comments_only: ~     # 留空 = 跳过评论采集
    data_fields:
      up_fields:                       # 只采集UP主基础信息
        - "mid"
        - "name" 
        - "fans"                       # 粉丝数
        - "video"                      # 视频总数
        - "sign"                       # 个人签名
      video_fields: ~                  # 留空 = 不采集视频字段
      comment_fields: ~                # 留空 = 不采集评论字段
  
  # 配置2：采集视频但跳过评论
  video_no_comments:
    up_id: 20813884
    nickname: "何同学-视频无评论"
    video_scope:
      daily_range_days: 28             # 采集28天视频
      monthly_range_days: 180          # 采集180天视频
      min_view_count: 0                # 0 = 不限制播放量
      max_videos_per_task: 0           # 0 = 不限制视频数量
      include_live_videos: false
    comments:
      max_comments_per_video: ~        # 留空 = 跳过评论采集
      include_hot_comments_only: ~     # 留空 = 跳过评论采集
  
  # 配置3：完整数据采集 (视频+评论)
  full:
    up_id: 20813884
    nickname: "何同学-完整"
    video_scope:
      daily_range_days: 90             # 采集90天视频
      monthly_range_days: 365          # 采集365天视频
      min_view_count: 0                # 0 = 不限制播放量
      max_videos_per_task: 0           # 0 = 不限制视频数量
      include_live_videos: true
    comments:
      max_comments_per_video: 0        # 0 = 不限制评论数量
      include_hot_comments_only: false # 采集所有评论
  
  # 配置4：测试用 (少量数据)
  test:
    up_id: 20813884
    nickname: "何同学-测试"
    video_scope:
      daily_range_days: 7              # 只采集7天视频
      monthly_range_days: ~            # 留空 = 跳过月任务
      min_view_count: 1000             # 最少1000播放量
      max_videos_per_task: 5           # 最多5个视频
      include_live_videos: false
    comments:
      max_comments_per_video: 10       # 每个视频最多10条评论
      include_hot_comments_only: true

# 多维表格API配置 (代号，真实值在GitHub Secrets)
api_config:
  main_table:
    api_key_secret: "MULTITABLE_API_KEY"     # GitHub Secret名称
    base_url_secret: "MULTITABLE_BASE_URL"   # GitHub Secret名称
    
    # 父子记录表格配置
    video_master_table_id: "video_master"   # 视频基础信息表ID (父记录)
    video_stats_table_id: "video_stats"     # 视频统计数据表ID (子记录)
    up_masters_table_id: "up_masters"       # UP主信息表ID (独立表)
    
    # 批量操作配置
    batch_size: 100                         # 批量上传大小
    max_retries: 3                          # 最大重试次数
    rate_limit_per_second: 10               # 每秒API调用限制
    
    # 父子记录关联配置
    enable_parent_child_linking: true       # 启用父子记录关联
    auto_create_parent_records: true        # 自动创建父记录
    
  # 封面URL获取配置
  cover_fetching:
    enabled: true                           # 启用封面URL获取
    cache_ttl_hours: 24                     # 封面URL缓存时间 (小时)
    fetch_timeout_seconds: 10               # 获取超时时间 (秒)
    fallback_cover_url: ""                  # 默认封面URL (获取失败时使用)
    
  # 本地缓存配置
  local_cache:
    enabled: true                           # 启用本地缓存
    cache_directory: "cache"                # 缓存目录
    parent_records_file: "bilibili_videos_parent.json"  # 父记录文件名
    child_records_prefix: "bilibili_videos_child"       # 子记录文件前缀
    known_videos_file: "known_videos.json"              # 已知视频文件名
    sync_status_file: "sync_status.json"                # 同步状态文件名
    auto_cleanup_days: 30                   # 自动清理天数
    max_cache_size_mb: 100                  # 最大缓存大小 (MB)
    
  # 同步策略配置
  sync_strategy:
    offline_first: true                     # 离线优先模式
    sync_on_api_available: true             # API可用时自动同步
    batch_sync_size: 100                    # 批量同步大小
    sync_retry_attempts: 3                  # 同步重试次数
    sync_timeout_seconds: 300               # 同步超时时间

# Webhook通知配置 (可选)
webhook:
  url_secret: "WEBHOOK_URL"                 # GitHub Secret名称
  enabled: true                             # 是否启用通知
  events: ["task_completed", "task_failed"] # 通知事件

# MediaCrawler集成配置
mediacrawler_integration:
  use_function_reference: true             # 使用函数引用而非继承
  adapter_mode: true                       # 启用适配器模式
  auto_update_compatibility: true          # 自动更新兼容性
  
  # MediaCrawler函数引用映射
  function_references:
    video_info: "bilibili_crawler.get_video_info"
    creator_info: "bilibili_crawler.get_creator_info"
    video_comments: "bilibili_crawler.get_video_comments"
    save_json: "tools.utils.save_json_file"
    load_json: "tools.utils.load_json_file"
    extract_integers: "tools.utils.extract_valid_integers"
  
  # 数据适配器配置
  data_adapters:
    video_data_adapter: "adapt_video_data"
    creator_data_adapter: "adapt_creator_data"
    comment_data_adapter: "adapt_comment_data"

# 系统配置
system:
  max_concurrency: 5                       # 最大并发数
  request_delay: 1.5                       # 请求间隔(秒)
  retry_attempts: 3                        # 重试次数
  timeout_minutes: 90                      # 任务超时时间
```

## 配置解析逻辑

### 字段值规则

```python
# 配置解析示例代码
def parse_config_value(value, field_name):
    """
    解析配置值的逻辑：
    - None/null/~ = 跳过该功能
    - 0 = 不限制
    - 具体数值 = 按数值限制
    """
    if value is None or value == "~":
        return "SKIP"  # 跳过该功能模块
    elif value == 0:
        return "UNLIMITED"  # 不限制
    else:
        return value  # 使用具体数值

# 使用示例
def should_execute_task(config):
    """判断是否应该执行整个任务"""
    up_id = config.get('up_id')
    if not up_id or up_id == "~":
        return False  # up_id为空，跳过整个任务
    return True

def should_execute_daily_tasks(config, task_type):
    """判断是否应该执行日任务 (8点和20点)"""
    if not should_execute_task(config):
        return False
    
    video_scope = config.get('video_scope', {})
    daily_range = parse_config_value(video_scope.get('daily_range_days'))
    
    if daily_range == "SKIP":
        return False  # daily_range_days为空，跳过所有日任务
    
    # 如果daily_range_days有值，8点和20点的日任务都会执行
    # 区别在于：8点是T1采集，20点是T2采集(用于计算增长率)
    return True

def should_execute_monthly_task(config):
    """判断是否应该执行月任务"""
    if not should_execute_task(config):
        return False
    
    video_scope = config.get('video_scope', {})
    monthly_range = parse_config_value(video_scope.get('monthly_range_days'))
    
    return monthly_range != "SKIP"  # monthly_range_days不为空才执行

def should_collect_comments(config):
    """判断是否应该采集评论"""
    comments = config.get('comments', {})
    max_comments = parse_config_value(comments.get('max_comments_per_video'))
    
    return max_comments != "SKIP"  # 评论字段不为空才采集评论

def get_task_specific_fields(config, task_type):
    """根据任务类型获取特定的字段配置"""
    task_specific = config.get('task_specific_fields', {})
    
    if task_type in ['daily_t1', 'daily_t2']:
        # 日任务使用daily_task配置
        return task_specific.get('daily_task', {})
    elif task_type == 'monthly':
        # 月任务使用monthly_task配置
        return task_specific.get('monthly_task', {})
    else:
        # 默认使用通用配置
        return config.get('data_fields', {})

def get_parent_child_config(config):
    """获取父子记录配置"""
    api_config = config.get('api_config', {}).get('main_table', {})
    return {
        'enabled': api_config.get('enable_parent_child_linking', True),
        'auto_create_parent': api_config.get('auto_create_parent_records', True),
        'video_master_table': api_config.get('video_master_table_id', 'video_master'),
        'video_stats_table': api_config.get('video_stats_table_id', 'video_stats'),
        'up_masters_table': api_config.get('up_masters_table_id', 'up_masters')
    }

def get_cover_fetching_config(config):
    """获取封面获取配置"""
    cover_config = config.get('api_config', {}).get('cover_fetching', {})
    return {
        'enabled': cover_config.get('enabled', True),
        'cache_ttl': cover_config.get('cache_ttl_hours', 24) * 3600,  # 转换为秒
        'timeout': cover_config.get('fetch_timeout_seconds', 10),
        'fallback_url': cover_config.get('fallback_cover_url', '')
    }

def get_local_cache_config(config):
    """获取本地缓存配置"""
    cache_config = config.get('api_config', {}).get('local_cache', {})
    return {
        'enabled': cache_config.get('enabled', True),
        'cache_directory': cache_config.get('cache_directory', 'cache'),
        'parent_records_file': cache_config.get('parent_records_file', 'bilibili_videos_parent.json'),
        'child_records_prefix': cache_config.get('child_records_prefix', 'bilibili_videos_child'),
        'known_videos_file': cache_config.get('known_videos_file', 'known_videos.json'),
        'sync_status_file': cache_config.get('sync_status_file', 'sync_status.json'),
        'auto_cleanup_days': cache_config.get('auto_cleanup_days', 30),
        'max_cache_size_mb': cache_config.get('max_cache_size_mb', 100)
    }

def get_sync_strategy_config(config):
    """获取同步策略配置"""
    sync_config = config.get('api_config', {}).get('sync_strategy', {})
    return {
        'offline_first': sync_config.get('offline_first', True),
        'sync_on_api_available': sync_config.get('sync_on_api_available', True),
        'batch_sync_size': sync_config.get('batch_sync_size', 100),
        'sync_retry_attempts': sync_config.get('sync_retry_attempts', 3),
        'sync_timeout_seconds': sync_config.get('sync_timeout_seconds', 300)
    }

def get_mediacrawler_integration_config(config):
    """获取MediaCrawler集成配置"""
    mc_config = config.get('mediacrawler_integration', {})
    return {
        'use_function_reference': mc_config.get('use_function_reference', True),
        'adapter_mode': mc_config.get('adapter_mode', True),
        'auto_update_compatibility': mc_config.get('auto_update_compatibility', True),
        'function_references': mc_config.get('function_references', {}),
        'data_adapters': mc_config.get('data_adapters', {})
    }

def validate_mediacrawler_compatibility(config):
    """验证MediaCrawler兼容性"""
    mc_config = get_mediacrawler_integration_config(config)
    
    if not mc_config.get('use_function_reference', True):
        return False, "Function reference mode is disabled"
    
    # 检查必需的函数引用
    required_functions = [
        'video_info', 'creator_info', 'video_comments',
        'save_json', 'load_json'
    ]
    
    function_refs = mc_config.get('function_references', {})
    missing_functions = [f for f in required_functions if f not in function_refs]
    
    if missing_functions:
        return False, f"Missing function references: {missing_functions}"
    
    return True, "MediaCrawler compatibility validated"

def should_sync_to_api(config):
    """判断是否应该同步到API"""
    sync_config = get_sync_strategy_config(config)
    
    # 检查是否启用API同步
    if not sync_config.get('sync_on_api_available', True):
        return False
    
    # 检查API配置是否存在
    api_key = os.getenv('MULTITABLE_API_KEY')
    base_url = os.getenv('MULTITABLE_BASE_URL')
    
    return bool(api_key and base_url)
```

### 执行逻辑示例

```yaml
# 示例1：只采集UP主信息
video_scope:
  daily_range_days: ~     # 跳过日任务视频
  monthly_range_days: ~   # 跳过月任务视频
comments:
  max_comments_per_video: ~  # 跳过评论采集
# 结果：只执行UP主粉丝数等基础信息采集

# 示例2：采集所有视频，不限制数量
video_scope:
  daily_range_days: 30    # 采集30天视频
  min_view_count: 0       # 不限制播放量
  max_videos_per_task: 0  # 不限制视频数量
comments:
  max_comments_per_video: ~  # 跳过评论采集
# 结果：采集30天内所有视频，不采集评论

# 示例3：完整采集
video_scope:
  daily_range_days: 90    # 采集90天视频
  min_view_count: 0       # 不限制播放量
  max_videos_per_task: 0  # 不限制视频数量
comments:
  max_comments_per_video: 0  # 不限制评论数量
# 结果：采集90天内所有视频和所有评论
```

### 任务类型特定字段配置示例

```python
# 任务类型特定字段使用示例
def get_fields_for_task(config, task_type):
    """根据任务类型获取字段配置"""
    
    # 获取任务特定字段配置
    task_fields = get_task_specific_fields(config, task_type)
    
    if task_type in ['daily_t1', 'daily_t2']:
        # 日任务：重点关注互动数据，字段较少，执行快速
        print("日任务字段配置:")
        print("- UP主字段: mid, name, fans, video (4个核心字段)")
        print("- 视频字段: aid, bvid, title, pubdate, view, reply, favorite, coin, like, share (10个核心字段)")
        print("- 特殊字段: hot_comments_json, update_time")
        print("- 优势: 字段少，执行快，重点关注互动数据变化")
        
    elif task_type == 'monthly':
        # 月任务：采集完整数据，字段较多，执行较慢但数据完整
        print("月任务字段配置:")
        print("- UP主字段: mid, name, fans, video, friend, sign, level, official_verify (8个完整字段)")
        print("- 视频字段: 所有17个字段，包括desc, duration, danmaku, tname等详细信息")
        print("- 特殊字段: hot_comments_json, update_time")
        print("- 优势: 数据完整，适合深度分析和历史存档")
    
    return task_fields

# 字段配置对比
daily_vs_monthly_comparison = {
    "daily_task": {
        "up_fields_count": 4,           # 只采集核心UP主信息
        "video_fields_count": 10,       # 重点关注互动数据
        "execution_speed": "快速",       # 字段少，执行快
        "data_completeness": "核心",     # 核心数据完整
        "use_case": "日常监控、趋势分析"
    },
    "monthly_task": {
        "up_fields_count": 8,           # 采集完整UP主信息
        "video_fields_count": 17,       # 采集所有视频字段
        "execution_speed": "较慢",       # 字段多，执行较慢
        "data_completeness": "完整",     # 数据完整详细
        "use_case": "深度分析、历史存档"
    }
}
```

### GitHub Secrets配置

```bash
# 必需的Secrets配置
MULTITABLE_API_KEY=your_multitable_api_key_here
MULTITABLE_BASE_URL=https://your-multitable-api.com
WEBHOOK_URL=https://your-webhook-endpoint.com/notify  # 可选
BILIBILI_COOKIES=your_bilibili_cookies_here
```

## 使用方法

### 1. GitHub Secrets配置

在GitHub仓库的Settings > Secrets中配置以下密钥：

```bash
# 多维表格API配置
MULTITABLE_MAIN_API_KEY=your_main_api_key_here
MULTITABLE_MAIN_BASE_URL=https://your-main-table-api.com
MULTITABLE_BACKUP_API_KEY=your_backup_api_key_here
MULTITABLE_BACKUP_BASE_URL=https://your-backup-table-api.com

# 开发环境API (可选)
MULTITABLE_DEV_API_KEY=your_dev_api_key_here
MULTITABLE_DEV_BASE_URL=https://your-dev-table-api.com

# Webhook通知配置
WEBHOOK_URL=https://your-webhook-endpoint.com/notify
WEBHOOK_SECRET=your_webhook_secret_key

# B站登录配置
BILIBILI_COOKIES=your_bilibili_cookies_here

# 可选通知配置
SLACK_WEBHOOK_URL=https://hooks.slack.com/your/webhook/url
EMAIL_SMTP_CONFIG={"host":"smtp.gmail.com","port":587,"user":"your@email.com","pass":"your_password"}
```

### 2. 配置文件加载逻辑

```python
# tracking_system/config/config_loader.py
import yaml
import os
from typing import Dict, Any, Optional

class ConfigLoader:
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.base_config = self.load_base_config()
        self.env_config = self.load_environment_config()
        self.merged_config = self.merge_configs()
    
    def load_base_config(self) -> Dict[str, Any]:
        """加载基础配置文件"""
        with open('config/targets.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_environment_config(self) -> Dict[str, Any]:
        """加载环境特定配置"""
        env_file = f'config/environments/{self.environment}.yaml'
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def merge_configs(self) -> Dict[str, Any]:
        """合并基础配置和环境配置"""
        merged = self.base_config.copy()
        
        # 深度合并环境配置
        def deep_merge(base: dict, override: dict):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(merged, self.env_config)
        return merged
    
    def get_target_group(self, group_name: str) -> Optional[Dict[str, Any]]:
        """获取指定目标组配置"""
        return self.merged_config.get('targets', {}).get(group_name)
    
    def get_task_config(self, task_type: str) -> Optional[Dict[str, Any]]:
        """获取任务类型配置"""
        return self.merged_config.get('task_types', {}).get(task_type)
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """获取API配置，自动从环境变量读取敏感信息"""
        api_config = self.merged_config.get('multitable_apis', {}).get(api_name, {})
        
        # 从环境变量读取敏感信息
        if 'api_key_secret' in api_config:
            api_config['api_key'] = os.getenv(api_config['api_key_secret'])
        if 'base_url_secret' in api_config:
            api_config['base_url'] = os.getenv(api_config['base_url_secret'])
        
        return api_config
```

### 3. GitHub Actions工作流集成

```yaml
# .github/workflows/bilibili-tracking.yml (更新版本)
name: B站视频数据跟踪系统

on:
  schedule:
    - cron: '0 8 * * *'     # T1
    - cron: '0 20 * * *'    # T2
    - cron: '0 8 * * 5'     # 月任务
  
  workflow_dispatch:
    inputs:
      task_type:
        description: '任务类型'
        required: true
        default: 'daily_t1'
        type: choice
        options:
        - daily_t1
        - daily_t2
        - monthly
      target_config:
        description: '目标配置'
        required: true
        default: 'default_target'
        type: choice
        options:
        - default_target      # 默认配置
        - up_only            # 只采集UP主信息
        - video_no_comments  # 采集视频但跳过评论
        - full               # 完整数据采集
        - test               # 测试配置
      custom_up_id:
        description: '自定义UP主ID (可选，覆盖配置文件中的up_id)'
        required: false
        default: ''
      debug_mode:
        description: '调试模式'
        required: false
        default: false
        type: boolean

jobs:
  bilibili-tracking:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    
    steps:
    - name: 检出代码
      uses: actions/checkout@v4
      
    - name: 设置Python环境
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
        
    - name: 安装依赖
      run: |
        pip install -r requirements.txt
        
    - name: 执行跟踪任务
      env:
        # 从Secrets读取所有配置
        MULTITABLE_MAIN_API_KEY: ${{ secrets.MULTITABLE_MAIN_API_KEY }}
        MULTITABLE_MAIN_BASE_URL: ${{ secrets.MULTITABLE_MAIN_BASE_URL }}
        MULTITABLE_BACKUP_API_KEY: ${{ secrets.MULTITABLE_BACKUP_API_KEY }}
        MULTITABLE_BACKUP_BASE_URL: ${{ secrets.MULTITABLE_BACKUP_BASE_URL }}
        MULTITABLE_DEV_API_KEY: ${{ secrets.MULTITABLE_DEV_API_KEY }}
        MULTITABLE_DEV_BASE_URL: ${{ secrets.MULTITABLE_DEV_BASE_URL }}
        WEBHOOK_URL: ${{ secrets.WEBHOOK_URL }}
        WEBHOOK_SECRET: ${{ secrets.WEBHOOK_SECRET }}
        BILIBILI_COOKIES: ${{ secrets.BILIBILI_COOKIES }}
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        EMAIL_SMTP_CONFIG: ${{ secrets.EMAIL_SMTP_CONFIG }}
        
        # 任务参数
        TASK_TYPE: ${{ github.event.inputs.task_type || 'auto' }}
        TARGET_GROUPS: ${{ github.event.inputs.target_groups }}
        ENVIRONMENT: ${{ github.event.inputs.environment || 'production' }}
        CONFIG_OVERRIDE: ${{ github.event.inputs.config_override || '{}' }}
        
      run: |
        python tracking_system/main.py \
          --environment $ENVIRONMENT \
          --task-type $TASK_TYPE \
          --target-groups "$TARGET_GROUPS" \
          --config-override '$CONFIG_OVERRIDE'
```

### 4. 主程序入口示例

```python
# tracking_system/main.py
import argparse
import json
from config.config_loader import ConfigLoader
from core.task_executor import TaskExecutor

def main():
    parser = argparse.ArgumentParser(description='B站视频数据跟踪系统')
    parser.add_argument('--environment', default='production', help='运行环境')
    parser.add_argument('--task-type', default='auto', help='任务类型')
    parser.add_argument('--target-groups', default='', help='目标组列表')
    parser.add_argument('--config-override', default='{}', help='配置覆盖')
    
    args = parser.parse_args()
    
    # 加载配置
    config_loader = ConfigLoader(environment=args.environment)
    
    # 解析配置覆盖
    config_override = json.loads(args.config_override)
    
    # 创建任务执行器
    executor = TaskExecutor(
        config_loader=config_loader,
        config_override=config_override
    )
    
    # 执行任务
    if args.task_type == 'auto':
        # 自动检测任务类型
        task_type = executor.detect_task_type()
    else:
        task_type = args.task_type
    
    # 解析目标组
    target_groups = args.target_groups.split(',') if args.target_groups else None
    
    # 执行任务
    result = executor.execute_task(
        task_type=task_type,
        target_groups=target_groups
    )
    
    print(f"任务执行完成: {result}")

if __name__ == '__main__':
    main()
```

## 配置文件优势

1. **灵活性**: 支持多环境、多目标组、多任务类型配置
2. **安全性**: 敏感信息通过GitHub Secrets管理，配置文件不包含密钥
3. **可扩展性**: 易于添加新的UP主、新的表格、新的通知方式
4. **可维护性**: 配置与代码分离，修改配置无需修改代码
5. **版本控制**: 配置文件可以版本控制，便于追踪变更

这样的配置系统确保了任务设置的灵活性，避免了硬编码，同时保持了安全性和可维护性。

## 使用示例

### 1. 自动化执行 (默认)
- 系统按照 `default_target` 配置自动执行
- 每天8点和20点采集视频数据
- 每四周周五采集历史数据

### 2. 手动执行 - 只更新UP主信息
1. 进入GitHub Actions页面
2. 选择 "Run workflow"
3. 设置参数：
   - task_type: `daily_t1`
   - target_config: `up_only`
   - custom_up_id: (留空使用默认，或填入其他UP主ID)

### 3. 手动执行 - 测试少量数据
1. 选择 "Run workflow"
2. 设置参数：
   - task_type: `daily_t1`
   - target_config: `test`
   - debug_mode: `true`

### 4. 手动执行 - 完整数据采集
1. 选择 "Run workflow"
2. 设置参数：
   - task_type: `monthly`
   - target_config: `full`
   - custom_up_id: `20813884` (或其他UP主ID)

这样的配置系统既保持了简单性，又提供了足够的灵活性来控制采集范围。通过留空/填0的规则，可以精确控制每次执行采集哪些数据。
## B站数据字段详细映射表 (带序号)

### 连续字段映射 (按类型分组)

| 序号 | 列 | 字段名 | 中文名称 | B站API字段 | 数据类型 | 开关配置 |
|------|----|---------|---------|-----------|---------|---------| 
| **UP主信息 (A-D列)** |
| 1 | A | up_mid | UP主ID | data.mid | number | up_fields.mid |
| 2 | B | up_name | UP主昵称 | data.name | string | up_fields.name |
| 3 | C | up_fans | 粉丝数 ⭐ | data.follower | number | up_fields.fans |
| 4 | D | up_video_count | 视频总数 ⭐ | data.archive_count | number | up_fields.video |
| **视频信息 (E-N列)** |
| 5 | E | video_aid | 视频AV号 ⭐ | data.View.aid | number | video_fields.aid |
| 6 | F | video_bvid | 视频BV号 ⭐ | data.View.bvid | string | video_fields.bvid |
| 7 | G | video_title | 视频标题 ⭐ | data.View.title | string | video_fields.title |
| 8 | H | video_desc | 视频描述 | data.View.desc | string | video_fields.desc |
| 9 | I | video_duration | 视频时长 | data.View.duration | number | video_fields.duration |
| 10 | J | video_pubdate | 发布时间 ⭐ | data.View.pubdate | timestamp | video_fields.pubdate |
| 11 | K | video_view | 播放量 ⭐ | data.View.stat.view | number | video_fields.view |
| 12 | L | video_danmaku | 弹幕数 | data.View.stat.danmaku | number | video_fields.danmaku |
| 13 | M | video_reply | 评论数 ⭐ | data.View.stat.reply | number | video_fields.reply |
| 14 | N | video_favorite | 收藏数 ⭐ | data.View.stat.favorite | number | video_fields.favorite |
| 15 | O | video_coin | 投币数 ⭐ | data.View.stat.coin | number | video_fields.coin |
| 16 | P | video_like | 点赞数 ⭐ | data.View.stat.like | number | video_fields.like |
| 17 | Q | video_share | 分享数 ⭐ | data.View.stat.share | number | video_fields.share |
| **特殊字段 (R-S列)** |
| 18 | R | hot_comments_json | 热门评论JSON ⭐ | - | json | special_fields.hot_comments |
| 19 | S | update_time | 更新时间 | - | datetime | system_fields.update_time |

### 任务类型特定字段配置示例 (父子记录架构)

```yaml
# 日任务字段配置 (T1/T2 - 8点和20点执行)
task_specific_fields:
  daily_task:
    # 父记录字段 (video_master表) - 新视频时创建
    master_fields:
      video_id: true     # 视频ID (BV号，主键)
      aid: true          # AV号
      title: true        # 视频标题 ⭐ 重要
      cover_url: true    # 封面URL ⭐ 新增 (首次获取)
      video_url: true    # 视频链接
      publish_time: true # 发布时间 ⭐ 重要
      up_id: true        # UP主ID
      up_name: true      # UP主昵称
      # 日任务跳过: description, duration, category (月任务时补充)
    
    # 子记录字段 (video_stats表) - 每次任务都创建
    stats_fields:
      view: true         # 11. K列 - 播放量 ⭐ 重要
      like: true         # 16. P列 - 点赞数 ⭐ 重要
      coin: true         # 15. O列 - 投币数 ⭐ 重要
      favorite: true     # 14. N列 - 收藏数 ⭐ 重要
      share: true        # 17. Q列 - 分享数 ⭐ 重要
      reply: true        # 13. M列 - 评论数 ⭐ 重要
      up_fans: true      # UP主粉丝数快照
      hot_comments: true # 18. R列 - 热门评论JSON ⭐ 重要
      # 日任务跳过: danmaku (月任务时采集)
    
    # UP主信息 (up_masters表) - 独立更新
    up_fields:  
      mid: true          # 1. A列 - UP主ID (必需)
      name: true         # 2. B列 - UP主昵称 (必需)
      fans: true         # 3. C列 - 粉丝数 ⭐ 重要
      video: true        # 4. D列 - 视频总数 ⭐ 重要
      # 日任务跳过: friend, sign, level, official_verify

  # 月任务字段配置 (每四周周五执行)
  monthly_task:
    # 父记录字段 (video_master表) - 补充完整信息
    master_fields:
      video_id: true     # 视频ID (BV号，主键)
      aid: true          # AV号
      title: true        # 视频标题 ⭐ 重要
      description: true  # 视频描述 (月任务补充)
      cover_url: true    # 封面URL ⭐ (已存在则跳过)
      video_url: true    # 视频链接
      publish_time: true # 发布时间 ⭐ 重要
      duration: true     # 视频时长 (月任务补充)
      category: true     # 分区名称 (月任务补充)
      up_id: true        # UP主ID
      up_name: true      # UP主昵称
    
    # 子记录字段 (video_stats表) - 完整统计数据
    stats_fields:
      view: true         # 11. K列 - 播放量 ⭐ 重要
      like: true         # 16. P列 - 点赞数 ⭐ 重要
      coin: true         # 15. O列 - 投币数 ⭐ 重要
      favorite: true     # 14. N列 - 收藏数 ⭐ 重要
      share: true        # 17. Q列 - 分享数 ⭐ 重要
      reply: true        # 13. M列 - 评论数 ⭐ 重要
      danmaku: true      # 12. L列 - 弹幕数 (月任务采集)
      up_fans: true      # UP主粉丝数快照
      hot_comments: true # 18. R列 - 热门评论JSON ⭐ 重要
    
    # UP主信息 (up_masters表) - 完整信息
    up_fields:  
      mid: true          # 1. A列 - UP主ID (必需)
      name: true         # 2. B列 - UP主昵称 (必需)
      fans: true         # 3. C列 - 粉丝数 ⭐ 重要
      video: true        # 4. D列 - 视频总数 ⭐ 重要
    

# 热门评论JSON配置 (R列)
hot_comments_json:  
  enabled: true        # 是否生成热门评论JSON
  max_count: 10        # 最多10条热评
  fields:              # JSON中包含的字段
    - "message"        # 评论内容
    - "uname"          # 评论者昵称
    - "mid"            # 评论者ID
    - "ctime"          # 评论时间
    - "like"           # 点赞数
    - "rcount"         # 回复数
```

### 多维表格输出示例 (父子记录架构)

#### 1. 视频基础信息表 (video_master) - 父记录
```
# 首次发现视频时创建，包含封面URL等静态信息
video_id | aid    | title    | cover_url                    | publish_time | up_id    | up_name | first_discovered
BV1xx... | 123456 | 测试视频 | https://i0.hdslb.com/xxx.jpg | 2024-01-14   | 20813884 | 何同学  | 2024-01-15 08:00
```

#### 2. 视频统计数据表 (video_stats) - 子记录
```
# 每次任务都创建新记录，记录动态统计数据
parent_video | video_id | view_count | like_count | coin_count | crawl_time          | data_source | time_point
rec_xxx      | BV1xx... | 500000     | 12000      | 3000       | 2024-01-15 08:00:00 | daily_t1    | T1
rec_xxx      | BV1xx... | 520000     | 12500      | 3100       | 2024-01-15 20:00:00 | daily_t2    | T2
```

#### 3. UP主信息表 (up_masters) - 独立表
```
# UP主信息独立更新
up_id    | up_name | fans_count | video_count | total_views | update_time         | data_source
20813884 | 何同学  | 1234567    | 89          | 45000000    | 2024-01-15 08:00:00 | daily_t1
```

#### 父子记录关联示例
```
# 通过parent_video字段建立关联
video_master (父记录):
  - record_id: rec_master_001
  - video_id: BV1xx...
  - title: 测试视频
  - cover_url: https://i0.hdslb.com/xxx.jpg

video_stats (子记录):
  - record_id: rec_stats_001
  - parent_video: rec_master_001  # 关联到父记录
  - video_id: BV1xx...
  - view_count: 500000
  - crawl_time: 2024-01-15 08:00:00
  
  - record_id: rec_stats_002
  - parent_video: rec_master_001  # 同一个父记录
  - video_id: BV1xx...
  - view_count: 520000
  - crawl_time: 2024-01-15 20:00:00
```

#### 父子记录架构对比表

| 记录类型 | 日任务处理 | 月任务处理 | 数据特点 | 更新频率 |
|----------|------------|------------|----------|----------|
| **父记录 (video_master)** | 新视频时创建 | 补充完整信息 | 静态信息+封面URL | 首次发现时 |
| **子记录 (video_stats)** | 每次都创建 | 每次都创建 | 动态统计数据 | 每次任务 |
| **UP主记录 (up_masters)** | 核心字段更新 | 完整字段更新 | UP主基础信息 | 每次任务 |

#### 执行效率对比 (父子记录架构)

| 任务类型 | 父记录操作 | 子记录操作 | 封面URL获取 | 执行效率 | 适用场景 |
|----------|------------|------------|-------------|----------|----------|
| **日任务** | 仅新视频创建 | 每次创建 | 仅新视频获取 | 高效快速 | 日常监控、增长率分析 |
| **月任务** | 补充详细信息 | 每次创建 | 缓存复用 | 中等速度 | 深度分析、数据存档 |

#### 父子记录架构优势

1. **存储优化**: 
   - 静态信息（标题、封面）只存储一次
   - 动态数据（播放量、点赞）按时间序列存储
   
2. **封面URL优化**:
   - 首次发现时获取并缓存
   - 后续任务直接复用，避免重复请求
   
3. **增量更新**:
   - 维护已知视频列表
   - 新视频创建父记录，已知视频只更新子记录
   
4. **查询效率**:
   - 父子关联支持复杂查询
   - 时间序列数据便于趋势分析
   
5. **API调用优化**:
   - 减少重复数据传输
   - 批量操作提高效率

这种基于函数引用和本地文件缓存的离线优先设计的优点：

1. **MediaCrawler无缝集成**: 
   - **函数引用**: 使用函数引用而非继承，确保MediaCrawler更新后的兼容性
   - **适配器模式**: 通过适配器转换数据格式，隔离版本差异
   - **自动兼容**: MediaCrawler功能更新时无需修改核心逻辑

2. **离线优先架构**: 
   - **本地缓存**: 基于MediaCrawler的JSON存储架构，数据先存本地
   - **API检测**: 只有检测到API配置才尝试同步到多维表格
   - **容错性强**: API失败不影响数据收集，保证系统稳定性

3. **文件结构优化**: 
   - **父记录文件**: 存储静态信息（标题、描述、封面URL等）
   - **子记录文件**: 按日期分割，存储动态统计数据
   - **状态文件**: 记录同步状态，支持增量同步

4. **GitHub Actions集成**: 
   - **分离执行**: 数据收集和API同步分为两个独立步骤
   - **环境变量**: 通过GitHub Secrets管理API配置
   - **灵活部署**: 可以只收集数据，也可以完整同步

5. **增量同步机制**: 
   - **已知视频列表**: 避免重复处理已知视频
   - **同步状态跟踪**: 记录已同步的记录，避免重复传输
   - **批量操作**: 提高同步效率，减少API调用

6. **存储效率**: 
   - **MediaCrawler函数**: 复用MediaCrawler的高效文件I/O函数
   - **文件锁机制**: 防止并发写入冲突
   - **自动清理**: 定期清理过期缓存文件

7. **配置灵活性**: 
   - **函数引用配置**: 可配置MediaCrawler函数引用映射
   - **适配器配置**: 支持自定义数据适配器
   - **兼容性检查**: 自动验证MediaCrawler版本兼容性

8. **监控和统计**: 
   - **缓存统计**: 实时监控缓存文件大小和记录数量
   - **同步结果**: 详细记录同步成功/失败的记录数
   - **兼容性监控**: 跟踪MediaCrawler函数调用状态

9. **开发友好**: 
   - **本地调试**: 可以在没有API的情况下测试数据收集
   - **版本兼容**: MediaCrawler更新时自动适配新功能
   - **函数测试**: 可以独立测试每个MediaCrawler函数引用