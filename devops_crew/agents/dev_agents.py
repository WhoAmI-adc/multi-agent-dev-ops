#!/usr/bin/env python3
"""
devops_crew.agents.dev_agents
------------------------------
5 个专业化软件开发智能体，全部继承自 BaseAgent。

智能体列表：
  - ArchitectAgent      架构师：负责系统设计与技术选型
  - DeveloperAgent      开发工程师：负责代码实现
  - TestEngineerAgent   测试工程师：负责测试设计与执行
  - CodeReviewerAgent   代码审查官：负责代码审查与质量保证
  - ProjectManagerAgent 项目经理：负责任务协调与进度管理
"""

from __future__ import annotations

from devops_crew.core.agent_base import BaseAgent, Task


# ──────────────────────────────────────────────────────────────────
# 1. 架构师
# ──────────────────────────────────────────────────────────────────

class ArchitectAgent(BaseAgent):
    """
    架构师智能体
    职责：分析需求、设计系统架构、制定技术规范。
    """
    agent_id = 'architect_agent'
    name = '架构师'
    role = '系统设计与技术选型'
    system_prompt = (
        '你是一名经验丰富的软件架构师，专注于系统设计、架构规划和技术选型。'
        '你的职责是分析业务需求，设计可扩展、高可用、易维护的系统架构，'
        '并制定清晰的技术规范供团队成员遵循。'
        '请用中文回答，输出要简洁专业，重点突出架构决策和技术理由。'
    )

    def think(self, context: str) -> str:
        """架构师专注于系统整体设计视角"""
        enhanced = (
            f"从架构师视角分析以下需求：\n{context}\n\n"
            '请思考：\n'
            '1. 核心功能模块有哪些？\n'
            '2. 模块间的依赖关系如何？\n'
            '3. 推荐的技术栈是什么？\n'
            '4. 需要注意哪些非功能性需求（性能、安全、扩展性）？'
        )
        from devops_crew.core.agent_base import _call_claude
        return _call_claude(self.system_prompt, enhanced)

    def plan(self, task: Task, thinking: str) -> list[str]:
        """架构师的计划侧重于设计文档产出"""
        return [
            '分析业务需求与技术约束',
            '设计系统整体架构（分层架构 / 微服务 / 模块化）',
            '定义核心接口与数据模型',
            '制定技术规范与开发标准',
            '输出架构设计文档',
        ]


# ──────────────────────────────────────────────────────────────────
# 2. 开发工程师
# ──────────────────────────────────────────────────────────────────

class DeveloperAgent(BaseAgent):
    """
    开发工程师智能体
    职责：根据架构设计实现代码，包括业务逻辑、API 和数据访问层。
    """
    agent_id = 'developer_agent'
    name = '开发工程师'
    role = '代码实现与功能开发'
    system_prompt = (
        '你是一名全栈开发工程师，擅长 Python、RESTful API、数据库设计和前端开发。'
        '你的职责是根据架构设计实现高质量的代码，遵循 SOLID 原则，'
        '确保代码可读性、可测试性和可维护性。'
        '请用中文回答，代码示例用 Python，要有完整的错误处理和注释。'
    )

    def think(self, context: str) -> str:
        """开发工程师从实现可行性角度分析"""
        enhanced = (
            f"从开发工程师视角分析以下任务：\n{context}\n\n"
            '请思考：\n'
            '1. 需要实现哪些核心类和函数？\n'
            '2. 数据流是怎样的？\n'
            '3. 哪些地方需要特别的错误处理？\n'
            '4. 如何保证代码的可测试性？'
        )
        from devops_crew.core.agent_base import _call_claude
        return _call_claude(self.system_prompt, enhanced)

    def plan(self, task: Task, thinking: str) -> list[str]:
        """开发工程师的计划侧重于代码实现步骤"""
        return [
            '搭建项目结构与环境配置',
            '实现数据模型与数据库操作层',
            '实现业务逻辑层（核心功能）',
            '实现 API 接口层（路由与控制器）',
            '添加日志、错误处理与文档注释',
        ]


# ──────────────────────────────────────────────────────────────────
# 3. 测试工程师
# ──────────────────────────────────────────────────────────────────

class TestEngineerAgent(BaseAgent):
    """
    测试工程师智能体
    职责：设计测试方案，编写单元测试、集成测试，并执行测试验证。
    """
    agent_id = 'test_engineer_agent'
    name = '测试工程师'
    role = '测试设计与质量保证'
    system_prompt = (
        '你是一名资深测试工程师，精通测试策略设计、自动化测试和 TDD/BDD 方法论。'
        '你的职责是设计全面的测试方案，编写高覆盖率的测试用例，'
        '识别边界条件和潜在的 Bug，确保系统质量。'
        '请用中文回答，测试用例用 pytest 格式，要覆盖正向、负向和边界场景。'
    )

    def think(self, context: str) -> str:
        """测试工程师从质量保证角度分析"""
        enhanced = (
            f"从测试工程师视角分析：\n{context}\n\n"
            '请思考：\n'
            '1. 需要测试哪些核心功能点？\n'
            '2. 有哪些边界条件和异常场景？\n'
            '3. 需要 Mock 哪些外部依赖？\n'
            '4. 如何衡量测试覆盖率是否充分？'
        )
        from devops_crew.core.agent_base import _call_claude
        return _call_claude(self.system_prompt, enhanced)

    def plan(self, task: Task, thinking: str) -> list[str]:
        """测试工程师的计划侧重于测试策略与用例"""
        return [
            '分析测试范围与风险区域',
            '编写单元测试用例（正向 + 异常 + 边界）',
            '编写集成测试用例',
            '配置测试环境与 Mock 数据',
            '生成测试覆盖率报告',
        ]


