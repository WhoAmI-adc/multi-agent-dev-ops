"""
Docker 容器操作工具模块

提供 Docker 容器管理的核心功能，包括：
- 容器列表查询
- 容器状态监控
- 容器重启操作
- 容器日志获取
- 镜像构建

注：本模块使用模拟数据演示功能，生产环境中需集成真实 Docker API。
"""

import json
import random
import logging
from datetime import datetime, timedelta
from typing import Optional
from crewai.tools import tool

logger = logging.getLogger(__name__)

# 模拟容器数据
MOCK_CONTAINERS = [
    {
        "id": "a1b2c3d4e5f6",
        "name": "web-frontend",
        "image": "nginx:1.25",
        "status": "running",
        "created": "2026-04-10T08:00:00Z",
        "ports": {"80/tcp": 8080, "443/tcp": 8443},
        "cpu_percent": 12.5,
        "memory_usage": "256MB",
        "memory_limit": "512MB",
        "restart_count": 0,
    },
    {
        "id": "b2c3d4e5f6a1",
        "name": "api-server",
        "image": "python:3.11-slim",
        "status": "running",
        "created": "2026-04-10T08:05:00Z",
        "ports": {"8000/tcp": 8000},
        "cpu_percent": 45.2,
        "memory_usage": "512MB",
        "memory_limit": "1GB",
        "restart_count": 2,
    },
    {
        "id": "c3d4e5f6a1b2",
        "name": "mysql-db",
        "image": "mysql:8.0",
        "status": "running",
        "created": "2026-04-09T20:00:00Z",
        "ports": {"3306/tcp": 3306},
        "cpu_percent": 78.9,
        "memory_usage": "2.1GB",
        "memory_limit": "4GB",
        "restart_count": 0,
    },
    {
        "id": "d4e5f6a1b2c3",
        "name": "redis-cache",
        "image": "redis:7.0",
        "status": "running",
        "created": "2026-04-09T20:00:00Z",
        "ports": {"6379/tcp": 6379},
        "cpu_percent": 5.1,
        "memory_usage": "128MB",
        "memory_limit": "256MB",
        "restart_count": 0,
    },
    {
        "id": "e5f6a1b2c3d4",
        "name": "worker-service",
        "image": "python:3.11-slim",
        "status": "exited",
        "created": "2026-04-10T08:10:00Z",
        "ports": {},
        "cpu_percent": 0.0,
        "memory_usage": "0MB",
        "memory_limit": "512MB",
        "restart_count": 5,
    },
    {
        "id": "f6a1b2c3d4e5",
        "name": "nginx-proxy",
        "image": "nginx:1.25",
        "status": "running",
        "created": "2026-04-10T07:55:00Z",
        "ports": {"80/tcp": 80, "443/tcp": 443},
        "cpu_percent": 8.3,
        "memory_usage": "64MB",
        "memory_limit": "128MB",
        "restart_count": 0,
    },
]

# 模拟容器日志
MOCK_LOGS = {
    "web-frontend": [
        "[2026-04-13 07:00:01] INFO: Nginx started successfully",
        "[2026-04-13 07:00:05] INFO: Listening on :80 and :443",
        "[2026-04-13 07:15:23] INFO: GET /api/health 200 0.002s",
        "[2026-04-13 07:16:45] INFO: GET /dashboard 200 0.045s",
        "[2026-04-13 07:20:11] WARN: Upstream response timeout, retrying...",
        "[2026-04-13 07:20:12] INFO: GET /dashboard 200 0.523s (retry)",
    ],
    "api-server": [
        "[2026-04-13 07:00:02] INFO: Application started on port 8000",
        "[2026-04-13 07:00:03] INFO: Connected to MySQL at mysql-db:3306",
        "[2026-04-13 07:00:03] INFO: Connected to Redis at redis-cache:6379",
        "[2026-04-13 07:10:45] ERROR: Database connection pool exhausted (pool_size=20)",
        "[2026-04-13 07:10:46] ERROR: Request failed: timeout waiting for DB connection",
        "[2026-04-13 07:10:47] WARN: Pool utilization at 100%, consider increasing pool size",
        "[2026-04-13 07:11:00] INFO: Slow query detected: SELECT * FROM orders (took 8.3s)",
        "[2026-04-13 07:15:00] ERROR: Database connection pool exhausted (pool_size=20)",
    ],
    "mysql-db": [
        "[2026-04-13 07:00:00] INFO: MySQL 8.0 started",
        "[2026-04-13 07:00:01] INFO: Ready for connections on port 3306",
        "[2026-04-13 07:05:30] WARN: Too many connections: current 198, max 200",
        "[2026-04-13 07:10:45] ERROR: Connection refused: max_connections reached",
        "[2026-04-13 07:10:46] WARN: InnoDB buffer pool at 95% capacity",
        "[2026-04-13 07:15:00] ERROR: Connection refused: max_connections reached",
    ],
    "redis-cache": [
        "[2026-04-13 07:00:00] INFO: Redis 7.0 started",
        "[2026-04-13 07:00:01] INFO: Ready to accept connections",
        "[2026-04-13 07:00:10] INFO: Loading RDB snapshot...",
        "[2026-04-13 07:00:11] INFO: RDB loaded successfully",
    ],
    "worker-service": [
        "[2026-04-13 06:55:00] INFO: Worker service starting...",
        "[2026-04-13 06:55:01] ERROR: Failed to connect to RabbitMQ: connection refused",
        "[2026-04-13 06:55:01] ERROR: Application startup failed",
        "[2026-04-13 06:55:02] INFO: Container exited with code 1",
    ],
    "nginx-proxy": [
        "[2026-04-13 07:00:00] INFO: Nginx proxy started",
        "[2026-04-13 07:00:01] INFO: Upstream pool: api-server:8000 (1 server)",
        "[2026-04-13 07:15:20] WARN: Upstream api-server slow response: 2.3s",
        "[2026-04-13 07:20:00] INFO: Health check passed for all upstreams",
    ],
}


