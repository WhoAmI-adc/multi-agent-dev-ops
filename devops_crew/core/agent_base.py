#!/usr/bin/env python3
"""
devops_crew.core.agent_base
----------------------------
完全自己编写的多智能体框架 — Agent 基类、Task 数据结构、Message 消息结构。
使用 Anthropic Claude API 作为 LLM 后端。
"""

from __future__ import annotations

import os
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────

@dataclass
class Message:
    """智能体之间传递的消息"""
    sender: str
    receiver: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            'message_id': self.message_id,
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
            'timestamp': self.timestamp,
        }


@dataclass
class Task:
    """分配给智能体的任务"""
    task_id: str
    task_type: str
    description: str
    context: dict = field(default_factory=dict)
    assigned_to: str = ''
    status: str = 'pending'           # pending | running | completed | failed
    result: str = ''
    created_at: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    completed_at: str = ''

    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'description': self.description,
            'assigned_to': self.assigned_to,
            'status': self.status,
            'result': self.result,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
        }


# ──────────────────────────────────────────────
# LLM 集成（Claude API）
# ──────────────────────────────────────────────

def _call_claude(system_prompt: str, user_message: str, model: str = 'claude-3-5-sonnet-20241022') -> str:
    """调用 Claude API，返回文本响应。若无法连接则返回模拟响应。"""
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        # 没有 API Key 时返回带结构的模拟响应（方便本地演示）
        return _mock_response(system_prompt, user_message)

    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
        )
        return resp.content[0].text
    except Exception as exc:
        logger.warning('Claude API 调用失败，使用模拟响应: %s', exc)
        return _mock_response(system_prompt, user_message)


def _mock_response(system_prompt: str, user_message: str) -> str:
    """当 API 不可用时生成结构化的模拟响应"""
    role_hint = ''
    for keyword, hint in [
        ('架构师', '设计了清晰的分层架构，包含接口层、业务层、数据层，并规划了模块间的依赖关系。'),
        ('开发工程师', '实现了核心业务逻辑，编写了可维护的代码，并添加了必要的注释与错误处理。'),
        ('测试工程师', '制定了全面的测试策略，涵盖单元测试、集成测试和边界条件测试，测试覆盖率达 90% 以上。'),
        ('代码审查', '完成了代码审查，确认代码符合规范，识别了潜在的安全隐患并提出改进建议。'),
        ('项目经理', '协调了各团队成员的工作，确保任务按时交付，并生成了详细的项目进度报告。'),
    ]:
        if keyword in system_prompt:
            role_hint = hint
            break
    if not role_hint:
        role_hint = '完成了任务分析与执行，输出了高质量的结果。'

    return (
        f"[模拟 LLM 响应]\n"
        f"根据任务要求：{user_message[:80]}...\n\n"
        f"执行结果：{role_hint}\n\n"
        f"关键产出：\n"
        f"1. 完成了核心功能的设计与实现\n"
        f"2. 确保了代码质量与可维护性\n"
        f"3. 记录了详细的技术文档"
    )


# ──────────────────────────────────────────────
# Agent 基类
# ──────────────────────────────────────────────

