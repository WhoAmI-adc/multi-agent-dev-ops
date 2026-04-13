# 系统架构设计文档

## 1. 系统概述

本系统是基于 **crewAI** 框架实现的多智能体 DevOps 运维平台，面向云原生应用的智能化运维场景。系统通过多个专业化 AI 智能体的协同协作，实现监控、诊断、修复、部署、优化等核心运维功能的自动化。

```
┌─────────────────────────────────────────────────────────────────┐
│                    多智能体 DevOps 运维系统                       │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  场景1      │  │  场景2      │  │  场景3      │                │
│  │  自动部署   │  │  故障诊断   │  │  性能优化   │                │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                │
│        │               │               │                         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                  DevOps Crew 协调层                     │     │
│  │                                                         │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │ 监控专家  │ │ 诊断专家  │ │ 修复专家  │ │ 部署专家  │  │     │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │     │
│  │       └────────────┴────────────┴──────────────┘        │     │
│  │                    ┌──────────┐                          │     │
│  │                    │ 优化专家  │                          │     │
│  │                    └──────────┘                          │     │
│  └────────────────────────────────────────────────────────┘     │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     工具层 (Tools)                       │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │ Docker   │ │   Log    │ │ Monitor  │ │   Git    │   │    │
│  │  │  Tools   │ │  Tools   │ │  Tools   │ │  Tools   │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  │                    ┌──────────┐                          │    │
│  │                    │   K8s    │                          │    │
│  │                    │  Tools   │                          │    │
│  │                    └──────────┘                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              基础设施层 (Infrastructure)                  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │  Docker  │ │  MySQL   │ │  Redis   │ │  Nginx   │   │    │
│  │  │ Containers│ │    DB    │ │  Cache   │ │  Proxy   │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  │                 ┌──────────────┐                         │    │
│  │                 │  Kubernetes  │                         │    │
│  │                 │   Cluster    │                         │    │
│  │                 └──────────────┘                         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 核心组件

### 2.1 智能体层（Agent Layer）

系统包含 **5个专业化智能体**，每个智能体专注于特定的运维领域：

| 智能体 | 角色 | 主要工具 | 输出 |
|--------|------|----------|------|
| infrastructure_monitor | 基础设施监控专家 | monitor_tools, k8s_tools | 监控报告、告警 |
| fault_diagnostician | 故障诊断专家 | log_tools, monitor_tools | 诊断报告 |
| auto_remediator | 自动化修复专家 | docker_tools, k8s_tools | 修复执行报告 |
| deployment_engineer | 部署运维专家 | git_tools, docker_tools, k8s_tools | 部署报告 |
| performance_optimizer | 性能优化专家 | monitor_tools, log_tools | 优化方案报告 |

### 2.2 工具层（Tool Layer）

工具层提供与基础设施交互的标准化接口：

```
tools/
├── docker_tools.py      # Docker 容器操作
│   ├── list_containers()
│   ├── get_container_status()
│   ├── restart_container()
│   ├── get_container_logs()
│   └── build_image()
│
├── log_tools.py         # 日志分析
│   ├── search_logs()
│   ├── analyze_errors()
│   ├── get_log_statistics()
│   └── filter_by_level()
│
├── monitor_tools.py     # 系统监控
│   ├── get_cpu_usage()
│   ├── get_memory_usage()
│   ├── get_disk_usage()
│   ├── check_service_health()
│   └── get_alerts()
│
├── git_tools.py         # Git 版本控制
│   ├── get_latest_commits()
│   ├── create_branch()
│   ├── merge_branch()
│   ├── get_commit_history()
│   └── get_diff()
│
└── kubernetes_tools.py  # K8s 集群操作
    ├── list_pods()
    ├── get_pod_status()
    ├── restart_pod()
    ├── scale_deployment()
    └── get_pod_logs()
```

### 2.3 任务层（Task Layer）

任务层定义了各智能体需要完成的具体工作单元，通过 YAML 配置文件声明式定义：

- `monitor_infrastructure_task` - 基础设施监控
- `check_alerts_task` - 告警检查处理
- `diagnose_fault_task` - 故障诊断分析
- `analyze_performance_task` - 性能分析
- `execute_remediation_task` - 执行修复
- `deploy_application_task` - 应用部署
- `optimize_performance_task` - 性能优化

## 3. 智能体协作模式

### 3.1 顺序协作（Sequential）

多数场景采用顺序协作模式，前一个智能体的输出作为后一个智能体的上下文：

```
监控专家 → 诊断专家 → 修复专家
   │           │          │
   │  监控报告  │  诊断报告 │  修复报告
   └──────────→└──────────→└─────────→ 最终结果
