"""
系统监控工具模块

提供系统资源监控和服务健康检查功能，包括：
- CPU 使用率监控
- 内存使用率监控
- 磁盘使用率监控
- 服务健康检查
- 告警管理

注：本模块使用模拟数据演示功能，生产环境中可集成 Prometheus、Zabbix 等监控系统。
"""

import json
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

from crewai.tools import tool

logger = logging.getLogger(__name__)

# 模拟服务监控数据
MOCK_SERVICES = {
    "api-server": {
        "host": "10.0.1.10",
        "port": 8000,
        "protocol": "http",
        "health_endpoint": "/api/health",
        "status": "degraded",
        "response_time_ms": 2340,
        "uptime_percent": 99.2,
        "last_check": "2026-04-13T07:20:00",
    },
    "mysql-db": {
        "host": "10.0.1.20",
        "port": 3306,
        "protocol": "tcp",
        "health_endpoint": None,
        "status": "warning",
        "response_time_ms": 450,
        "uptime_percent": 99.8,
        "last_check": "2026-04-13T07:20:00",
    },
    "redis-cache": {
        "host": "10.0.1.30",
        "port": 6379,
        "protocol": "tcp",
        "health_endpoint": None,
        "status": "healthy",
        "response_time_ms": 2,
        "uptime_percent": 100.0,
        "last_check": "2026-04-13T07:20:00",
    },
    "nginx-proxy": {
        "host": "10.0.1.5",
        "port": 80,
        "protocol": "http",
        "health_endpoint": "/health",
        "status": "healthy",
        "response_time_ms": 15,
        "uptime_percent": 99.99,
        "last_check": "2026-04-13T07:20:00",
    },
    "worker-service": {
        "host": "10.0.1.40",
        "port": 9000,
        "protocol": "http",
        "health_endpoint": "/health",
        "status": "down",
        "response_time_ms": None,
        "uptime_percent": 85.0,
        "last_check": "2026-04-13T07:20:00",
    },
}

# 模拟节点资源数据
MOCK_NODES = {
    "node-1": {
        "ip": "10.0.1.1",
        "role": "master",
        "cpu_cores": 8,
        "cpu_percent": 72.5,
        "memory_total_gb": 16,
        "memory_used_gb": 13.8,
        "memory_percent": 86.3,
        "disk_total_gb": 200,
        "disk_used_gb": 145,
        "disk_percent": 72.5,
        "disk_io_read_mbps": 45.2,
        "disk_io_write_mbps": 23.8,
        "network_in_mbps": 125.6,
        "network_out_mbps": 87.3,
        "load_average": [3.2, 3.8, 4.1],
    },
    "node-2": {
        "ip": "10.0.1.2",
        "role": "worker",
        "cpu_cores": 8,
        "cpu_percent": 45.2,
        "memory_total_gb": 16,
        "memory_used_gb": 8.4,
        "memory_percent": 52.5,
        "disk_total_gb": 200,
        "disk_used_gb": 98,
        "disk_percent": 49.0,
        "disk_io_read_mbps": 12.5,
        "disk_io_write_mbps": 8.2,
        "network_in_mbps": 56.3,
        "network_out_mbps": 42.1,
        "load_average": [1.8, 2.1, 2.3],
    },
    "node-3": {
        "ip": "10.0.1.3",
        "role": "worker",
        "cpu_cores": 8,
        "cpu_percent": 88.9,
        "memory_total_gb": 16,
        "memory_used_gb": 14.2,
        "memory_percent": 88.8,
        "disk_total_gb": 200,
        "disk_used_gb": 178,
        "disk_percent": 89.0,
        "disk_io_read_mbps": 78.5,
        "disk_io_write_mbps": 45.2,
        "network_in_mbps": 210.5,
        "network_out_mbps": 185.3,
        "load_average": [6.2, 6.8, 7.1],
    },
}

