"""
场景3：性能优化分析演示

场景说明：
  系统性能持续下降，P99 延迟从 500ms 升至 3000ms，CPU 和内存使用率
  偏高。性能优化专家协同基础设施监控专家进行全面的性能分析和优化建议。
  收集指标 → 分析瓶颈 → 制定方案 → 预期效果评估。

演示目标：
  - 展示多维度性能分析（CPU/内存/IO/数据库）
  - 提供优先级排序的优化建议
  - 量化优化预期收益

运行方式：
  python scenario3_optimization.py
  python scenario3_optimization.py --demo
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


def run_optimization_scenario(
    performance_issue: str = "系统P99延迟从500ms升至3000ms，CPU使用率85%，内存使用率88%",
    optimization_target: str = "将P99延迟降至1秒以内，CPU使用率降至60%以下",
    service_name: str = "production-cluster",
    analysis_period: str = "最近7天",
) -> None:
    """
    运行性能优化场景

    Args:
        performance_issue: 性能问题描述
        optimization_target: 优化目标
        service_name: 目标服务/集群
        analysis_period: 分析周期
    """
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print("⚡ 场景3：系统性能优化分析")
    print("=" * 70)
    print(f"""
📊 性能问题：
   问题描述：{performance_issue}
   优化目标：{optimization_target}
   分析范围：{service_name}
   分析周期：{analysis_period}
   开始时间：{start_time.strftime('%Y-%m-%d %H:%M:%S')}

📖 场景说明：
   系统性能持续下滑，需要全面的性能分析和优化方案。智能体团队：
   1. 基础设施监控专家：收集各维度性能指标
   2. 性能优化专家：深度分析瓶颈，制定优化方案

🤖 参与智能体：
   - 基础设施监控专家（指标收集）
   - 性能优化专家（分析和方案制定）
""")
    print("-" * 70)

    print("\n⏳ 正在初始化 DevOps 多智能体团队...\n")

    try:
        from devops_crew.crew import DevOpsCrew

        inputs = {
            "performance_issue": performance_issue,
            "performance_analysis": performance_issue,
            "optimization_target": optimization_target,
            "service_name": service_name,
            "analysis_period": analysis_period,
        }

        crew_instance = DevOpsCrew()
        optimization_crew = crew_instance.optimization_crew()

        print("✅ 智能体团队就绪，开始性能分析...\n")
        print("-" * 70)

        result = optimization_crew.kickoff(inputs=inputs)

        end_time = datetime.now()
        duration = (end_time - start_time).seconds

        print("\n" + "=" * 70)
        print("✅ 性能优化分析完成！")
        print("=" * 70)
        print(f"""
📊 分析摘要：
   分析范围：{service_name}
   分析周期：{analysis_period}
   耗时：    {duration} 秒
   完成时间：{end_time.strftime('%Y-%m-%d %H:%M:%S')}
