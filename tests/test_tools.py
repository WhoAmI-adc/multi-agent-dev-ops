"""
工具模块单元测试

测试 DevOps Crew 中所有工具的基本功能，无需 LLM API 即可运行。
"""

import json
import sys
import os
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== Docker 工具测试 ====================

class TestDockerTools:
    """测试 Docker 工具模块"""

    def test_list_containers_all(self):
        """测试列出所有容器"""
        from devops_crew.tools.docker_tools import list_containers
        result = list_containers.run("all")
        data = json.loads(result)

        assert "total" in data
        assert "containers" in data
        assert data["total"] > 0
        assert isinstance(data["containers"], list)

    def test_list_containers_running(self):
        """测试列出运行中的容器"""
        from devops_crew.tools.docker_tools import list_containers
        result = list_containers.run("running")
        data = json.loads(result)

        assert "containers" in data
        for container in data["containers"]:
            assert container["status"] == "running"

    def test_get_container_status_existing(self):
        """测试获取存在的容器状态"""
        from devops_crew.tools.docker_tools import get_container_status
        result = get_container_status.run("web-frontend")
        data = json.loads(result)

        assert "name" in data
        assert data["name"] == "web-frontend"
        assert "status" in data
        assert "resources" in data

    def test_get_container_status_not_found(self):
        """测试获取不存在的容器状态"""
        from devops_crew.tools.docker_tools import get_container_status
        result = get_container_status.run("nonexistent-container")
        data = json.loads(result)

        assert "error" in data

    def test_restart_container(self):
        """测试重启容器"""
        from devops_crew.tools.docker_tools import restart_container
        result = restart_container.run("web-frontend", 30)
        data = json.loads(result)

        assert "success" in data
        assert data["success"] is True
        assert "actions" in data
        assert len(data["actions"]) > 0

    def test_get_container_logs(self):
        """测试获取容器日志"""
        from devops_crew.tools.docker_tools import get_container_logs
        result = get_container_logs.run("api-server", 10, None, None)
        data = json.loads(result)

        assert "container_name" in data
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_get_container_logs_with_filter(self):
        """测试按级别过滤容器日志"""
        from devops_crew.tools.docker_tools import get_container_logs
        result = get_container_logs.run("api-server", 50, None, "ERROR")
        data = json.loads(result)

        assert "logs" in data
        for log in data["logs"]:
            assert "ERROR" in log

    def test_build_image(self):
        """测试构建 Docker 镜像"""
        from devops_crew.tools.docker_tools import build_image
        result = build_image.run("my-app", "v1.0.0", ".", None)
        data = json.loads(result)

        assert "success" in data
        assert data["success"] is True
        assert "image_name" in data
        assert "my-app:v1.0.0" in data["image_name"]


# ==================== 日志工具测试 ====================

class TestLogTools:
    """测试日志分析工具模块"""

    def test_search_logs_basic(self):
        """测试基本日志搜索"""
        from devops_crew.tools.log_tools import search_logs
        result = search_logs.run("connection pool", None, None, None, 10)
        data = json.loads(result)

        assert "keyword" in data
        assert "results" in data
        assert data["total_found"] > 0

    def test_search_logs_with_service(self):
        """测试按服务过滤搜索"""
        from devops_crew.tools.log_tools import search_logs
        result = search_logs.run("connection", "api-server", None, None, 20)
        data = json.loads(result)

        assert data["service_filter"] == "api-server"
        for entry in data["results"]:
            assert entry["service"] == "api-server"

    def test_search_logs_no_results(self):
        """测试搜索无结果的情况"""
        from devops_crew.tools.log_tools import search_logs
        result = search_logs.run("xyzzy_nonexistent_pattern_12345", None, None, None, 10)
        data = json.loads(result)

        assert data["total_found"] == 0
        assert data["results"] == []

    def test_analyze_errors(self):
        """测试错误日志分析"""
        from devops_crew.tools.log_tools import analyze_errors
        result = analyze_errors.run(None, 30)
        data = json.loads(result)

        assert "summary" in data
        assert "error_patterns" in data
        assert "root_cause_hints" in data
        assert "service_breakdown" in data

    def test_analyze_errors_for_service(self):
        """测试针对特定服务的错误分析"""
        from devops_crew.tools.log_tools import analyze_errors
        result = analyze_errors.run("api-server", 30)
        data = json.loads(result)

        assert data["service_filter"] == "api-server"

    def test_get_log_statistics(self):
        """测试日志统计"""
        from devops_crew.tools.log_tools import get_log_statistics
        result = get_log_statistics.run(None, "service")
        data = json.loads(result)

        assert "total_log_entries" in data
        assert "by_level" in data
        assert "error_rate" in data
        assert "health_score" in data
        assert "score" in data["health_score"]

    def test_filter_by_level_error(self):
        """测试按 ERROR 级别过滤"""
        from devops_crew.tools.log_tools import filter_by_level
        result = filter_by_level.run("ERROR", None, 50)
        data = json.loads(result)

        assert "entries" in data
        for entry in data["entries"]:
            assert entry["level"] in ("ERROR",)

    def test_filter_by_level_warn(self):
        """测试按 WARN 级别过滤（包含更高级别）"""
        from devops_crew.tools.log_tools import filter_by_level
        result = filter_by_level.run("WARN", None, 50)
        data = json.loads(result)

        assert "entries" in data
        for entry in data["entries"]:
            assert entry["level"] in ("WARN", "ERROR", "CRITICAL")


