"""
日志分析工具模块

提供系统日志的搜索、分析和统计功能，包括：
- 日志搜索（按关键词、时间范围）
- 错误日志分析
- 日志统计摘要
- 按日志级别过滤

注：本模块使用模拟数据演示功能，生产环境中需集成 ELK Stack 或其他日志平台。
"""

import json
import re
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from crewai.tools import tool

logger = logging.getLogger(__name__)

# 模拟系统日志数据库
MOCK_SYSTEM_LOGS = [
    # API 服务日志
    {"timestamp": "2026-04-13T07:00:02", "service": "api-server", "level": "INFO",  "message": "Application started on port 8000", "trace_id": None},
    {"timestamp": "2026-04-13T07:00:03", "service": "api-server", "level": "INFO",  "message": "Connected to MySQL at mysql-db:3306", "trace_id": None},
    {"timestamp": "2026-04-13T07:00:03", "service": "api-server", "level": "INFO",  "message": "Connected to Redis at redis-cache:6379", "trace_id": None},
    {"timestamp": "2026-04-13T07:05:15", "service": "api-server", "level": "INFO",  "message": "GET /api/v1/orders 200 OK (0.045s)", "trace_id": "abc123"},
    {"timestamp": "2026-04-13T07:08:30", "service": "api-server", "level": "WARN",  "message": "Database connection pool at 80% capacity (16/20)", "trace_id": None},
    {"timestamp": "2026-04-13T07:10:45", "service": "api-server", "level": "ERROR", "message": "Database connection pool exhausted (pool_size=20, waiting=8)", "trace_id": "def456"},
    {"timestamp": "2026-04-13T07:10:46", "service": "api-server", "level": "ERROR", "message": "Timeout waiting for DB connection after 5000ms", "trace_id": "def456"},
    {"timestamp": "2026-04-13T07:10:47", "service": "api-server", "level": "ERROR", "message": "POST /api/v1/orders 503 Service Unavailable (5.002s)", "trace_id": "def456"},
    {"timestamp": "2026-04-13T07:11:00", "service": "api-server", "level": "WARN",  "message": "Slow query detected: SELECT * FROM orders WHERE status='pending' (took 8.3s)", "trace_id": "ghi789"},
    {"timestamp": "2026-04-13T07:11:30", "service": "api-server", "level": "ERROR", "message": "Database connection pool exhausted (pool_size=20, waiting=12)", "trace_id": "jkl012"},
    {"timestamp": "2026-04-13T07:12:00", "service": "api-server", "level": "ERROR", "message": "Failed to execute query: connection reset by peer", "trace_id": "jkl012"},
    {"timestamp": "2026-04-13T07:15:00", "service": "api-server", "level": "ERROR", "message": "Database connection pool exhausted (pool_size=20, waiting=15)", "trace_id": "mno345"},
    {"timestamp": "2026-04-13T07:15:01", "service": "api-server", "level": "ERROR", "message": "CircuitBreaker opened for mysql-db:3306", "trace_id": None},
    # MySQL 数据库日志
    {"timestamp": "2026-04-13T07:00:00", "service": "mysql-db", "level": "INFO",  "message": "MySQL 8.0.35 started", "trace_id": None},
    {"timestamp": "2026-04-13T07:00:01", "service": "mysql-db", "level": "INFO",  "message": "Ready for connections on port 3306", "trace_id": None},
    {"timestamp": "2026-04-13T07:05:30", "service": "mysql-db", "level": "WARN",  "message": "Too many connections: current=198 max_connections=200", "trace_id": None},
    {"timestamp": "2026-04-13T07:08:45", "service": "mysql-db", "level": "WARN",  "message": "InnoDB: Buffer pool hit rate 87/1000, young-making rate 32/1000", "trace_id": None},
    {"timestamp": "2026-04-13T07:10:45", "service": "mysql-db", "level": "ERROR", "message": "Can't create a new thread: Resource temporarily unavailable", "trace_id": None},
    {"timestamp": "2026-04-13T07:10:46", "service": "mysql-db", "level": "ERROR", "message": "Aborted connection 198 to db: 'appdb' user: 'appuser' host: 'api-server'", "trace_id": None},
    {"timestamp": "2026-04-13T07:11:00", "service": "mysql-db", "level": "WARN",  "message": "Long query detected (8.312s): SELECT * FROM orders WHERE status='pending'", "trace_id": None},
    {"timestamp": "2026-04-13T07:15:00", "service": "mysql-db", "level": "ERROR", "message": "Aborted connection 200 to db: 'appdb' user: 'appuser'", "trace_id": None},
    # Nginx 代理日志
    {"timestamp": "2026-04-13T07:00:00", "service": "nginx-proxy", "level": "INFO",  "message": "Nginx started, worker processes: 4", "trace_id": None},
    {"timestamp": "2026-04-13T07:10:50", "service": "nginx-proxy", "level": "ERROR", "message": "upstream timed out (110: Connection timed out) while reading response header", "trace_id": None},
    {"timestamp": "2026-04-13T07:10:51", "service": "nginx-proxy", "level": "WARN",  "message": "upstream api-server response time: 5.234s (threshold: 2s)", "trace_id": None},
    # Worker 服务日志
    {"timestamp": "2026-04-13T06:55:00", "service": "worker-service", "level": "INFO",  "message": "Worker service starting...", "trace_id": None},
    {"timestamp": "2026-04-13T06:55:01", "service": "worker-service", "level": "ERROR", "message": "Failed to connect to RabbitMQ at rabbitmq:5672: Connection refused", "trace_id": None},
    {"timestamp": "2026-04-13T06:55:01", "service": "worker-service", "level": "ERROR", "message": "Startup failed: required service unavailable", "trace_id": None},
    # Redis 日志
    {"timestamp": "2026-04-13T07:00:00", "service": "redis-cache", "level": "INFO",  "message": "Server started, Redis version=7.0.12", "trace_id": None},
    {"timestamp": "2026-04-13T07:00:01", "service": "redis-cache", "level": "INFO",  "message": "DB loaded from disk: 0.021 seconds", "trace_id": None},
]


