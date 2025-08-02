# 配置模板说明

这个目录包含了不同使用场景的配置模板文件。

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

## 使用方法

1. 复制合适的模板到根目录
2. 重命名为 `daily_task_config.yaml`
3. 根据实际情况修改配置项
4. 开始使用

## 配置优先级

1. 根目录的 `daily_task_config.yaml` (主配置)
2. 环境变量 (如 UP_ID, BILIBILI_COOKIES)
3. 模板文件中的默认值