```

### 3.2 专家团队（Crew）

根据不同场景，组建不同的专家团队：

| 场景 | 参与智能体 | 协作流程 |
|------|----------|---------|
| 监控告警 | 监控专家 | 单智能体 |
| 故障诊断 | 监控专家 + 诊断专家 | 顺序 |
| 故障修复 | 诊断专家 + 修复专家 | 顺序 |
| 自动部署 | 部署专家 + 监控专家 | 顺序 |
| 性能优化 | 监控专家 + 优化专家 | 顺序 |

## 4. 数据流设计

### 4.1 输入数据

```yaml
inputs:
  service_name: "目标服务名称"
  fault_description: "故障描述（诊断场景）"
  app_name: "应用名称（部署场景）"
  version: "版本号（部署场景）"
  environment: "目标环境（部署场景）"
  performance_issue: "性能问题描述（优化场景）"
```

### 4.2 工具调用链

以故障诊断场景为例：

```
用户触发 → fault_description
    ↓
监控专家
    ├── get_alerts() → 告警列表
    ├── get_cpu_usage() → CPU 指标
    ├── get_memory_usage() → 内存指标
    └── list_pods() → Pod 状态
    ↓ (监控报告作为上下文传给诊断专家)
诊断专家
    ├── search_logs(keyword=错误关键词) → 相关日志
    ├── analyze_errors(service=服务名) → 错误模式
    ├── filter_by_level(level=ERROR) → 错误日志
    └── get_pod_logs(pod_name=异常Pod) → Pod 日志
    ↓ (诊断报告)
用户 → 诊断结论和修复建议
```

### 4.3 输出数据

每个场景生成结构化的报告输出：

- **监控报告**：资源使用情况、告警列表、风险预警
- **诊断报告**：根因分析、置信度评估、修复建议
- **修复报告**（`remediation_report.md`）：执行步骤、验证结果、回滚计划
- **部署报告**（`deployment_report.md`）：部署摘要、变更内容、健康验证
- **优化报告**（`optimization_report.md`）：瓶颈分析、优化方案、预期 ROI

## 5. 技术架构选型

### 5.1 框架选择

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 多智能体框架 | crewAI | 成熟的多智能体框架，支持角色、任务、工具定义 |
| LLM | DeepSeek | 高性价比，中文支持好，适合中文场景 |
| 工具接口 | crewAI Tools | 标准化工具定义，自动注入智能体上下文 |
| 配置管理 | YAML | 声明式配置，易于维护和扩展 |

### 5.2 扩展性设计

系统采用模块化设计，易于扩展：

1. **新增智能体**：在 `agents.yaml` 中添加配置，在 `crew.py` 中实现方法
2. **新增工具**：在 `tools/` 目录添加新工具文件，使用 `@tool` 装饰器注册
3. **新增场景**：基于现有智能体和工具组合新的 Crew 即可
4. **切换 LLM**：通过环境变量 `LLM_MODEL` 和 `LLM_API_KEY` 配置

### 5.3 可靠性设计

- **错误处理**：所有工具函数包含完整的异常捕获和错误返回
- **演示模式**：当 LLM API 不可用时，场景脚本自动切换到演示模式
- **工具容错**：工具调用失败时返回结构化错误信息而非异常
- **幂等设计**：所有工具操作设计为幂等，重复调用不产生副作用（模拟环境）

## 6. 部署架构

### 6.1 开发环境

```bash
# 安装依赖
pip install crewai

# 配置 LLM
export DEEPSEEK_API_KEY=your_api_key

# 运行系统
cd devops_crew && python main.py
```

### 6.2 生产集成

在生产环境中，工具层需要集成真实的基础设施：

```
docker_tools.py   →  Docker Engine API / docker SDK
log_tools.py      →  Elasticsearch / Loki / 日志平台 API
monitor_tools.py  →  Prometheus / Zabbix / 云监控 API  
git_tools.py      →  GitHub / GitLab / Gitea API
kubernetes_tools.py → Kubernetes API Server / kubectl
```

---

*文档版本：v1.0 | 最后更新：2026-04-13*
