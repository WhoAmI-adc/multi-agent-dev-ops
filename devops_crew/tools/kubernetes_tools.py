"""
Kubernetes 集群操作工具模块

提供 Kubernetes 集群管理和操作功能，包括：
- Pod 列表和状态查询
- Pod 重启操作
- Deployment 扩缩容
- Pod 日志获取

注：本模块使用模拟数据演示功能，生产环境中需集成真实 Kubernetes API（kubectl/client-go）。
"""

import json
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

from crewai.tools import tool

logger = logging.getLogger(__name__)

# 模拟 Pod 数据
MOCK_PODS = [
    {
        "name": "api-server-7d9f8b6c5-x2k4p",
        "namespace": "production",
        "deployment": "api-server",
        "node": "node-1",
        "status": "Running",
        "ready": "1/1",
        "restarts": 0,
        "cpu_request": "200m",
        "cpu_limit": "1000m",
        "cpu_usage": "850m",
        "memory_request": "256Mi",
        "memory_limit": "1Gi",
        "memory_usage": "768Mi",
        "ip": "10.244.1.10",
        "created": "2026-04-13T07:00:00",
        "phase": "Running",
        "conditions": {
            "PodScheduled": True,
            "Initialized": True,
            "ContainersReady": True,
            "Ready": True,
        },
    },
    {
        "name": "api-server-7d9f8b6c5-m8n3r",
        "namespace": "production",
        "deployment": "api-server",
        "node": "node-2",
        "status": "Running",
        "ready": "1/1",
        "restarts": 1,
        "cpu_request": "200m",
        "cpu_limit": "1000m",
        "cpu_usage": "920m",
        "memory_request": "256Mi",
        "memory_limit": "1Gi",
        "memory_usage": "812Mi",
        "ip": "10.244.2.15",
        "created": "2026-04-13T07:00:00",
        "phase": "Running",
        "conditions": {
            "PodScheduled": True,
            "Initialized": True,
            "ContainersReady": True,
            "Ready": True,
        },
    },
    {
        "name": "mysql-db-0",
        "namespace": "production",
        "deployment": "mysql-db",
        "node": "node-1",
        "status": "Running",
        "ready": "1/1",
        "restarts": 0,
        "cpu_request": "500m",
        "cpu_limit": "2000m",
        "cpu_usage": "1800m",
        "memory_request": "1Gi",
        "memory_limit": "4Gi",
        "memory_usage": "3.8Gi",
        "ip": "10.244.1.20",
        "created": "2026-04-09T20:00:00",
        "phase": "Running",
        "conditions": {
            "PodScheduled": True,
            "Initialized": True,
            "ContainersReady": True,
            "Ready": True,
        },
    },
    {
        "name": "redis-cache-0",
        "namespace": "production",
        "deployment": "redis-cache",
        "node": "node-2",
        "status": "Running",
        "ready": "1/1",
        "restarts": 0,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "cpu_usage": "45m",
        "memory_request": "128Mi",
        "memory_limit": "256Mi",
        "memory_usage": "120Mi",
        "ip": "10.244.2.30",
        "created": "2026-04-09T20:00:00",
        "phase": "Running",
        "conditions": {
            "PodScheduled": True,
            "Initialized": True,
            "ContainersReady": True,
            "Ready": True,
        },
    },
    {
        "name": "worker-service-6b4d9c8f7-k9j2l",
        "namespace": "production",
        "deployment": "worker-service",
        "node": "node-3",
        "status": "CrashLoopBackOff",
        "ready": "0/1",
        "restarts": 8,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "cpu_usage": "0m",
        "memory_request": "128Mi",
        "memory_limit": "512Mi",
        "memory_usage": "0Mi",
        "ip": "10.244.3.40",
        "created": "2026-04-13T06:50:00",
        "phase": "Running",
        "conditions": {
            "PodScheduled": True,
            "Initialized": True,
            "ContainersReady": False,
            "Ready": False,
        },
    },
    {
        "name": "nginx-proxy-5f6d8b9c4-p1q3r",
        "namespace": "production",
        "deployment": "nginx-proxy",
        "node": "node-2",
        "status": "Running",
        "ready": "1/1",
        "restarts": 0,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "cpu_usage": "78m",
        "memory_request": "64Mi",
        "memory_limit": "128Mi",
        "memory_usage": "58Mi",
        "ip": "10.244.2.5",
        "created": "2026-04-10T07:55:00",
        "phase": "Running",
        "conditions": {
            "PodScheduled": True,
            "Initialized": True,
            "ContainersReady": True,
            "Ready": True,
        },
    },
]