@tool("search_logs")
def search_logs(
    keyword: str,
    service: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    max_results: int = 20,
) -> str:
    """
    在系统日志中搜索包含指定关键词的日志条目。

    Args:
        keyword: 搜索关键词（支持正则表达式）
        service: 限定服务名称（可选）
        start_time: 开始时间（格式：HH:MM 或 ISO8601，可选）
        end_time: 结束时间（格式：HH:MM 或 ISO8601，可选）
        max_results: 最大返回数量（默认20）

    Returns:
        JSON 格式的搜索结果
    """
    logger.info("搜索日志: keyword='%s', service='%s'", keyword, service)

    results = []
    pattern = re.compile(keyword, re.IGNORECASE)

    for log_entry in MOCK_SYSTEM_LOGS:
        # 服务过滤
        if service and log_entry["service"] != service:
            continue

        # 关键词匹配
        if not pattern.search(log_entry["message"]):
            continue

        results.append(log_entry)

    # 限制返回数量
    results = results[:max_results]

    response = {
        "keyword": keyword,
        "service_filter": service,
        "total_found": len(results),
        "results": results,
    }

    return json.dumps(response, ensure_ascii=False, indent=2)


@tool("analyze_errors")
def analyze_errors(
    service: Optional[str] = None,
    time_window_minutes: int = 30,
) -> str:
    """
    分析系统错误日志，识别错误模式和根因。

    Args:
        service: 限定分析的服务名称（None 表示分析所有服务）
        time_window_minutes: 分析时间窗口（分钟）

    Returns:
        JSON 格式的错误分析报告
    """
    logger.info("分析错误日志: service='%s', 时间窗口=%d分钟", service, time_window_minutes)

    # 过滤错误日志
    error_logs = [
        log for log in MOCK_SYSTEM_LOGS
        if log["level"] in ("ERROR", "WARN")
        and (service is None or log["service"] == service)
    ]

    # 按服务分组
    by_service = defaultdict(list)
    for log in error_logs:
        by_service[log["service"]].append(log)

    # 错误模式识别
    error_patterns = []
    all_errors = [log for log in error_logs if log["level"] == "ERROR"]

    # 简单的模式聚合（生产环境可用更复杂的算法）
    pattern_counter = Counter()
    for log in all_errors:
        # 提取模式（去除具体数值）
        normalized = re.sub(r"\d+", "N", log["message"])
        normalized = re.sub(r"[a-f0-9]{8,}", "HASH", normalized)
        pattern_counter[normalized] += 1

    for pattern_msg, count in pattern_counter.most_common(5):
        error_patterns.append({
            "pattern": pattern_msg,
            "count": count,
            "severity": "HIGH" if count > 2 else "MEDIUM",
        })

    # 时间线分析
    timeline = []
    for log in sorted(error_logs, key=lambda x: x["timestamp"]):
        timeline.append({
            "time": log["timestamp"].split("T")[1],
            "service": log["service"],
            "level": log["level"],
            "message": log["message"][:80] + ("..." if len(log["message"]) > 80 else ""),
        })

    # 构建分析报告
    report = {
        "analysis_period": f"最近 {time_window_minutes} 分钟",
        "service_filter": service or "所有服务",
        "summary": {
            "total_errors": sum(1 for log in error_logs if log["level"] == "ERROR"),
            "total_warnings": sum(1 for log in error_logs if log["level"] == "WARN"),
            "affected_services": list(by_service.keys()),
        },
        "error_patterns": error_patterns,
        "service_breakdown": {
            svc: {
                "error_count": sum(1 for log in logs if log["level"] == "ERROR"),
                "warn_count": sum(1 for log in logs if log["level"] == "WARN"),
                "first_error": min(log["timestamp"] for log in logs),
                "last_error": max(log["timestamp"] for log in logs),
            }
            for svc, logs in by_service.items()
        },
        "timeline": timeline[:20],  # 最多显示20条时间线事件
        "root_cause_hints": _generate_root_cause_hints(error_logs),
    }

    return json.dumps(report, ensure_ascii=False, indent=2)