@tool("list_containers")
def list_containers(status_filter: str = "all") -> str:
    """
    列出 Docker 环境中的所有容器。

    Args:
        status_filter: 过滤器，可选值为 'all'、'running'、'exited'、'stopped'

    Returns:
        JSON 格式的容器列表信息
    """
    logger.info("列出容器，过滤器: %s", status_filter)

    containers = MOCK_CONTAINERS
    if status_filter != "all":
        containers = [c for c in containers if c["status"] == status_filter]

    summary = {
        "total": len(containers),
        "running": sum(1 for c in MOCK_CONTAINERS if c["status"] == "running"),
        "exited": sum(1 for c in MOCK_CONTAINERS if c["status"] == "exited"),
        "containers": [
            {
                "id": c["id"][:12],
                "name": c["name"],
                "image": c["image"],
                "status": c["status"],
                "ports": c["ports"],
                "restart_count": c["restart_count"],
            }
            for c in containers
        ],
    }

    return json.dumps(summary, ensure_ascii=False, indent=2)


@tool("get_container_status")
def get_container_status(container_name: str) -> str:
    """
    获取指定容器的详细状态信息。

    Args:
        container_name: 容器名称

    Returns:
        JSON 格式的容器状态详情
    """
    logger.info("获取容器状态: %s", container_name)

    container = next(
        (c for c in MOCK_CONTAINERS if c["name"] == container_name), None
    )

    if not container:
        return json.dumps(
            {"error": f"容器 '{container_name}' 不存在", "available": [c["name"] for c in MOCK_CONTAINERS]},
            ensure_ascii=False,
        )

    # 模拟动态指标
    status_detail = {
        "id": container["id"],
        "name": container["name"],
        "image": container["image"],
        "status": container["status"],
        "created": container["created"],
        "uptime": _calculate_uptime(container["created"]),
        "ports": container["ports"],
        "resources": {
            "cpu_percent": container["cpu_percent"] + random.uniform(-2, 2),
            "memory_usage": container["memory_usage"],
            "memory_limit": container["memory_limit"],
            "memory_percent": _parse_memory_percent(
                container["memory_usage"], container["memory_limit"]
            ),
        },
        "restart_count": container["restart_count"],
        "health": "healthy" if container["status"] == "running" and container["restart_count"] < 3 else "unhealthy",
    }

    return json.dumps(status_detail, ensure_ascii=False, indent=2)