# 模拟 Deployment 数据
MOCK_DEPLOYMENTS = {
    "api-server": {
        "name": "api-server",
        "namespace": "production",
        "replicas": 2,
        "ready_replicas": 2,
        "available_replicas": 2,
        "updated_replicas": 2,
        "image": "company/api-server:v2.1.0",
        "strategy": "RollingUpdate",
        "max_surge": "1",
        "max_unavailable": "0",
        "labels": {"app": "api-server", "version": "v2.1.0"},
        "created": "2026-04-10T08:00:00",
    },
    "mysql-db": {
        "name": "mysql-db",
        "namespace": "production",
        "replicas": 1,
        "ready_replicas": 1,
        "available_replicas": 1,
        "updated_replicas": 1,
        "image": "mysql:8.0.35",
        "strategy": "Recreate",
        "labels": {"app": "mysql-db"},
        "created": "2026-04-09T20:00:00",
    },
    "redis-cache": {
        "name": "redis-cache",
        "namespace": "production",
        "replicas": 1,
        "ready_replicas": 1,
        "available_replicas": 1,
        "updated_replicas": 1,
        "image": "redis:7.0.12",
        "strategy": "Recreate",
        "labels": {"app": "redis-cache"},
        "created": "2026-04-09T20:00:00",
    },
    "worker-service": {
        "name": "worker-service",
        "namespace": "production",
        "replicas": 1,
        "ready_replicas": 0,
        "available_replicas": 0,
        "updated_replicas": 1,
        "image": "company/worker-service:v2.1.0",
        "strategy": "RollingUpdate",
        "labels": {"app": "worker-service"},
        "created": "2026-04-10T08:10:00",
    },
    "nginx-proxy": {
        "name": "nginx-proxy",
        "namespace": "production",
        "replicas": 2,
        "ready_replicas": 2,
        "available_replicas": 2,
        "updated_replicas": 2,
        "image": "nginx:1.25",
        "strategy": "RollingUpdate",
        "labels": {"app": "nginx-proxy"},
        "created": "2026-04-10T07:55:00",
    },
}

# 模拟 Pod 日志
MOCK_POD_LOGS = {
    "worker-service-6b4d9c8f7-k9j2l": [
        "[2026-04-13 07:20:01] INFO: Starting worker-service v2.1.0",
        "[2026-04-13 07:20:02] INFO: Loading configuration from /etc/config/app.yaml",
        "[2026-04-13 07:20:02] ERROR: Failed to connect to RabbitMQ at rabbitmq:5672",
        "[2026-04-13 07:20:02] ERROR: Connection refused: No route to host",
        "[2026-04-13 07:20:02] FATAL: Critical dependency unavailable, exiting...",
        "[Previous container crashed, restarting... (attempt 8)]",
    ],
    "api-server-7d9f8b6c5-x2k4p": [
        "[2026-04-13 07:00:02] INFO: Application started",
        "[2026-04-13 07:10:45] ERROR: DB pool exhausted",
        "[2026-04-13 07:15:00] ERROR: DB pool exhausted",
    ],
}