# ──────────────────────────────────────────────────────────────────
# 4. 代码审查官
# ──────────────────────────────────────────────────────────────────

class CodeReviewerAgent(BaseAgent):
    """
    代码审查官智能体
    职责：对代码进行全面审查，识别问题，提出改进建议。
    """
    agent_id = 'code_reviewer_agent'
    name = '代码审查官'
    role = '代码审查与质量把控'
    system_prompt = (
        '你是一名代码审查专家，具备深厚的软件工程经验和对代码质量的严格标准。'
        '你的职责是审查代码实现，识别安全漏洞、性能问题、代码异味和可维护性问题，'
        '并提出具体可行的改进建议。'
        '请用中文回答，审查意见要具体到代码层面，改进建议要可操作。'
    )

    def think(self, context: str) -> str:
        """代码审查官从代码质量角度审视"""
        enhanced = (
            f"作为代码审查官，审视以下内容：\n{context}\n\n"
            '请从以下维度进行分析：\n'
            '1. 代码规范性（命名、注释、格式）\n'
            '2. 安全性（SQL 注入、XSS、认证漏洞）\n'
            '3. 性能（算法复杂度、数据库查询优化）\n'
            '4. 可维护性（模块化、耦合度、SOLID 原则）\n'
            '5. 错误处理完整性'
        )
        from devops_crew.core.agent_base import _call_claude
        return _call_claude(self.system_prompt, enhanced)

    def plan(self, task: Task, thinking: str) -> list[str]:
        """代码审查官的计划侧重于系统性审查"""
        return [
            '审查代码结构与架构合规性',
            '检查安全漏洞与潜在风险',
            '分析性能瓶颈与优化机会',
            '评估代码可读性与可维护性',
            '输出审查报告与改进建议清单',
        ]


# ──────────────────────────────────────────────────────────────────
# 5. 项目经理
# ──────────────────────────────────────────────────────────────────

class ProjectManagerAgent(BaseAgent):
    """
    项目经理智能体
    职责：协调团队任务、跟踪项目进度、汇总成果并生成报告。
    """
    agent_id = 'project_manager_agent'
    name = '项目经理'
    role = '任务协调与进度管理'
    system_prompt = (
        '你是一名经验丰富的项目经理，擅长敏捷开发、项目规划和团队协调。'
        '你的职责是分解项目任务、分配工作、跟踪进度、识别风险，'
        '并确保项目按时高质量交付。'
        '请用中文回答，输出要包含任务列表、时间线和风险评估。'
    )

    def think(self, context: str) -> str:
        """项目经理从项目管理角度分析"""
        enhanced = (
            f"作为项目经理，分析以下项目需求：\n{context}\n\n"
            '请思考：\n'
            '1. 项目可以拆分为哪些子任务？\n'
            '2. 各任务的依赖关系是什么？\n'
            '3. 预计各任务的工作量？\n'
            '4. 主要风险点在哪里，如何应对？'
        )
        from devops_crew.core.agent_base import _call_claude
        return _call_claude(self.system_prompt, enhanced)

    def plan(self, task: Task, thinking: str) -> list[str]:
        """项目经理的计划侧重于项目管理流程"""
        return [
            '拆解项目任务并制定优先级',
            '分配任务给对应专业角色',
            '跟踪任务执行进度与质量',
            '识别和处理阻塞性问题',
            '汇总成果并生成项目报告',
        ]

    def coordinate(self, task_description: str, team_results: dict[str, str]) -> str:
        """
        协调功能：综合各智能体的执行结果，输出项目汇总报告。

        Args:
            task_description: 项目整体描述
            team_results:      dict {agent_name: result_text}

        Returns:
            综合项目报告
        """
        results_text = '\n\n'.join(
            f'【{agent}】:\n{result[:300]}' for agent, result in team_results.items()
        )
        from devops_crew.core.agent_base import _call_claude
        prompt = (
            f"项目：{task_description}\n\n"
            f"各成员完成情况：\n{results_text}\n\n"
            '请生成项目完成汇总报告，包含：\n'
            '1. 项目完成情况概述\n'
            '2. 各角色贡献摘要\n'
            '3. 主要成果与产出\n'
            '4. 后续建议'
        )
        return _call_claude(self.system_prompt, prompt)
