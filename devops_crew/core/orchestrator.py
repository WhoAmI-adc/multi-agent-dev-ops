"""
多智能体协调引擎（Orchestrator）

负责：
- 注册和管理所有智能体
- 构建并执行工作流（序列化 / 并行）
- 维护通信总线和共享知识库
- 提供完整的执行日志和任务追踪
#!/usr/bin/env python3
"""
devops_crew.core.orchestrator
------------------------------
多智能体协调引擎。

职责：
  - 管理所有智能体实例
  - 定义并执行工作流（多个有序步骤）
  - 记录任务执行轨迹与通信日志
  - 生成执行报告
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .agent_base import AgentBase, AgentTask, CommunicationBus, TaskResult
import uuid
import logging
from datetime import datetime
from typing import Callable

from .agent_base import BaseAgent, Task, Message

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 数据类
# ──────────────────────────────────────────────────────────────────────────────

class StepType(Enum):
    """工作流步骤类型"""
    SEQUENTIAL = "sequential"   # 序列执行（下一步依赖上一步输出）
    PARALLEL = "parallel"        # 并行执行（同时启动多个智能体）
    CONDITIONAL = "conditional"  # 条件执行（根据前一步结果决定）


@dataclass
class WorkflowStep:
    """
    工作流中的单个步骤

    Attributes
    ----------
    agent_id    : 执行该步骤的智能体 ID
    task_title  : 任务标题（简短描述）
    task_desc   : 任务详细描述
    step_type   : 步骤执行类型
    context_keys: 从上一步结果中提取并注入上下文的键列表
    condition   : 可选条件函数，返回 False 时跳过此步骤
    """
    agent_id: str
    task_title: str
    task_desc: str
    step_type: StepType = StepType.SEQUENTIAL
    context_keys: List[str] = field(default_factory=list)
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    priority: int = 5


@dataclass
class WorkflowResult:
    """完整工作流的执行结果"""
    workflow_id: str
    workflow_name: str
    success: bool
    start_time: str
    end_time: str
    duration: float
    step_results: List[Dict[str, Any]]
    shared_context: Dict[str, Any]
    communication_log: List[Dict[str, Any]]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "success": self.success,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 2),
            "step_count": len(self.step_results),
            "step_results": self.step_results,
            "error": self.error,
        }

    def get_summary(self) -> str:
        """生成人类可读的执行摘要"""
        status = "成功" if self.success else "失败"
        lines = [
            f"工作流【{self.workflow_name}】执行{status}",
            f"总耗时：{self.duration:.1f} 秒",
            f"执行步骤：{len(self.step_results)} 步",
        ]
        for i, step in enumerate(self.step_results, 1):
            icon = "✅" if step.get("success") else "❌"
            lines.append(
                f"  {icon} 步骤 {i}: [{step.get('agent_name', '?')}] "
                f"{step.get('task_title', step.get('task_id', ''))}"
            )
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# 协调器
# ──────────────────────────────────────────────────────────────────────────────