@tool("get_log_statistics")
def get_log_statistics(
    service: Optional[str] = None,
    group_by: str = "service",
) -> str:
    """
    获取日志统计信息，包括各级别日志数量、趋势等。

    Args:
        service: 限定服务名称（可选）
        group_by: 统计维度，可选 'service'、'level'、'hour'

    Returns:
        JSON 格式的统计信息
    """
    logger.info("获取日志统计: service='%s', group_by='%s'", service, group_by)

    logs = MOCK_SYSTEM_LOGS
    if service:
        logs = [log for log in logs if log["service"] == service]

    total = len(logs)
    by_level = Counter(log["level"] for log in logs)
    by_service = Counter(log["service"] for log in logs)

    # 按小时统计
    by_hour = Counter()
    for log in logs:
        hour = log["timestamp"].split("T")[1][:2]
        by_hour[hour] += 1

    stats = {
        "total_log_entries": total,
        "by_level": dict(by_level),
        "error_rate": round(by_level.get("ERROR", 0) / max(total, 1) * 100, 2),
        "by_service": dict(by_service.most_common()),
        "by_hour": dict(sorted(by_hour.items())),
        "health_score": _calculate_health_score(by_level, total),
        "top_issues": [
            log["message"][:100]
            for log in logs
            if log["level"] == "ERROR"
        ][:5],
    }

    return json.dumps(stats, ensure_ascii=False, indent=2)


@tool("filter_by_level")
def filter_by_level(
    level: str,
    service: Optional[str] = None,
    limit: int = 30,
) -> str:
    """
    按日志级别过滤日志条目。

    Args:
        level: 日志级别（DEBUG/INFO/WARN/ERROR/CRITICAL）
        service: 限定服务名称（可选）
        limit: 最大返回数量

    Returns:
        JSON 格式的过滤结果
    """
    logger.info("按级别过滤日志: level='%s', service='%s'", level, service)

    level_upper = level.upper()
    # 日志级别层次（包含更高级别的选项）
    level_hierarchy = {"DEBUG": 0, "INFO": 1, "WARN": 2, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
    min_level = level_hierarchy.get(level_upper, 0)

    filtered = [
        log for log in MOCK_SYSTEM_LOGS
        if level_hierarchy.get(log["level"], 0) >= min_level
        and (service is None or log["service"] == service)
    ]

    filtered = filtered[:limit]

    result = {
        "level_filter": level_upper,
        "service_filter": service,
        "total_matched": len(filtered),
        "entries": filtered,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def _generate_root_cause_hints(error_logs: list) -> list:
    """根据错误日志生成根因提示"""
    hints = []
    messages = [log["message"].lower() for log in error_logs]

    if any("connection pool exhausted" in msg for msg in messages):
        hints.append({
            "hypothesis": "数据库连接池耗尽",
            "evidence": "多次出现 'connection pool exhausted' 错误",
            "confidence": "HIGH",
            "suggestion": "增大连接池大小或优化查询以减少连接持有时间",
        })

    if any("slow query" in msg or "long query" in msg for msg in messages):
        hints.append({
            "hypothesis": "存在慢查询导致连接长时间占用",
            "evidence": "检测到查询执行时间超过阈值",
            "confidence": "HIGH",
            "suggestion": "分析慢查询，添加适当索引",
        })

    if any("too many connections" in msg for msg in messages):
        hints.append({
            "hypothesis": "MySQL max_connections 配置过低",
            "evidence": "MySQL 连接数接近 max_connections 限制",
            "confidence": "MEDIUM",
            "suggestion": "调高 MySQL max_connections 参数",
        })

    if any("connection refused" in msg for msg in messages):
        hints.append({
            "hypothesis": "依赖服务不可用",
            "evidence": "存在连接被拒绝的错误",
            "confidence": "HIGH",
            "suggestion": "检查并启动缺失的依赖服务",
        })

    return hints


def _calculate_health_score(by_level: Counter, total: int) -> dict:
    """计算系统健康评分"""
    if total == 0:
        return {"score": 100, "grade": "A", "description": "无日志数据"}

    error_count = by_level.get("ERROR", 0)
    warn_count = by_level.get("WARN", 0)

    error_rate = error_count / total * 100
    warn_rate = warn_count / total * 100

    score = 100 - (error_rate * 3) - (warn_rate * 1)
    score = max(0, min(100, score))

    if score >= 90:
        grade, description = "A", "系统运行良好"
    elif score >= 75:
        grade, description = "B", "系统基本正常，有少量警告"
    elif score >= 60:
        grade, description = "C", "系统存在明显问题，需要关注"
    elif score >= 40:
        grade, description = "D", "系统存在严重问题，需要立即处理"
    else:
        grade, description = "F", "系统故障，需要紧急干预"

    return {
        "score": round(score, 1),
        "grade": grade,
        "description": description,
        "error_rate_percent": round(error_rate, 2),
        "warn_rate_percent": round(warn_rate, 2),
    }
