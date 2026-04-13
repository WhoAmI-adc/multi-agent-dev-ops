# 运维场景说明文档

## 概述

本系统设计了 **4个典型的运维场景**，覆盖日常运维工作中最常见的操作类型。每个场景均由多个专业化智能体协作完成，展示了多智能体系统在实际 DevOps 工作中的应用价值。

---

## 场景1：自动化部署流程（scenario1_deploy.py）

### 1.1 场景背景

研发团队完成了 API 服务 v2.2.0 版本的开发，新版本优化了数据库连接池配置，修复了慢查询问题。现在需要将其部署到生产环境，同时确保部署过程零停机。

### 1.2 参与智能体

| 智能体 | 职责 |
|--------|------|
| 部署运维专家（主导） | 检查代码变更、构建镜像、执行 K8s 部署 |
| 基础设施监控专家（验证） | 验证部署后服务健康状态 |

### 1.3 执行流程

```
用户触发部署
     ↓
【部署专家】检查代码仓库
     ├── get_latest_commits() → 获取最新提交
     └── get_diff() → 查看具体变更内容
     ↓
【部署专家】构建 Docker 镜像
     └── build_image(api-server, v2.2.0) → 构建并打标签
     ↓
【部署专家】执行 K8s 滚动更新
     └── scale_deployment(api-server, replicas=2) → 滚动替换 Pod
     ↓
【部署专家】验证部署状态
     └── list_pods(namespace=production) → 确认新 Pod 就绪
     ↓
【监控专家】服务健康检查
     ├── check_service_health(api-server) → 检查健康端点
     └── get_alerts() → 确认无新告警产生
     ↓
输出：部署报告（deployment_report.md）
```

### 1.4 预期输出

**部署报告摘要（示例）**：
```
## 部署报告

**应用版本**：api-server:v2.2.0
**目标环境**：production
**部署时间**：2026-04-13 08:00:00
**部署状态**：✅ 成功

### 代码变更摘要
- 优化数据库连接池配置（pool_size: 5→20）
- 修复订单查询 N+1 问题
- 更新 Docker 基础镜像

### 部署验证
- 新 Pod 启动耗时：28s
- 健康检查状态：通过
- 服务响应时间：256ms（较部署前改善 90%）
```

### 1.5 运行示例

```bash
# 使用演示模式（无需 LLM API）
python scenario1_deploy.py --demo

# 完整 AI 模式
python scenario1_deploy.py --app api-server --version v2.2.0 --env production

# 使用 devops_crew 主入口
python devops_crew/main.py --scenario deploy --app api-server --version v2.2.0
```

---

## 场景2：故障诊断和自动修复（scenario2_diagnosis.py）

### 2.1 场景背景

生产环境告警触发：API 服务响应时间升至 5 秒，错误率达到 30%。运维团队需要快速定位根因并执行修复操作，将 MTTR（平均修复时间）控制在 15 分钟内。

### 2.2 参与智能体

| 智能体 | 职责 |
|--------|------|
| 故障诊断专家（主导） | 分析日志、识别错误模式、定位根因 |
| 自动修复专家（执行） | 根据诊断结果执行修复操作 |

### 2.3 执行流程

```
告警触发：API 错误率 30%
     ↓
【诊断专家】分析错误日志
     ├── filter_by_level(level=ERROR, service=api-server)
     └── search_logs(keyword="connection pool")
     ↓
【诊断专家】错误模式识别
     └── analyze_errors(service=api-server, time_window=30)
     ↓
【诊断专家】关联分析（DB 日志）
     └── analyze_errors(service=mysql-db, time_window=30)
     ↓
【诊断专家】检查异常 Pod
     ├── list_pods(namespace=production)
     └── get_pod_logs(pod=worker-service-xxx)
     ↓
根因确认：
  1. DB 连接池耗尽（pool_size 不足）
  2. 慢查询占用连接（缺少索引）
  3. worker-service 崩溃（RabbitMQ 不可用）
     ↓
【修复专家】执行修复
     ├── restart_pod(worker-service-xxx) → 重启崩溃 Pod
     └── scale_deployment(api-server, replicas=3) → 扩容缓解压力
     ↓
【修复专家】验证恢复
     └── check_service_health(api-server) → 确认服务恢复
     ↓
输出：诊断报告 + 修复执行报告（remediation_report.md）
```

### 2.4 预期输出

