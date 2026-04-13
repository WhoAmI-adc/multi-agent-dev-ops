"""
场景4：监控告警处理演示

场景说明：
  系统监控检测到多个并发告警触发，包括高 CPU 使用率、服务宕机、
  磁盘空间不足等。监控告警系统触发后，多智能体团队协作处理：
  检测告警 → 分析原因 → 采取行动 → 生成处理报告。

演示目标：
  - 展示告警处理的自动化工作流
  - 演示多智能体协作处理并发告警
  - 生成完整的告警处理报告

运行方式：
  python scenario4_monitoring.py
  python scenario4_monitoring.py --demo
"""

import sys
import logging
import argparse
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_monitoring_scenario(
    service_name: str = "production-cluster",
) -> None:
    """
    运行监控告警处理场景

    Args:
        service_name: 要监控的服务/集群名称
    """
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print("📡 场景4：监控告警处理")
    print("=" * 70)
    print(f"""
🔔 告警触发：
   监控范围：{service_name}
   触发时间：{start_time.strftime('%Y-%m-%d %H:%M:%S')}
   告警状态：🔴 多个紧急告警触发

📖 场景说明：
   系统监控检测到并发告警，需要快速响应和处理：
   1. 基础设施监控专家：汇总所有告警，评估影响范围
   2. 故障诊断专家：分析告警根因
   3. 自动修复专家：执行缓解措施

🤖 参与智能体：
   - 基础设施监控专家（告警收集和分类）
   - 故障诊断专家（根因分析）
   - 自动修复专家（处理动作）
""")
    print("-" * 70)

    print("\n⏳ 正在初始化 DevOps 多智能体团队...\n")

    try:
        from devops_crew.crew import DevOpsCrew

        inputs = {
            "service_name": service_name,
            "fault_description": f"{service_name} 检测到多个并发告警，包括高CPU、内存、服务异常",
            "diagnosis_result": "根据告警信息和初步分析，需要进行修复",
        }

        crew_instance = DevOpsCrew()

        # 使用监控专用团队
        monitoring_crew = crew_instance.monitoring_crew()

        print("✅ 智能体团队就绪，开始处理告警...\n")
        print("-" * 70)

        result = monitoring_crew.kickoff(inputs=inputs)

        end_time = datetime.now()
        duration = (end_time - start_time).seconds

        print("\n" + "=" * 70)
        print("✅ 告警处理流程完成！")
        print("=" * 70)
        print(f"""
📊 处理摘要：
   监控范围：{service_name}
   响应时间：{duration} 秒
   完成时间：{end_time.strftime('%Y-%m-%d %H:%M:%S')}
""")

        if result:
            print("📄 告警处理报告：")
            print("-" * 70)
            print(str(result)[:2000])

    except ImportError:
        print(f"\n⚠️  LLM 未配置，切换到演示模式...\n")
        _run_demo_mode(service_name)

    except Exception as e:
        logger.error("场景执行失败: %s", e, exc_info=True)
        print(f"\n❌ 执行错误: {e}")
        _run_demo_mode(service_name)


