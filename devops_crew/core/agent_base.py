"""
智能体基类模块

提供多智能体系统的核心基础设施：
- AgentBase：所有智能体的基类，封装思考、规划、执行、总结四个阶段
- AgentMemory：智能体记忆机制，支持短期和长期记忆存储
- CommunicationBus：智能体间通信总线，支持消息发布/订阅
- AgentTask：任务描述数据类
- TaskResult：任务执行结果数据类
- AgentStatus：智能体状态枚举
#!/usr/bin/env python3
"""
devops_crew.core.agent_base
----------------------------
完全自己编写的多智能体框架 — Agent 基类、Task 数据结构、Message 消息结构。
使用 Anthropic Claude API 作为 LLM 后端。
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 枚举与数据类
# ──────────────────────────────────────────────────────────────────────────────

class AgentStatus(Enum):
    """智能体运行状态"""
    IDLE = "idle"           # 空闲，等待任务
    THINKING = "thinking"  # 思考推理阶段
    PLANNING = "planning"  # 规划制定阶段
    EXECUTING = "executing"  # 执行任务阶段
    SUMMARIZING = "summarizing"  # 总结阶段
    WAITING = "waiting"    # 等待其他智能体结果
    ERROR = "error"        # 发生错误
    DONE = "done"          # 任务完成


