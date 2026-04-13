"""
场景2：故障诊断和自动修复演示

场景说明：
  生产环境 API 服务出现故障，响应时间急剧升高，错误率超过阈值。
  多智能体团队协作进行故障诊断和自动修复：
  检测异常 → 收集日志 → 诊断根因 → 执行修复 → 验证恢复。

演示目标：
  - 展示多智能体协作排查生产故障
  - 演示日志分析、根因诊断、自动修复的完整流程
  - 展示告警→诊断→修复的闭环自动化

运行方式：
  python scenario2_diagnosis.py
  python scenario2_diagnosis.py --fault "数据库连接池耗尽"
"""

import sys
import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_diagnosis_scenario(
    fault_description: str = "API服务响应时间超过5秒，错误率达到30%，数据库连接失败",
    service_name: str = "api-server",
) -> None:
    """
    运行故障诊断和修复场景

    Args:
        fault_description: 故障现象描述
        service_name: 出现故障的服务
    """
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print("🔧 场景2：故障诊断和自动修复")
    print("=" * 70)
    print(f"""
🚨 告警信息：
   故障描述：{fault_description}
   影响服务：{service_name}
   发现时间：{start_time.strftime('%Y-%m-%d %H:%M:%S')}
   严重程度：🔴 紧急

📖 场景说明：
   生产环境出现故障，需要快速诊断并修复。智能体团队将：
   1. 基础设施监控专家：收集异常指标，确认故障范围
   2. 故障诊断专家：分析日志，定位根因
   3. 自动修复专家：执行修复操作，验证恢复

🤖 参与智能体：
   - 基础设施监控专家（异常检测）
   - 故障诊断专家（根因分析）
   - 自动修复专家（执行修复）
""")
    print("-" * 70)

    print("\n⏳ 正在初始化 DevOps 多智能体团队...\n")

    try:
        from devops_crew.crew import DevOpsCrew

        inputs = {
            "fault_description": fault_description,
            "service_name": service_name,
            "diagnosis_result": fault_description,  # 为修复任务提供上下文
        }

        crew_instance = DevOpsCrew()
        remediation_crew = crew_instance.remediation_crew()

        print(f"✅ 智能体团队就绪，开始故障诊断流程...\n")
        print("-" * 70)

        result = remediation_crew.kickoff(inputs=inputs)

        end_time = datetime.now()
        duration = (end_time - start_time).seconds

        print("\n" + "=" * 70)
        print("✅ 故障处理流程完成！")
        print("=" * 70)
        print(f"""
📊 处理摘要：
   故障服务：{service_name}
   MTTR：   {duration} 秒（平均修复时间）
   完成时间：{end_time.strftime('%Y-%m-%d %H:%M:%S')}
""")

        if result:
            print("📄 诊断和修复报告：")
            print("-" * 70)
            print(str(result)[:2000])

    except ImportError:
        print(f"\n⚠️  LLM 未配置，切换到演示模式...\n")
        _run_demo_mode(fault_description, service_name)

    except Exception as e:
        logger.error("场景执行失败: %s", e, exc_info=True)
        print(f"\n❌ 执行错误: {e}")
        print("\n💡 切换到演示模式...")
        _run_demo_mode(fault_description, service_name)


