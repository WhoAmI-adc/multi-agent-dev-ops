"""
DevOps Crew 包初始化模块
"""

try:
    from devops_crew.crew import DevOpsCrew
    __all__ = ["DevOpsCrew"]
except ImportError:
    # crewai 未安装时，仅暴露自研框架模块
    __all__ = []
