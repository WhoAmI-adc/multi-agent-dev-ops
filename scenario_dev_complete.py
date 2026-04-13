"""
scenario_dev_complete.py
--------------------------
3 个完整的多智能体软件开发场景，展示自研框架的协作能力。

场景列表：
  1. scenario_1_user_authentication()  — 用户认证模块开发（5 步）
  2. scenario_2_data_processing()      — 数据处理模块开发（4 步）
  3. scenario_3_api_service()          — REST API 服务开发（4 步）

运行方式：
  python scenario_dev_complete.py
"""

from __future__ import annotations

import logging
import sys
import os
import time
from typing import Any, Callable, Dict, List, Optional

# ── 路径配置 ──────────────────────────────────────────────────────────────────
import sys
import os
import json
from datetime import datetime

# 将项目根目录加入 sys.path，确保可以导入 devops_crew
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from devops_crew.core.agent_base import CommunicationBus
from devops_crew.core.orchestrator import Orchestrator, WorkflowResult, WorkflowStep, StepType
from devops_crew.agents.dev_agents import (
    ArchitectAgent,
    DeveloperAgent,
    TesterAgent,
    CodeReviewerAgent,
    ProjectManagerAgent,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 场景定义：元数据
# ──────────────────────────────────────────────────────────────────────────────

SCENARIOS_META = [
    {
        "id": "auth_module",
        "name": "用户认证模块开发",
        "description": (
            "从零开始构建企业级用户认证系统，涵盖注册、登录、JWT 令牌管理、"
            "密码加密和权限控制，完整走过架构 → 开发 → 测试 → 审查 → 总结的全流程。"
        ),
        "icon": "fas fa-user-shield",
        "agents": ["architect", "developer", "tester", "reviewer", "pm"],
        "steps": [
            "项目规划与需求分析",
            "系统架构设计",
            "核心认证功能开发",
            "安全增强与边界处理",
            "单元测试与覆盖率分析",
            "代码质量与安全审查",
            "项目收尾与发布准备",
        ],
        "expected_duration": "8-15 分钟",
        "complexity": "中等",
        "tech_tags": ["JWT", "bcrypt", "FastAPI", "PostgreSQL", "Redis"],
    },
    {
        "id": "data_pipeline",
        "name": "数据处理模块开发",
        "description": (
            "设计并实现高性能大规模数据处理系统，支持批处理和流处理两种模式，"
            "涵盖数据清洗、转换、聚合和存储，使用多智能体协作完成从架构到交付的全过程。"
        ),
        "icon": "fas fa-database",
        "agents": ["architect", "developer", "tester", "reviewer", "pm"],
        "steps": [
            "数据需求分析与规划",
            "数据管道架构设计",
            "核心处理引擎开发",
            "性能优化与并发控制",
            "数据质量测试套件",
            "可靠性与容错审查",
            "部署配置与文档整理",
        ],
        "expected_duration": "8-15 分钟",
        "complexity": "较高",
        "tech_tags": ["Pandas", "Apache Kafka", "Celery", "Redis", "MinIO"],
    },
    {
        "id": "rest_api",
        "name": "REST API 服务开发",
        "description": (
            "构建符合 RESTful 规范的 API 服务，包含完整的 CRUD 操作、请求验证、"
            "分页、过滤、认证中间件和自动文档生成，展示标准化 API 开发的最佳实践。"
        ),
        "icon": "fas fa-server",
        "agents": ["architect", "developer", "tester", "reviewer", "pm"],
        "steps": [
            "API 规范设计",
            "服务架构规划",
            "核心 API 端点开发",
            "中间件与认证集成",
            "API 集成测试",
            "安全与性能审查",
            "文档与部署准备",
        ],
        "expected_duration": "8-15 分钟",
        "complexity": "中等",
        "tech_tags": ["FastAPI", "OpenAPI", "OAuth2", "Pydantic", "SQLAlchemy"],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# 协调器构建函数
# ──────────────────────────────────────────────────────────────────────────────

def _build_orchestrator(llm_model: Optional[str] = None) -> Orchestrator:
    """创建并返回已注册所有开发智能体的协调器实例"""
    bus = CommunicationBus()
    orch = Orchestrator(name="SoftwareDevOrchestrator")

    # 创建并注册 5 个专业智能体
    agents = [
        ArchitectAgent(bus=bus, llm_model=llm_model),
        DeveloperAgent(bus=bus, llm_model=llm_model),
        TesterAgent(bus=bus, llm_model=llm_model),
        CodeReviewerAgent(bus=bus, llm_model=llm_model),
        ProjectManagerAgent(bus=bus, llm_model=llm_model),
    ]
    for agent in agents:
        orch.register(agent)

    return orch


# ──────────────────────────────────────────────────────────────────────────────
# 场景 1：用户认证模块开发
# ──────────────────────────────────────────────────────────────────────────────

_AUTH_REQUIREMENT = """
开发一个企业级用户认证和授权模块，要求：

功能需求：
1. 用户注册（邮箱 + 密码，密码强度校验）
2. 用户登录（JWT Access Token + Refresh Token 双令牌机制）
3. 密码修改和重置（邮件验证码）
4. 多因素认证（TOTP / 短信验证码）
5. 基于角色的权限控制（RBAC：管理员、普通用户、访客）
6. 登录日志和异常行为检测（暴力破解防护）

非功能需求：
- 响应时间：P99 < 200ms
- 可用性：99.9%
- 密码存储：bcrypt（cost=12）
- 令牌有效期：Access 15min / Refresh 7day
- 兼容：RESTful API + WebSocket 通知
"""

def _build_auth_steps() -> List[WorkflowStep]:
    """构建用户认证场景的工作流步骤"""
    return [
        WorkflowStep(
            agent_id="pm",
            task_title="需求分析与项目规划",
            task_desc=(
                f"分析用户认证模块的需求，制定项目计划。\n\n需求：{_AUTH_REQUIREMENT}"
            ),
            step_type=StepType.SEQUENTIAL,
            priority=1,
        ),
        WorkflowStep(
            agent_id="architect",
            task_title="认证系统架构设计",
            task_desc=(
                f"为用户认证系统设计完整架构，包括组件设计、数据模型和技术选型。\n\n"
                f"需求：{_AUTH_REQUIREMENT}"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["pm_latest"],
            priority=2,
        ),
        WorkflowStep(
            agent_id="developer",
            task_title="核心认证功能实现",
            task_desc=(
                "根据架构设计实现认证模块核心功能：用户注册、登录、JWT 管理、"
                "密码加密、权限校验等核心逻辑。"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["architecture_design", "tech_stack"],
            priority=3,
        ),
        WorkflowStep(
            agent_id="tester",
            task_title="认证模块单元测试",
            task_desc=(
                "针对认证模块编写全面的测试用例，重点覆盖：正常登录、密码错误、"
                "令牌过期、权限越权、暴力破解防护等场景。"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "interfaces"],
            priority=4,
        ),
        WorkflowStep(
            agent_id="reviewer",
            task_title="安全性与代码质量审查",
            task_desc=(
                "对认证模块进行严格审查，特别关注：密码存储安全、令牌安全、"
                "SQL 注入防护、权限绕过风险、敏感信息泄露等安全问题。"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "test_code", "architecture_design"],
            priority=5,
        ),
        WorkflowStep(
            agent_id="pm",
            task_title="项目收尾与发布准备",
            task_desc=(
                "汇总所有智能体的输出，生成最终项目报告：评估完成度、总结技术决策、"
                "整理已知问题、提供部署检查清单和上线建议。"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=[
                "architecture_design", "core_code", "test_code",
                "quality_review", "review_conclusion",
            ],
            priority=6,
        ),
    ]


def run_scenario_auth(
    *,
    llm_model: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> WorkflowResult:
    """
    运行场景 1：用户认证模块开发

    Parameters
    ----------
    llm_model         : 使用的 LLM 模型名称（可选）
    progress_callback : 进度回调 (step_idx, total_steps, step_name)

    Returns
    -------
    WorkflowResult
    """
    logger.info("=" * 60)
    logger.info("场景 1：用户认证模块开发")
    logger.info("=" * 60)

    orch = _build_orchestrator(llm_model=llm_model)
    orch.share("requirement", _AUTH_REQUIREMENT, source="scenario")

    result = orch.run_workflow(
        name="用户认证模块开发",
        steps=_build_auth_steps(),
        initial_context={"requirement": _AUTH_REQUIREMENT},
        progress_callback=progress_callback,
    )

    _print_result(result)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 场景 2：数据处理模块开发
# ──────────────────────────────────────────────────────────────────────────────

_DATA_REQUIREMENT = """
开发一个高性能大规模数据处理系统，支持以下功能：

批处理功能：
1. 从多种数据源读取（CSV、JSON、Parquet、数据库）
2. 数据清洗（去重、缺失值填充、异常值检测）
3. 数据转换（类型转换、字段映射、数据规范化）
4. 数据聚合（分组统计、窗口函数、Join 操作）
5. 结果输出到目标存储（数据仓库、文件系统、API）

流处理功能：
1. 实时数据消费（Kafka 消息队列）
2. 流数据清洗和过滤
3. 实时聚合和告警
4. 低延迟窗口计算

非功能需求：
- 吞吐量：100万条/分钟（批处理）、10万条/秒（流处理）
- 水平扩展：支持分布式部署
- 容错：断点续传、失败重试（最多3次）
- 监控：处理进度、成功率、延迟指标
"""

def _build_data_steps() -> List[WorkflowStep]:
    """构建数据处理场景的工作流步骤"""
    return [
        WorkflowStep(
            agent_id="pm",
            task_title="数据需求分析与规划",
            task_desc=f"分析数据处理模块的需求，制定开发计划。\n\n需求：{_DATA_REQUIREMENT}",
            step_type=StepType.SEQUENTIAL,
            priority=1,
        ),
        WorkflowStep(
            agent_id="architect",
            task_title="数据管道架构设计",
            task_desc=(
                f"设计高性能数据处理管道的架构，包括：批处理引擎选型（Pandas/Spark）、"
                f"流处理方案（Kafka+Faust）、存储层设计、容错机制。\n\n需求：{_DATA_REQUIREMENT}"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["pm_latest"],
            priority=2,
        ),
        WorkflowStep(
            agent_id="developer",
            task_title="核心处理引擎开发",
            task_desc=(
                "实现数据处理管道的核心组件：DataReader（多源读取）、"
                "DataCleaner（清洗）、DataTransformer（转换）、DataAggregator（聚合）、"
                "DataWriter（输出），支持插件化扩展。"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["architecture_design", "tech_stack"],
            priority=3,
        ),
        WorkflowStep(
            agent_id="developer",
            task_title="性能优化与并发控制",
            task_desc=(
                "对已实现的数据处理引擎进行性能优化：\n"
                "1. 向量化操作替换循环\n"
                "2. 内存映射文件处理大文件\n"
                "3. 多进程并行处理\n"
                "4. 连接池和缓存优化\n"
                "5. 背压控制防止内存溢出"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "architecture_design"],
            priority=4,
        ),
        WorkflowStep(
            agent_id="tester",
            task_title="数据质量测试套件",
            task_desc=(
                "设计数据处理模块的测试策略并生成测试代码，重点测试：\n"
                "- 数据清洗的准确性（缺失值、异常值、重复数据）\n"
                "- 大文件处理的内存使用\n"
                "- 并发处理的线程安全性\n"
                "- 故障恢复和断点续传\n"
                "- 输出数据的完整性验证"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "interfaces"],
            priority=5,
        ),
        WorkflowStep(
            agent_id="reviewer",
            task_title="可靠性与容错代码审查",
            task_desc=(
                "审查数据处理模块的代码质量，重点关注：\n"
                "- 资源泄漏（文件句柄、数据库连接、内存）\n"
                "- 异常处理的完整性和合理性\n"
                "- 并发安全和竞争条件\n"
                "- 日志记录和可观测性\n"
                "- 代码的可维护性和可扩展性"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "test_code"],
            priority=6,
        ),
        WorkflowStep(
            agent_id="pm",
            task_title="部署配置与文档整理",
            task_desc=(
                "整合所有开发成果，准备部署：\n"
                "1. 生成部署配置（Docker Compose / K8s）\n"
                "2. 整理 API 文档和使用手册\n"
                "3. 性能基准测试报告\n"
                "4. 运维手册（监控、告警、故障排除）\n"
                "5. 发布说明和变更日志"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=[
                "architecture_design", "core_code",
                "test_code", "review_conclusion",
            ],
            priority=7,
        ),
    ]


def run_scenario_data_pipeline(
    *,
    llm_model: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> WorkflowResult:
    """
    运行场景 2：数据处理模块开发

    Parameters
    ----------
    llm_model         : 使用的 LLM 模型名称（可选）
    progress_callback : 进度回调 (step_idx, total_steps, step_name)

    Returns
    -------
    WorkflowResult
    """
    logger.info("=" * 60)
    logger.info("场景 2：数据处理模块开发")
    logger.info("=" * 60)

    orch = _build_orchestrator(llm_model=llm_model)
    orch.share("requirement", _DATA_REQUIREMENT, source="scenario")

    result = orch.run_workflow(
        name="数据处理模块开发",
        steps=_build_data_steps(),
        initial_context={"requirement": _DATA_REQUIREMENT},
        progress_callback=progress_callback,
    )

    _print_result(result)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 场景 3：REST API 服务开发
# ──────────────────────────────────────────────────────────────────────────────

_API_REQUIREMENT = """
开发一个符合 RESTful 最佳实践的电商商品管理 API 服务，包含：

核心 API 端点：
1. 商品管理：CRUD（分页、排序、过滤、全文搜索）
2. 分类管理：树状结构分类，支持无限层级
3. 库存管理：库存查询、出入库记录、库存告警
4. 图片管理：多图上传、压缩、CDN 分发
5. 价格策略：原价、促销价、会员价、批量定价

API 规范要求：
- 遵循 OpenAPI 3.0 规范，自动生成 Swagger 文档
- JSON API 格式，统一的响应结构
- 版本控制：URL 路径版本（/api/v1/）
- 分页：游标分页（支持大数据量）
- 错误码：标准 HTTP 状态码 + 业务错误码
- 国际化：多语言错误提示

非功能需求：
- 响应时间：P95 < 100ms（列表）、P99 < 50ms（详情）
- QPS：单实例 1000+
- 认证：JWT Bearer Token + API Key 双通道
- 限流：每用户 1000 次/分钟，全局 10000 次/分钟
- 缓存：Redis 缓存热点数据（TTL 5分钟）
"""

def _build_api_steps() -> List[WorkflowStep]:
    """构建 REST API 场景的工作流步骤"""
    return [
        WorkflowStep(
            agent_id="architect",
            task_title="API 规范与服务架构设计",
            task_desc=(
                f"设计电商商品管理 API 的完整架构：\n"
                f"1. API 端点设计（URL 结构、HTTP 方法、请求/响应格式）\n"
                f"2. 数据模型设计（商品、分类、库存的 ER 图）\n"
                f"3. 服务分层架构（路由层→服务层→数据访问层）\n"
                f"4. 中间件栈（认证、限流、缓存、日志）\n"
                f"5. 技术选型（FastAPI + PostgreSQL + Redis）\n\n"
                f"需求：{_API_REQUIREMENT}"
            ),
            step_type=StepType.SEQUENTIAL,
            priority=1,
        ),
        WorkflowStep(
            agent_id="pm",
            task_title="API 开发计划与里程碑",
            task_desc=(
                f"基于架构设计，制定 API 开发计划：\n"
                f"1. 功能优先级排序（MoSCoW 方法）\n"
                f"2. Sprint 计划（每 Sprint 2 周）\n"
                f"3. 团队分工和时间估算\n"
                f"4. API 版本发布计划\n"
                f"需求：{_API_REQUIREMENT}"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["architecture_design", "tech_stack"],
            priority=2,
        ),
        WorkflowStep(
            agent_id="developer",
            task_title="核心 API 端点实现",
            task_desc=(
                "使用 FastAPI 实现商品管理 API 的核心端点：\n"
                "- GET /api/v1/products（列表，支持分页/过滤/排序）\n"
                "- POST /api/v1/products（创建商品）\n"
                "- GET /api/v1/products/{id}（商品详情）\n"
                "- PUT /api/v1/products/{id}（更新商品）\n"
                "- DELETE /api/v1/products/{id}（删除商品）\n"
                "包含 Pydantic 数据验证、SQLAlchemy ORM、统一错误处理。"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["architecture_design", "tech_stack"],
            priority=3,
        ),
        WorkflowStep(
            agent_id="developer",
            task_title="认证中间件与限流集成",
            task_desc=(
                "实现 API 的横切关注点：\n"
                "1. JWT 认证中间件（Bearer Token 验证）\n"
                "2. API Key 认证（用于服务间调用）\n"
                "3. Redis 限流中间件（滑动窗口算法）\n"
                "4. Redis 响应缓存（可配置 TTL）\n"
                "5. 请求日志记录（含 trace_id 追踪）\n"
                "6. CORS 配置和安全头注入"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "architecture_design"],
            priority=4,
        ),
        WorkflowStep(
            agent_id="tester",
            task_title="API 集成测试套件",
            task_desc=(
                "为商品管理 API 编写完整的测试套件：\n"
                "单元测试：\n"
                "- 数据验证（正常/异常输入）\n"
                "- 业务逻辑（价格计算、库存扣减）\n"
                "集成测试：\n"
                "- 完整 CRUD 流程\n"
                "- 分页和过滤功能\n"
                "- 认证和权限测试\n"
                "- 限流测试（超限触发 429）\n"
                "性能测试：使用 locust 描述压测方案"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "interfaces"],
            priority=5,
        ),
        WorkflowStep(
            agent_id="reviewer",
            task_title="API 安全性与性能审查",
            task_desc=(
                "对 API 服务进行全面审查：\n"
                "安全审查：\n"
                "- API 认证绕过风险\n"
                "- SQL 注入和参数污染\n"
                "- 敏感数据暴露（商品成本、用户信息）\n"
                "- 速率限制绕过\n"
                "性能审查：\n"
                "- N+1 查询问题\n"
                "- 缺少索引的查询\n"
                "- 无效的缓存使用\n"
                "- 大响应体优化"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=["core_code", "test_code", "architecture_design"],
            priority=6,
        ),
        WorkflowStep(
            agent_id="pm",
            task_title="API 文档与部署准备",
            task_desc=(
                "完成 API 发布前的准备工作：\n"
                "1. OpenAPI 文档完整性检查\n"
                "2. Postman Collection 导出\n"
                "3. Docker 镜像打包配置\n"
                "4. 环境变量和配置管理\n"
                "5. 数据库迁移脚本\n"
                "6. API 变更日志和版本说明\n"
                "7. SLA 和监控告警配置"
            ),
            step_type=StepType.SEQUENTIAL,
            context_keys=[
                "architecture_design", "core_code",
                "test_code", "review_conclusion",
            ],
            priority=7,
        ),
    ]


def run_scenario_rest_api(
    *,
    llm_model: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> WorkflowResult:
    """
    运行场景 3：REST API 服务开发

    Parameters
    ----------
    llm_model         : 使用的 LLM 模型名称（可选）
    progress_callback : 进度回调 (step_idx, total_steps, step_name)

    Returns
    -------
    WorkflowResult
    """
    logger.info("=" * 60)
    logger.info("场景 3：REST API 服务开发")
    logger.info("=" * 60)

    orch = _build_orchestrator(llm_model=llm_model)
    orch.share("requirement", _API_REQUIREMENT, source="scenario")

    result = orch.run_workflow(
        name="REST API 服务开发",
        steps=_build_api_steps(),
        initial_context={"requirement": _API_REQUIREMENT},
        progress_callback=progress_callback,
    )

    _print_result(result)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────────────────────────────────────

def _print_result(result: WorkflowResult) -> None:
    """格式化打印工作流结果"""
    print("\n" + "=" * 70)
    print(result.get_summary())
    print("=" * 70)
    if result.error:
        print(f"错误信息: {result.error}")


def run_all_scenarios(
    *,
    llm_model: Optional[str] = None,
    scenario_ids: Optional[List[str]] = None,
) -> Dict[str, WorkflowResult]:
    """
    运行所有（或指定的）软件开发场景

    Parameters
    ----------
    llm_model    : LLM 模型名称（可选）
    scenario_ids : 要运行的场景 ID 列表；None 表示运行全部

    Returns
    -------
    dict mapping scenario_id -> WorkflowResult
    """
    runners = {
        "auth_module": run_scenario_auth,
        "data_pipeline": run_scenario_data_pipeline,
        "rest_api": run_scenario_rest_api,
    }

    ids_to_run = scenario_ids or list(runners.keys())
    results: Dict[str, WorkflowResult] = {}

    total = len(ids_to_run)
    for i, sid in enumerate(ids_to_run, 1):
        if sid not in runners:
            logger.warning("未知场景 ID: %s，跳过", sid)
            continue

        print(f"\n{'─' * 70}")
        print(f"[{i}/{total}] 开始运行场景: {sid}")
        print("─" * 70)

        start = time.time()
        results[sid] = runners[sid](llm_model=llm_model)
        elapsed = time.time() - start

        status = "✅ 成功" if results[sid].success else "❌ 失败"
        print(f"[{i}/{total}] 场景 {sid} {status}，耗时 {elapsed:.1f}s\n")

    # 汇总报告
    print("\n" + "=" * 70)
    print("【所有场景执行汇总】")
    print("=" * 70)
    success_count = sum(1 for r in results.values() if r.success)
    print(f"成功：{success_count}/{len(results)}")
    for sid, res in results.items():
        icon = "✅" if res.success else "❌"
        meta = next((m for m in SCENARIOS_META if m["id"] == sid), {})
        name = meta.get("name", sid)
        print(f"  {icon} {name} — {res.duration:.1f}s")
    print("=" * 70)

    return results


def get_scenario_meta(scenario_id: str) -> Optional[Dict[str, Any]]:
    """根据 ID 获取场景元数据"""
    return next((m for m in SCENARIOS_META if m["id"] == scenario_id), None)


# ──────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="多智能体软件开发框架 — 场景执行入口"
    )
    parser.add_argument(
        "--scenario",
        choices=["auth_module", "data_pipeline", "rest_api", "all"],
        default="all",
        help="要运行的场景（默认：all）",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM 模型名称（如 gpt-4o-mini、deepseek-chat）",
    )
    args = parser.parse_args()

    if args.scenario == "all":
        run_all_scenarios(llm_model=args.model)
    else:
        runner_map = {
            "auth_module": run_scenario_auth,
            "data_pipeline": run_scenario_data_pipeline,
            "rest_api": run_scenario_rest_api,
        }
        runner_map[args.scenario](llm_model=args.model)

