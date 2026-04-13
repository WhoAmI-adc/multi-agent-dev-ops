"""
DevOps Crew 入口文件

多智能体 DevOps 系统的主入口，支持多种运行模式：
- 完整系统运行
- 单独场景运行（监控、诊断、部署、优化）
- 交互式模式

使用方法：
    python main.py                    # 交互式选择场景
    python main.py --scenario monitor # 运行监控场景
    python main.py --scenario diagnose --fault "服务响应超时"
    python main.py --scenario deploy --app myapp --version v1.2.0
    python main.py --scenario optimize
"""

import sys
import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_monitoring_scenario(service_name: str = "production-cluster") -> dict:
    """
    运行监控场景：检查基础设施状态和告警

    Args:
        service_name: 要监控的服务/集群名称

    Returns:
        监控结果字典
    """
    from devops_crew.crew import DevOpsCrew

    print("\n" + "=" * 65)
    print("🔍 场景：基础设施监控")
    print("=" * 65)
    print(f"📋 监控目标：{service_name}")
    print(f"⏰ 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    inputs = {
        "service_name": service_name,
    }

    crew_instance = DevOpsCrew()
    result = crew_instance.monitoring_crew().kickoff(inputs=inputs)

    print("\n" + "=" * 65)
    print("✅ 监控检查完成")
    print("=" * 65)

    return {"scenario": "monitoring", "result": str(result)}


def run_diagnosis_scenario(
    fault_description: str = "服务响应时间异常，错误率升高",
    service_name: str = "api-server",
) -> dict:
    """
    运行故障诊断场景

    Args:
        fault_description: 故障描述
        service_name: 出现故障的服务名称

    Returns:
        诊断结果字典
    """
    from devops_crew.crew import DevOpsCrew

    print("\n" + "=" * 65)
    print("🔧 场景：故障诊断")
    print("=" * 65)
    print(f"⚠️  故障描述：{fault_description}")
    print(f"🎯 目标服务：{service_name}")
    print(f"⏰ 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    inputs = {
        "fault_description": fault_description,
        "service_name": service_name,
    }

    crew_instance = DevOpsCrew()
    result = crew_instance.diagnosis_crew().kickoff(inputs=inputs)

    print("\n" + "=" * 65)
    print("✅ 故障诊断完成")
    print("=" * 65)

    return {"scenario": "diagnosis", "result": str(result)}


def run_deployment_scenario(
    app_name: str = "api-server",
    version: str = "v2.2.0",
    environment: str = "production",
) -> dict:
    """
    运行部署场景

    Args:
        app_name: 应用名称
        version: 部署版本
        environment: 目标环境

    Returns:
        部署结果字典
    """
    from devops_crew.crew import DevOpsCrew

    print("\n" + "=" * 65)
    print("🚀 场景：自动化部署")
    print("=" * 65)
    print(f"📦 应用名称：{app_name}")
    print(f"🏷️  部署版本：{version}")
    print(f"🌍 目标环境：{environment}")
    print(f"⏰ 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    inputs = {
        "app_name": app_name,
        "version": version,
        "environment": environment,
        "service_name": app_name,
    }

    crew_instance = DevOpsCrew()
    result = crew_instance.deployment_crew().kickoff(inputs=inputs)

    print("\n" + "=" * 65)
    print("✅ 部署完成")
    print("=" * 65)

    return {"scenario": "deployment", "result": str(result)}


def run_optimization_scenario(
    performance_issue: str = "系统响应时间偏高，CPU使用率过高",
    optimization_target: str = "降低P99延迟到1秒以内，CPU使用率降至60%以下",
    service_name: str = "production-cluster",
    analysis_period: str = "最近7天",
) -> dict:
    """
    运行性能优化场景

    Args:
        performance_issue: 性能问题描述
        optimization_target: 优化目标
        service_name: 服务名称
        analysis_period: 分析周期

    Returns:
        优化结果字典
    """
    from devops_crew.crew import DevOpsCrew

    print("\n" + "=" * 65)
    print("⚡ 场景：性能优化")
    print("=" * 65)
    print(f"📊 性能问题：{performance_issue}")
    print(f"🎯 优化目标：{optimization_target}")
    print(f"⏰ 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    inputs = {
        "performance_issue": performance_issue,
        "performance_analysis": performance_issue,
        "optimization_target": optimization_target,
        "service_name": service_name,
        "analysis_period": analysis_period,
    }

    crew_instance = DevOpsCrew()
    result = crew_instance.optimization_crew().kickoff(inputs=inputs)

    print("\n" + "=" * 65)
    print("✅ 性能优化分析完成")
    print("=" * 65)

    return {"scenario": "optimization", "result": str(result)}