""")

        if result:
            print("📄 性能优化报告：")
            print("-" * 70)
            print(str(result)[:2000])

    except ImportError:
        print(f"\n⚠️  LLM 未配置，切换到演示模式...\n")
        _run_demo_mode(performance_issue, optimization_target, service_name)

    except Exception as e:
        logger.error("场景执行失败: %s", e, exc_info=True)
        print(f"\n❌ 执行错误: {e}")
        _run_demo_mode(performance_issue, optimization_target, service_name)


def _run_demo_mode(
    performance_issue: str,
    optimization_target: str,
    service_name: str,
) -> None:
    """演示模式：展示性能分析流程"""
    print("\n" + "=" * 70)
    print("🎭 演示模式：模拟性能优化分析流程")
    print("=" * 70)

    from devops_crew.tools.monitor_tools import (
        get_cpu_usage,
        get_memory_usage,
        get_disk_usage,
        check_service_health,
    )
    from devops_crew.tools.log_tools import get_log_statistics, analyze_errors
    from devops_crew.tools.kubernetes_tools import list_pods, get_pod_status

    print(f"\n📊 步骤1：【监控专家】收集系统资源使用情况")
    print("-" * 50)

    cpu_data = json.loads(get_cpu_usage.run(None))
    mem_data = json.loads(get_memory_usage.run(None))
    disk_data = json.loads(get_disk_usage.run(None))

    print("✅ 资源使用情况汇总：")
    print(f"   集群平均 CPU：{cpu_data.get('cluster_avg_cpu', 'N/A')}%")
    if 'nodes' in cpu_data:
        for node in cpu_data['nodes']:
            status_icon = "🔴" if node['status'] == 'critical' else ("🟡" if node['status'] == 'warning' else "🟢")
            print(f"   {status_icon} {node['node']}: CPU {node['cpu_percent']}%")

    print(f"\n   内存使用情况：")
    if 'nodes' in mem_data:
        for node in mem_data['nodes']:
            status_icon = "🔴" if node['status'] == 'critical' else ("🟡" if node['status'] == 'warning' else "🟢")
            print(f"   {status_icon} {node['node']}: 内存 {node['percent']}% ({node['used_gb']}GB/{node['total_gb']}GB)")

    print(f"\n🔬 步骤2：【监控专家】识别高负载服务")
    print("-" * 50)
    pods = json.loads(list_pods.run("production", None, None))
    high_cpu_pods = [
        p for p in pods['pods']
        if p.get('cpu_usage', '0m').replace('m', '').isdigit()
        and int(p.get('cpu_usage', '0m').replace('m', '')) > 500
    ]
    print(f"✅ Pod 资源使用分析：")
    for pod in pods['pods']:
        print(f"   📦 {pod['name'][:40]:<40} CPU: {pod['cpu_usage']:<8} 内存: {pod['memory_usage']}")

    print(f"\n📋 步骤3：【性能专家】分析日志中的性能问题")
    print("-" * 50)
    log_stats = json.loads(get_log_statistics.run(None, "service"))
    print(f"✅ 日志统计分析：")
    print(f"   总日志条数: {log_stats['total_log_entries']}")
    print(f"   错误率: {log_stats['error_rate']}%")
    print(f"   健康评分: {log_stats['health_score']['score']}/100 ({log_stats['health_score']['grade']})")
    print(f"   {log_stats['health_score']['description']}")
    if log_stats.get('top_issues'):
        print(f"   主要问题 TOP 3:")
        for i, issue in enumerate(log_stats['top_issues'][:3], 1):
            print(f"   {i}. {issue[:60]}...")

    print(f"\n🎯 步骤4：【性能专家】瓶颈分析和优化建议")
    print("-" * 50)

    # 生成综合优化报告
    optimization_report = {
        "性能瓶颈分析": [
            {
                "瓶颈": "数据库连接池",
                "严重程度": "🔴 高",
                "当前状况": "pool_size=5，高峰期全部耗尽",
                "影响": "API 请求 503 错误",
            },
            {
                "瓶颈": "MySQL 慢查询",
                "严重程度": "🔴 高",
                "当前状况": "orders 表全表扫描，耗时 8-12s",
                "影响": "连接长时间占用，加剧连接池压力",
            },
            {
                "瓶颈": "Node-3 资源过载",
                "严重程度": "🟡 中",
                "当前状况": "CPU 88.9%，内存 88.8%，磁盘 89%",
                "影响": "Pod 调度性能下降",
            },
            {
                "瓶颈": "API 副本不足",
                "严重程度": "🟡 中",
                "当前状况": "仅 2 个副本，单点压力大",
                "影响": "高峰期响应时间升高",
            },
        ],
        "优化方案（按优先级排序）": [
            {
                "优先级": "P1 - 立即执行",
                "措施": "增大数据库连接池",
                "配置": "pool_size: 5→20, max_overflow: 5→30",
                "预期效果": "消除连接池耗尽，503 错误降至 0",
                "实施风险": "低",
                "预计时间": "30 分钟（重新部署）",
            },
            {
                "优先级": "P1 - 立即执行",
                "措施": "为 orders.status 字段添加索引",
                "配置": "CREATE INDEX idx_orders_status ON orders(status, created_at)",
                "预期效果": "慢查询时间: 8-12s → 0.1-0.3s",
                "实施风险": "低",
                "预计时间": "5 分钟（在线 DDL）",
            },
            {
                "优先级": "P2 - 本周内",
                "措施": "水平扩展 API 服务",
                "配置": "replicas: 2→4",
                "预期效果": "P99 延迟降低 50%，吞吐量翻倍",
                "实施风险": "低",
                "预计时间": "10 分钟（K8s 滚动更新）",
            },
            {
                "优先级": "P2 - 本周内",
                "措施": "迁移 Node-3 部分 Pod",
                "配置": "使用 node affinity 均衡负载",
                "预期效果": "Node-3 CPU 降至 60%，提高集群稳定性",
                "实施风险": "中",
                "预计时间": "1 小时",
            },
            {
                "优先级": "P3 - 下个迭代",
                "措施": "实现读写分离",
                "配置": "主库写，从库读，使用 ProxySQL 路由",
                "预期效果": "主库压力降低 70%",
                "实施风险": "中",
                "预计时间": "1 周",
            },
        ],
    }

    print("✅ 性能优化报告生成完成：")
    print()

    print("  🔴 发现性能瓶颈：")
    for item in optimization_report["性能瓶颈分析"]:
        print(f"     {item['严重程度']} {item['瓶颈']}: {item['影响']}")

    print()
    print("  💡 优化建议（按优先级）：")
    for plan in optimization_report["优化方案（按优先级排序）"]:
        print(f"     [{plan['优先级']}]")
        print(f"       措施: {plan['措施']}")
        print(f"       预期: {plan['预期效果']}")
        print(f"       时间: {plan['预计时间']}")
        print()

    print("\n" + "=" * 70)
    print("🎉 演示：性能优化分析完成！")
    print("=" * 70)
    print(f"""
📊 优化分析摘要（演示）：

   当前性能评分：58/100 (D 级 - 需要改善)
   目标性能评分：85/100 (B 级 - 良好)

   关键指标改善预测：
   ┌─────────────────────────────────────────┐
   │ 指标           │ 当前值  │ 优化后预测  │
   ├─────────────────────────────────────────│
   │ P99 延迟       │ 3000ms │ <1000ms    │
   │ API 错误率     │ 30%    │ <1%        │
   │ DB 连接成功率  │ 70%    │ >99%       │
   │ CPU 使用率     │ 85%    │ <65%       │
   │ 内存使用率     │ 88%    │ <75%       │
   └─────────────────────────────────────────┘

   预计优化实施总周期：1 周
   预期 ROI：硬件成本节省 20%，用户体验提升 60%
""")


def main():
    parser = argparse.ArgumentParser(
        description="场景3：系统性能优化分析演示",
    )
    parser.add_argument(
        "--issue",
        default="系统P99延迟从500ms升至3000ms，CPU使用率85%，内存使用率88%",
        help="性能问题描述",
    )
    parser.add_argument(
        "--target",
        default="将P99延迟降至1秒以内，CPU使用率降至60%以下",
        help="优化目标",
    )
    parser.add_argument("--service", default="production-cluster", help="服务名称")
    parser.add_argument("--demo", action="store_true", help="使用演示模式")

    args = parser.parse_args()

    if args.demo:
        _run_demo_mode(args.issue, args.target, args.service)
    else:
        run_optimization_scenario(args.issue, args.target, args.service)


if __name__ == "__main__":
    main()
