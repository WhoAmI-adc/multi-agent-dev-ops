from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
import os

# 配置 DeepSeek LLM
deepseek_llm = LLM(
    model='deepseek/deepseek-chat',
    base_url='https://api.deepseek.com/v1',
    api_key='sk-a98016496af84e38a725c25b5aa0e551',
    stream=False,
    temperature=0.3,
)

@CrewBase
class MyFirstCrew():
    """运维智能体团队"""

    @agent
    def monitor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['monitor_agent'],
            llm=deepseek_llm,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def log_analyzer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['log_analyzer_agent'],
            llm=deepseek_llm,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def diagnosis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['diagnosis_agent'],
            llm=deepseek_llm,
            verbose=True,
            allow_delegation=True,
        )

    @agent
    def remediation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['remediation_agent'],
            llm=deepseek_llm,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def monitor_task(self) -> Task:
        return Task(
            config=self.tasks_config['monitor_task'],
        )

    @task
    def log_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['log_analysis_task'],
        )

    @task
    def diagnosis_task(self) -> Task:
        # 注意：这里不使用 context 参数，而是在 YAML 中配置依赖
        return Task(
            config=self.tasks_config['diagnosis_task'],
        )

    @task
    def remediation_task(self) -> Task:
        return Task(
            config=self.tasks_config['remediation_task'],
        )

    @crew
    def crew(self) -> Crew:
        """创建运维智能体团队"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # 顺序执行自然会有依赖关系
            verbose=True,
        )