# 模拟告警数据
MOCK_ALERTS = [
    {
        "id": "alert-001",
        "severity": "critical",
        "rule": "HighCPUUsage",
        "service": "node-3",
        "message": "CPU使用率持续超过85%超过10分钟 (当前: 88.9%)",
        "started_at": "2026-04-13T07:10:00",
        "duration": "10m",
        "status": "firing",
        "labels": {"node": "node-3", "threshold": "85%"},
    },
    {
        "id": "alert-002",
        "severity": "critical",
        "rule": "HighMemoryUsage",
        "service": "node-3",
        "message": "内存使用率超过85% (当前: 88.8%)",
        "started_at": "2026-04-13T07:08:00",
        "duration": "12m",
        "status": "firing",
        "labels": {"node": "node-3", "threshold": "85%"},
    },
    {
        "id": "alert-003",
        "severity": "critical",
        "rule": "ServiceDown",
        "service": "worker-service",
        "message": "服务 worker-service 已停止运行超过25分钟",
        "started_at": "2026-04-13T06:55:00",
        "duration": "25m",
        "status": "firing",
        "labels": {"service": "worker-service"},
    },
    {
        "id": "alert-004",
        "severity": "warning",
        "rule": "HighDiskUsage",
        "service": "node-3",
        "message": "磁盘使用率超过80% (当前: 89.0%)",
        "started_at": "2026-04-13T06:30:00",
        "duration": "50m",
        "status": "firing",
        "labels": {"node": "node-3", "mount": "/", "threshold": "80%"},
    },
    {
        "id": "alert-005",
        "severity": "warning",
        "rule": "SlowResponseTime",
        "service": "api-server",
        "message": "API响应时间超过2秒 (当前: 2340ms，阈值: 2000ms)",
        "started_at": "2026-04-13T07:10:00",
        "duration": "10m",
        "status": "firing",
        "labels": {"service": "api-server", "endpoint": "/api/v1/orders"},
    },
    {
        "id": "alert-006",
        "severity": "warning",
        "rule": "HighDBConnections",
        "service": "mysql-db",
        "message": "MySQL连接数接近上限 (当前: 198/200)",
        "started_at": "2026-04-13T07:05:30",
        "duration": "14m30s",
        "status": "firing",
        "labels": {"service": "mysql-db"},
    },
]


@tool("get_cpu_usage")
def get_cpu_usage(node: Optional[str] = None) -> str:
    """
    获取系统 CPU 使用率信息。

    Args:
        node: 指定节点名称（可选，None 表示获取所有节点）

    Returns:
        JSON 格式的 CPU 使用率数据
    """
    logger.info("获取CPU使用率: node='%s'", node)

    if node and node in MOCK_NODES:
        data = MOCK_NODES[node]
        result = {
            "node": node,
            "ip": data["ip"],
            "role": data["role"],
            "cpu_cores": data["cpu_cores"],
            "cpu_percent": round(data["cpu_percent"] + random.uniform(-2, 2), 1),
            "load_average": {
                "1min": data["load_average"][0],
                "5min": data["load_average"][1],
                "15min": data["load_average"][2],
            },
            "status": "critical" if data["cpu_percent"] > 85 else ("warning" if data["cpu_percent"] > 70 else "normal"),
            "timestamp": datetime.now().isoformat(),
        }
    elif node:
        return json.dumps({"error": f"节点 '{node}' 不存在", "available": list(MOCK_NODES.keys())}, ensure_ascii=False)
    else:
        nodes_data = []
        total_cpu = 0
        for node_name, data in MOCK_NODES.items():
            cpu = round(data["cpu_percent"] + random.uniform(-1, 1), 1)
            total_cpu += cpu
            nodes_data.append({
                "node": node_name,
                "ip": data["ip"],
                "role": data["role"],
                "cpu_percent": cpu,
                "load_1min": data["load_average"][0],
                "status": "critical" if cpu > 85 else ("warning" if cpu > 70 else "normal"),
            })

        result = {
            "cluster_avg_cpu": round(total_cpu / len(MOCK_NODES), 1),
            "nodes": nodes_data,
            "high_usage_nodes": [n["node"] for n in nodes_data if n["cpu_percent"] > 80],
            "timestamp": datetime.now().isoformat(),
        }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_memory_usage")