class BaseAgent:
    """
    多智能体框架 Agent 基类。
    所有专业化智能体继承此类，并可按需覆盖各阶段方法。

    执行流程：think → plan → execute_step（逐步） → summarize
    """

    # 子类覆盖这些属性
    agent_id: str = 'base_agent'
    name: str = '基础智能体'
    role: str = '通用角色'
    system_prompt: str = '你是一个通用 AI 助手。'

    def __init__(self):
        self._messages: list[Message] = []
        self._task_log: list[Task] = []
        logger.debug('Agent 初始化: %s (%s)', self.name, self.agent_id)

    # ── 四阶段执行方法 ──────────────────────────

    def think(self, context: str) -> str:
        """
        阶段 1：使用 LLM 分析当前上下文，生成思考结果。

        Args:
            context: 需要分析的上下文信息

        Returns:
            LLM 的思考与分析结论
        """
        prompt = f"请分析以下上下文，给出你的思考与见解：\n\n{context}"
        thinking = _call_claude(self.system_prompt, prompt)
        logger.debug('[%s] think() 完成', self.name)
        return thinking

    def plan(self, task: Task, thinking: str) -> list[str]:
        """
        阶段 2：基于思考结果，制定具体执行计划（步骤列表）。

        Args:
            task:     当前任务对象
            thinking: think() 的输出

        Returns:
            执行步骤列表（字符串列表）
        """
        prompt = (
            f"任务：{task.description}\n\n"
            f"你的分析：{thinking[:500]}\n\n"
            f"请列出 3-5 个具体的执行步骤（每行一个步骤，不要编号前缀）："
        )
        raw = _call_claude(self.system_prompt, prompt)

        # 解析步骤列表
        steps = [
            line.strip().lstrip('0123456789.-） )、')
            for line in raw.splitlines()
            if line.strip() and not line.strip().startswith('[')
        ]
        steps = [s for s in steps if len(s) > 5][:5]
        if not steps:
            steps = [f'执行 {task.task_type} 核心步骤', '验证执行结果', '输出完成报告']
        logger.debug('[%s] plan() 生成 %d 个步骤', self.name, len(steps))
        return steps

    def execute_step(self, step: str, context: str = '') -> str:
        """
        阶段 3：执行单个步骤并返回结果。

        Args:
            step:    步骤描述
            context: 额外上下文（可选）

        Returns:
            该步骤的执行结果
        """
        prompt = f"请执行以下步骤并给出详细结果：\n步骤：{step}\n上下文：{context}"
        result = _call_claude(self.system_prompt, prompt)
        logger.debug('[%s] execute_step: %s', self.name, step[:50])
        return result

    def summarize(self, task: Task, results: list[str]) -> str:
        """
        阶段 4：综合所有步骤结果，生成最终总结。

        Args:
            task:    当前任务对象
            results: 各步骤执行结果列表

        Returns:
            任务执行总结
        """
        combined = '\n'.join(f'步骤 {i+1}: {r[:200]}' for i, r in enumerate(results))
        prompt = (
            f"任务：{task.description}\n\n"
            f"各步骤执行结果：\n{combined}\n\n"
            f"请综合以上结果，生成简洁的任务完成总结（不超过 300 字）："
        )
        summary = _call_claude(self.system_prompt, prompt)
        logger.debug('[%s] summarize() 完成', self.name)
        return summary

    # ── 消息收发 ───────────────────────────────

    def send_message(self, receiver: str, content: str) -> Message:
        """发送消息给另一个智能体"""
        msg = Message(sender=self.agent_id, receiver=receiver, content=content)
        self._messages.append(msg)
        return msg

    def receive_message(self, message: Message) -> None:
        """接收来自其他智能体的消息"""
        self._messages.append(message)

    # ── 完整任务执行入口 ────────────────────────

    def execute_task(self, task: Task) -> Task:
        """
        执行完整任务（think → plan → execute_step × N → summarize）。
        修改 task 对象的 status / result / completed_at 字段并返回。
        """
        logger.info('[%s] 开始执行任务: %s', self.name, task.description[:60])
        task.status = 'running'
        task.assigned_to = self.agent_id

        # 阶段 1：思考
        thinking = self.think(task.description + '\n' + str(task.context))

        # 阶段 2：规划
        steps = self.plan(task, thinking)

        # 阶段 3：逐步执行
        step_results: list[str] = []
        for step in steps:
            result = self.execute_step(step, context=task.description)
            step_results.append(result)

        # 阶段 4：总结
        summary = self.summarize(task, step_results)

        task.result = summary
        task.status = 'completed'
        task.completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._task_log.append(task)
        logger.info('[%s] 任务完成: %s', self.name, task.task_id)
        return task

    # ── 属性访问 ───────────────────────────────

    @property
    def message_history(self) -> list[Message]:
        return list(self._messages)

    @property
    def task_history(self) -> list[Task]:
        return list(self._task_log)

    def to_dict(self) -> dict:
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'role': self.role,
            'tasks_completed': len([t for t in self._task_log if t.status == 'completed']),
            'messages_sent': len([m for m in self._messages if m.sender == self.agent_id]),
        }
