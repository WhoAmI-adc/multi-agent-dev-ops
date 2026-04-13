"""
多智能体框架单元测试

测试自研多智能体框架的核心组件，无需 LLM API 即可运行。
"""

import sys
import os
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== AgentTask 数据类测试 ====================

class TestAgentTask:
    """测试 AgentTask 数据类"""

    def test_create_task_defaults(self):
        """测试默认值创建任务"""
        from devops_crew.core.agent_base import AgentTask
        task = AgentTask(title="测试任务", description="这是一个测试")
        assert task.title == "测试任务"
        assert task.description == "这是一个测试"
        assert task.priority == 5
        assert task.status == "pending" if hasattr(task, 'status') else True
        assert len(task.id) > 0

    def test_task_to_dict(self):
        """测试任务序列化"""
        from devops_crew.core.agent_base import AgentTask
        task = AgentTask(
            title="架构设计",
            description="设计系统架构",
            priority=1,
        )
        d = task.to_dict()
        assert "id" in d
        assert d["title"] == "架构设计"
        assert d["description"] == "设计系统架构"
        assert d["priority"] == 1

    def test_task_context(self):
        """测试任务上下文"""
        from devops_crew.core.agent_base import AgentTask
        task = AgentTask(
            title="代码审查",
            description="审查认证模块代码",
            context={"language": "Python", "module": "auth"},
        )
        assert task.context["language"] == "Python"
        assert task.context["module"] == "auth"

    def test_task_auto_id(self):
        """测试任务 ID 自动生成"""
        from devops_crew.core.agent_base import AgentTask
        task1 = AgentTask(title="任务1", description="描述1")
        task2 = AgentTask(title="任务2", description="描述2")
        assert task1.id != task2.id


# ==================== TaskResult 数据类测试 ====================

class TestTaskResult:
    """测试 TaskResult 数据类"""

    def test_create_result_success(self):
        """测试创建成功结果"""
        from devops_crew.core.agent_base import TaskResult
        result = TaskResult(
            task_id="task-001",
            agent_id="architect",
            agent_name="架构师",
            success=True,
            output="设计完成",
        )
        assert result.success is True
        assert result.output == "设计完成"
        assert result.error is None

    def test_create_result_failure(self):
        """测试创建失败结果"""
        from devops_crew.core.agent_base import TaskResult
        result = TaskResult(
            task_id="task-002",
            agent_id="developer",
            agent_name="开发工程师",
            success=False,
            output="",
            error="API 调用失败",
        )
        assert result.success is False
        assert result.error == "API 调用失败"

    def test_result_to_dict(self):
        """测试结果序列化"""
        from devops_crew.core.agent_base import TaskResult
        result = TaskResult(
            task_id="task-003",
            agent_id="tester",
            agent_name="测试工程师",
            success=True,
            output="测试通过",
            duration=3.14,
            steps=["步骤1", "步骤2"],
        )
        d = result.to_dict()
        assert d["task_id"] == "task-003"
        assert d["success"] is True
        assert d["duration"] == 3.14
        assert len(d["steps"]) == 2

    def test_result_artifacts(self):
        """测试结果附件"""
        from devops_crew.core.agent_base import TaskResult
        result = TaskResult(
            task_id="task-004",
            agent_id="developer",
            agent_name="开发工程师",
            success=True,
            output="代码生成完成",
            artifacts={"code": "def hello(): pass", "lang": "Python"},
        )
        assert result.artifacts["lang"] == "Python"


# ==================== AgentMemory 测试 ====================