def _run_demo_mode(fault_description: str, service_name: str) -> None:
    """演示模式：展示故障诊断流程的各步骤工具调用结果"""
    print("\n" + "=" * 70)
    print("🎭 演示模式：模拟故障诊断和修复流程")
    print("=" * 70)

    from devops_crew.tools.monitor_tools import get_alerts, check_service_health, get_cpu_usage
    from devops_crew.tools.log_tools import analyze_errors, search_logs, filter_by_level
    from devops_crew.tools.kubernetes_tools import list_pods, get_pod_status, restart_pod
    from devops_crew.tools.docker_tools import get_container_logs

    print(f"\n🚨 步骤1：【监控专家】确认告警和异常指标")
    print("-" * 50)
    alerts = get_alerts.run(None, None, "firing")
    print("✅ 当前活跃告警：")
    import json
    alerts_data = json.loads(alerts)
    print(f"   发现 {alerts_data['total_alerts']} 个告警")
    print(f"   - 紧急告警: {alerts_data['critical_count']} 个")
    print(f"   - 警告告警: {alerts_data['warning_count']} 个")
    for alert in alerts_data['alerts'][:3]:
        print(f"   ⚠️  [{alert['severity'].upper()}] {alert['message']}")

    print(f"\n📋 步骤2：【诊断专家】分析错误日志")
    print("-" * 50)
    error_logs = filter_by_level.run("ERROR", service_name, 10)
    error_data = json.loads(error_logs)
    print(f"✅ 分析完成，发现 {error_data['total_matched']} 条错误日志")
    for entry in error_data['entries'][:3]:
        print(f"   🔴 [{entry['service']}] {entry['message'][:60]}...")

    print(f"\n🔬 步骤3：【诊断专家】深度错误分析")
    print("-" * 50)
    analysis = analyze_errors.run(service_name, 30)
    analysis_data = json.loads(analysis)
    print(f"✅ 错误模式分析完成")
    print(f"   错误总数: {analysis_data['summary']['total_errors']}")
    print(f"   受影响服务: {', '.join(analysis_data['summary']['affected_services'])}")
    if analysis_data.get('root_cause_hints'):
        print(f"   🎯 疑似根因:")
        for hint in analysis_data['root_cause_hints'][:2]:
            print(f"      [{hint['confidence']}] {hint['hypothesis']}")
            print(f"      建议: {hint['suggestion']}")

    print(f"\n🔍 步骤4：【诊断专家】检查 Pod 状态")
    print("-" * 50)
    pods = list_pods.run("production", None, None)
    pods_data = json.loads(pods)
    print(f"✅ Pod 状态检查完成")
    problematic = [p for p in pods_data['pods'] if p['status'] != 'Running' or p['restarts'] > 3]
    if problematic:
        print(f"   发现 {len(problematic)} 个异常 Pod:")
        for pod in problematic:
            print(f"   ❌ {pod['name']}: {pod['status']} (重启次数: {pod['restarts']})")

    print(f"\n🔧 步骤5：【修复专家】执行修复操作")
    print("-" * 50)
    # 重启问题容器
    restart_result = restart_pod.run("worker-service-6b4d9c8f7-k9j2l", "production")
    restart_data = json.loads(restart_result)
    if restart_data['success']:
        print(f"✅ Pod 重启成功")
        print(f"   新 Pod: {restart_data['new_pod']}")

    print(f"\n❤️  步骤6：【监控专家】验证服务恢复")
    print("-" * 50)
    health = check_service_health.run(None)
    health_data = json.loads(health)
    print(f"✅ 健康检查完成")
    print(f"   整体状态: {health_data['summary']['overall_status']}")
    print(f"   正常服务: {health_data['summary']['healthy']}/{health_data['summary']['total']}")

    print("\n" + "=" * 70)
    print("🎉 演示：故障诊断和修复流程完成！")
    print("=" * 70)
    print(f"""
📊 处理摘要（演示）：
   故障服务：{service_name}
   根因：    数据库连接池耗尽 + 慢查询
   修复措施：重启异常 Pod，建议增大连接池配置
   状态：    ✅ 已处理

📝 根因总结：
   1. MySQL 连接数达到 max_connections 上限
   2. 慢查询（无索引全表扫描）占用连接过久
   3. 连接池耗尽导致 API 请求失败

🔧 修复建议：
   1. 立即：重启 worker-service Pod
   2. 短期：增大 DB 连接池（pool_size: 5→20）
   3. 长期：对 orders 表 status 字段添加索引
""")


def main():
    parser = argparse.ArgumentParser(
        description="场景2：故障诊断和自动修复演示",
    )
    parser.add_argument(
        "--fault",
        default="API服务响应时间超过5秒，错误率达到30%，数据库连接失败",
        help="故障描述",
    )
    parser.add_argument("--service", default="api-server", help="故障服务名称")
    parser.add_argument("--demo", action="store_true", help="使用演示模式")

    args = parser.parse_args()

    if args.demo:
        _run_demo_mode(args.fault, args.service)
    else:
        run_diagnosis_scenario(args.fault, args.service)


if __name__ == "__main__":
    main()
