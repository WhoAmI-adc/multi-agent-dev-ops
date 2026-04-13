"""
5个软件开发专业化智能体实现

每个智能体继承 AgentBase，实现专属的 execute() 方法，
在执行阶段调用 LLM 完成与自身角色对应的专业任务。
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

import json
import logging
import time
from typing import Any, Dict, List, Optional

from devops_crew.core.agent_base import AgentBase, AgentTask, CommunicationBus, _call_llm

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 1. 架构师智能体
# ──────────────────────────────────────────────────────────────────────────────

class ArchitectAgent(AgentBase):
    """
    架构师智能体

    职责：
    - 分析业务需求，确定系统边界
    - 制定整体技术架构（分层、微服务、数据流）
    - 选择合适的技术栈和框架
    - 输出架构文档和组件关系图（文本描述）
    """

    def __init__(
        self,
        bus: Optional[CommunicationBus] = None,
        llm_model: Optional[str] = None,
    ):
        super().__init__(
            agent_id="architect",
            name="架构师",
            role="软件架构师",
            goal="设计高质量、可扩展、安全的系统架构，为整个开发团队提供清晰的技术路线图",
            backstory=(
                "拥有 10 年以上系统设计经验，精通微服务、DDD、CQRS 等架构模式，"
                "擅长在业务需求、技术可行性和团队能力之间找到最佳平衡点。"
            ),
            bus=bus,
            llm_model=llm_model,
        )

    def execute(
        self,
        task: AgentTask,
        thought: str,
        plan: List[str],
    ) -> Dict[str, Any]:
        """执行架构设计：分析需求 → 设计架构 → 选型 → 输出文档"""
        context = task.context
        requirement = context.get("requirement", task.description)

        # ── 需求分析 ──────────────────────────────────────────────────────────
        analysis_prompt = (
            f"作为软件架构师，分析以下需求：\n\n{requirement}\n\n"
            f"请输出：\n"
            f"1. 核心功能边界（3-5条）\n"
            f"2. 质量属性要求（性能、安全性、可用性）\n"
            f"3. 技术约束和假设条件"
        )
        analysis = _call_llm(analysis_prompt, model=self.llm_model)
        self.memory.remember("requirement_analysis", analysis, source=task.id)

        # ── 架构设计 ──────────────────────────────────────────────────────────
        arch_prompt = (
            f"基于需求分析：\n{analysis}\n\n"
            f"请设计系统架构，包含：\n"
            f"1. 整体架构风格（分层/微服务/事件驱动）\n"
            f"2. 核心组件及职责（列出组件名称和功能）\n"
            f"3. 组件间交互关系和数据流\n"
            f"4. 数据存储方案（数据库选型和模型设计）\n"
            f"5. 接口设计原则（REST/GraphQL/gRPC）"
        )
        architecture = _call_llm(arch_prompt, model=self.llm_model)
        self.memory.store("architecture_design", architecture)

        # ── 技术选型 ──────────────────────────────────────────────────────────
        tech_prompt = (
            f"基于架构设计：\n{architecture}\n\n"
            f"请进行技术选型，给出：\n"
            f"1. 后端语言和框架（带版本）\n"
            f"2. 数据库（主数据库 + 缓存）\n"
            f"3. 消息队列（如需要）\n"
            f"4. 容器化和部署方案\n"
            f"5. 主要第三方库和工具\n"
            f"每项给出选型理由（1-2句话）。"
        )
        tech_stack = _call_llm(tech_prompt, model=self.llm_model)
        self.memory.store("tech_stack", tech_stack)

        # ── 组合输出 ──────────────────────────────────────────────────────────
        full_output = (
            f"# 架构设计报告\n\n"
            f"## 需求分析\n{analysis}\n\n"
            f"## 系统架构\n{architecture}\n\n"
            f"## 技术选型\n{tech_stack}"
        )

        # 通知其他智能体架构已确认
        self.broadcast("architecture_ready", {
            "architecture": architecture,
            "tech_stack": tech_stack,
        })

        return {
            "output": full_output,
            "artifacts": {
                "requirement_analysis": analysis,
                "architecture_design": architecture,
                "tech_stack": tech_stack,
            },
        }


# ──────────────────────────────────────────────────────────────────────────────
# 2. 开发工程师智能体
# ──────────────────────────────────────────────────────────────────────────────

class DeveloperAgent(AgentBase):
    """
    开发工程师智能体

    职责：
    - 根据架构设计实现核心功能代码
    - 遵循代码规范和最佳实践
    - 编写清晰的注释和文档
    - 实现单元可测试的模块化代码
    """

    def __init__(
        self,
        bus: Optional[CommunicationBus] = None,
        llm_model: Optional[str] = None,
    ):
        super().__init__(
            agent_id="developer",
            name="开发工程师",
            role="高级软件工程师",
            goal="实现高质量、可维护、符合架构设计的功能代码，遵循 SOLID 原则和编码规范",
            backstory=(
                "全栈开发工程师，精通 Python、TypeScript、Java 等语言，"
                "对代码质量有强烈追求，注重可读性、可测试性和性能优化。"
            ),
            bus=bus,
            llm_model=llm_model,
        )

    def execute(
        self,
        task: AgentTask,
        thought: str,
        plan: List[str],
    ) -> Dict[str, Any]:
        """执行代码开发：设计接口 → 实现核心逻辑 → 添加错误处理 → 代码优化"""
        context = task.context
        requirement = context.get("requirement", task.description)
        architecture = context.get("architecture_design", "")
        tech_stack = context.get("tech_stack", "Python/FastAPI")

        # ── 接口设计 ──────────────────────────────────────────────────────────
        interface_prompt = (
            f"作为开发工程师，基于需求：\n{requirement}\n"
            f"架构：{architecture[:400] if architecture else '标准分层架构'}\n\n"
            f"请设计核心接口和类（只输出接口定义，不实现）：\n"
            f"1. 主要类和方法签名\n"
            f"2. 数据模型（字段和类型）\n"
            f"3. 关键接口契约（输入/输出）"
        )
        interfaces = _call_llm(interface_prompt, model=self.llm_model)
        self.memory.remember("interfaces", interfaces, source=task.id)

        # ── 核心代码实现 ──────────────────────────────────────────────────────
        impl_prompt = (
            f"基于接口设计：\n{interfaces}\n\n"
            f"使用 {tech_stack} 实现核心功能代码。\n"
            f"要求：\n"
            f"- 完整的类和方法实现（Python 代码块）\n"
            f"- 适当的类型注解\n"
            f"- 异常处理\n"
            f"- 关键步骤注释\n"
            f"- 遵循 SOLID 原则"
        )
        core_code = _call_llm(impl_prompt, model=self.llm_model)
        self.memory.store("core_implementation", core_code)

        # ── 优化建议 ──────────────────────────────────────────────────────────
        opt_prompt = (
            f"审视以下代码实现：\n{core_code[:600]}\n\n"
            f"请给出 3-5 条性能优化和代码质量改进建议（简短，每条 1-2 句）。"
        )
        optimizations = _call_llm(opt_prompt, model=self.llm_model)
        self.memory.store("optimizations", optimizations)

        full_output = (
            f"# 代码实现报告\n\n"
            f"## 接口设计\n{interfaces}\n\n"
            f"## 核心代码\n{core_code}\n\n"
            f"## 优化建议\n{optimizations}"
        )

        # 通知代码已完成
        self.broadcast("code_ready", {
            "interfaces": interfaces,
            "core_code": core_code,
        })

        return {
            "output": full_output,
            "artifacts": {
                "interfaces": interfaces,
                "core_code": core_code,
                "optimizations": optimizations,
            },
        }


# ──────────────────────────────────────────────────────────────────────────────
# 3. 测试工程师智能体
# ──────────────────────────────────────────────────────────────────────────────

class TesterAgent(AgentBase):
    """
    测试工程师智能体

    职责：
    - 分析代码并设计测试策略
    - 生成单元测试和集成测试用例
    - 评估测试覆盖率和质量
    - 识别边界条件和潜在缺陷
    """

    def __init__(
        self,
        bus: Optional[CommunicationBus] = None,
        llm_model: Optional[str] = None,
    ):
        super().__init__(
            agent_id="tester",
            name="测试工程师",
            role="高级测试工程师",
            goal="确保代码质量，通过全面的测试覆盖识别缺陷，达到 85% 以上的代码覆盖率",
            backstory=(
                "测试驱动开发（TDD）的倡导者，熟练使用 pytest、Jest、JUnit 等测试框架，"
                "擅长边界条件分析、等价类划分和变异测试。"
            ),
            bus=bus,
            llm_model=llm_model,
        )

    def execute(
        self,
        task: AgentTask,
        thought: str,
        plan: List[str],
    ) -> Dict[str, Any]:
        """执行测试：分析代码 → 设计用例 → 生成测试代码 → 评估覆盖率"""
        context = task.context
        core_code = context.get("core_code", context.get("developer_output", ""))
        requirement = context.get("requirement", task.description)

        # ── 测试策略设计 ──────────────────────────────────────────────────────
        strategy_prompt = (
            f"作为测试工程师，基于以下代码/需求分析测试策略：\n\n"
            f"需求：{requirement}\n"
            f"代码摘要：{core_code[:500] if core_code else '待测试的软件模块'}\n\n"
            f"请输出测试策略：\n"
            f"1. 测试类型（单元/集成/端对端）及优先级\n"
            f"2. 测试边界条件（正常路径 + 异常路径）\n"
            f"3. 模拟对象（Mock）需求\n"
            f"4. 预期覆盖率目标"
        )
        strategy = _call_llm(strategy_prompt, model=self.llm_model)
        self.memory.remember("test_strategy", strategy, source=task.id)

        # ── 测试用例生成 ──────────────────────────────────────────────────────
        testcase_prompt = (
            f"基于测试策略：\n{strategy}\n\n"
            f"用 pytest 生成完整的单元测试代码，包含：\n"
            f"- 正常流程测试（至少 3 个）\n"
            f"- 异常处理测试（至少 2 个）\n"
            f"- 边界条件测试（至少 2 个）\n"
            f"使用 fixtures、parametrize 等 pytest 特性，添加 docstring 说明用例目的。"
        )
        test_code = _call_llm(testcase_prompt, model=self.llm_model)
        self.memory.store("test_code", test_code)

        # ── 质量评估 ──────────────────────────────────────────────────────────
        quality_prompt = (
            f"评估以下测试用例的质量：\n{test_code[:600]}\n\n"
            f"请给出：\n"
            f"1. 预估覆盖率（百分比）\n"
            f"2. 测试强度评分（1-10）\n"
            f"3. 发现的潜在缺陷或未覆盖场景\n"
            f"4. 改进建议（2-3 条）"
        )
        quality_report = _call_llm(quality_prompt, model=self.llm_model)
        self.memory.store("quality_report", quality_report)

        full_output = (
            f"# 测试报告\n\n"
            f"## 测试策略\n{strategy}\n\n"
            f"## 测试代码\n{test_code}\n\n"
            f"## 质量评估\n{quality_report}"
        )

        self.broadcast("tests_ready", {
            "test_code": test_code,
            "quality_report": quality_report,
        })

        return {
            "output": full_output,
            "artifacts": {
                "test_strategy": strategy,
                "test_code": test_code,
                "quality_report": quality_report,
            },
        }


# ──────────────────────────────────────────────────────────────────────────────
# 4. 代码审查官智能体
# ──────────────────────────────────────────────────────────────────────────────

class CodeReviewerAgent(AgentBase):
    """
    代码审查官智能体

    职责：
    - 全面审查代码质量（可读性、可维护性、性能）
    - 检测安全漏洞和潜在 Bug
    - 确保符合编码规范和最佳实践
    - 提供具体、可操作的改进建议
    """

    def __init__(
        self,
        bus: Optional[CommunicationBus] = None,
        llm_model: Optional[str] = None,
    ):
        super().__init__(
            agent_id="reviewer",
            name="代码审查官",
            role="资深代码审查专家",
            goal="通过严格的代码审查确保代码质量，防止技术债务积累，保障系统安全性",
            backstory=(
                "在大型软件公司主导代码审查流程多年，深谙 OWASP 安全规范、"
                "Clean Code 原则和各语言的最佳实践，以严谨和建设性著称。"
            ),
            bus=bus,
            llm_model=llm_model,
        )

    def execute(
        self,
        task: AgentTask,
        thought: str,
        plan: List[str],
    ) -> Dict[str, Any]:
        """执行代码审查：质量检查 → 安全扫描 → 性能分析 → 综合评分"""
        context = task.context
        core_code = context.get("core_code", context.get("developer_output", ""))
        test_code = context.get("test_code", "")
        architecture = context.get("architecture_design", "")

        # ── 代码质量审查 ──────────────────────────────────────────────────────
        quality_prompt = (
            f"作为资深代码审查官，审查以下代码：\n\n"
            f"{core_code[:800] if core_code else task.description}\n\n"
            f"请从以下维度审查：\n"
            f"1. 代码可读性（命名、结构、注释）\n"
            f"2. 可维护性（模块化、耦合度、可扩展性）\n"
            f"3. 代码规范符合度（PEP8/PSF 等）\n"
            f"4. 发现的问题（列出具体问题和位置）"
        )
        quality_review = _call_llm(quality_prompt, model=self.llm_model)
        self.memory.remember("quality_review", quality_review, source=task.id)

        # ── 安全审查 ──────────────────────────────────────────────────────────
        security_prompt = (
            f"对代码进行安全审查：\n{core_code[:600] if core_code else task.description}\n\n"
            f"检查以下安全问题（OWASP Top 10）：\n"
            f"1. SQL 注入 / NoSQL 注入\n"
            f"2. 身份验证和会话管理漏洞\n"
            f"3. 敏感数据暴露\n"
            f"4. 权限控制问题\n"
            f"5. 输入验证不足\n"
            f"给出安全风险等级（高/中/低）和修复建议。"
        )
        security_review = _call_llm(security_prompt, model=self.llm_model)
        self.memory.store("security_review", security_review)

        # ── 综合评分 ──────────────────────────────────────────────────────────
        score_prompt = (
            f"综合以下审查结果，给出最终评分：\n"
            f"质量审查：{quality_review[:400]}\n"
            f"安全审查：{security_review[:400]}\n\n"
            f"请给出：\n"
            f"1. 综合评分（0-10分）及理由\n"
            f"2. 必须修复的问题（阻塞合并）\n"
            f"3. 建议修复的问题（不阻塞但需改进）\n"
            f"4. 审查结论：✅ 批准合并 / ⚠️ 需修改后合并 / ❌ 拒绝合并"
        )
        final_score = _call_llm(score_prompt, model=self.llm_model)
        self.memory.store("review_conclusion", final_score)

        full_output = (
            f"# 代码审查报告\n\n"
            f"## 质量审查\n{quality_review}\n\n"
            f"## 安全审查\n{security_review}\n\n"
            f"## 综合评分与结论\n{final_score}"
        )

        self.broadcast("review_ready", {
            "quality_review": quality_review,
            "security_review": security_review,
            "final_score": final_score,
        })

        return {
            "output": full_output,
            "artifacts": {
                "quality_review": quality_review,
                "security_review": security_review,
                "review_conclusion": final_score,
            },
        }


# ──────────────────────────────────────────────────────────────────────────────
# 5. 项目经理智能体
# ──────────────────────────────────────────────────────────────────────────────

class ProjectManagerAgent(AgentBase):
    """
    项目经理智能体

    职责：
    - 分解需求为可管理的任务
    - 协调各智能体的工作优先级
    - 跟踪项目进度和风险
    - 汇总输出综合项目报告
    """

    def __init__(
        self,
        bus: Optional[CommunicationBus] = None,
        llm_model: Optional[str] = None,
    ):
        super().__init__(
            agent_id="pm",
            name="项目经理",
            role="敏捷项目经理",
            goal="确保项目按时、高质量交付，有效协调团队资源，及时识别和化解风险",
            backstory=(
                "PMP 认证项目经理，拥有敏捷和 DevOps 双重背景，"
                "擅长将技术团队的输出转化为业务价值，以高情商和数据驱动决策著称。"
            ),
            bus=bus,
            llm_model=llm_model,
        )

    def execute(
        self,
        task: AgentTask,
        thought: str,
        plan: List[str],
    ) -> Dict[str, Any]:
        """执行项目管理：需求分解 → 资源规划 → 风险评估 → 进度报告"""
        context = task.context
        requirement = context.get("requirement", task.description)

        # 收集各智能体的输出（如果存在）
        arch_output = context.get("architect_output", "")
        dev_output = context.get("developer_output", "")
        test_output = context.get("tester_output", "")
        review_output = context.get("reviewer_output", "")

        # ── 需求分解和任务规划 ────────────────────────────────────────────────
        breakdown_prompt = (
            f"作为敏捷项目经理，将以下需求分解为可执行任务：\n\n{requirement}\n\n"
            f"请输出：\n"
            f"1. 用户故事列表（3-5 个，格式：'作为...我想要...以便...'）\n"
            f"2. 对应的验收标准\n"
            f"3. 任务分解和估算（故事点）\n"
            f"4. Sprint 计划（1-2 个 Sprint）"
        )
        breakdown = _call_llm(breakdown_prompt, model=self.llm_model)
        self.memory.remember("task_breakdown", breakdown, source=task.id)

        # ── 风险评估 ──────────────────────────────────────────────────────────
        risk_prompt = (
            f"基于项目需求：\n{requirement}\n"
            f"以及当前开发状态（架构：{'已完成' if arch_output else '待完成'}，"
            f"开发：{'已完成' if dev_output else '待完成'}，"
            f"测试：{'已完成' if test_output else '待完成'}，"
            f"审查：{'已完成' if review_output else '待完成'}）\n\n"
            f"请进行风险评估：\n"
            f"1. 识别 3-5 个主要风险（技术/资源/时间/质量）\n"
            f"2. 每个风险的影响（高/中/低）和可能性\n"
            f"3. 对应的缓解策略"
        )
        risk_assessment = _call_llm(risk_prompt, model=self.llm_model)
        self.memory.store("risk_assessment", risk_assessment)

        # ── 综合进度报告 ──────────────────────────────────────────────────────
        # 统计哪些智能体已完成工作
        completed_agents = []
        if arch_output:
            completed_agents.append("架构师")
        if dev_output:
            completed_agents.append("开发工程师")
        if test_output:
            completed_agents.append("测试工程师")
        if review_output:
            completed_agents.append("代码审查官")

        completion_pct = int(len(completed_agents) / 4 * 100) if completed_agents else 25

        report_prompt = (
            f"生成项目进度报告：\n"
            f"项目：{task.title}\n"
            f"已完成工作：{', '.join(completed_agents) if completed_agents else '项目初始化'}\n"
            f"完成度：{completion_pct}%\n"
            f"任务分解：{breakdown[:300]}\n"
            f"风险评估摘要：{risk_assessment[:300]}\n\n"
            f"请输出：\n"
            f"1. 项目状态摘要（3-4 句话）\n"
            f"2. 下一步行动项（3-5 条）\n"
            f"3. 预计完成时间\n"
            f"4. 项目健康状态：🟢 健康 / 🟡 需关注 / 🔴 风险"
        )
        progress_report = _call_llm(report_prompt, model=self.llm_model)
        self.memory.store("progress_report", progress_report)

        full_output = (
            f"# 项目管理报告\n\n"
            f"## 需求分解与任务规划\n{breakdown}\n\n"
            f"## 风险评估\n{risk_assessment}\n\n"
            f"## 项目进度报告\n{progress_report}"
        )

        self.broadcast("pm_report_ready", {
            "completion_pct": completion_pct,
            "progress_report": progress_report,
        })

        return {
            "output": full_output,
            "artifacts": {
                "task_breakdown": breakdown,
                "risk_assessment": risk_assessment,
                "progress_report": progress_report,
                "completion_pct": completion_pct,
            },
        }


# ──────────────────────────────────────────────────────────────────────────────
# 团队工厂函数
# ──────────────────────────────────────────────────────────────────────────────

def create_dev_team(
    bus: Optional[CommunicationBus] = None,
    llm_model: Optional[str] = None,
) -> Dict[str, AgentBase]:
    """
    创建完整的软件开发智能体团队

    Returns
    -------
    dict mapping agent_id -> AgentBase instance
    """
    agents = [
        ArchitectAgent(bus=bus, llm_model=llm_model),
        DeveloperAgent(bus=bus, llm_model=llm_model),
        TesterAgent(bus=bus, llm_model=llm_model),
        CodeReviewerAgent(bus=bus, llm_model=llm_model),
        ProjectManagerAgent(bus=bus, llm_model=llm_model),
    ]
    return {a.agent_id: a for a in agents}
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
