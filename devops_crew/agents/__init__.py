"""
软件开发专业化智能体模块

提供 5 个专业化智能体：
- ArchitectAgent    ：架构师，负责系统设计和技术选型
- DeveloperAgent    ：开发工程师，负责代码实现和优化
- TesterAgent       ：测试工程师，负责单元测试生成和质量评估
- CodeReviewerAgent ：代码审查官，负责代码审查和质量监控
- ProjectManagerAgent：项目经理，负责任务协调和进度管理
"""

from .dev_agents import (
    ArchitectAgent,
    DeveloperAgent,
    TesterAgent,
    CodeReviewerAgent,
    ProjectManagerAgent,
    create_dev_team,
)

__all__ = [
    "ArchitectAgent",
    "DeveloperAgent",
    "TesterAgent",
    "CodeReviewerAgent",
    "ProjectManagerAgent",
    "create_dev_team",
devops_crew.agents - 开发智能体包
"""
from .dev_agents import (
    ArchitectAgent,
    DeveloperAgent,
    TestEngineerAgent,
    CodeReviewerAgent,
    ProjectManagerAgent,
)

__all__ = [
    'ArchitectAgent',
    'DeveloperAgent',
    'TestEngineerAgent',
    'CodeReviewerAgent',
    'ProjectManagerAgent',
]