class TestAgentMemory:
    """测试 AgentMemory 记忆系统"""

    def test_short_term_memory(self):
        """测试短期记忆读写"""
        from devops_crew.core.agent_base import AgentMemory
        mem = AgentMemory(stm_capacity=10)
        mem.remember("architecture", "分层架构设计")
        mem.remember("tech_stack", "Python/FastAPI")

        recent = mem.recall_recent(2)
        assert len(recent) == 2
        keys = [r["key"] for r in recent]
        assert "architecture" in keys
        assert "tech_stack" in keys

    def test_long_term_memory(self):
        """测试长期记忆读写"""
        from devops_crew.core.agent_base import AgentMemory
        mem = AgentMemory()
        mem.store("project_guidelines", "遵循 SOLID 原则")
        value = mem.retrieve("project_guidelines")
        assert value == "遵循 SOLID 原则"

    def test_long_term_memory_default(self):
        """测试长期记忆默认值"""
        from devops_crew.core.agent_base import AgentMemory
        mem = AgentMemory()
        value = mem.retrieve("nonexistent_key", default="默认值")
        assert value == "默认值"

    def test_stm_capacity_limit(self):
        """测试短期记忆容量限制"""
        from devops_crew.core.agent_base import AgentMemory
        mem = AgentMemory(stm_capacity=3)
        for i in range(5):
            mem.remember(f"key_{i}", f"value_{i}")
        recent = mem.recall_recent(10)
        assert len(recent) <= 3  # 不超过容量

    def test_forget_long_term(self):
        """测试删除长期记忆"""
        from devops_crew.core.agent_base import AgentMemory
        mem = AgentMemory()
        mem.store("temp_data", "临时数据")
        mem.forget("temp_data")
        value = mem.retrieve("temp_data")
        assert value is None

    def test_memory_snapshot(self):
        """测试记忆快照"""
        from devops_crew.core.agent_base import AgentMemory
        mem = AgentMemory()
        mem.remember("stm_key", "stm_value")
        mem.store("ltm_key", "ltm_value")
        snapshot = mem.snapshot()
        assert "stm" in snapshot
        assert "ltm" in snapshot

    def test_recall_by_key(self):
        """测试按键名查找短期记忆"""
        from devops_crew.core.agent_base import AgentMemory
        mem = AgentMemory()
        mem.remember("task_result", "第一次结果")
        mem.remember("other_key", "其他内容")
        mem.remember("task_result", "第二次结果")
        results = mem.recall_by_key("task_result")
        assert len(results) == 2


# ==================== CommunicationBus 测试 ====================

class TestCommunicationBus:
    """测试 CommunicationBus 通信总线"""

    def test_publish_and_subscribe(self):
        """测试发布/订阅消息"""
        from devops_crew.core.agent_base import CommunicationBus
        bus = CommunicationBus()
        received = []

        def handler(msg):
            received.append(msg)

        bus.subscribe("architecture_ready", handler)
        bus.publish("architecture_ready", {"design": "分层架构"}, sender="architect")

        assert len(received) == 1
        assert received[0]["content"]["design"] == "分层架构"

    def test_no_subscriber(self):
        """测试无订阅者时发布不报错"""
        from devops_crew.core.agent_base import CommunicationBus
        bus = CommunicationBus()
        # Should not raise
        bus.publish("some_topic", "content", sender="agent")

    def test_message_history(self):
        """测试消息历史记录"""
        from devops_crew.core.agent_base import CommunicationBus
        bus = CommunicationBus()
        bus.publish("topic_a", "消息1", sender="agent_1")
        bus.publish("topic_b", "消息2", sender="agent_2")
        history = bus.get_messages()
        assert len(history) == 2

    def test_multiple_subscribers(self):
        """测试多个订阅者"""
        from devops_crew.core.agent_base import CommunicationBus
        bus = CommunicationBus()
        received_a = []
        received_b = []

        bus.subscribe("event", lambda m: received_a.append(m))
        bus.subscribe("event", lambda m: received_b.append(m))
        bus.publish("event", "data", sender="source")

        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_agent_messages(self):
        """测试智能体消息查询"""
        from devops_crew.core.agent_base import CommunicationBus
        bus = CommunicationBus()
        bus.publish("task_done", "完成", sender="architect", recipient="developer")
        msgs = bus.get_messages(sender="architect")
        assert len(msgs) >= 1


# ==================== AgentStatus 测试 ====================