def get_memory_usage(node: Optional[str] = None) -> str:
    """
    获取系统内存使用率信息。

    Args:
        node: 指定节点名称（可选，None 表示获取所有节点）

    Returns:
        JSON 格式的内存使用率数据
    """
    logger.info("获取内存使用率: node='%s'", node)

    if node and node in MOCK_NODES:
        data = MOCK_NODES[node]
        result = {
            "node": node,
            "ip": data["ip"],
            "total_gb": data["memory_total_gb"],
            "used_gb": data["memory_used_gb"],
            "available_gb": round(data["memory_total_gb"] - data["memory_used_gb"], 1),
            "percent": data["memory_percent"],
            "status": "critical" if data["memory_percent"] > 90 else ("warning" if data["memory_percent"] > 80 else "normal"),
            "timestamp": datetime.now().isoformat(),
        }
    elif node:
        return json.dumps({"error": f"节点 '{node}' 不存在"}, ensure_ascii=False)
    else:
        nodes_data = []
        for node_name, data in MOCK_NODES.items():
            nodes_data.append({
                "node": node_name,
                "total_gb": data["memory_total_gb"],
                "used_gb": data["memory_used_gb"],
                "percent": data["memory_percent"],
                "status": "critical" if data["memory_percent"] > 90 else ("warning" if data["memory_percent"] > 80 else "normal"),
            })

        result = {
            "nodes": nodes_data,
            "high_usage_nodes": [n["node"] for n in nodes_data if n["percent"] > 80],
            "timestamp": datetime.now().isoformat(),
        }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_disk_usage")
def get_disk_usage(node: Optional[str] = None) -> str:
    """
    获取系统磁盘使用率信息。

    Args:
        node: 指定节点名称（可选，None 表示获取所有节点）

    Returns:
        JSON 格式的磁盘使用率数据
    """
    logger.info("获取磁盘使用率: node='%s'", node)

    if node and node in MOCK_NODES:
        data = MOCK_NODES[node]
        result = {
            "node": node,
            "ip": data["ip"],
            "total_gb": data["disk_total_gb"],
            "used_gb": data["disk_used_gb"],
            "free_gb": data["disk_total_gb"] - data["disk_used_gb"],
            "percent": data["disk_percent"],
            "io": {
                "read_mbps": data["disk_io_read_mbps"],
                "write_mbps": data["disk_io_write_mbps"],
            },
            "status": "critical" if data["disk_percent"] > 90 else ("warning" if data["disk_percent"] > 80 else "normal"),
            "timestamp": datetime.now().isoformat(),
        }
    elif node:
        return json.dumps({"error": f"节点 '{node}' 不存在"}, ensure_ascii=False)
    else:
        nodes_data = []
        for node_name, data in MOCK_NODES.items():
            nodes_data.append({
                "node": node_name,
                "total_gb": data["disk_total_gb"],
                "used_gb": data["disk_used_gb"],
                "percent": data["disk_percent"],
                "status": "critical" if data["disk_percent"] > 90 else ("warning" if data["disk_percent"] > 80 else "normal"),
            })

        result = {
            "nodes": nodes_data,
            "high_usage_nodes": [n["node"] for n in nodes_data if n["percent"] > 80],
            "timestamp": datetime.now().isoformat(),
        }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("check_service_health")