# ==================== 监控工具测试 ====================

class TestMonitorTools:
    """测试系统监控工具模块"""

    def test_get_cpu_usage_all_nodes(self):
        """测试获取所有节点 CPU 使用率"""
        from devops_crew.tools.monitor_tools import get_cpu_usage
        result = get_cpu_usage.run(None)
        data = json.loads(result)

        assert "nodes" in data
        assert len(data["nodes"]) > 0
        for node in data["nodes"]:
            assert "cpu_percent" in node
            assert 0 <= node["cpu_percent"] <= 100

    def test_get_cpu_usage_specific_node(self):
        """测试获取特定节点 CPU 使用率"""
        from devops_crew.tools.monitor_tools import get_cpu_usage
        result = get_cpu_usage.run("node-1")
        data = json.loads(result)

        assert data["node"] == "node-1"
        assert "cpu_percent" in data
        assert "load_average" in data

    def test_get_cpu_usage_invalid_node(self):
        """测试获取不存在节点的 CPU 使用率"""
        from devops_crew.tools.monitor_tools import get_cpu_usage
        result = get_cpu_usage.run("node-999")
        data = json.loads(result)

        assert "error" in data

    def test_get_memory_usage(self):
        """测试获取内存使用率"""
        from devops_crew.tools.monitor_tools import get_memory_usage
        result = get_memory_usage.run(None)
        data = json.loads(result)

        assert "nodes" in data
        for node in data["nodes"]:
            assert "percent" in node
            assert 0 <= node["percent"] <= 100

    def test_get_disk_usage(self):
        """测试获取磁盘使用率"""
        from devops_crew.tools.monitor_tools import get_disk_usage
        result = get_disk_usage.run(None)
        data = json.loads(result)

        assert "nodes" in data
        for node in data["nodes"]:
            assert "percent" in node

    def test_check_service_health_all(self):
        """测试检查所有服务健康状态"""
        from devops_crew.tools.monitor_tools import check_service_health
        result = check_service_health.run(None)
        data = json.loads(result)

        assert "summary" in data
        assert "services" in data
        assert "total" in data["summary"]
        assert data["summary"]["total"] > 0

    def test_check_service_health_specific(self):
        """测试检查特定服务健康状态"""
        from devops_crew.tools.monitor_tools import check_service_health
        result = check_service_health.run("api-server")
        data = json.loads(result)

        assert data["service"] == "api-server"
        assert "status" in data
        assert "health_details" in data

    def test_get_alerts_all(self):
        """测试获取所有告警"""
        from devops_crew.tools.monitor_tools import get_alerts
        result = get_alerts.run(None, None, "firing")
        data = json.loads(result)

        assert "total_alerts" in data
        assert "alerts" in data
        assert data["total_alerts"] > 0

    def test_get_alerts_critical_only(self):
        """测试只获取紧急告警"""
        from devops_crew.tools.monitor_tools import get_alerts
        result = get_alerts.run("critical", None, "firing")
        data = json.loads(result)

        assert "alerts" in data
        for alert in data["alerts"]:
            assert alert["severity"] == "critical"


# ==================== Git 工具测试 ====================

