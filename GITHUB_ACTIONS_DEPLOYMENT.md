# GitHub Actions 部署文件清单

## 🚀 GitHub Actions 工作流程文件
```
.github/workflows/
├── daily-morning.yml      # 每日8:00数据采集
├── daily-evening.yml      # 每日20:00数据采集  
└── weekly-historical.yml  # 每周五8:00历史数据处理
```

## 🔧 GitHub Actions 脚本文件
```
.github/scripts/
├── enhanced_cookie_rotation.py    # 增强Cookie轮换管理（主脚本）
├── bilibili_cookie_tester.py      # B站Cookie连通性测试
├── cookie_cleanup_manager.py      # Cookie清理管理
└── feishu_notifier.py             # 飞书Webhook通知脚本
```

## 📖 GitHub Actions 说明文件
```
.github/
└── README.md                      # GitHub Actions配置说明
```

## ⚙️ 项目核心文件（GitHub Actions会使用）
```
./
├── bilibili_core/                 # 核心代码模块
├── daily_task_config.yaml        # 主配置文件
├── requirements.txt               # Python依赖
├── run_daily_task.py             # 日任务执行脚本
├── run_monthly_task.py           # 月任务执行脚本
└── README.md                     # 项目说明
```

## 🗑️ 已清理的文件
- ❌ `test_*.py` - 所有测试脚本
- ❌ `LOCAL_TEST_GUIDE.md` - 本地测试指南
- ❌ `PROJECT_STRUCTURE.md` - 项目结构说明
- ❌ `test_workflow.sh` - 测试工作流脚本
- ❌ `*_report.json` - 临时报告文件
- ❌ `.DS_Store` - 系统文件
- ❌ `.github/scripts/cookie_rotation.py` - 旧版本脚本

## ✅ 保留的重要文件
- ✅ `daily_task_config.yaml.backup` - 配置文件备份
- ✅ `.gitignore` - Git忽略规则
- ✅ 所有 `bilibili_core/` 模块文件
- ✅ 所有 GitHub Actions 相关文件

## 🎯 部署就绪状态
项目已清理完毕，只保留GitHub Actions部署必需的文件，可以安全推送到GitHub仓库。