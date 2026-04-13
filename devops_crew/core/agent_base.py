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
            "deadline": self.deadline,
            "created_at": self.created_at,
        }

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
