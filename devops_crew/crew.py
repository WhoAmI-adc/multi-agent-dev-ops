"""
DevOps Crew 主配置模块

定义多智能体运维团队的核心配置，包括：
- 5个专业化运维智能体
- 智能体工具分配
- 团队协作流程
"""

import logging
import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

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

logger = logging.getLogger(__name__)

# 配置 LLM（支持通过环境变量设置）
def _create_llm() -> LLM:
    """创建 LLM 实例，支持多种模型配置"""
    model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
    api_key = os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")

    return LLM(
        model=model,
        base_url=base_url,
        api_key=api_key,
        stream=False,
        temperature=0.3,
    )


@CrewBase
class DevOpsCrew:
    """
    多智能体 DevOps 运维团队

    包含5个专业化智能体，协同完成各类运维任务：
    1. 基础设施监控专家 - 监控和告警
    2. 故障诊断专家 - 日志分析和根因诊断
    3. 自动修复专家 - 执行修复操作
    4. 部署运维专家 - CI/CD 和部署管理
    5. 性能优化专家 - 性能分析和优化
    """

    # ==================== 智能体定义 ====================

    @agent
    def infrastructure_monitor(self) -> Agent:
        """基础设施监控专家"""
        return Agent(
            config=self.agents_config["infrastructure_monitor"],
            llm=_create_llm(),
            tools=[
                get_cpu_usage,
                get_memory_usage,
                get_disk_usage,
                check_service_health,
                get_alerts,
                list_pods,
                list_containers,
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=5,
        )

    @agent
    def fault_diagnostician(self) -> Agent:
        """故障诊断专家"""
        return Agent(
            config=self.agents_config["fault_diagnostician"],
            llm=_create_llm(),
            tools=[
                search_logs,
                analyze_errors,
                get_log_statistics,
                filter_by_level,
                get_container_logs,
                get_pod_logs,
                get_pod_status,
                get_cpu_usage,
                get_memory_usage,
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @agent
    def auto_remediator(self) -> Agent:
        """自动化修复专家"""
        return Agent(
            config=self.agents_config["auto_remediator"],
            llm=_create_llm(),
            tools=[
                restart_container,
                restart_pod,
                scale_deployment,
                check_service_health,
                get_alerts,
                get_pod_status,
                list_pods,
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=6,
        )

    @agent
    def deployment_engineer(self) -> Agent:
        """部署运维专家"""
        return Agent(
            config=self.agents_config["deployment_engineer"],
            llm=_create_llm(),
            tools=[
                get_latest_commits,
                create_branch,
                merge_branch,
                get_commit_history,
                get_diff,
                build_image,
                list_containers,
                scale_deployment,
                list_pods,
                get_pod_status,
            ],
            verbose=True,
            allow_delegation=True,
            max_iter=10,
        )

    @agent
    def performance_optimizer(self) -> Agent:
        """性能优化专家"""
        return Agent(
            config=self.agents_config["performance_optimizer"],
            llm=_create_llm(),
            tools=[
                get_cpu_usage,
                get_memory_usage,
                get_disk_usage,
                get_log_statistics,
                analyze_errors,
                check_service_health,
                list_pods,
                get_pod_status,
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    # ==================== 任务定义 ====================

    @task
    def monitor_infrastructure_task(self) -> Task:
        """基础设施监控任务"""
        return Task(
            config=self.tasks_config["monitor_infrastructure_task"],
        )

    @task
    def check_alerts_task(self) -> Task:
        """告警检查任务"""
        return Task(
            config=self.tasks_config["check_alerts_task"],
        )

    @task
    def diagnose_fault_task(self) -> Task:
        """故障诊断任务"""
        return Task(
            config=self.tasks_config["diagnose_fault_task"],
        )

    @task
    def analyze_performance_task(self) -> Task:
        """性能分析任务"""
        return Task(
            config=self.tasks_config["analyze_performance_task"],
        )

    @task
    def execute_remediation_task(self) -> Task:
        """修复执行任务"""
        return Task(
            config=self.tasks_config["execute_remediation_task"],
        )

    @task
    def restart_services_task(self) -> Task:
        """服务重启任务"""
        return Task(
            config=self.tasks_config["restart_services_task"],
        )

    @task
    def deploy_application_task(self) -> Task:
        """应用部署任务"""
        return Task(
            config=self.tasks_config["deploy_application_task"],
        )

    @task
    def rollback_deployment_task(self) -> Task:
        """部署回滚任务"""
        return Task(
            config=self.tasks_config["rollback_deployment_task"],
        )

    @task
    def optimize_performance_task(self) -> Task:
        """性能优化任务"""
        return Task(
            config=self.tasks_config["optimize_performance_task"],
        )

    @task
    def generate_optimization_report_task(self) -> Task:
        """生成优化报告任务"""
        return Task(
            config=self.tasks_config["generate_optimization_report_task"],
        )

    # ==================== Crew 定义 ====================

    @crew
    def crew(self) -> Crew:
        """创建完整的多智能体运维团队"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            cache=True,
        )

    def monitoring_crew(self) -> Crew:
        """创建专注于监控和告警的子团队"""
        return Crew(
            agents=[self.infrastructure_monitor()],
            tasks=[self.monitor_infrastructure_task(), self.check_alerts_task()],
            process=Process.sequential,
            verbose=True,
        )

    def diagnosis_crew(self) -> Crew:
        """创建专注于故障诊断的子团队"""
        return Crew(
            agents=[self.infrastructure_monitor(), self.fault_diagnostician()],
            tasks=[self.monitor_infrastructure_task(), self.diagnose_fault_task()],
            process=Process.sequential,
            verbose=True,
        )

    def remediation_crew(self) -> Crew:
        """创建专注于故障修复的子团队"""
        return Crew(
            agents=[
                self.fault_diagnostician(),
                self.auto_remediator(),
            ],
            tasks=[self.diagnose_fault_task(), self.execute_remediation_task()],
            process=Process.sequential,
            verbose=True,
        )

    def deployment_crew(self) -> Crew:
        """创建专注于部署的子团队"""
        return Crew(
            agents=[self.deployment_engineer(), self.infrastructure_monitor()],
            tasks=[self.deploy_application_task(), self.monitor_infrastructure_task()],
            process=Process.sequential,
            verbose=True,
        )

    def optimization_crew(self) -> Crew:
        """创建专注于性能优化的子团队"""
        return Crew(
            agents=[self.infrastructure_monitor(), self.performance_optimizer()],
            tasks=[self.analyze_performance_task(), self.optimize_performance_task()],
            process=Process.sequential,
            verbose=True,
        )