class TestAgentStatus:
    """测试 AgentStatus 枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        from devops_crew.core.agent_base import AgentStatus
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.THINKING.value == "thinking"
        assert AgentStatus.PLANNING.value == "planning"
        assert AgentStatus.EXECUTING.value == "executing"
        assert AgentStatus.DONE.value == "done"
        assert AgentStatus.ERROR.value == "error"

    def test_status_comparison(self):
        """测试状态比较"""
        from devops_crew.core.agent_base import AgentStatus
        assert AgentStatus.IDLE != AgentStatus.EXECUTING
        assert AgentStatus.DONE == AgentStatus.DONE


# ==================== 智能体初始化测试 ====================

class TestAgentInitialization:
    """测试智能体初始化（无需 LLM）"""

    def test_architect_agent_init(self):
        """测试架构师智能体初始化"""
        from devops_crew.agents.dev_agents import ArchitectAgent
        agent = ArchitectAgent()
        assert agent.name == "架构师"
        assert agent.agent_id == "architect"
        assert agent.role is not None
        assert agent.backstory is not None

    def test_developer_agent_init(self):
        """测试开发工程师智能体初始化"""
        from devops_crew.agents.dev_agents import DeveloperAgent
        agent = DeveloperAgent()
        assert agent.name == "开发工程师"
        assert agent.agent_id == "developer"

    def test_tester_agent_init(self):
        """测试测试工程师智能体初始化"""
        from devops_crew.agents.dev_agents import TesterAgent
        agent = TesterAgent()
        assert agent.name == "测试工程师"
        assert agent.agent_id == "tester"

    def test_reviewer_agent_init(self):
        """测试代码审查官智能体初始化"""
        from devops_crew.agents.dev_agents import CodeReviewerAgent
        agent = CodeReviewerAgent()
        assert agent.name == "代码审查官"
        assert agent.agent_id == "reviewer"

    def test_pm_agent_init(self):
        """测试项目经理智能体初始化"""
        from devops_crew.agents.dev_agents import ProjectManagerAgent
        agent = ProjectManagerAgent()
        assert agent.name == "项目经理"
        assert agent.agent_id == "pm"

    def test_agent_initial_status(self):
        """测试智能体初始状态"""
        from devops_crew.agents.dev_agents import ArchitectAgent
        from devops_crew.core.agent_base import AgentStatus
        agent = ArchitectAgent()
        assert agent.status == AgentStatus.IDLE

    def test_create_dev_team(self):
        """测试创建开发团队"""
        from devops_crew.agents.dev_agents import create_dev_team
        team = create_dev_team()
        assert "architect" in team
        assert "developer" in team
        assert "tester" in team
        assert "reviewer" in team
        assert "pm" in team
        assert len(team) == 5


# ==================== Orchestrator 测试 ====================

class TestOrchestrator:
    """测试 Orchestrator 协调引擎（使用 mock LLM）"""

    @patch("devops_crew.core.agent_base._call_llm")
    def test_orchestrator_init(self, mock_llm):
        """测试协调器初始化"""
        from devops_crew.core.orchestrator import Orchestrator
        mock_llm.return_value = "Mock LLM response"
        orch = Orchestrator(name="测试协调器")
        assert orch.name == "测试协调器"

    @patch("devops_crew.core.agent_base._call_llm")
    def test_orchestrator_register_agents(self, mock_llm):
        """测试注册智能体"""
        from devops_crew.core.orchestrator import Orchestrator
        from devops_crew.agents.dev_agents import create_dev_team
        mock_llm.return_value = "Mock response"
        orch = Orchestrator(name="测试协调器")
        team = create_dev_team()
        for agent in team.values():
            orch.register(agent)
        assert len(orch._agents) == 5

    @patch("devops_crew.core.agent_base._call_llm")
    def test_orchestrator_workflow_creation(self, mock_llm):
        """测试工作流创建"""
        from devops_crew.core.orchestrator import Orchestrator, WorkflowStep, StepType
        from devops_crew.agents.dev_agents import ArchitectAgent
        mock_llm.return_value = "Mock LLM response for architecture"
        orch = Orchestrator(name="测试协调器")
        agent = ArchitectAgent()
        orch.register(agent)

        steps = [
            WorkflowStep(
                agent_id="architect",
                task_title="测试设计任务",
                task_desc="这是一个测试任务描述",
                step_type=StepType.SEQUENTIAL,
            )
        ]
        assert len(steps) == 1
        assert steps[0].agent_id == "architect"

    @patch("devops_crew.core.agent_base._call_llm")
    def test_workflow_execution_with_mock(self, mock_llm):
        """测试工作流执行（使用 mock LLM）"""
        mock_llm.return_value = (
            "这是模拟的 LLM 响应，包含架构设计方案。\n"
            "1. 分层架构\n2. REST API\n3. 数据库设计"
        )

        from devops_crew.core.orchestrator import Orchestrator, WorkflowStep, StepType
        from devops_crew.agents.dev_agents import ArchitectAgent

        orch = Orchestrator(name="测试协调器")
        agent = ArchitectAgent()
        orch.register(agent)

        steps = [
            WorkflowStep(
                agent_id="architect",
                task_title="系统架构设计",
                task_desc="设计一个简单的 Web 应用架构",
                step_type=StepType.SEQUENTIAL,
            )
        ]

        result = orch.run_workflow(
            name="测试工作流",
            steps=steps,
        )
        assert result is not None
        assert len(result.step_results) == 1


# ==================== 场景元数据测试 ====================

class TestScenarioMeta:
    """测试场景元数据"""

    def test_scenarios_meta_count(self):
        """测试场景元数据数量"""
        from scenario_dev_complete import SCENARIOS_META
        assert len(SCENARIOS_META) == 3

    def test_scenarios_meta_structure(self):
        """测试场景元数据结构"""
        from scenario_dev_complete import SCENARIOS_META
        for meta in SCENARIOS_META:
            assert "id" in meta
            assert "name" in meta
            assert "description" in meta

    def test_auth_scenario_meta(self):
        """测试认证场景元数据"""
        from scenario_dev_complete import SCENARIOS_META
        auth = next((m for m in SCENARIOS_META if m["id"] == "auth_module"), None)
        assert auth is not None
        assert "用户认证" in auth["name"]

    def test_data_pipeline_scenario_meta(self):
        """测试数据处理场景元数据"""
        from scenario_dev_complete import SCENARIOS_META
        data = next((m for m in SCENARIOS_META if m["id"] == "data_pipeline"), None)
        assert data is not None

    def test_rest_api_scenario_meta(self):
        """测试 REST API 场景元数据"""
        from scenario_dev_complete import SCENARIOS_META
        api = next((m for m in SCENARIOS_META if m["id"] == "rest_api"), None)
        assert api is not None

    def test_scenario_functions_importable(self):
        """测试场景函数可导入"""
        from scenario_dev_complete import (
            run_scenario_auth,
            run_scenario_data_pipeline,
            run_scenario_rest_api,
            run_all_scenarios,
            get_scenario_meta,
        )
        assert callable(run_scenario_auth)
        assert callable(run_scenario_data_pipeline)
        assert callable(run_scenario_rest_api)
        assert callable(run_all_scenarios)
        assert callable(get_scenario_meta)

    def test_get_scenario_meta(self):
        """测试按 ID 获取场景元数据"""
        from scenario_dev_complete import get_scenario_meta
        meta = get_scenario_meta("auth_module")
        assert meta is not None
        assert meta["id"] == "auth_module"

    def test_get_scenario_meta_not_found(self):
        """测试获取不存在的场景元数据"""
        from scenario_dev_complete import get_scenario_meta
        meta = get_scenario_meta("nonexistent_scenario")
        assert meta is None


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试：验证各模块协同工作"""

    def test_all_agents_importable(self):
        """测试所有智能体可导入"""
        from devops_crew.agents import (
            ArchitectAgent,
            DeveloperAgent,
            TesterAgent,
            CodeReviewerAgent,
            ProjectManagerAgent,
            create_dev_team,
        )
        assert ArchitectAgent is not None
        assert DeveloperAgent is not None
        assert TesterAgent is not None
        assert CodeReviewerAgent is not None
        assert ProjectManagerAgent is not None

    def test_core_framework_importable(self):
        """测试核心框架可导入"""
        from devops_crew.core import (
            AgentBase,
            AgentStatus,
            TaskResult,
            AgentTask,
            AgentMemory,
            CommunicationBus,
            Orchestrator,
            WorkflowStep,
            WorkflowResult,
        )
        assert AgentBase is not None
        assert Orchestrator is not None

    def test_agent_with_bus(self):
        """测试智能体与通信总线集成"""
        from devops_crew.core.agent_base import CommunicationBus
        from devops_crew.agents.dev_agents import ArchitectAgent, DeveloperAgent

        bus = CommunicationBus()
        arch = ArchitectAgent(bus=bus)
        dev = DeveloperAgent(bus=bus)

        # 订阅消息
        received = []
        bus.subscribe("architecture_ready", lambda m: received.append(m))

        # 架构师广播消息
        arch.broadcast("architecture_ready", {"design": "微服务"})
        assert len(received) == 1

    @patch("devops_crew.core.agent_base._call_llm")
    def test_full_agent_status_flow(self, mock_llm):
        """测试智能体状态流转"""
        mock_llm.return_value = "1. 分析需求\n2. 设计架构\n3. 完成文档"
        from devops_crew.core.agent_base import AgentStatus, AgentTask
        from devops_crew.agents.dev_agents import ArchitectAgent

        agent = ArchitectAgent()
        assert agent.status == AgentStatus.IDLE

        task = AgentTask(
            title="测试架构设计",
            description="为测试应用设计架构",
        )
        result = agent.run(task)
        assert result is not None
        # After completion, status should be IDLE or DONE
        assert agent.status in (AgentStatus.IDLE, AgentStatus.DONE)