**诊断报告摘要（示例）**：
```
## 故障诊断报告

**故障时间**：2026-04-13 07:10:00
**影响范围**：api-server（所有请求的 30% 失败）
**根因**：数据库连接池耗尽（置信度：HIGH）

### 故障链
1. orders 表全表扫描（8-12秒/次）
   ↓ 导致
2. DB 连接长时间占用
   ↓ 导致
3. 连接池（pool_size=5）耗尽
   ↓ 导致
4. API 请求 503 错误

### 修复建议
短期：重启 worker-service，扩容 api-server
长期：增大连接池，为 orders.status 加索引
```

### 2.5 运行示例

```bash
# 演示模式
python scenario2_diagnosis.py --demo

# 自定义故障描述
python scenario2_diagnosis.py --fault "内存使用率持续增长，疑似内存泄漏"

# 使用主入口
python devops_crew/main.py --scenario diagnose --fault "数据库连接池耗尽"
```

---

## 场景3：性能优化分析（scenario3_optimization.py）

### 3.1 场景背景

系统在最近7天内性能持续下滑：P99 延迟从 500ms 升至 3000ms，CPU 使用率维持在 85% 以上，用户体验明显下降。需要系统性地分析瓶颈并制定优化方案。

### 3.2 参与智能体

| 智能体 | 职责 |
|--------|------|
| 基础设施监控专家 | 收集多维度性能指标 |
| 性能优化专家（主导） | 深度分析瓶颈，制定优化方案 |

### 3.3 执行流程

```
性能问题触发优化流程
     ↓
【监控专家】收集系统指标
     ├── get_cpu_usage() → 各节点 CPU 使用率
     ├── get_memory_usage() → 内存使用情况
     ├── get_disk_usage() → 磁盘 IO 情况
     └── check_service_health() → 服务响应时间
     ↓
【优化专家】分析日志中的性能问题
     ├── get_log_statistics() → 错误率和健康评分
     └── analyze_errors(time_window=60) → 性能相关错误
     ↓
【优化专家】识别高负载组件
     ├── list_pods() → Pod 资源使用排行
     └── get_pod_status(mysql-db-0) → DB Pod 详情
     ↓
【优化专家】制定优化方案
     按优先级（P1/P2/P3）输出：
     - P1 数据库索引优化（立即执行）
     - P1 连接池配置调整（立即执行）
     - P2 服务水平扩展（本周内）
     - P3 读写分离架构（下个迭代）
     ↓
输出：性能优化报告（optimization_report.md）
```

### 3.4 预期输出

**优化报告摘要（示例）**：
```
## 性能优化报告

**分析周期**：最近 7 天
**当前性能评分**：58/100 (D 级)
**优化目标**：P99 < 1000ms，CPU < 60%

### 发现的瓶颈
1. 🔴 [HIGH] 数据库连接池不足（pool_size=5）
2. 🔴 [HIGH] 慢查询无索引（orders.status 全表扫描）
3. 🟡 [MED] node-3 资源过载
4. 🟡 [MED] API 副本数不足

### 优化方案
| 优先级 | 措施 | 预期效果 | 耗时 |
|--------|------|---------|------|
| P1 | 添加 orders.status 索引 | 查询: 8s→0.1s | 5 分钟 |
| P1 | 扩大连接池配置 | 消除 503 错误 | 30 分钟 |
| P2 | API 扩容至 4 副本 | P99 降低 50% | 10 分钟 |
| P3 | 实现读写分离 | 主库压力降 70% | 1 周 |

**预期优化后评分**：85/100 (B 级)
```

### 3.5 运行示例

```bash
# 演示模式（推荐，无需 LLM API）
python scenario3_optimization.py --demo

# 自定义问题描述
python scenario3_optimization.py --issue "数据库 IO 瓶颈，磁盘写入接近饱和"

# 使用主入口
python devops_crew/main.py --scenario optimize
```

---

## 场景4：监控告警处理（scenario4_monitoring.py）

### 4.1 场景背景

凌晨 2 点，监控系统同时触发 6 个告警：2个紧急（CPU过高、内存过高）、1个紧急（服务宕机）、3个警告（磁盘、响应时间、DB连接数）。值班工程师需要快速处理。

### 4.2 参与智能体

| 智能体 | 职责 |
|--------|------|
| 基础设施监控专家（主导） | 收集和分类所有告警 |
| 故障诊断专家（分析） | 分析告警根因 |
| 自动修复专家（处理） | 执行可自动化的修复动作 |

