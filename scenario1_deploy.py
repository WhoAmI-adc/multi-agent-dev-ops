"""
场景1：自动化部署流程演示

场景说明：
  新版本 v2.2.0 需要部署到生产环境。部署运维专家将协同基础设施
  监控专家完成整个部署流程：检查代码 → 构建镜像 → 部署应用 → 验证健康。

演示目标：
  - 展示多智能体协作完成复杂部署任务
  - 演示 Git 操作、Docker 构建、K8s 部署的工具集成
  - 展示部署前后的健康验证流程

运行方式：
  python scenario1_deploy.py
  python scenario1_deploy.py --app myapp --version v2.2.0 --env production
"""

import sys
import logging
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# 添加项目路径
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_deploy_scenario(
    app_name: str = "api-server",
    version: str = "v2.2.0",
    environment: str = "production",
) -> None:
    """
    运行自动化部署场景

    Args:
        app_name: 要部署的应用名称
        version: 部署的版本号
        environment: 目标环境（production/staging/development）
    """
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print("🚀 场景1：自动化部署流程")
    print("=" * 70)
    print(f"""
📋 部署信息：
   应用名称：{app_name}
   版本号：  {version}
   目标环境：{environment}
   开始时间：{start_time.strftime('%Y-%m-%d %H:%M:%S')}

📖 场景说明：
   新版本需要部署到生产环境。多智能体团队将协作完成：
   1. 部署运维专家：检查代码变更、构建镜像、执行部署
   2. 基础设施监控专家：验证部署后系统健康状态

🤖 参与智能体：
   - 部署运维专家（主导）
   - 基础设施监控专家（验证）
""")
    print("-" * 70)

    print("\n⏳ 正在初始化 DevOps 多智能体团队...\n")

    try:
        from devops_crew.crew import DevOpsCrew

        inputs = {
            "app_name": app_name,
            "version": version,
            "environment": environment,
            "service_name": app_name,
        }

        # 创建部署专用团队
        crew_instance = DevOpsCrew()
        deployment_crew = crew_instance.deployment_crew()

        print(f"✅ 智能体团队就绪，开始执行部署流程...\n")
        print("-" * 70)

        # 执行部署
        result = deployment_crew.kickoff(inputs=inputs)

        end_time = datetime.now()
        duration = (end_time - start_time).seconds

        print("\n" + "=" * 70)
        print(f"✅ 部署流程执行完成！")
        print("=" * 70)
        print(f"""
📊 执行摘要：
   应用：     {app_name}:{version}
   环境：     {environment}
   耗时：     {duration} 秒
   完成时间：{end_time.strftime('%Y-%m-%d %H:%M:%S')}
""")

        if result:
            print("📄 执行结果：")
            print("-" * 70)
            print(str(result)[:2000])  # 截取前2000字符显示

    except ImportError as e:
        logger.error("导入失败，请确保已安装依赖: pip install crewai")
        print(f"\n❌ 导入错误: {e}")
        print("\n💡 提示：请先安装依赖：")
        print("   pip install crewai")
        _run_demo_mode(app_name, version, environment)

    except Exception as e:
        logger.error("部署场景执行失败: %s", e, exc_info=True)
        print(f"\n❌ 执行错误: {e}")
        print("\n💡 切换到演示模式...")
        _run_demo_mode(app_name, version, environment)


def _run_demo_mode(app_name: str, version: str, environment: str) -> None:
    """
    演示模式：展示部署流程的预期输出（不需要 LLM API）

    当 API 密钥未配置或网络不可用时，展示模拟的部署流程输出。
    """
    print("\n" + "=" * 70)
    print("🎭 演示模式：模拟部署流程输出")
    print("=" * 70)

    # 直接使用工具演示
    from devops_crew.tools.git_tools import get_latest_commits, get_diff
    from devops_crew.tools.docker_tools import build_image, list_containers
    from devops_crew.tools.kubernetes_tools import (
        scale_deployment,
        list_pods,
        get_pod_status,
    )
    from devops_crew.tools.monitor_tools import check_service_health, get_alerts

    print(f"\n📋 步骤1：检查代码仓库最新变更")
    print("-" * 50)
    commits_result = get_latest_commits.run("main", 3)
    print(f"✅ 代码检查完成")
    print(f"   最新提交：{commits_result[:200]}...")

    print(f"\n🔨 步骤2：构建 Docker 镜像 {app_name}:{version}")
    print("-" * 50)
    build_result = build_image.run(app_name, version, ".", None)
    print(f"✅ 镜像构建成功")

    print(f"\n🚀 步骤3：部署到 {environment} 环境")
    print("-" * 50)
    scale_result = scale_deployment.run("api-server", 2, environment)
    print(f"✅ 部署命令已下发")

    print(f"\n🔍 步骤4：验证部署状态")
    print("-" * 50)
    pods_result = list_pods.run(environment, "api-server", None)
    print(f"✅ Pod 状态验证完成")

    print(f"\n❤️  步骤5：服务健康检查")
    print("-" * 50)
    health_result = check_service_health.run(app_name)
    print(f"✅ 健康检查完成")

    print("\n" + "=" * 70)
    print(f"🎉 演示部署流程完成！")
    print("=" * 70)
    print(f"""
📊 部署摘要（演示）：
   应用版本：{app_name}:{version}
   目标环境：{environment}
   部署状态：✅ 成功

📝 说明：
   在实际运行中，以上每个步骤由对应的 AI 智能体分析结果并做出
   决策，实现真正的智能化部署。演示模式仅展示工具调用效果。
""")


def main():
    parser = argparse.ArgumentParser(
        description="场景1：自动化部署流程演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--app", default="api-server", help="应用名称")
    parser.add_argument("--version", default="v2.2.0", help="版本号")
    parser.add_argument("--env", default="production", help="目标环境")
    parser.add_argument("--demo", action="store_true", help="强制使用演示模式（不调用 LLM）")

    args = parser.parse_args()

    if args.demo:
        _run_demo_mode(args.app, args.version, args.env)
    else:
        run_deploy_scenario(args.app, args.version, args.env)


if __name__ == "__main__":
    main()