@dataclass
class AgentTask:
    """智能体任务描述"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5          # 1（最高）～ 10（最低）
    deadline: Optional[float] = None   # Unix 时间戳
    created_at: float = field(default_factory=time.time)
    assigned_to: str = ""      # 目标智能体 ID

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
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
class TaskResult:
    """任务执行结果"""
    task_id: str
    agent_id: str
    agent_name: str
    success: bool
    output: str
    artifacts: Dict[str, Any] = field(default_factory=dict)  # 代码、报告等附件
    duration: float = 0.0       # 执行耗时（秒）
    steps: List[str] = field(default_factory=list)  # 执行步骤记录
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "success": self.success,
            "output": self.output,
            "artifacts": self.artifacts,
            "duration": round(self.duration, 2),
            "steps": self.steps,
            "timestamp": self.timestamp,
            "error": self.error,
        }


# ──────────────────────────────────────────────────────────────────────────────
# 智能体记忆
# ──────────────────────────────────────────────────────────────────────────────

class AgentMemory:
    """
    智能体记忆系统

    短期记忆（STM）：最近的对话和推理步骤，容量有限（FIFO 队列）
    长期记忆（LTM）：重要知识和经验，以键值对形式持久存储
    """

    def __init__(self, stm_capacity: int = 20):
        self._stm: Deque[Dict[str, Any]] = deque(maxlen=stm_capacity)
        self._ltm: Dict[str, Any] = {}

    # ── 短期记忆 ──────────────────────────────────────────────────────────────

    def remember(self, key: str, value: Any, *, source: str = "self") -> None:
        """向短期记忆写入一条记录"""
        entry = {
            "key": key,
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        }
        self._stm.append(entry)

    def recall_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        """回忆最近 n 条短期记忆"""
        items = list(self._stm)
        return items[-n:] if len(items) >= n else items

    def recall_by_key(self, key: str) -> List[Any]:
        """从短期记忆中查找所有匹配 key 的值"""
        return [entry["value"] for entry in self._stm if entry["key"] == key]

    # ── 长期记忆 ──────────────────────────────────────────────────────────────

    def store(self, key: str, value: Any) -> None:
        """向长期记忆存储信息"""
        self._ltm[key] = {"value": value, "updated_at": datetime.now().isoformat()}

    def retrieve(self, key: str, default: Any = None) -> Any:
        """从长期记忆检索信息"""
        entry = self._ltm.get(key)
        return entry["value"] if entry else default

    def forget(self, key: str) -> None:
        """删除长期记忆中的某条信息"""
        self._ltm.pop(key, None)

    def ltm_keys(self) -> List[str]:
        """列出所有长期记忆键"""
        return list(self._ltm.keys())

    def snapshot(self) -> Dict[str, Any]:
        """获取完整记忆快照（用于调试/日志）"""
        return {
            "stm": list(self._stm),
            "ltm": self._ltm,
        }


# ──────────────────────────────────────────────────────────────────────────────
# 通信总线
# ──────────────────────────────────────────────────────────────────────────────

class CommunicationBus:
    """
    多智能体通信总线

    基于发布/订阅模式，支持：
    - 广播消息（所有订阅者均收到）
    - 点对点消息（指定收件智能体）
    - 消息历史查询
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}   # topic → [handler]
        self._messages: List[Dict[str, Any]] = []           # 完整消息历史

    def subscribe(self, topic: str, handler: Callable) -> None:
        """订阅某个话题"""
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(
        self,
        topic: str,
        content: Any,
        *,
        sender: str = "unknown",
        recipient: Optional[str] = None,
    ) -> None:
        """发布一条消息到总线"""
        msg = {
            "id": str(uuid.uuid4())[:8],
            "topic": topic,
            "content": content,
            "sender": sender,
            "recipient": recipient,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._messages.append(msg)
        logger.debug("[Bus] %s → %s: %s", sender, recipient or "all", topic)

        for handler in self._subscribers.get(topic, []):
            try:
                handler(msg)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("消息处理器异常 [%s]: %s", topic, exc)

    def get_messages(
        self,
        *,
        topic: Optional[str] = None,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """查询消息历史"""
        msgs = self._messages
        if topic:
            msgs = [m for m in msgs if m["topic"] == topic]
        if sender:
            msgs = [m for m in msgs if m["sender"] == sender]
        if recipient:
            msgs = [m for m in msgs if m["recipient"] in (recipient, None)]
        return msgs[-limit:]

    def clear(self) -> None:
        """清空消息历史（新任务开始前调用）"""
        self._messages.clear()


# ──────────────────────────────────────────────────────────────────────────────
# LLM 推理辅助
# ──────────────────────────────────────────────────────────────────────────────

def _call_llm(prompt: str, *, model: Optional[str] = None) -> str:
    """
    调用 LLM 接口进行推理。

    优先使用环境变量 OPENAI_API_KEY / OPENAI_BASE_URL；
    若未配置则回退到模拟推理（仅用于本地演示）。
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        # 无 API Key：返回结构化模拟输出，保证系统可完整演示
        return _simulate_llm_response(prompt)

    try:
        import openai  # pylint: disable=import-outside-toplevel

        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("LLM 调用失败，回退到模拟输出: %s", exc)
        return _simulate_llm_response(prompt)


def _simulate_llm_response(prompt: str) -> str:
    """当 LLM 不可用时生成结构化模拟响应，确保演示完整性"""
    prompt_lower = prompt.lower()

    if "架构" in prompt or "architect" in prompt_lower:
        return (
            "【架构设计分析】\n"
            "1. 采用分层架构：表示层、业务逻辑层、数据访问层\n"
            "2. 核心组件：认证服务、JWT Token 管理、用户仓储\n"
            "3. 技术选型：Python/FastAPI、Redis（会话存储）、PostgreSQL（用户数据）\n"
            "4. 安全设计：bcrypt 密码哈希、刷新令牌、速率限制\n"
            "5. 扩展性：无状态设计，支持水平扩展"
        )
    if "代码" in prompt or "implement" in prompt_lower or "develop" in prompt_lower:
        return (
            "【代码实现方案】\n"
            "```python\n"
            "class AuthService:\n"
            "    def __init__(self, user_repo, token_manager):\n"
            "        self.user_repo = user_repo\n"
            "        self.token_manager = token_manager\n\n"
            "    def login(self, username: str, password: str) -> dict:\n"
            "        user = self.user_repo.find_by_username(username)\n"
            "        if not user or not bcrypt.checkpw(password, user.password_hash):\n"
            "            raise AuthenticationError('用户名或密码错误')\n"
            "        token = self.token_manager.generate(user.id)\n"
            "        return {'access_token': token, 'token_type': 'Bearer'}\n"
            "```\n"
            "代码符合 SOLID 原则，已添加类型注解和异常处理。"
        )
    if "测试" in prompt or "test" in prompt_lower:
        return (
            "【测试方案】\n"
            "单元测试覆盖率目标：85%+\n"
            "测试用例：\n"
            "- test_login_success: 正确凭据登录成功\n"
            "- test_login_wrong_password: 密码错误返回 401\n"
            "- test_login_user_not_found: 用户不存在返回 404\n"
            "- test_token_expiry: 令牌过期返回 401\n"
            "- test_refresh_token: 刷新令牌正常工作\n"
            "集成测试：端对端 API 流程验证"
        )
    if "审查" in prompt or "review" in prompt_lower:
        return (
            "【代码审查报告】\n"
            "✅ 优点：结构清晰，职责分离，安全实践良好\n"
            "⚠️ 建议改进：\n"
            "1. 增加输入验证和参数校验\n"
            "2. 完善错误日志记录\n"
            "3. 考虑添加速率限制防止暴力破解\n"
            "4. 建议添加 API 文档注释\n"
            "综合评分：8.5/10，可进入生产"
        )
    if "计划" in prompt or "plan" in prompt_lower or "manage" in prompt_lower:
        return (
            "【项目计划】\n"
            "阶段 1（第 1-2 天）：需求分析和架构设计\n"
            "阶段 2（第 3-5 天）：核心功能开发\n"
            "阶段 3（第 6-7 天）：测试和代码审查\n"
            "阶段 4（第 8 天）：修复问题，发布上线\n"
            "里程碑：架构确认 → 代码完成 → 测试通过 → 上线"
        )
    return (
        "【分析结果】\n"
        "已完成对任务的深入分析和处理。\n"
        "关键发现：任务目标明确，技术方案可行，建议按既定方案执行。\n"
        "风险评估：低风险，可直接推进。"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 智能体基类
# ──────────────────────────────────────────────────────────────────────────────

class AgentBase(ABC):
    """
    智能体基类

    所有专业化智能体必须继承此类，并实现 execute() 方法。
    基类提供完整的 think → plan → execute → summarize 工作流，
    以及记忆管理、通信总线接入等公共能力。
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        *,
        bus: Optional[CommunicationBus] = None,
        llm_model: Optional[str] = None,
        stm_capacity: int = 20,
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm_model = llm_model
        self.memory = AgentMemory(stm_capacity=stm_capacity)
        self.bus = bus
        self.status = AgentStatus.IDLE
        self._task_history: List[TaskResult] = []
        self._current_task: Optional[AgentTask] = None

        logger.debug("智能体已初始化: %s (%s)", name, agent_id)

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def is_busy(self) -> bool:
        return self.status not in (AgentStatus.IDLE, AgentStatus.DONE, AgentStatus.ERROR)

    @property
    def task_count(self) -> int:
        return len(self._task_history)

    # ── 通信 ──────────────────────────────────────────────────────────────────

    def send_message(self, topic: str, content: Any, *, recipient: Optional[str] = None) -> None:
        """向通信总线发布消息"""
        if self.bus:
            self.bus.publish(topic, content, sender=self.agent_id, recipient=recipient)

    def broadcast(self, topic: str, content: Any) -> None:
        """广播消息给所有智能体"""
        self.send_message(topic, content, recipient=None)

    # ── 核心工作流 ────────────────────────────────────────────────────────────

    def run(self, task: AgentTask) -> TaskResult:
        """
        运行完整的 think → plan → execute → summarize 工作流

        Returns
        -------
        TaskResult
            包含执行结果、步骤记录和产出物的完整结果
        """
        start_time = time.time()
        self._current_task = task
        steps: List[str] = []
        artifacts: Dict[str, Any] = {}

        logger.info("[%s] 开始处理任务: %s", self.name, task.title)

        try:
            # 阶段 1：思考
            self.status = AgentStatus.THINKING
            self.broadcast("agent_status", {"agent": self.agent_id, "status": "thinking"})
            thought = self._think(task)
            steps.append(f"思考: {thought[:120]}{'...' if len(thought) > 120 else ''}")
            self.memory.remember("thought", thought, source=task.id)

            # 阶段 2：规划
            self.status = AgentStatus.PLANNING
            self.broadcast("agent_status", {"agent": self.agent_id, "status": "planning"})
            plan = self._plan(task, thought)
            steps.append(f"规划: 制定了 {len(plan)} 步执行计划")
            self.memory.remember("plan", plan, source=task.id)

            # 阶段 3：执行
            self.status = AgentStatus.EXECUTING
            self.broadcast("agent_status", {"agent": self.agent_id, "status": "executing"})
            result_data = self.execute(task, thought, plan)
            output = result_data.get("output", "")
            artifacts = result_data.get("artifacts", {})
            steps.append(f"执行: 完成 {len(plan)} 个子任务")

            # 阶段 4：总结
            self.status = AgentStatus.SUMMARIZING
            self.broadcast("agent_status", {"agent": self.agent_id, "status": "summarizing"})
            summary = self._summarize(task, output)
            steps.append(f"总结: {summary[:120]}{'...' if len(summary) > 120 else ''}")
            self.memory.store(f"task_{task.id}_result", summary)

            duration = time.time() - start_time
            result = TaskResult(
                task_id=task.id,
                agent_id=self.agent_id,
                agent_name=self.name,
                success=True,
                output=output,
                artifacts=artifacts,
                duration=duration,
                steps=steps,
            )
            self._task_history.append(result)

            # 通知任务完成
            self.broadcast("task_completed", {
                "agent": self.agent_id,
                "task_id": task.id,
                "summary": summary,
            })
            logger.info("[%s] 任务完成，耗时 %.2fs", self.name, duration)

        except Exception as exc:  # pylint: disable=broad-except
            duration = time.time() - start_time
            logger.exception("[%s] 任务失败: %s", self.name, exc)
            result = TaskResult(
                task_id=task.id,
                agent_id=self.agent_id,
                agent_name=self.name,
                success=False,
                output="",
                duration=duration,
                steps=steps,
                error=str(exc),
            )
            self._task_history.append(result)
            self.status = AgentStatus.ERROR
            return result

        self.status = AgentStatus.DONE
        self._current_task = None
        return result

    # ── 内部推理方法 ──────────────────────────────────────────────────────────

    def _think(self, task: AgentTask) -> str:
        """思考阶段：理解任务、收集相关记忆、形成初步判断"""
        recent_memory = self.memory.recall_recent(3)
        memory_context = ""
        if recent_memory:
            memory_context = "\n\n我的近期记忆：\n" + "\n".join(
                f"- {m['key']}: {str(m['value'])[:100]}" for m in recent_memory
            )

        prompt = (
            f"你是 {self.role}。\n"
            f"你的目标：{self.goal}\n"
            f"你的背景：{self.backstory}\n"
            f"{memory_context}\n\n"
            f"当前任务：{task.title}\n"
            f"任务描述：{task.description}\n"
            f"任务上下文：{json.dumps(task.context, ensure_ascii=False)}\n\n"
            f"请思考：\n"
            f"1. 这个任务的核心挑战是什么？\n"
            f"2. 基于你的专业知识，最佳解决思路是什么？\n"
            f"3. 有哪些潜在风险需要考虑？"
        )
        return _call_llm(prompt, model=self.llm_model)

    def _plan(self, task: AgentTask, thought: str) -> List[str]:
        """规划阶段：将任务分解为具体的执行步骤"""
        prompt = (
            f"你是 {self.role}，已完成初步思考：\n{thought}\n\n"
            f"任务：{task.title}\n"
            f"请制定详细的执行计划，列出 3-6 个具体可执行的步骤。\n"
            f"每个步骤单独一行，以数字开头（如 '1. ...'）。"
        )
        plan_text = _call_llm(prompt, model=self.llm_model)

        # 解析步骤列表
        steps = []
        for line in plan_text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                clean = line.lstrip("0123456789.-）) ").strip()
                if clean:
                    steps.append(clean)
        return steps if steps else ["分析需求", "设计方案", "实施执行", "验证结果"]

    @abstractmethod
    def execute(
        self,
        task: AgentTask,
        thought: str,
        plan: List[str],
    ) -> Dict[str, Any]:
        """
        执行阶段（子类必须实现）

        Parameters
        ----------
        task    : 当前任务
        thought : 思考阶段的推理结果
        plan    : 规划阶段生成的步骤列表

        Returns
        -------
        dict with keys:
            - output (str)           : 主输出文本
            - artifacts (dict)       : 代码、报告等产出物
        """

    def _summarize(self, task: AgentTask, output: str) -> str:
        """总结阶段：提炼执行结果，形成可被其他智能体使用的摘要"""
        prompt = (
            f"你是 {self.role}。\n"
            f"你刚完成了任务 '{task.title}'，执行结果如下：\n{output[:800]}\n\n"
            f"请用 2-3 句话总结：完成了什么、关键产出是什么、其他智能体需要知道什么。"
        )
        return _call_llm(prompt, model=self.llm_model)

    # ── 状态查询 ──────────────────────────────────────────────────────────────

    def get_status_dict(self) -> Dict[str, Any]:
        """返回智能体当前状态的字典表示"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "status": self.status.value,
            "is_busy": self.is_busy,
            "task_count": self.task_count,
            "current_task": (
                self._current_task.title if self._current_task else None
            ),
        }

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务历史（最近 limit 条）"""
        return [r.to_dict() for r in self._task_history[-limit:]]

    def __repr__(self) -> str:
        return f"<Agent {self.name} [{self.status.value}]>"
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
