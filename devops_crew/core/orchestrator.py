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

import uuid
import logging
from datetime import datetime
from typing import Callable

from .agent_base import BaseAgent, Task, Message

logger = logging.getLogger(__name__)


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
