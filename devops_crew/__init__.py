"""
DevOps Crew 包初始化模块
"""

try:
    from devops_crew.crew import DevOpsCrew
    __all__ = ["DevOpsCrew"]
except ImportError:
    # crewai 未安装时，仅暴露自研框架模块
    # crewai 未安装时跳过旧框架导入，自研框架子模块仍可正常使用
    __all__ = []
