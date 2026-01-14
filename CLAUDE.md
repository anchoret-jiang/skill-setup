# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

Claude Code 技能安装助手 - 终端风格的 Web 界面，用于管理和安装 Claude Code 技能。

## 开发命令

**一键启动（推荐）：**
```bash
./start.sh
```
- 前端: http://localhost:8001
- 后端: http://localhost:8000

**安装依赖：**
```bash
pip install fastapi uvicorn python-multipart
```

## 架构

**后端** (`skill-assistant/backend/main.py`)：
- FastAPI REST API，启用 CORS
- 接口：
  - `POST /upload` - 上传并解析技能 zip 文件
  - `POST /install` - 安装技能到 Claude 目录并注册
  - `GET /installed` - 列出已安装的技能
  - `DELETE /installed/{skill_id}` - 卸载技能
  - `GET /config` - 获取配置信息
- 技能安装到 `~/.claude/plugins/marketplaces/anthropic-agent-skills/`
- 缓存复制到 `~/.claude/plugins/cache/anthropic-agent-skills/`
- 更新 `~/.claude/plugins/installed_plugins.json` 注册

**前端** (`skill-assistant/frontend/index.html`)：
- 单文件 React 应用（React 18、Tailwind CSS、Babel）
- 终端/黑客风格 UI（JetBrains Mono + Orbitron 字体）
- 功能组件：
  - Toast 通知系统
  - 技能详情模态框
  - 搜索过滤
  - 安装进度条

## 技能格式

```yaml
---
name: 技能名称
description: 技能描述
---

# 技能内容
...
```

## 关键目录

- `skill-assistant/backend/` - FastAPI 后端
- `skill-assistant/frontend/` - React 前端
- `sample-skills/` - 示例技能
- `start.sh` - 一键启动脚本

### Claude Code 技能目录

- `~/.claude/plugins/marketplaces/anthropic-agent-skills/` - 技能源
- `~/.claude/plugins/cache/anthropic-agent-skills/` - 缓存
- `~/.claude/plugins/installed_plugins.json` - 注册文件