def _run_demo_mode(service_name: str) -> None:
    """演示模式：展示完整的告警处理流程"""
    print("\n" + "=" * 70)
    print("🎭 演示模式：模拟监控告警处理流程")
    print("=" * 70)

    from devops_crew.tools.monitor_tools import (
        get_alerts,
        check_service_health,
        get_cpu_usage,
        get_memory_usage,
        get_disk_usage,
    )
    from devops_crew.tools.log_tools import analyze_errors, filter_by_level
    from devops_crew.tools.kubernetes_tools import list_pods, restart_pod

    now = datetime.now()

    print(f"\n🔔 步骤1：【监控专家】收集当前所有告警")
    print("-" * 50)
    alerts_raw = get_alerts.run(None, None, "firing")
    alerts_data = json.loads(alerts_raw)

    print(f"✅ 告警汇总：共 {alerts_data['total_alerts']} 个活跃告警")
    print(f"   🔴 紧急告警: {alerts_data['critical_count']} 个")
    print(f"   🟡 警告告警: {alerts_data['warning_count']} 个")
    print()
    print("   告警详情：")
    for alert in alerts_data['alerts']:
        icon = "🔴" if alert['severity'] == 'critical' else "🟡"
        print(f"   {icon} [{alert['id']}] {alert['rule']}")
        print(f"      目标: {alert['service']} | 持续: {alert['duration']}")
        print(f"      详情: {alert['message']}")
        print()

    print(f"\n📊 步骤2：【监控专家】收集资源使用指标")
    print("-" * 50)
    cpu_data = json.loads(get_cpu_usage.run(None))
    mem_data = json.loads(get_memory_usage.run(None))
    disk_data = json.loads(get_disk_usage.run(None))

    print("✅ 当前资源使用情况：")
    print(f"\n   CPU 使用率（集群平均: {cpu_data.get('cluster_avg_cpu')}%）：")
    for node in cpu_data.get('nodes', []):
        bar = "█" * int(node['cpu_percent'] / 5) + "░" * (20 - int(node['cpu_percent'] / 5))
        status = "🔴" if node['cpu_percent'] > 85 else ("🟡" if node['cpu_percent'] > 70 else "🟢")
        print(f"   {status} {node['node']}: [{bar}] {node['cpu_percent']}%")

    print(f"\n   内存使用率：")
    for node in mem_data.get('nodes', []):
        bar = "█" * int(node['percent'] / 5) + "░" * (20 - int(node['percent'] / 5))
        status = "🔴" if node['percent'] > 90 else ("🟡" if node['percent'] > 80 else "🟢")
        print(f"   {status} {node['node']}: [{bar}] {node['percent']}%")

    print(f"\n📋 步骤3：【诊断专家】分析告警根因")
    print("-" * 50)
    error_analysis = json.loads(analyze_errors.run(None, 30))

    print("✅ 根因分析结果：")
    print(f"   错误总数: {error_analysis['summary']['total_errors']}")
    print(f"   受影响服务: {', '.join(error_analysis['summary']['affected_services'])}")

    if error_analysis.get('root_cause_hints'):
        print(f"\n   🎯 识别到的根因：")
        for i, hint in enumerate(error_analysis['root_cause_hints'], 1):
            confidence_icon = "🔴" if hint['confidence'] == 'HIGH' else "🟡"
            print(f"   {i}. {confidence_icon} [{hint['confidence']}置信度] {hint['hypothesis']}")
            print(f"      证据: {hint['evidence']}")
            print(f"      建议: {hint['suggestion']}")
            print()

    print(f"\n🔍 步骤4：【修复专家】检查 Pod 状态")
    print("-" * 50)
    pods_data = json.loads(list_pods.run("production", None, None))
    print(f"✅ Pod 状态检查：")
    print(f"   总 Pod 数: {pods_data['total_pods']}")
    print(f"   运行中: {pods_data['running']}")
    print(f"   异常: {pods_data['not_ready']}")

    abnormal_pods = [p for p in pods_data['pods'] if p['status'] != 'Running' or p['restarts'] > 3]
    if abnormal_pods:
        print(f"\n   异常 Pod 列表：")
        for pod in abnormal_pods:
            print(f"   ❌ {pod['name']}")
            print(f"      状态: {pod['status']} | 重启次数: {pod['restarts']}")

    print(f"\n🔧 步骤5：【修复专家】执行修复动作")
    print("-" * 50)

    actions_taken = []

    # 重启崩溃的 Pod
    for pod in abnormal_pods:
        if pod['status'] == 'CrashLoopBackOff' or pod['restarts'] > 5:
            restart_result = json.loads(restart_pod.run(pod['name'], "production"))
            if restart_result['success']:
                print(f"✅ 重启 Pod: {pod['name']}")
                print(f"   新 Pod: {restart_result['new_pod']}")
                actions_taken.append(f"重启 Pod {pod['name']}")

    if not actions_taken:
        print("ℹ️  当前无需立即执行的修复操作")
        actions_taken.append("监控状态，等待告警自动恢复")

    print(f"\n❤️  步骤6：【监控专家】验证修复效果，更新健康状态")
    print("-" * 50)
    health_data = json.loads(check_service_health.run(None))

    print("✅ 服务健康状态：")
    print(f"   整体状态: {health_data['summary']['overall_status']}")
    status_map = {
        "healthy": "🟢 正常",
        "degraded": "🟡 降级",
        "critical": "🔴 严重",
    }
    for svc in health_data['services']:
        status = status_map.get(svc['status'], svc['status'])
        rt = f"{svc['response_time_ms']}ms" if svc['response_time_ms'] else "N/A"
        print(f"   {status} {svc['service']:<20} 响应时间: {rt:<8} 可用性: {svc['uptime_percent']}%")

    # 生成告警处理报告
    print(f"\n📄 步骤7：生成告警处理报告")
    print("-" * 50)

    report = {
        "报告时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "监控范围": service_name,
        "告警统计": {
            "紧急告警": alerts_data['critical_count'],
            "警告告警": alerts_data['warning_count'],
            "已处理": len(actions_taken),
        },
        "根因分析": [h['hypothesis'] for h in error_analysis.get('root_cause_hints', [])],
        "执行动作": actions_taken,
        "当前状态": health_data['summary']['overall_status'],
    }

    print("✅ 告警处理报告：")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("\n" + "=" * 70)
    print("🎉 演示：监控告警处理完成！")
    print("=" * 70)
    print(f"""
📊 告警处理摘要（演示）：

   处理时间：{(datetime.now() - now).seconds} 秒
   告警总数：{alerts_data['total_alerts']} 个
   
   处理结果：
   ┌──────────────────────────────────────────────┐
   │ 告警 ID  │ 状态   │ 处理措施               │
   ├──────────────────────────────────────────────│
   │ alert-001│ 🔄 处理中│ 等待 Node-3 负载均衡  │
   │ alert-002│ 🔄 处理中│ 清理内存，等待优化    │
   │ alert-003│ ✅ 已处理│ 重启 worker-service   │
   │ alert-004│ 🔄 处理中│ 计划磁盘清理          │
   │ alert-005│ 🔄 处理中│ 等待 DB 优化          │
   │ alert-006│ 🔄 处理中│ 等待连接池配置更新    │
   └──────────────────────────────────────────────┘

   下一步行动：
   1. 📧 通知研发团队增大 MySQL 连接池配置
   2. 🗑️  清理 Node-3 磁盘空间（日志归档）
   3. 📈 监控 API 响应时间是否恢复正常
   4. 📝 在事后复盘会议中分析根因
""")


def main():
    parser = argparse.ArgumentParser(
        description="场景4：监控告警处理演示",
    )
    parser.add_argument("--service", default="production-cluster", help="监控范围")
    parser.add_argument("--demo", action="store_true", help="使用演示模式")

    args = parser.parse_args()

    if args.demo:
        _run_demo_mode(args.service)
    else:
        run_monitoring_scenario(args.service)


if __name__ == "__main__":
    main()
