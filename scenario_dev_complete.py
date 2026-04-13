#!/usr/bin/env python3
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

import sys
import os
import json
from datetime import datetime

# 将项目根目录加入 sys.path，确保可以导入 devops_crew
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from devops_crew.core.agent_base import Task
from devops_crew.core.orchestrator import Orchestrator, Workflow, WorkflowStep
from devops_crew.agents.dev_agents import (
    ArchitectAgent,
    DeveloperAgent,
    TestEngineerAgent,
    CodeReviewerAgent,
    ProjectManagerAgent,
)


# ──────────────────────────────────────────────
# 辅助：构建并注册了所有 5 个智能体的 Orchestrator
# ──────────────────────────────────────────────

def _build_orchestrator() -> Orchestrator:
    """创建并返回注册了全部 5 个开发智能体的协调器"""
    orch = Orchestrator()
    orch.register_agent(ArchitectAgent())
    orch.register_agent(DeveloperAgent())
    orch.register_agent(TestEngineerAgent())
    orch.register_agent(CodeReviewerAgent())
    orch.register_agent(ProjectManagerAgent())
    return orch


def _print_progress(step_idx: int, total: int, agent_name: str, message: str) -> None:
    """简单的终端进度回调"""
    bar_len = 30
    filled = int(bar_len * step_idx / total)
    bar = '█' * filled + '░' * (bar_len - filled)
    pct = int(step_idx / total * 100)
    print(f'  [{bar}] {pct:3d}%  {message}')


def _print_report(report: dict) -> None:
    """将报告关键信息打印到终端"""
    sep = '=' * 70
    print(f'\n{sep}')
    print(f'  工作流: {report["workflow_name"]}')
    print(f'  状态  : {report["status"]}')
    print(f'  耗时  : {report["duration_seconds"]} 秒')
    print(f'  步骤  : {report["completed_steps"]}/{report["total_steps"]} 完成')
    print(f'  消息数: {report["communication_count"]} 条通信记录')
    print(f'{sep}')
    print('\n【综合总结】')
    summary = report.get('final_summary', '')
    print(summary[:800] if len(summary) > 800 else summary)
    print(f'\n{sep}\n')


# ──────────────────────────────────────────────
# 场景 1：用户认证模块开发（5 步）
# ──────────────────────────────────────────────

