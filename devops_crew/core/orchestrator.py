"""
多智能体协调引擎（Orchestrator）

负责：
- 注册和管理所有智能体
- 构建并执行工作流（序列化 / 并行）
- 维护通信总线和共享知识库
- 提供完整的执行日志和任务追踪
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