class TestGitTools:
    """测试 Git 版本控制工具模块"""

    def test_get_latest_commits(self):
        """测试获取最新提交记录"""
        from devops_crew.tools.git_tools import get_latest_commits
        result = get_latest_commits.run("main", 3)
        data = json.loads(result)

        assert "commits" in data
        assert len(data["commits"]) <= 3
        for commit in data["commits"]:
            assert "sha" in commit
            assert "message" in commit
            assert "author" in commit

    def test_get_latest_commits_invalid_branch(self):
        """测试获取不存在分支的提交"""
        from devops_crew.tools.git_tools import get_latest_commits
        result = get_latest_commits.run("nonexistent-branch", 5)
        data = json.loads(result)

        assert "error" in data

    def test_create_branch(self):
        """测试创建新分支"""
        from devops_crew.tools.git_tools import create_branch
        result = create_branch.run("feature/test-feature", "main", "测试分支")
        data = json.loads(result)

        assert "success" in data
        assert data["success"] is True
        assert data["branch_name"] == "feature/test-feature"

    def test_create_branch_invalid_name(self):
        """测试创建含非法字符的分支"""
        from devops_crew.tools.git_tools import create_branch
        result = create_branch.run("feature/test branch with spaces", "main", None)
        data = json.loads(result)

        assert data["success"] is False
        assert "error" in data

    def test_merge_branch_protected(self):
        """测试合并到受保护分支（应拒绝）"""
        from devops_crew.tools.git_tools import merge_branch
        result = merge_branch.run("develop", "main", None)
        data = json.loads(result)

        # main 分支受保护，应拒绝直接合并
        assert data["success"] is False

    def test_merge_branch_unprotected(self):
        """测试合并到非受保护分支"""
        from devops_crew.tools.git_tools import merge_branch
        result = merge_branch.run("feature/db-optimization", "develop", "合并数据库优化")
        data = json.loads(result)

        assert data["success"] is True

    def test_get_commit_history(self):
        """测试获取提交历史"""
        from devops_crew.tools.git_tools import get_commit_history
        result = get_commit_history.run("main", None, 7, 1, 5)
        data = json.loads(result)

        assert "commits" in data
        assert "pagination" in data
        assert "statistics" in data

    def test_get_diff_by_commit(self):
        """测试获取提交的代码差异"""
        from devops_crew.tools.git_tools import get_diff
        result = get_diff.run("a1b2c3d", None, "main", None)
        data = json.loads(result)

        assert "commit" in data
        assert "diff" in data


# ==================== Kubernetes 工具测试 ====================