### 4.3 执行流程

```
告警触发（PagerDuty / 钉钉 / 企业微信通知）
     ↓
【监控专家】汇总所有告警
     └── get_alerts(status=firing) → 6 个活跃告警
     ↓
【监控专家】收集当前资源状态
     ├── get_cpu_usage() → node-3: 88.9%（紧急）
     ├── get_memory_usage() → node-3: 88.8%（紧急）
     └── get_disk_usage() → node-3: 89.0%（警告）
     ↓
【监控专家】服务健康检查
     └── check_service_health() → worker-service: DOWN
     ↓
【诊断专家】分析根因
     ├── analyze_errors() → DB 连接池耗尽 + 慢查询
     └── filter_by_level(ERROR) → 错误时间线
     ↓
告警分类和优先级：
  🔴 P1（立即处理）：worker-service 宕机
  🔴 P1（立即处理）：node-3 CPU/内存过高
  🟡 P2（1小时内）：磁盘使用率高
  🟡 P2（今天内）：API 响应时间、DB 连接数
     ↓
【修复专家】执行自动化修复
     ├── restart_pod(worker-service-xxx) → 重启宕机服务
     └── scale_deployment(api-server, 3) → 扩容减轻压力
     ↓
生成告警处理报告 + 通知相关人员
     ↓
输出：告警处理报告
```

### 4.4 预期输出

**告警处理报告（示例）**：
```
## 告警处理报告

**处理时间**：2026-04-13 07:20
**告警总数**：6 个（3 紧急 + 3 警告）
**自动处理**：2 个（worker-service 重启、api-server 扩容）
**需要人工**：4 个（资源优化、配置调整）

### 告警处理详情
| 告警 | 严重程度 | 状态 | 处理措施 |
|------|---------|------|---------|
| worker-service 宕机 | 🔴 紧急 | ✅ 已处理 | 重启 Pod |
| Node-3 CPU 过高 | 🔴 紧急 | 🔄 处理中 | 等待负载均衡 |
| Node-3 内存过高 | 🔴 紧急 | 🔄 处理中 | 等待优化 |
| 磁盘使用率高 | 🟡 警告 | 📋 待处理 | 计划日志清理 |
| API 响应时间慢 | 🟡 警告 | 🔄 处理中 | 等待 DB 优化 |
| DB 连接数高 | 🟡 警告 | 📋 待处理 | 计划配置更新 |

### 后续行动
1. 通知研发团队 review DB 连接池配置 PR
2. 运维团队清理 Node-3 磁盘（日志归档）
3. 下周安排 Node 负载均衡优化
```

### 4.5 运行示例

```bash
# 演示模式
python scenario4_monitoring.py --demo

# 完整 AI 模式
python scenario4_monitoring.py --service production-cluster

# 使用主入口
python devops_crew/main.py --scenario monitor
```

---

## 场景对比

| 维度 | 场景1 部署 | 场景2 故障 | 场景3 优化 | 场景4 监控 |
|------|-----------|-----------|-----------|-----------|
| 触发方式 | 主动（人工触发） | 被动（告警驱动） | 主动（周期分析） | 被动（告警触发） |
| 时间紧迫性 | 中 | 高（分钟级） | 低 | 高（分钟级） |
| 智能体数量 | 2 | 2-3 | 2 | 3 |
| 主要输出 | 部署报告 | 诊断+修复报告 | 优化方案 | 告警处理报告 |
| 核心价值 | 标准化部署 | 快速定位根因 | 预防性优化 | 自动化响应 |

---

## 快速运行指南

### 演示模式（无需 LLM API）

```bash
# 安装依赖
pip install crewai

# 所有场景均支持 --demo 模式，无需配置 LLM API
python scenario1_deploy.py --demo
python scenario2_diagnosis.py --demo
python scenario3_optimization.py --demo
python scenario4_monitoring.py --demo
```

### 完整 AI 模式

```bash
# 配置 LLM
export DEEPSEEK_API_KEY=your_api_key
# 或者编辑 devops_crew/crew.py 中的 api_key

# 通过统一入口运行
python devops_crew/main.py

# 或直接运行场景脚本
python scenario1_deploy.py --app myapp --version v1.0.0
```

---

*文档版本：v1.0 | 最后更新：2026-04-13*
