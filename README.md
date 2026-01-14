# Claude Code 技能安装助手

一个终端风格的 Web 界面，用于管理和安装 Claude Code 技能。技能将直接安装到 Claude Code 的技能目录并完成注册。

## 前置要求

- Python 3.8+
- 现代 Web 浏览器

## 快速开始

```bash
# 安装依赖
pip install fastapi uvicorn python-multipart

# 一键启动
./start.sh
```

服务启动后：
- 前端界面: http://localhost:8001
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

按 `Ctrl+C` 停止所有服务。

## 功能特性

### 核心功能
- **拖放上传** - 支持 `.zip` 压缩包或包含 `SKILL.md` 的文件夹
- **自动解析** - 自动检测技能名称和描述
- **一键安装** - 直接安装到 Claude Code 技能目录
- **完整注册** - 自动更新 `installed_plugins.json`
- **技能管理** - 查看和卸载已安装的技能

### 界面特性
- **终端风格 UI** - 霓虹绿/青色配色，等宽字体，发光效果
- **技能搜索** - 按名称或描述快速过滤技能
- **详情预览** - 点击查看技能完整信息
- **Toast 通知** - 优雅的操作反馈提示
- **进度动画** - 安装过程的视觉反馈

## 技能安装位置

技能将安装到以下 Claude Code 目录：

```
~/.claude/plugins/
├── marketplaces/anthropic-agent-skills/  # 技能源目录
├── cache/anthropic-agent-skills/         # 技能缓存
└── installed_plugins.json                # 注册文件
```

## 技能格式

技能需要包含 `SKILL.md` 文件，格式如下：

```yaml
---
name: 技能名称
description: 技能描述
---

# 技能内容
...
```

## 示例技能

`sample-skills/obsidian-markdown.zip` 提供了一个示例技能用于测试。

## 手动启动

如果不使用 `start.sh`，可以手动启动：

```bash
# 终端 1: 启动后端
cd skill-assistant/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2: 启动前端
cd skill-assistant/frontend
python3 -m http.server 8001
```