def check_service_health(service_name: Optional[str] = None) -> str:
    """
    检查服务健康状态。

    Args:
        service_name: 服务名称（可选，None 表示检查所有服务）

    Returns:
        JSON 格式的服务健康状态
    """
    logger.info("检查服务健康状态: service='%s'", service_name)

    if service_name and service_name in MOCK_SERVICES:
        svc = MOCK_SERVICES[service_name]
        result = {
            "service": service_name,
            "host": svc["host"],
            "port": svc["port"],
            "status": svc["status"],
            "response_time_ms": svc["response_time_ms"],
            "uptime_percent": svc["uptime_percent"],
            "last_check": svc["last_check"],
            "health_details": _get_health_details(service_name, svc),
        }
    elif service_name:
        return json.dumps({"error": f"服务 '{service_name}' 不存在", "available": list(MOCK_SERVICES.keys())}, ensure_ascii=False)
    else:
        services_data = []
        for svc_name, svc in MOCK_SERVICES.items():
            services_data.append({
                "service": svc_name,
                "status": svc["status"],
                "response_time_ms": svc["response_time_ms"],
                "uptime_percent": svc["uptime_percent"],
            })

        healthy = sum(1 for s in services_data if s["status"] == "healthy")
        degraded = sum(1 for s in services_data if s["status"] == "degraded")
        down = sum(1 for s in services_data if s["status"] == "down")

        result = {
            "summary": {
                "total": len(services_data),
                "healthy": healthy,
                "degraded": degraded,
                "warning": sum(1 for s in services_data if s["status"] == "warning"),
                "down": down,
                "overall_status": "critical" if down > 0 else ("degraded" if degraded > 0 else "healthy"),
            },
            "services": services_data,
            "timestamp": datetime.now().isoformat(),
        }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_alerts")
def get_alerts(
    severity: Optional[str] = None,
    service: Optional[str] = None,
    status: str = "firing",
) -> str:
    """
    获取当前系统告警列表。

    Args:
        severity: 告警严重程度过滤（critical/warning/info，可选）
        service: 服务名称过滤（可选）
        status: 告警状态过滤（firing/resolved，默认 'firing'）

    Returns:
        JSON 格式的告警列表
    """
    logger.info("获取告警: severity='%s', service='%s', status='%s'", severity, service, status)

    alerts = MOCK_ALERTS

    if severity:
        alerts = [a for a in alerts if a["severity"] == severity.lower()]

    if service:
        alerts = [a for a in alerts if a["service"] == service]

    if status:
        alerts = [a for a in alerts if a["status"] == status]

    # 按严重程度排序
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts = sorted(alerts, key=lambda x: severity_order.get(x["severity"], 99))

    result = {
        "total_alerts": len(alerts),
        "critical_count": sum(1 for a in alerts if a["severity"] == "critical"),
        "warning_count": sum(1 for a in alerts if a["severity"] == "warning"),
        "alerts": alerts,
        "retrieved_at": datetime.now().isoformat(),
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def _get_health_details(service_name: str, svc: dict) -> dict:
    """获取服务健康详情"""
    details = {
        "checks": [],
        "issues": [],
        "recommendations": [],
    }

    # 响应时间检查
    if svc["response_time_ms"] is None:
        details["checks"].append({"name": "连接检查", "status": "FAIL", "message": "无法连接"})
        details["issues"].append("服务无响应")
    elif svc["response_time_ms"] > 2000:
        details["checks"].append({
            "name": "响应时间",
            "status": "WARN",
            "message": f"响应时间 {svc['response_time_ms']}ms 超过阈值 2000ms",
        })
        details["recommendations"].append("检查服务负载和数据库查询性能")
    else:
        details["checks"].append({
            "name": "响应时间",
            "status": "OK",
            "message": f"响应时间 {svc['response_time_ms']}ms 正常",
        })

    # 可用性检查
    if svc["uptime_percent"] < 99:
        details["checks"].append({
            "name": "可用性",
            "status": "WARN",
            "message": f"过去24小时可用性 {svc['uptime_percent']}% 低于目标 99%",
        })
        details["recommendations"].append("检查服务重启原因，考虑增加副本数")
    else:
        details["checks"].append({
            "name": "可用性",
            "status": "OK",
            "message": f"可用性 {svc['uptime_percent']}% 达标",
        })

    return details