def interactive_menu() -> None:
    """交互式场景选择菜单"""
    print("\n" + "=" * 65)
    print("🤖 多智能体 DevOps 运维系统")
    print("   武汉大学本科毕业设计 | 多智能体协同软件运维")
    print("=" * 65)
    print()
    print("请选择运维场景：")
    print()
    print("  1. 🔍 基础设施监控  - 实时检查系统状态和告警")
    print("  2. 🔧 故障诊断      - 分析故障原因并给出修复建议")
    print("  3. 🚀 自动化部署    - 执行应用程序部署流程")
    print("  4. ⚡ 性能优化      - 分析性能瓶颈并提出优化方案")
    print("  5. 🚪 退出")
    print()

    while True:
        choice = input("请输入选项 (1-5): ").strip()

        if choice == "1":
            service = input("请输入监控目标 [默认: production-cluster]: ").strip() or "production-cluster"
            run_monitoring_scenario(service)
            break

        elif choice == "2":
            print("\n常见故障描述示例：")
            print("  - 数据库连接池耗尽，API响应超时")
            print("  - 服务内存持续增长，OOM崩溃")
            print("  - worker-service 启动失败")
            fault = input("\n请描述故障现象 [默认: API响应超时，错误率升高]: ").strip()
            fault = fault or "API响应超时，错误率升高"
            service = input("请输入故障服务 [默认: api-server]: ").strip() or "api-server"
            run_diagnosis_scenario(fault, service)
            break

        elif choice == "3":
            app = input("请输入应用名称 [默认: api-server]: ").strip() or "api-server"
            version = input("请输入部署版本 [默认: v2.2.0]: ").strip() or "v2.2.0"
            env = input("请输入目标环境 [默认: production]: ").strip() or "production"
            run_deployment_scenario(app, version, env)
            break

        elif choice == "4":
            issue = input(
                "请描述性能问题 [默认: 系统响应时间偏高]: "
            ).strip() or "系统响应时间偏高，CPU使用率过高"
            run_optimization_scenario(performance_issue=issue)
            break

        elif choice == "5":
            print("\n👋 再见！")
            sys.exit(0)

        else:
            print("❌ 无效选项，请输入 1-5")


def main() -> None:
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="多智能体 DevOps 运维系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py                                    # 交互式菜单
  python main.py --scenario monitor                 # 监控场景
  python main.py --scenario diagnose                # 诊断场景
  python main.py --scenario deploy --app myapp      # 部署场景
  python main.py --scenario optimize                # 优化场景
        """,
    )

    parser.add_argument(
        "--scenario",
        choices=["monitor", "diagnose", "deploy", "optimize"],
        help="运行指定场景",
    )
    parser.add_argument("--service", default="production-cluster", help="服务/集群名称")
    parser.add_argument("--fault", default="服务响应异常", help="故障描述（用于诊断场景）")
    parser.add_argument("--app", default="api-server", help="应用名称（用于部署场景）")
    parser.add_argument("--version", default="v2.2.0", help="部署版本（用于部署场景）")
    parser.add_argument("--env", default="production", help="目标环境（用于部署场景）")
    parser.add_argument(
        "--issue",
        default="系统响应时间偏高，CPU使用率过高",
        help="性能问题描述（用于优化场景）",
    )

    args = parser.parse_args()

    try:
        if args.scenario == "monitor":
            run_monitoring_scenario(args.service)
        elif args.scenario == "diagnose":
            run_diagnosis_scenario(args.fault, args.service)
        elif args.scenario == "deploy":
            run_deployment_scenario(args.app, args.version, args.env)
        elif args.scenario == "optimize":
            run_optimization_scenario(performance_issue=args.issue)
        else:
            # 无参数时进入交互式菜单
            interactive_menu()

    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
        sys.exit(0)
    except Exception as exc:
        logger.error("运行出错: %s", exc, exc_info=True)
        print(f"\n❌ 错误: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