@tool("list_pods")
def list_pods(
    namespace: str = "production",
    deployment: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> str:
    """
    列出 Kubernetes 集群中的 Pod。

    Args:
        namespace: Kubernetes 命名空间（默认 'production'）
        deployment: 按 Deployment 名称过滤（可选）
        status_filter: 按状态过滤，如 'Running'、'CrashLoopBackOff'（可选）

    Returns:
        JSON 格式的 Pod 列表
    """
    logger.info(
        "列出Pod: namespace='%s', deployment='%s', status='%s'",
        namespace,
        deployment,
        status_filter,
    )

    pods = [p for p in MOCK_PODS if p["namespace"] == namespace]

    if deployment:
        pods = [p for p in pods if p["deployment"] == deployment]

    if status_filter:
        pods = [p for p in pods if p["status"] == status_filter]

    # 统计
    running = sum(1 for p in pods if p["status"] == "Running" and p["ready"] != "0/1")
    not_ready = sum(1 for p in pods if "0/" in p.get("ready", ""))

    result = {
        "namespace": namespace,
        "total_pods": len(pods),
        "running": running,
        "not_ready": not_ready,
        "pods": [
            {
                "name": p["name"],
                "deployment": p["deployment"],
                "node": p["node"],
                "status": p["status"],
                "ready": p["ready"],
                "restarts": p["restarts"],
                "cpu_usage": p["cpu_usage"],
                "memory_usage": p["memory_usage"],
                "ip": p["ip"],
                "age": _calculate_age(p["created"]),
            }
            for p in pods
        ],
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_pod_status")
def get_pod_status(pod_name: str, namespace: str = "production") -> str:
    """
    获取指定 Pod 的详细状态信息。

    Args:
        pod_name: Pod 名称
        namespace: Kubernetes 命名空间（默认 'production'）

    Returns:
        JSON 格式的 Pod 详细状态
    """
    logger.info("获取Pod状态: pod='%s', namespace='%s'", pod_name, namespace)

    pod = next(
        (p for p in MOCK_PODS if p["name"] == pod_name and p["namespace"] == namespace),
        None,
    )

    if not pod:
        available = [p["name"] for p in MOCK_PODS if p["namespace"] == namespace]
        return json.dumps(
            {
                "error": f"Pod '{pod_name}' 在命名空间 '{namespace}' 中不存在",
                "available_pods": available,
            },
            ensure_ascii=False,
        )

    # 生成问题诊断
    issues = []
    if pod["restarts"] > 3:
        issues.append({
            "type": "频繁重启",
            "severity": "HIGH",
            "description": f"Pod 已重启 {pod['restarts']} 次，可能存在崩溃循环",
        })
    if pod["status"] == "CrashLoopBackOff":
        issues.append({
            "type": "崩溃循环",
            "severity": "CRITICAL",
            "description": "Pod 处于 CrashLoopBackOff 状态，启动失败后不断重试",
        })
    if not pod["conditions"].get("Ready"):
        issues.append({
            "type": "未就绪",
            "severity": "HIGH",
            "description": "Pod 健康检查未通过，无法接收流量",
        })

    result = {
        "name": pod["name"],
        "namespace": pod["namespace"],
        "deployment": pod["deployment"],
        "node": pod["node"],
        "ip": pod["ip"],
        "status": pod["status"],
        "ready": pod["ready"],
        "restarts": pod["restarts"],
        "phase": pod["phase"],
        "created": pod["created"],
        "age": _calculate_age(pod["created"]),
        "resources": {
            "cpu": {
                "request": pod["cpu_request"],
                "limit": pod["cpu_limit"],
                "usage": pod["cpu_usage"],
            },
            "memory": {
                "request": pod["memory_request"],
                "limit": pod["memory_limit"],
                "usage": pod["memory_usage"],
            },
        },
        "conditions": pod["conditions"],
        "issues": issues,
        "health": "healthy" if not issues else ("critical" if any(i["severity"] == "CRITICAL" for i in issues) else "warning"),
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("restart_pod")
def restart_pod(pod_name: str, namespace: str = "production") -> str:
    """
    重启指定的 Kubernetes Pod（通过删除 Pod 触发重新调度）。

    Args:
        pod_name: Pod 名称
        namespace: Kubernetes 命名空间（默认 'production'）

    Returns:
        JSON 格式的重启结果
    """
    logger.info("重启Pod: pod='%s', namespace='%s'", pod_name, namespace)

    pod = next(
        (p for p in MOCK_PODS if p["name"] == pod_name and p["namespace"] == namespace),
        None,
    )

    if not pod:
        return json.dumps(
            {"success": False, "error": f"Pod '{pod_name}' 不存在"},
            ensure_ascii=False,
        )

    # 生成新的 Pod 名称（模拟 K8s 重新调度）
    new_pod_suffix = "".join(random.choices("abcdefghijklmnop0123456789", k=5))
    base_name = pod["name"].rsplit("-", 1)[0]
    new_pod_name = f"{base_name}-{new_pod_suffix}"

    result = {
        "success": True,
        "action": "delete_and_reschedule",
        "old_pod": pod_name,
        "new_pod": new_pod_name,
        "deployment": pod["deployment"],
        "namespace": namespace,
        "node": pod["node"],
        "timeline": [
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "event": f"Pod '{pod_name}' 删除请求已发送",
            },
            {
                "time": (datetime.now() + timedelta(seconds=2)).strftime("%H:%M:%S"),
                "event": "Pod 正在终止（Terminating）",
            },
            {
                "time": (datetime.now() + timedelta(seconds=5)).strftime("%H:%M:%S"),
                "event": f"新 Pod '{new_pod_name}' 已调度到 {pod['node']}",
            },
            {
                "time": (datetime.now() + timedelta(seconds=15)).strftime("%H:%M:%S"),
                "event": "容器镜像拉取完成",
            },
            {
                "time": (datetime.now() + timedelta(seconds=20)).strftime("%H:%M:%S"),
                "event": "容器启动成功",
            },
            {
                "time": (datetime.now() + timedelta(seconds=30)).strftime("%H:%M:%S"),
                "event": "健康检查通过，Pod 进入 Ready 状态",
            },
        ],
        "total_time": "~30s",
        "message": f"Pod '{pod_name}' 已重启，新 Pod 名称: '{new_pod_name}'",
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("scale_deployment")
def scale_deployment(
    deployment_name: str,
    replicas: int,
    namespace: str = "production",
) -> str:
    """
    对 Kubernetes Deployment 进行扩缩容操作。

    Args:
        deployment_name: Deployment 名称
        replicas: 目标副本数量
        namespace: Kubernetes 命名空间（默认 'production'）

    Returns:
        JSON 格式的扩缩容结果
    """
    logger.info(
        "扩缩容Deployment: %s -> %d 副本 (namespace: %s)",
        deployment_name,
        replicas,
        namespace,
    )

    if deployment_name not in MOCK_DEPLOYMENTS:
        return json.dumps(
            {
                "success": False,
                "error": f"Deployment '{deployment_name}' 不存在",
                "available": list(MOCK_DEPLOYMENTS.keys()),
            },
            ensure_ascii=False,
        )

    if replicas < 0:
        return json.dumps(
            {"success": False, "error": "副本数不能为负数"},
            ensure_ascii=False,
        )

    if replicas > 20:
        return json.dumps(
            {"success": False, "error": "副本数超过允许上限（20）"},
            ensure_ascii=False,
        )

    deployment = MOCK_DEPLOYMENTS[deployment_name]
    old_replicas = deployment["replicas"]
    action = "扩容" if replicas > old_replicas else ("缩容" if replicas < old_replicas else "无变化")

    # 估算完成时间
    diff = abs(replicas - old_replicas)
    estimated_time = f"~{diff * 30}s" if diff > 0 else "立即完成"

    result = {
        "success": True,
        "deployment": deployment_name,
        "namespace": namespace,
        "action": action,
        "old_replicas": old_replicas,
        "new_replicas": replicas,
        "strategy": deployment.get("strategy", "RollingUpdate"),
        "estimated_completion": estimated_time,
        "scaling_events": _generate_scaling_events(deployment_name, old_replicas, replicas),
        "message": f"Deployment '{deployment_name}' 已{action}：{old_replicas} -> {replicas} 副本",
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_pod_logs")
def get_pod_logs(
    pod_name: str,
    namespace: str = "production",
    container: Optional[str] = None,
    lines: int = 50,
    previous: bool = False,
) -> str:
    """
    获取指定 Pod 的日志。

    Args:
        pod_name: Pod 名称
        namespace: Kubernetes 命名空间（默认 'production'）
        container: 容器名称（Pod 内有多个容器时使用，可选）
        lines: 获取最近N行日志（默认50）
        previous: 是否获取上一个容器实例的日志（用于查看崩溃原因）

    Returns:
        JSON 格式的 Pod 日志
    """
    logger.info(
        "获取Pod日志: pod='%s', namespace='%s', previous=%s", pod_name, namespace, previous
    )

    pod = next(
        (p for p in MOCK_PODS if p["name"] == pod_name and p["namespace"] == namespace),
        None,
    )

    if not pod:
        return json.dumps(
            {"error": f"Pod '{pod_name}' 不存在"},
            ensure_ascii=False,
        )

    # 获取模拟日志
    pod_logs = MOCK_POD_LOGS.get(pod_name, [
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: {pod['deployment']} started",
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Ready to serve requests",
    ])

    # 取最后N行
    pod_logs = pod_logs[-lines:]

    result = {
        "pod_name": pod_name,
        "namespace": namespace,
        "container": container or pod["deployment"],
        "deployment": pod["deployment"],
        "previous_container": previous,
        "total_lines": len(pod_logs),
        "logs": pod_logs,
        "pod_status": pod["status"],
        "restart_count": pod["restarts"],
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def _calculate_age(created_time: str) -> str:
    """计算 Pod 年龄"""
    try:
        created = datetime.fromisoformat(created_time)
        now = datetime.now()
        delta = now - created
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if days > 0:
            return f"{days}d{hours}h"
        elif hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"
    except Exception:
        return "Unknown"


def _generate_scaling_events(deployment: str, old: int, new: int) -> list:
    """生成扩缩容事件列表"""
    events = []
    now = datetime.now()

    if old == new:
        events.append({
            "time": now.strftime("%H:%M:%S"),
            "event": f"副本数无变化，维持 {new} 个副本",
        })
        return events

    events.append({
        "time": now.strftime("%H:%M:%S"),
        "event": f"Deployment '{deployment}' 副本数更新: {old} -> {new}",
    })

    if new > old:
        for i in range(new - old):
            events.append({
                "time": (now + timedelta(seconds=10 + i * 30)).strftime("%H:%M:%S"),
                "event": f"新 Pod #{old + i + 1} 已启动并通过健康检查",
            })
    else:
        for i in range(old - new):
            events.append({
                "time": (now + timedelta(seconds=5 + i * 15)).strftime("%H:%M:%S"),
                "event": f"Pod #{old - i} 已优雅停止",
            })

    events.append({
        "time": (now + timedelta(seconds=abs(new - old) * 30 + 15)).strftime("%H:%M:%S"),
        "event": f"扩缩容完成，当前运行 {new} 个副本",
    })

    return events
