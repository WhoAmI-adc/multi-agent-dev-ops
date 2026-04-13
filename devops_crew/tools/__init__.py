"""
DevOps Crew 工具模块初始化

导出所有可用的 DevOps 运维工具。
"""

from devops_crew.tools.docker_tools import (
    list_containers,
    get_container_status,
    restart_container,
    get_container_logs,
    build_image,
)

from devops_crew.tools.log_tools import (
    search_logs,
    analyze_errors,
    get_log_statistics,
    filter_by_level,
)

from devops_crew.tools.monitor_tools import (
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    check_service_health,
    get_alerts,
)

from devops_crew.tools.git_tools import (
    get_latest_commits,
    create_branch,
    merge_branch,
    get_commit_history,
    get_diff,
)

from devops_crew.tools.kubernetes_tools import (
    list_pods,
    get_pod_status,
    restart_pod,
    scale_deployment,
    get_pod_logs,
)

__all__ = [
    # Docker 工具
    "list_containers",
    "get_container_status",
    "restart_container",
    "get_container_logs",
    "build_image",
    # 日志工具
    "search_logs",
    "analyze_errors",
    "get_log_statistics",
    "filter_by_level",
    # 监控工具
    "get_cpu_usage",
    "get_memory_usage",
    "get_disk_usage",
    "check_service_health",
    "get_alerts",
    # Git 工具
    "get_latest_commits",
    "create_branch",
    "merge_branch",
    "get_commit_history",
    "get_diff",
    # Kubernetes 工具
    "list_pods",
    "get_pod_status",
    "restart_pod",
    "scale_deployment",
    "get_pod_logs",
]