class TestKubernetesTools:
    """测试 Kubernetes 集群操作工具模块"""

    def test_list_pods_all(self):
        """测试列出所有 Pod"""
        from devops_crew.tools.kubernetes_tools import list_pods
        result = list_pods.run("production", None, None)
        data = json.loads(result)

        assert "pods" in data
        assert "total_pods" in data
        assert data["total_pods"] > 0

    def test_list_pods_by_deployment(self):
        """测试按 Deployment 过滤 Pod"""
        from devops_crew.tools.kubernetes_tools import list_pods
        result = list_pods.run("production", "api-server", None)
        data = json.loads(result)

        assert "pods" in data
        for pod in data["pods"]:
            assert pod["deployment"] == "api-server"

    def test_list_pods_by_status(self):
        """测试按状态过滤 Pod"""
        from devops_crew.tools.kubernetes_tools import list_pods
        result = list_pods.run("production", None, "CrashLoopBackOff")
        data = json.loads(result)

        assert "pods" in data
        for pod in data["pods"]:
            assert pod["status"] == "CrashLoopBackOff"

    def test_get_pod_status_existing(self):
        """测试获取存在 Pod 的状态"""
        from devops_crew.tools.kubernetes_tools import get_pod_status
        result = get_pod_status.run("mysql-db-0", "production")
        data = json.loads(result)

        assert "name" in data
        assert data["name"] == "mysql-db-0"
        assert "status" in data
        assert "resources" in data

    def test_get_pod_status_with_issues(self):
        """测试获取有问题 Pod 的状态（应包含 issues）"""
        from devops_crew.tools.kubernetes_tools import get_pod_status
        result = get_pod_status.run("worker-service-6b4d9c8f7-k9j2l", "production")
        data = json.loads(result)

        assert "issues" in data
        assert len(data["issues"]) > 0
        assert data["health"] in ("warning", "critical")

    def test_get_pod_status_not_found(self):
        """测试获取不存在 Pod 的状态"""
        from devops_crew.tools.kubernetes_tools import get_pod_status
        result = get_pod_status.run("nonexistent-pod-xyz", "production")
        data = json.loads(result)

        assert "error" in data

    def test_restart_pod(self):
        """测试重启 Pod"""
        from devops_crew.tools.kubernetes_tools import restart_pod
        result = restart_pod.run("api-server-7d9f8b6c5-x2k4p", "production")
        data = json.loads(result)

        assert "success" in data
        assert data["success"] is True
        assert "new_pod" in data
        assert "timeline" in data

    def test_scale_deployment_up(self):
        """测试扩容 Deployment"""
        from devops_crew.tools.kubernetes_tools import scale_deployment
        result = scale_deployment.run("api-server", 4, "production")
        data = json.loads(result)

        assert data["success"] is True
        assert data["new_replicas"] == 4
        assert data["action"] == "扩容"

    def test_scale_deployment_down(self):
        """测试缩容 Deployment"""
        from devops_crew.tools.kubernetes_tools import scale_deployment
        result = scale_deployment.run("api-server", 1, "production")
        data = json.loads(result)

        assert data["success"] is True
        assert data["new_replicas"] == 1
        assert data["action"] == "缩容"

    def test_scale_deployment_invalid(self):
        """测试无效的扩缩容操作"""
        from devops_crew.tools.kubernetes_tools import scale_deployment

        # 负数副本
        result = scale_deployment.run("api-server", -1, "production")
        data = json.loads(result)
        assert data["success"] is False

        # 超出最大值
        result = scale_deployment.run("api-server", 100, "production")
        data = json.loads(result)
        assert data["success"] is False

    def test_get_pod_logs(self):
        """测试获取 Pod 日志"""
        from devops_crew.tools.kubernetes_tools import get_pod_logs
        result = get_pod_logs.run("worker-service-6b4d9c8f7-k9j2l", "production", None, 20, False)
        data = json.loads(result)

        assert "pod_name" in data
        assert "logs" in data
        assert isinstance(data["logs"], list)


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试：模拟完整的运维场景工具调用链"""

    def test_monitoring_workflow(self):
        """测试监控告警工作流"""
        from devops_crew.tools.monitor_tools import get_alerts, check_service_health, get_cpu_usage

        # 1. 获取当前告警
        alerts_result = json.loads(get_alerts.run(None, None, "firing"))
        assert alerts_result["total_alerts"] > 0

        # 2. 检查服务健康状态
        health_result = json.loads(check_service_health.run(None))
        assert "summary" in health_result

        # 3. 收集 CPU 指标
        cpu_result = json.loads(get_cpu_usage.run(None))
        assert "nodes" in cpu_result

        # 验证告警中有高 CPU 告警（与 CPU 数据一致）
        high_cpu_alerts = [
            a for a in alerts_result["alerts"]
            if "CPU" in a.get("message", "") or "cpu" in a.get("rule", "").lower()
        ]
        high_cpu_nodes = [n for n in cpu_result["nodes"] if n["cpu_percent"] > 80]
        assert len(high_cpu_nodes) > 0

    def test_diagnosis_workflow(self):
        """测试故障诊断工作流"""
        from devops_crew.tools.log_tools import analyze_errors, filter_by_level
        from devops_crew.tools.kubernetes_tools import list_pods, get_pod_logs

        # 1. 分析错误日志
        errors = json.loads(analyze_errors.run("api-server", 30))
        assert "root_cause_hints" in errors

        # 2. 获取错误详情
        error_logs = json.loads(filter_by_level.run("ERROR", "api-server", 20))
        assert len(error_logs["entries"]) > 0

        # 3. 检查 Pod 状态
        pods = json.loads(list_pods.run("production", None, None))
        problem_pods = [p for p in pods["pods"] if p["restarts"] > 3]
        assert len(problem_pods) > 0

        # 4. 获取问题 Pod 日志
        if problem_pods:
            pod_logs = json.loads(
                get_pod_logs.run(problem_pods[0]["name"], "production", None, 20, False)
            )
            assert "logs" in pod_logs

    def test_deployment_workflow(self):
        """测试部署工作流"""
        from devops_crew.tools.git_tools import get_latest_commits, get_diff
        from devops_crew.tools.docker_tools import build_image
        from devops_crew.tools.kubernetes_tools import scale_deployment, list_pods

        # 1. 获取最新代码
        commits = json.loads(get_latest_commits.run("main", 3))
        assert len(commits["commits"]) > 0

        # 2. 查看代码变更
        diff = json.loads(get_diff.run("a1b2c3d", None, "main", None))
        assert "diff" in diff

        # 3. 构建镜像
        build = json.loads(build_image.run("api-server", "v2.2.0", ".", None))
        assert build["success"] is True

        # 4. 部署
        deploy = json.loads(scale_deployment.run("api-server", 2, "production"))
        assert deploy["success"] is True

        # 5. 验证
        pods = json.loads(list_pods.run("production", "api-server", None))
        assert pods["total_pods"] > 0