class Orchestrator:
    """
    多智能体协调引擎

    功能：
    1. 注册/注销智能体
    2. 构建工作流并执行（序列化、并行）
    3. 维护共享知识库，让智能体间共享信息
    4. 记录完整的通信日志和任务追踪
    5. 提供执行状态查询接口
    """

    def __init__(self, name: str = "Orchestrator"):
        self.name = name
        self.bus = CommunicationBus()
        self._agents: Dict[str, AgentBase] = {}
        self._shared_context: Dict[str, Any] = {}    # 共享知识库
        self._workflow_history: List[WorkflowResult] = []
        self._log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="agent")

        # 订阅通信事件
        self.bus.subscribe("agent_status", self._on_agent_status)
        self.bus.subscribe("task_completed", self._on_task_completed)

        logger.info("[%s] 协调器已初始化", name)

    # ── 智能体管理 ────────────────────────────────────────────────────────────

    def register(self, agent: AgentBase) -> None:
        """注册一个智能体并连接通信总线"""
        agent.bus = self.bus
        self._agents[agent.agent_id] = agent
        self._add_log("INFO", f"智能体已注册: {agent.name} ({agent.role})", source="orchestrator")
        logger.info("[%s] 注册智能体: %s", self.name, agent.name)

    def unregister(self, agent_id: str) -> None:
        """注销智能体"""
        agent = self._agents.pop(agent_id, None)
        if agent:
            self._add_log("INFO", f"智能体已注销: {agent.name}", source="orchestrator")

    def get_agent(self, agent_id: str) -> Optional[AgentBase]:
        """按 ID 获取智能体"""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有已注册智能体的状态"""
        return [a.get_status_dict() for a in self._agents.values()]

    # ── 知识共享 ──────────────────────────────────────────────────────────────

    def share(self, key: str, value: Any, *, source: str = "orchestrator") -> None:
        """向共享知识库写入信息"""
        with self._lock:
            self._shared_context[key] = value
        self._add_log("DEBUG", f"共享知识已更新: {key}", source=source)

    def get_shared(self, key: str, default: Any = None) -> Any:
        """从共享知识库读取信息"""
        return self._shared_context.get(key, default)

    # ── 工作流执行 ────────────────────────────────────────────────────────────

    def run_workflow(
        self,
        name: str,
        steps: List[WorkflowStep],
        *,
        initial_context: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> WorkflowResult:
        """
        执行一个完整的多智能体工作流

        Parameters
        ----------
        name             : 工作流名称
        steps            : 工作流步骤列表
        initial_context  : 工作流启动时注入的初始上下文
        progress_callback: 进度回调函数 (step_idx, total_steps, step_name)

        Returns
        -------
        WorkflowResult   : 包含所有步骤结果的完整工作流结果
        """
        workflow_id = str(uuid.uuid4())[:8]
        start_ts = time.time()
        start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._add_log(
            "INFO",
            f"工作流【{name}】开始执行，共 {len(steps)} 个步骤",
            source="orchestrator",
        )

        # 初始化工作流上下文（合并共享知识库）
        context: Dict[str, Any] = dict(self._shared_context)
        if initial_context:
            context.update(initial_context)

        step_results: List[Dict[str, Any]] = []
        overall_success = True
        error_msg: Optional[str] = None

        try:
            for idx, step in enumerate(steps, 1):
                # 条件检查
                if step.condition and not step.condition(context):
                    self._add_log(
                        "INFO",
                        f"步骤 {idx} [{step.task_title}] 条件不满足，跳过",
                        source="orchestrator",
                    )
                    continue

                # 进度回调
                if progress_callback:
                    progress_callback(idx, len(steps), step.task_title)

                self._add_log(
                    "INFO",
                    f"执行步骤 {idx}/{len(steps)}: [{step.agent_id}] {step.task_title}",
                    source="orchestrator",
                )

                # 构建任务上下文（从共享知识库提取指定键）
                task_ctx = dict(context)
                for key in step.context_keys:
                    if key in context:
                        task_ctx[key] = context[key]

                task = AgentTask(
                    title=step.task_title,
                    description=step.task_desc,
                    context=task_ctx,
                    priority=step.priority,
                    assigned_to=step.agent_id,
                )

                # 执行步骤
                if step.step_type == StepType.PARALLEL:
                    result = self._run_parallel_step(step, task)
                else:
                    result = self._run_sequential_step(step, task)

                # 将结果写入工作流上下文
                result_dict = result.to_dict()
                result_dict["task_title"] = step.task_title
                step_results.append(result_dict)

                if result.success:
                    # 将产出物和输出共享给后续步骤
                    context[f"step_{idx}_output"] = result.output
                    context[f"{step.agent_id}_output"] = result.output
                    for art_key, art_val in result.artifacts.items():
                        context[art_key] = art_val
                    # 更新共享知识库
                    self.share(f"{step.agent_id}_latest", result.output, source=step.agent_id)
                else:
                    overall_success = False
                    error_msg = result.error or f"步骤 {idx} 执行失败"
                    self._add_log(
                        "ERROR",
                        f"步骤 {idx} 失败: {error_msg}",
                        source="orchestrator",
                    )
                    # 允许后续步骤继续（尽力而为模式）

        except Exception as exc:  # pylint: disable=broad-except
            overall_success = False
            error_msg = str(exc)
            logger.exception("[%s] 工作流异常", self.name)

        duration = time.time() - start_ts
        end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status = "成功" if overall_success else "失败"
        self._add_log(
            "INFO" if overall_success else "ERROR",
            f"工作流【{name}】执行{status}，耗时 {duration:.1f}s",
            source="orchestrator",
        )

        wf_result = WorkflowResult(
            workflow_id=workflow_id,
            workflow_name=name,
            success=overall_success,
            start_time=start_str,
            end_time=end_str,
            duration=duration,
            step_results=step_results,
            shared_context=dict(context),
            communication_log=self.bus.get_messages(limit=100),
            error=error_msg,
        )
        self._workflow_history.append(wf_result)
        return wf_result

    def _run_sequential_step(self, step: WorkflowStep, task: AgentTask) -> TaskResult:
        """在当前线程中顺序执行一个步骤"""
        agent = self._agents.get(step.agent_id)
        if not agent:
            return TaskResult(
                task_id=task.id,
                agent_id=step.agent_id,
                agent_name=step.agent_id,
                success=False,
                output="",
                error=f"智能体 '{step.agent_id}' 未注册",
            )
        return agent.run(task)

    def _run_parallel_step(self, step: WorkflowStep, task: AgentTask) -> TaskResult:
        """在线程池中并行执行步骤（目前单智能体并行，可扩展为多智能体）"""
        future: Future = self._executor.submit(self._run_sequential_step, step, task)
        try:
            return future.result(timeout=120)
        except Exception as exc:  # pylint: disable=broad-except
            return TaskResult(
                task_id=task.id,
                agent_id=step.agent_id,
                agent_name=step.agent_id,
                success=False,
                output="",
                error=str(exc),
            )

    # ── 事件处理 ──────────────────────────────────────────────────────────────

    def _on_agent_status(self, msg: Dict[str, Any]) -> None:
        """处理智能体状态变更事件"""
        content = msg.get("content", {})
        self._add_log(
            "DEBUG",
            f"智能体状态: {content.get('agent')} → {content.get('status')}",
            source="bus",
        )

    def _on_task_completed(self, msg: Dict[str, Any]) -> None:
        """处理任务完成事件"""
        content = msg.get("content", {})
        self._add_log(
            "INFO",
            f"任务完成: [{content.get('agent')}] {content.get('task_id')} "
            f"— {str(content.get('summary', ''))[:80]}",
            source="bus",
        )

    # ── 日志 ──────────────────────────────────────────────────────────────────

    def _add_log(self, level: str, message: str, *, source: str = "orchestrator") -> None:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "source": source,
            "message": message,
        }
        self._log.append(entry)
        logger.log(
            getattr(logging, level, logging.INFO),
            "[%s] %s", source, message,
        )

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近 limit 条日志"""
        return self._log[-limit:]

    def get_workflow_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取工作流执行历史"""
        return [r.to_dict() for r in self._workflow_history[-limit:]]

    def reset(self) -> None:
        """重置协调器状态（保留智能体注册）"""
        self._shared_context.clear()
        self._log.clear()
        self.bus.clear()
        self._add_log("INFO", "协调器已重置", source="orchestrator")

    def shutdown(self) -> None:
        """关闭协调器，释放线程池资源"""
        self._executor.shutdown(wait=False)
        logger.info("[%s] 协调器已关闭", self.name)
# ──────────────────────────────────────────────
# 工作流步骤描述
# ──────────────────────────────────────────────

class WorkflowStep:
    """描述工作流中的一个步骤"""

    def __init__(
        self,
        step_id: str,
        agent_id: str,
        task_type: str,
        description: str,
        context: dict | None = None,
    ):
        self.step_id = step_id
        self.agent_id = agent_id
        self.task_type = task_type
        self.description = description
        self.context: dict = context or {}


class Workflow:
    """工作流定义：一个有名称和有序步骤的执行序列"""

    def __init__(self, workflow_id: str, name: str, description: str):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps: list[WorkflowStep] = []

    def add_step(self, step: WorkflowStep) -> 'Workflow':
        self.steps.append(step)
        return self


# ──────────────────────────────────────────────
# 协调引擎
# ──────────────────────────────────────────────

class Orchestrator:
    """
    多智能体协调引擎。

    使用方式：
        orch = Orchestrator()
        orch.register_agent(ArchitectAgent())
        orch.register_agent(DeveloperAgent())

        workflow = Workflow('wf-001', '用户认证开发', '...')
        workflow.add_step(WorkflowStep('s1', 'architect_agent', 'design', '设计架构'))
        workflow.add_step(WorkflowStep('s2', 'developer_agent', 'implement', '实现代码'))

        report = orch.execute_workflow(workflow)
    """

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._communication_log: list[Message] = []
        self._task_registry: dict[str, Task] = {}
        self._workflow_history: list[dict] = []
        logger.info('Orchestrator 已初始化')

    # ── 智能体管理 ─────────────────────────────

    def register_agent(self, agent: BaseAgent) -> None:
        """注册一个智能体到协调器"""
        self._agents[agent.agent_id] = agent
        logger.info('智能体已注册: %s (%s)', agent.name, agent.agent_id)

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    @property
    def registered_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    # ── 工作流执行 ─────────────────────────────

    def execute_workflow(
        self,
        workflow: Workflow,
        progress_callback: Callable[[int, int, str, str], None] | None = None,
    ) -> dict:
        """
        执行工作流，按步骤依次调用对应智能体。

        Args:
            workflow:          要执行的工作流
            progress_callback: 可选回调，签名 (step_idx, total, agent_name, message)

        Returns:
            执行报告 dict
        """
        run_id = str(uuid.uuid4())[:8]
        started_at = datetime.now()
        logger.info('[Orchestrator] 开始执行工作流: %s (run_id=%s)', workflow.name, run_id)

        step_results: dict[str, dict] = {}
        team_results: dict[str, str] = {}
        total = len(workflow.steps)
        failed = False

        for idx, step in enumerate(workflow.steps, 1):
            agent = self._agents.get(step.agent_id)
            if agent is None:
                logger.error('找不到智能体: %s', step.agent_id)
                step_results[step.step_id] = {
                    'status': 'failed',
                    'error': f'智能体 {step.agent_id} 未注册',
                }
                failed = True
                continue

            # 构建任务
            task = Task(
                task_id=f'{run_id}-{step.step_id}',
                task_type=step.task_type,
                description=step.description,
                context={**step.context, 'workflow': workflow.name, 'step': idx},
            )
            self._task_registry[task.task_id] = task

            # 进度通知
            msg = f'[步骤 {idx}/{total}] {agent.name} 正在执行: {step.description[:50]}'
            logger.info(msg)
            if progress_callback:
                progress_callback(idx, total, agent.name, msg)

            # 广播开始消息
            self._broadcast(
                sender='orchestrator',
                receiver=step.agent_id,
                content=f'请开始执行步骤 {idx}: {step.description}',
            )

            # 执行任务
            completed_task = agent.execute_task(task)

            # 收集结果
            step_results[step.step_id] = {
                'step_idx': idx,
                'agent': agent.name,
                'task_type': step.task_type,
                'description': step.description,
                'status': completed_task.status,
                'result': completed_task.result,
                'completed_at': completed_task.completed_at,
            }
            team_results[agent.name] = completed_task.result

            # 广播完成消息
            self._broadcast(
                sender=step.agent_id,
                receiver='orchestrator',
                content=f'步骤 {idx} 完成: {completed_task.result[:100]}',
            )

            if progress_callback:
                progress_callback(idx, total, agent.name, f'✅ {agent.name} 完成步骤 {idx}')

        # 生成最终报告
        duration = (datetime.now() - started_at).total_seconds()
        status = 'failed' if failed else 'completed'

        report = self._build_report(
            run_id=run_id,
            workflow=workflow,
            step_results=step_results,
            team_results=team_results,
            status=status,
            duration=duration,
            started_at=started_at,
        )

        self._workflow_history.append(report)
        logger.info('[Orchestrator] 工作流执行完毕，耗时 %.1f 秒', duration)
        return report

    # ── 内部辅助 ───────────────────────────────

    def _broadcast(self, sender: str, receiver: str, content: str) -> None:
        """记录一条通信消息"""
        msg = Message(sender=sender, receiver=receiver, content=content)
        self._communication_log.append(msg)

    def _build_report(
        self,
        run_id: str,
        workflow: Workflow,
        step_results: dict,
        team_results: dict,
        status: str,
        duration: float,
        started_at: datetime,
    ) -> dict:
        """构建工作流执行报告"""
        # 尝试用 PM 生成综合总结，若未注册 PM 则使用简单拼接
        pm = self._agents.get('project_manager_agent')
        if pm and hasattr(pm, 'coordinate') and team_results:
            try:
                final_summary = pm.coordinate(workflow.description, team_results)  # type: ignore[attr-defined]
            except Exception:
                final_summary = self._simple_summary(team_results)
        else:
            final_summary = self._simple_summary(team_results)

        return {
            'run_id': run_id,
            'workflow_id': workflow.workflow_id,
            'workflow_name': workflow.name,
            'description': workflow.description,
            'status': status,
            'started_at': started_at.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': round(duration, 2),
            'total_steps': len(workflow.steps),
            'completed_steps': sum(1 for v in step_results.values() if v.get('status') == 'completed'),
            'step_results': step_results,
            'final_summary': final_summary,
            'communication_count': len(self._communication_log),
        }

    @staticmethod
    def _simple_summary(team_results: dict) -> str:
        parts = [f'【{name}】: {result[:150]}' for name, result in team_results.items()]
        return '项目执行完成。\n\n' + '\n\n'.join(parts)

    # ── 查询接口 ───────────────────────────────

    @property
    def communication_log(self) -> list[dict]:
        return [m.to_dict() for m in self._communication_log]

    @property
    def workflow_history(self) -> list[dict]:
        return list(self._workflow_history)

    def get_framework_status(self) -> dict:
        """返回框架整体状态，供 Web API 使用"""
        return {
            'framework': '自研多智能体软件开发框架',
            'version': '1.0.0',
            'agents': [a.to_dict() for a in self._agents.values()],
            'total_agents': len(self._agents),
            'workflows_executed': len(self._workflow_history),
            'total_tasks': len(self._task_registry),
            'total_messages': len(self._communication_log),
        }