@tool("restart_container")
def restart_container(container_name: str, timeout: int = 30) -> str:
    """
    重启指定的 Docker 容器。

    Args:
        container_name: 要重启的容器名称
        timeout: 等待容器停止的超时时间（秒）

    Returns:
        JSON 格式的重启结果
    """
    logger.info("重启容器: %s (超时: %ds)", container_name, timeout)

    container = next(
        (c for c in MOCK_CONTAINERS if c["name"] == container_name), None
    )

    if not container:
        return json.dumps(
            {"success": False, "error": f"容器 '{container_name}' 不存在"},
            ensure_ascii=False,
        )

    # 模拟重启过程
    restart_time = datetime.now()
    result = {
        "success": True,
        "container_name": container_name,
        "container_id": container["id"][:12],
        "actions": [
            {
                "step": "发送停止信号 (SIGTERM)",
                "time": restart_time.strftime("%H:%M:%S"),
                "status": "completed",
            },
            {
                "step": f"等待容器停止（最多 {timeout}s）",
                "time": (restart_time + timedelta(seconds=2)).strftime("%H:%M:%S"),
                "status": "completed",
                "elapsed": "2s",
            },
            {
                "step": "启动容器",
                "time": (restart_time + timedelta(seconds=3)).strftime("%H:%M:%S"),
                "status": "completed",
            },
            {
                "step": "健康检查",
                "time": (restart_time + timedelta(seconds=8)).strftime("%H:%M:%S"),
                "status": "completed",
                "result": "passed",
            },
        ],
        "new_status": "running",
        "total_time": "8s",
        "message": f"容器 '{container_name}' 已成功重启",
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_container_logs")
def get_container_logs(
    container_name: str,
    lines: int = 50,
    since: Optional[str] = None,
    level_filter: Optional[str] = None,
) -> str:
    """
    获取指定容器的日志。

    Args:
        container_name: 容器名称
        lines: 获取最近N行日志
        since: 从指定时间开始的日志（格式：HH:MM:SS 或 ISO8601）
        level_filter: 日志级别过滤（ERROR/WARN/INFO）

    Returns:
        容器日志内容
    """
    logger.info(
        "获取容器日志: %s (行数: %d, 级别: %s)", container_name, lines, level_filter
    )

    if container_name not in MOCK_LOGS:
        return json.dumps(
            {
                "error": f"容器 '{container_name}' 的日志不存在",
                "available_containers": list(MOCK_LOGS.keys()),
            },
            ensure_ascii=False,
        )

    logs = MOCK_LOGS[container_name]

    # 按级别过滤
    if level_filter:
        logs = [log for log in logs if level_filter.upper() in log]

    # 取最后N行
    logs = logs[-lines:]

    result = {
        "container_name": container_name,
        "total_lines": len(logs),
        "filter_applied": level_filter,
        "logs": logs,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("build_image")
def build_image(
    image_name: str,
    tag: str = "latest",
    dockerfile_path: str = ".",
    build_args: Optional[dict] = None,
) -> str:
    """
    构建 Docker 镜像。

    Args:
        image_name: 镜像名称
        tag: 镜像标签
        dockerfile_path: Dockerfile 所在路径
        build_args: 构建参数字典

    Returns:
        JSON 格式的构建结果
    """
    logger.info("构建镜像: %s:%s (路径: %s)", image_name, tag, dockerfile_path)

    full_image_name = f"{image_name}:{tag}"
    build_start = datetime.now()

    # 模拟构建步骤
    build_steps = [
        {"step": 1, "description": "从缓存加载基础镜像", "time": "0.5s", "status": "cached"},
        {"step": 2, "description": "安装系统依赖", "time": "15.2s", "status": "completed"},
        {"step": 3, "description": "复制应用代码", "time": "0.3s", "status": "completed"},
        {"step": 4, "description": "安装 Python 依赖（pip install）", "time": "45.8s", "status": "completed"},
        {"step": 5, "description": "配置环境变量", "time": "0.1s", "status": "completed"},
        {"step": 6, "description": "运行测试", "time": "12.4s", "status": "completed"},
        {"step": 7, "description": "清理构建缓存", "time": "1.2s", "status": "completed"},
    ]

    result = {
        "success": True,
        "image_name": full_image_name,
        "image_id": "sha256:" + "".join(random.choices("0123456789abcdef", k=12)),
        "dockerfile_path": dockerfile_path,
        "build_args": build_args or {},
        "build_steps": build_steps,
        "image_size": "487MB",
        "build_time": "75.5s",
        "started_at": build_start.isoformat(),
        "completed_at": (build_start + timedelta(seconds=75)).isoformat(),
        "cache_used": True,
        "layers_created": 7,
        "message": f"镜像 '{full_image_name}' 构建成功",
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def _calculate_uptime(created_time: str) -> str:
    """计算容器运行时间"""
    try:
        created = datetime.fromisoformat(created_time.replace("Z", "+00:00"))
        now = datetime.now().astimezone()
        delta = now - created
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{minutes}分钟"
    except Exception:
        return "未知"


def _parse_memory_percent(usage: str, limit: str) -> float:
    """计算内存使用百分比"""
    try:
        def parse_mb(s):
            s = s.upper().strip()
            if s.endswith("GB"):
                return float(s[:-2]) * 1024
            elif s.endswith("MB"):
                return float(s[:-2])
            return float(s)

        return round(parse_mb(usage) / parse_mb(limit) * 100, 1)
    except Exception:
        return 0.0
