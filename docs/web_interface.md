# Web 界面使用指南

## 简介

本文档介绍多智能体 DevOps 系统的 Web 管理界面，基于 **Flask + Bootstrap 5 + WebSocket** 实现，提供实时系统监控、场景执行、日志查看等功能。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Web 应用

```bash
python web_interface/app.py
```

### 3. 访问界面

打开浏览器，访问：

```
http://localhost:5000
```

---

## 页面功能说明

### 🏠 仪表板（Dashboard）

**路径：** `/`

- 实时展示 CPU、内存、磁盘使用率（每 5 秒自动刷新）
- 显示 5 个智能体的在线/忙碌/离线状态
- 性能趋势折线图（最近 20 个时间点）
- 当前告警列表
- 最近 5 次任务执行记录

### 🎬 场景运行（Scenarios）

**路径：** `/scenarios`

| 场景 | 描述 | 参与智能体 |
|------|------|-----------|
| 自动化部署流程 | 代码检出到生产部署全流程 | 监控专家、修复专家 |
| 故障诊断和修复 | 异常检测、根因分析、自动修复 | 全部 4 个专家 |
| 性能优化分析 | 瓶颈识别与优化建议 | 监控、日志、诊断专家 |
| 监控告警处理 | 告警分类与自动响应 | 监控、诊断专家 |

**使用步骤：**
1. 选择目标场景，点击「执行场景」按钮
2. 系统自动弹出执行面板，显示进度条
3. 智能体对话窗口实时展示各专家的操作日志
4. 执行完成后显示最终结果

### 📋 日志查看（Logs）

**路径：** `/logs`

- WebSocket 实时推送新日志
- 支持按级别过滤：`ALL / INFO / WARNING / ERROR`
- 关键词搜索与高亮
- 一键导出日志为 `.txt` 文件
- 自动滚动开关

### 📈 执行历史（History）

**路径：** `/history`

- 展示所有历史任务，支持按场景名和状态搜索
- 点击任意行可查看执行详情（耗时、结果等）

### ⚙️ 系统设置（Settings）

**路径：** `/settings`

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| CPU 告警阈值 | 超过该值触发 DANGER 告警 | 80% |
| 内存告警阈值 | 超过该值触发 WARNING 告警 | 85% |
| 磁盘告警阈值 | 超过该值触发 DANGER 告警 | 90% |
| 日志级别 | 系统日志记录级别 | INFO |
| 自动刷新间隔 | 仪表板刷新周期（秒） | 5 |
| 最大日志行数 | 内存中保留的最大日志条数 | 500 |

---

## REST API 文档

### GET /api/dashboard

返回仪表板所有数据。

**响应示例：**
```json
{
  "metrics": {"cpu_percent": 42.1, "memory_percent": 65.3, ...},
  "agents": [{"id": "monitor_agent", "name": "监控专家", "status": "online"}, ...],
  "alerts": [],
  "alert_count": 0,
  "running_tasks": 0,
  "recent_history": [...]
}
```

### GET /api/scenarios

返回所有可用场景列表。

### POST /api/scenarios/{id}/run

启动指定场景的执行。

**请求体（可选）：**
```json
{}
```

**响应：**
```json
{"task_id": "deployment_1710000000000", "status": "started", "scenario": {...}}
```

### GET /api/logs

获取日志列表。

**查询参数：**
- `level`：`ALL / INFO / WARNING / ERROR`（默认 `ALL`）
- `search`：关键词过滤
- `limit`：返回条数（默认 200）

### GET /api/history

获取执行历史。

**查询参数：**
- `search`：场景名关键词
- `status`：`ALL / success / failed`

### GET /api/settings

获取当前系统设置。

### POST /api/settings

更新系统设置。

---

## WebSocket 事件

| 事件名 | 方向 | 描述 |
|--------|------|------|
| `connect` | 客户端 → 服务端 | 连接建立 |
| `log_history` | 服务端 → 客户端 | 连接后推送最近 50 条日志 |
| `new_log` | 服务端 → 客户端 | 实时推送新日志条目 |
| `task_started` | 服务端 → 客户端 | 场景开始执行 |
| `task_progress` | 服务端 → 客户端 | 场景执行进度更新 |
| `task_completed` | 服务端 → 客户端 | 场景执行完成 |
| `task_failed` | 服务端 → 客户端 | 场景执行失败 |
| `request_metrics` | 客户端 → 服务端 | 请求即时指标 |
| `metrics_update` | 服务端 → 客户端 | 返回即时指标 |

---

## 技术架构

```
web_interface/
├── app.py                    # Flask 主应用（REST API + WebSocket）
├── __init__.py
├── templates/
│   ├── base.html             # 基础模板（导航栏、Toast）
│   ├── index.html            # 仪表板
│   ├── scenarios.html        # 场景运行器
│   ├── logs.html             # 日志查看器
│   ├── history.html          # 执行历史
│   └── settings.html         # 系统设置
└── static/
    ├── css/
    │   ├── style.css         # 全局样式
    │   └── dashboard.css     # 仪表板样式
    └── js/
        ├── main.js           # WebSocket + 通用工具
        ├── dashboard.js      # 仪表板逻辑
        ├── scenarios.js      # 场景执行逻辑
        └── logs.js           # 日志流处理
```

**前端依赖（CDN）：**
- Bootstrap 5.3
- Font Awesome 6.4
- Chart.js 4.4
- Socket.IO 4.6

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `5000` | 监听端口 |
| `DEBUG` | `false` | 是否开启调试模式 |
| `SECRET_KEY` | `devops-web-secret-2024` | Flask Session 密钥 |