def scenario_1_user_authentication() -> dict:
    """
    用户认证模块开发 — 5 步完整流程：
      架构师设计 → 开发实现 → 测试生成 → 代码审查 → 开发优化
    """
    print('\n' + '─' * 70)
    print('  场景 1：用户认证模块开发')
    print('  描述：设计并实现一个安全的用户认证系统（JWT + bcrypt）')
    print('─' * 70)

    orch = _build_orchestrator()

    workflow = Workflow(
        workflow_id='wf-auth-001',
        name='用户认证模块开发',
        description=(
            '开发一个完整的用户认证模块，包括用户注册、登录、JWT Token 颁发、'
            'Token 刷新和权限校验功能。要求使用 bcrypt 加密密码，'
            'JWT 有效期 24 小时，支持 Refresh Token 机制。'
        ),
    )

    workflow.add_step(WorkflowStep(
        step_id='s1-arch',
        agent_id='architect_agent',
        task_type='architecture_design',
        description=(
            '设计用户认证模块的系统架构：\n'
            '- 定义认证流程（注册→登录→Token 颁发→刷新→权限校验）\n'
            '- 设计数据模型（User 表、Token 表）\n'
            '- 规划 API 端点（POST /register, POST /login, POST /refresh, GET /profile）\n'
            '- 选择技术栈（Flask + SQLAlchemy + PyJWT + bcrypt）'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s2-dev',
        agent_id='developer_agent',
        task_type='code_implementation',
        description=(
            '实现用户认证模块的核心代码：\n'
            '- User 模型（id, username, email, password_hash, created_at）\n'
            '- 密码加密（bcrypt.hashpw / bcrypt.checkpw）\n'
            '- JWT 生成与验证（PyJWT，HS256 算法）\n'
            '- 注册、登录、刷新 Token 的业务逻辑\n'
            '- 认证装饰器 @require_auth'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s3-test',
        agent_id='test_engineer_agent',
        task_type='test_design',
        description=(
            '为用户认证模块编写测试用例：\n'
            '- 测试用户注册（正常、邮箱重复、密码格式错误）\n'
            '- 测试登录（正确密码、错误密码、不存在的用户）\n'
            '- 测试 JWT 验证（有效 Token、过期 Token、伪造 Token）\n'
            '- 测试权限装饰器（有 Token、无 Token、权限不足）'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s4-review',
        agent_id='code_reviewer_agent',
        task_type='code_review',
        description=(
            '审查用户认证模块代码：\n'
            '- 检查密码存储安全性（不能明文、bcrypt cost factor）\n'
            '- 检查 JWT Secret Key 管理（不能硬编码、应从环境变量读取）\n'
            '- 检查 SQL 注入防护（使用 ORM 参数化查询）\n'
            '- 检查输入校验（email 格式、密码长度、用户名规则）\n'
            '- 检查错误响应是否泄露敏感信息'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s5-optimize',
        agent_id='developer_agent',
        task_type='code_optimization',
        description=(
            '根据代码审查意见优化认证模块：\n'
            '- 修复所有安全问题\n'
            '- 添加速率限制（防暴力破解）\n'
            '- 添加登录失败计数器（连续 5 次失败锁定账户）\n'
            '- 完善错误处理和日志记录\n'
            '- 优化数据库查询性能（添加索引）'
        ),
    ))

    report = orch.execute_workflow(workflow, progress_callback=_print_progress)
    _print_report(report)
    return report


# ──────────────────────────────────────────────
# 场景 2：数据处理模块开发（4 步）
# ──────────────────────────────────────────────

def scenario_2_data_processing() -> dict:
    """
    数据处理模块开发 — 4 步流程：
      架构师设计 → 开发实现 → 测试生成 → 代码审查
    """
    print('\n' + '─' * 70)
    print('  场景 2：数据处理模块开发')
    print('  描述：构建高性能数据清洗、转换和聚合管道')
    print('─' * 70)

    orch = _build_orchestrator()

    workflow = Workflow(
        workflow_id='wf-data-001',
        name='数据处理模块开发',
        description=(
            '开发一个通用数据处理模块，支持 CSV/JSON/Excel 数据导入，'
            '提供数据清洗（去重、缺失值处理、格式校正）、'
            '数据转换（类型转换、字段映射、标准化）和'
            '数据聚合（分组统计、时间序列汇总）功能，'
            '并支持将结果导出为多种格式。'
        ),
    )

    workflow.add_step(WorkflowStep(
        step_id='s1-arch',
        agent_id='architect_agent',
        task_type='architecture_design',
        description=(
            '设计数据处理模块架构：\n'
            '- 管道模式（Pipeline Pattern）设计\n'
            '- DataSource 抽象层（CSV/JSON/Excel 适配器）\n'
            '- Transformer 接口与内置转换器\n'
            '- Aggregator 接口与内置聚合器\n'
            '- DataSink 输出层设计'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s2-dev',
        agent_id='developer_agent',
        task_type='code_implementation',
        description=(
            '实现数据处理模块：\n'
            '- DataPipeline 核心类（链式调用 API）\n'
            '- CsvReader / JsonReader / ExcelReader\n'
            '- DeduplicationTransformer（去重）\n'
            '- NullFillerTransformer（缺失值填充）\n'
            '- TypeCastTransformer（类型转换）\n'
            '- GroupByAggregator（分组聚合）\n'
            '- 使用 pandas 作为底层计算引擎'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s3-test',
        agent_id='test_engineer_agent',
        task_type='test_design',
        description=(
            '编写数据处理模块的测试：\n'
            '- 测试各 Reader 对不同格式文件的读取\n'
            '- 测试去重逻辑（完全重复行、部分字段重复）\n'
            '- 测试缺失值处理（均值填充、中位数填充、删除行）\n'
            '- 测试分组聚合的准确性\n'
            '- 测试大数据量下的性能（10 万行以内 < 5 秒）'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s4-review',
        agent_id='code_reviewer_agent',
        task_type='code_review',
        description=(
            '审查数据处理模块代码：\n'
            '- 检查内存管理（大文件是否使用分块读取）\n'
            '- 检查错误处理（文件不存在、格式错误、编码问题）\n'
            '- 检查 API 设计的一致性和易用性\n'
            '- 检查是否有数据泄漏风险（日志中打印敏感字段）\n'
            '- 评估代码的可扩展性（添加新格式支持的难度）'
        ),
    ))

    report = orch.execute_workflow(workflow, progress_callback=_print_progress)
    _print_report(report)
    return report


# ──────────────────────────────────────────────
# 场景 3：REST API 服务开发（4 步）
# ──────────────────────────────────────────────

def scenario_3_api_service() -> dict:
    """
    REST API 服务开发 — 4 步流程：
      架构师设计 → 开发实现 → 测试生成 → 代码审查
    """
    print('\n' + '─' * 70)
    print('  场景 3：REST API 服务开发')
    print('  描述：设计并实现一个符合 RESTful 规范的 API 服务')
    print('─' * 70)

    orch = _build_orchestrator()

    workflow = Workflow(
        workflow_id='wf-api-001',
        name='REST API 服务开发',
        description=(
            '开发一个商品管理 REST API 服务，提供完整的 CRUD 操作，'
            '支持分页查询、排序、过滤，包含请求参数校验、统一错误响应格式、'
            'API 版本控制（/api/v1/）、OpenAPI 文档自动生成，'
            '并实现 JWT 认证保护敏感端点。'
        ),
    )

    workflow.add_step(WorkflowStep(
        step_id='s1-arch',
        agent_id='architect_agent',
        task_type='api_design',
        description=(
            '设计 REST API 服务架构：\n'
            '- 定义资源模型（Product: id, name, price, category, stock, created_at）\n'
            '- 设计 API 端点（GET/POST /products, GET/PUT/DELETE /products/{id}）\n'
            '- 规划请求/响应格式（统一 JSON 包装）\n'
            '- 设计错误码体系（4xx 客户端错误、5xx 服务端错误）\n'
            '- 规划中间件栈（认证、限流、CORS、日志）'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s2-dev',
        agent_id='developer_agent',
        task_type='code_implementation',
        description=(
            '实现 REST API 服务：\n'
            '- Flask 应用工厂模式\n'
            '- Product 模型与 SQLAlchemy ORM\n'
            '- Blueprint 路由注册（/api/v1/products）\n'
            '- 请求校验（marshmallow 或 pydantic）\n'
            '- 分页实现（page、per_page 参数，返回 total_count）\n'
            '- 统一响应格式（{"success": true, "data": {...}, "message": ""}）'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s3-test',
        agent_id='test_engineer_agent',
        task_type='integration_test',
        description=(
            '编写 REST API 集成测试：\n'
            '- 测试完整 CRUD 流程（创建→查询→更新→删除）\n'
            '- 测试分页查询（第一页、最后一页、超出范围）\n'
            '- 测试参数校验（必填项缺失、类型错误、格式非法）\n'
            '- 测试认证保护（无 Token 返回 401、无权限返回 403）\n'
            '- 测试并发访问的数据一致性'
        ),
    ))

    workflow.add_step(WorkflowStep(
        step_id='s4-review',
        agent_id='code_reviewer_agent',
        task_type='code_review',
        description=(
            '审查 REST API 代码：\n'
            '- 检查 RESTful 规范符合度（动词使用、状态码正确性）\n'
            '- 检查 SQL 注入防护（ORM 参数化）\n'
            '- 检查批量查询的 N+1 问题\n'
            '- 检查响应数据是否包含不必要的敏感字段\n'
            '- 评估 API 版本控制策略的扩展性'
        ),
    ))

    report = orch.execute_workflow(workflow, progress_callback=_print_progress)
    _print_report(report)
    return report


# ──────────────────────────────────────────────
# 主入口：依次运行全部 3 个场景
# ──────────────────────────────────────────────

def main() -> None:
    start = datetime.now()
    print('\n' + '═' * 70)
    print('  多智能体软件开发框架 — 完整场景演示')
    print(f'  启动时间: {start.strftime("%Y-%m-%d %H:%M:%S")}')
    print('═' * 70)

    all_reports = []

    report1 = scenario_1_user_authentication()
    all_reports.append(report1)

    report2 = scenario_2_data_processing()
    all_reports.append(report2)

    report3 = scenario_3_api_service()
    all_reports.append(report3)

    # 汇总
    total_duration = sum(r['duration_seconds'] for r in all_reports)
    total_steps = sum(r['total_steps'] for r in all_reports)
    completed_steps = sum(r['completed_steps'] for r in all_reports)
    total_messages = sum(r['communication_count'] for r in all_reports)

    print('\n' + '═' * 70)
    print('  全部场景执行完毕！')
    print(f'  总耗时    : {total_duration:.1f} 秒')
    print(f'  完成步骤  : {completed_steps}/{total_steps}')
    print(f'  通信记录  : {total_messages} 条')
    print('═' * 70 + '\n')

    # 可选：保存报告
    report_path = os.path.join(_ROOT, 'dev_scenario_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_reports, f, ensure_ascii=False, indent=2)
    print(f'  📄 完整报告已保存至: {report_path}')


if __name__ == '__main__':
    main()
