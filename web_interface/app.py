#!/usr/bin/env python3
"""
多智能体 DevOps / 软件开发系统 - Web 管理界面
Flask 后端主文件，提供 RESTful API 和 WebSocket 实时通信
"""

import os
import sys
import json
import time
import logging
import threading
import psutil
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# 将项目根目录和 my_first_crew 模块路径加入 sys.path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_CREW_PATH = os.path.join(os.path.dirname(__file__), '..', 'my_first_crew', 'src')
for _p in (_ROOT, _CREW_PATH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 延迟导入软件开发场景（避免 import 失败影响整体启动）
try:
    from scenario_dev_complete import (
        SCENARIOS_META as DEV_SCENARIOS_META,
        run_scenario_auth,
        run_scenario_data_pipeline,
        run_scenario_rest_api,
    )
    _DEV_SCENARIOS_AVAILABLE = True
except Exception as _e:  # pylint: disable=broad-except
    _DEV_SCENARIOS_AVAILABLE = False
    logging.getLogger(__name__).warning("软件开发场景模块加载失败: %s", _e)
    DEV_SCENARIOS_META = []

# ──────────────────────────────────────────────
# 应用初始化
# ──────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devops-web-secret-2024')

CORS(app, resources={r'/api/*': {'origins': '*'}})
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 内存存储（用于演示；生产环境应替换为数据库）
# ──────────────────────────────────────────────
execution_history = []      # 执行历史列表
log_buffer = []             # 日志缓冲
running_tasks = {}          # 当前运行中的任务

# 系统设置（可通过设置页面修改）
system_settings = {
    'cpu_alert_threshold': 80,
    'memory_alert_threshold': 85,
    'disk_alert_threshold': 90,
    'log_level': 'INFO',
    'auto_refresh_interval': 5,
    'max_log_lines': 500,
}

# 场景定义
SCENARIOS = [
    {
        'id': 'deployment',
        'name': '自动化部署流程',
        'description': '执行完整的自动化部署流程，包括代码检出、构建、测试和部署到生产环境。',
        'icon': 'fas fa-rocket',
        'expected_duration': '2-5 分钟',
        'agents': ['monitor_agent', 'remediation_agent'],
        'steps': ['代码检出', '环境检查', '依赖安装', '运行测试', '构建镜像', '部署服务', '健康检查'],
    },
    {
        'id': 'diagnosis',
        'name': '故障诊断和修复',
        'description': '自动检测系统异常，分析根因，并执行修复方案，恢复服务正常运行。',
        'icon': 'fas fa-stethoscope',
        'expected_duration': '3-8 分钟',
        'agents': ['monitor_agent', 'log_analyzer_agent', 'diagnosis_agent', 'remediation_agent'],
        'steps': ['异常检测', '日志收集', '根因分析', '制定方案', '执行修复', '验证结果'],
    },
    {
        'id': 'optimization',
        'name': '性能优化分析',
        'description': '全面分析系统性能瓶颈，提供优化建议，并自动执行可安全执行的优化操作。',
        'icon': 'fas fa-chart-line',
        'expected_duration': '5-10 分钟',
        'agents': ['monitor_agent', 'log_analyzer_agent', 'diagnosis_agent'],
        'steps': ['性能基线收集', '瓶颈识别', '资源分析', '优化建议生成', '执行优化', '效果验证'],
    },
    {
        'id': 'monitoring',
        'name': '监控告警处理',
        'description': '处理监控系统发来的告警，自动分类告警级别，并触发相应的处理流程。',
        'icon': 'fas fa-bell',
        'expected_duration': '1-3 分钟',
        'agents': ['monitor_agent', 'diagnosis_agent'],
        'steps': ['告警接收', '优先级评估', '影响范围分析', '通知相关人员', '执行处理', '关闭告警'],
    },
]

# 智能体定义
AGENTS = [
    {'id': 'monitor_agent',      'name': '监控专家',   'role': '系统监控与指标采集', 'icon': 'fas fa-eye'},
    {'id': 'log_analyzer_agent', 'name': '日志分析师', 'role': '日志解析与异常检测', 'icon': 'fas fa-file-alt'},
    {'id': 'diagnosis_agent',    'name': '诊断专家',   'role': '根因分析与问题定位', 'icon': 'fas fa-search'},
    {'id': 'remediation_agent',  'name': '修复专家',   'role': '故障修复与服务恢复', 'icon': 'fas fa-wrench'},
    {'id': 'deploy_agent',       'name': '部署专家',   'role': '自动化部署与发布管理', 'icon': 'fas fa-cloud-upload-alt'},
]


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def get_system_metrics():
    """获取当前系统资源指标"""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        'cpu_percent': round(cpu, 1),
        'memory_percent': round(mem.percent, 1),
        'memory_used_gb': round(mem.used / (1024 ** 3), 2),
        'memory_total_gb': round(mem.total / (1024 ** 3), 2),
        'disk_percent': round(disk.percent, 1),
        'disk_used_gb': round(disk.used / (1024 ** 3), 2),
        'disk_total_gb': round(disk.total / (1024 ** 3), 2),
        'timestamp': datetime.now().strftime('%H:%M:%S'),
    }


def get_agent_statuses():
    """根据当前运行任务计算每个智能体的状态"""
    busy_agents = set()
    for task_info in running_tasks.values():
        busy_agents.update(task_info.get('active_agents', []))

    statuses = []
    for agent in AGENTS:
        if agent['id'] in busy_agents:
            status = 'busy'
        else:
            status = 'online'
        statuses.append({**agent, 'status': status})
    return statuses


def get_active_alerts(metrics):
    """根据系统指标生成告警列表"""
    alerts = []
    if metrics['cpu_percent'] >= system_settings['cpu_alert_threshold']:
        alerts.append({'level': 'danger', 'message': f"CPU 使用率过高: {metrics['cpu_percent']}%"})
    if metrics['memory_percent'] >= system_settings['memory_alert_threshold']:
        alerts.append({'level': 'warning', 'message': f"内存使用率较高: {metrics['memory_percent']}%"})
    if metrics['disk_percent'] >= system_settings['disk_alert_threshold']:
        alerts.append({'level': 'danger', 'message': f"磁盘使用率过高: {metrics['disk_percent']}%"})
    return alerts


def add_log(level, message, source='system'):
    """添加一条日志并通过 WebSocket 广播"""
    entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'level': level.upper(),
        'source': source,
        'message': message,
    }
    log_buffer.append(entry)
    # 保持缓冲大小
    if len(log_buffer) > system_settings['max_log_lines']:
        log_buffer.pop(0)
    # 实时推送
    socketio.emit('new_log', entry)
    logger.log(getattr(logging, level.upper(), logging.INFO), '[%s] %s', source, message)
    return entry


def run_scenario_thread(scenario_id, task_id, params):
    """在后台线程中执行场景，并通过 WebSocket 推送进度"""
    scenario = next((s for s in SCENARIOS if s['id'] == scenario_id), None)
    if not scenario:
        return

    running_tasks[task_id] = {
        'scenario_id': scenario_id,
        'scenario_name': scenario['name'],
        'start_time': datetime.now(),
        'status': 'running',
        'active_agents': scenario['agents'],
        'progress': 0,
    }

    add_log('INFO', f"开始执行场景: {scenario['name']}", source='orchestrator')
    socketio.emit('task_started', {'task_id': task_id, 'scenario': scenario})

    steps = scenario['steps']
    total = len(steps)

    try:
        for idx, step in enumerate(steps, 1):
            # 模拟步骤执行（实际项目中替换为真实 Crew AI 调用）
            progress = int(idx / total * 100)
            running_tasks[task_id]['progress'] = progress

            # 选一个活跃智能体模拟对话
            active_agent_id = scenario['agents'][idx % len(scenario['agents'])]
            active_agent = next((a for a in AGENTS if a['id'] == active_agent_id), AGENTS[0])

            step_msg = f"[步骤 {idx}/{total}] {step} — 正在处理..."
            add_log('INFO', step_msg, source=active_agent['name'])

            socketio.emit('task_progress', {
                'task_id': task_id,
                'step': step,
                'step_index': idx,
                'total_steps': total,
                'progress': progress,
                'agent': active_agent,
                'message': step_msg,
            })

            # 模拟执行耗时（0.8 ~ 2 秒每步）
            time.sleep(1.2)

        # 场景执行完毕
        duration = (datetime.now() - running_tasks[task_id]['start_time']).total_seconds()
        result_msg = f"场景 [{scenario['name']}] 执行完成，耗时 {duration:.1f} 秒"
        add_log('INFO', result_msg, source='orchestrator')

        history_entry = {
            'id': task_id,
            'scenario_id': scenario_id,
            'scenario_name': scenario['name'],
            'start_time': running_tasks[task_id]['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'duration': round(duration, 1),
            'status': 'success',
            'params': params,
            'result': result_msg,
        }
        execution_history.append(history_entry)

        running_tasks[task_id]['status'] = 'completed'
        socketio.emit('task_completed', {'task_id': task_id, 'result': result_msg, 'history': history_entry})

    except Exception as exc:
        err_msg = f"场景执行失败: {exc}"
        add_log('ERROR', err_msg, source='orchestrator')
        running_tasks[task_id]['status'] = 'failed'
        execution_history.append({
            'id': task_id,
            'scenario_id': scenario_id,
            'scenario_name': scenario['name'],
            'start_time': running_tasks[task_id]['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'duration': 0,
            'status': 'failed',
            'params': params,
            'result': err_msg,
        })
        socketio.emit('task_failed', {'task_id': task_id, 'error': err_msg})

    finally:
        running_tasks.pop(task_id, None)


# ──────────────────────────────────────────────
# 页面路由
# ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scenarios')
def scenarios():
    return render_template('scenarios.html')


@app.route('/logs')
def logs():
    return render_template('logs.html')


@app.route('/history')
def history():
    return render_template('history.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/software-dev')
def software_dev():
    """软件开发智能体框架 Web 界面"""
    return render_template('software_dev_index.html')


# ──────────────────────────────────────────────
# 软件开发场景数据（对外暴露给 API）
# ──────────────────────────────────────────────

# 软件开发智能体定义（5 个专业角色）
DEV_AGENTS = [
    {
        'id': 'architect',
        'name': '架构师',
        'role': '系统架构设计与技术选型',
        'icon': 'fas fa-drafting-compass',
        'color': 'primary',
    },
    {
        'id': 'developer',
        'name': '开发工程师',
        'role': '代码实现与功能开发',
        'icon': 'fas fa-code',
        'color': 'success',
    },
    {
        'id': 'tester',
        'name': '测试工程师',
        'role': '单元测试生成与质量评估',
        'icon': 'fas fa-vial',
        'color': 'info',
    },
    {
        'id': 'reviewer',
        'name': '代码审查官',
        'role': '代码审查与安全扫描',
        'icon': 'fas fa-search-plus',
        'color': 'warning',
    },
    {
        'id': 'pm',
        'name': '项目经理',
        'role': '任务协调与进度管理',
        'icon': 'fas fa-tasks',
        'color': 'danger',
    },
]

# 软件开发场景的运行状态存储
dev_running_tasks: dict = {}
dev_execution_history: list = []
dev_agent_statuses: dict = {a['id']: 'online' for a in DEV_AGENTS}


def _get_dev_agent_statuses() -> list:
    """获取软件开发智能体当前状态列表"""
    busy = set()
    for t in dev_running_tasks.values():
        busy.update(t.get('active_agents', []))
    result = []
    for agent in DEV_AGENTS:
        result.append({
            **agent,
            'status': 'busy' if agent['id'] in busy else 'online',
        })
    return result


def _run_dev_scenario_thread(scenario_id: str, task_id: str, params: dict) -> None:
    """在后台线程中执行软件开发场景"""
    meta = next((m for m in DEV_SCENARIOS_META if m['id'] == scenario_id), None)
    if not meta:
        return

    runner_map = {
        'auth_module': run_scenario_auth,
        'data_pipeline': run_scenario_data_pipeline,
        'rest_api': run_scenario_rest_api,
    }
    runner = runner_map.get(scenario_id)
    if not runner or not _DEV_SCENARIOS_AVAILABLE:
        # 若模块不可用，走模拟流程
        _run_dev_scenario_simulated(scenario_id, task_id, params, meta)
        return

    dev_running_tasks[task_id] = {
        'scenario_id': scenario_id,
        'scenario_name': meta['name'],
        'start_time': datetime.now(),
        'status': 'running',
        'active_agents': meta['agents'],
        'progress': 0,
    }
    add_log('INFO', f"[软件开发] 开始执行场景: {meta['name']}", source='dev-orchestrator')
    socketio.emit('dev_task_started', {'task_id': task_id, 'scenario': meta})

    steps = meta['steps']
    total = len(steps)

    def _progress_cb(step_idx: int, total_steps: int, step_name: str) -> None:
        progress = int(step_idx / total_steps * 100)
        dev_running_tasks[task_id]['progress'] = progress
        agent_ids = meta['agents']
        active_agent_id = agent_ids[step_idx % len(agent_ids)]
        active_agent = next((a for a in DEV_AGENTS if a['id'] == active_agent_id), DEV_AGENTS[0])
        msg = f"[步骤 {step_idx}/{total_steps}] {step_name} — 正在处理..."
        add_log('INFO', msg, source=active_agent['name'])
        socketio.emit('dev_task_progress', {
            'task_id': task_id,
            'step': step_name,
            'step_index': step_idx,
            'total_steps': total_steps,
            'progress': progress,
            'agent': active_agent,
            'message': msg,
        })

    try:
        wf_result = runner(progress_callback=_progress_cb)
        duration = wf_result.duration
        result_msg = f"场景 [{meta['name']}] 执行完成，耗时 {duration:.1f} 秒"
        add_log('INFO', result_msg, source='dev-orchestrator')

        history_entry = {
            'id': task_id,
            'scenario_id': scenario_id,
            'scenario_name': meta['name'],
            'start_time': dev_running_tasks[task_id]['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'duration': round(duration, 1),
            'status': 'success' if wf_result.success else 'failed',
            'params': params,
            'result': result_msg,
            'step_results': wf_result.step_results,
        }
        dev_execution_history.append(history_entry)
        dev_running_tasks[task_id]['status'] = 'completed'
        socketio.emit('dev_task_completed', {
            'task_id': task_id,
            'result': result_msg,
            'history': history_entry,
        })

    except Exception as exc:  # pylint: disable=broad-except
        err_msg = f"场景执行失败: {exc}"
        add_log('ERROR', err_msg, source='dev-orchestrator')
        dev_running_tasks[task_id]['status'] = 'failed'
        dev_execution_history.append({
            'id': task_id,
            'scenario_id': scenario_id,
            'scenario_name': meta['name'],
            'start_time': dev_running_tasks[task_id]['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'duration': 0,
            'status': 'failed',
            'params': params,
            'result': err_msg,
        })
        socketio.emit('dev_task_failed', {'task_id': task_id, 'error': err_msg})

    finally:
        dev_running_tasks.pop(task_id, None)


def _run_dev_scenario_simulated(scenario_id: str, task_id: str, params: dict, meta: dict) -> None:
    """在场景模块不可用时运行模拟流程"""
    dev_running_tasks[task_id] = {
        'scenario_id': scenario_id,
        'scenario_name': meta['name'],
        'start_time': datetime.now(),
        'status': 'running',
        'active_agents': meta['agents'],
        'progress': 0,
    }
    add_log('INFO', f"[软件开发-模拟] 开始场景: {meta['name']}", source='dev-orchestrator')
    socketio.emit('dev_task_started', {'task_id': task_id, 'scenario': meta})

    steps = meta['steps']
    total = len(steps)

    try:
        for idx, step in enumerate(steps, 1):
            progress = int(idx / total * 100)
            dev_running_tasks[task_id]['progress'] = progress
            agent_ids = meta['agents']
            active_agent_id = agent_ids[idx % len(agent_ids)]
            active_agent = next((a for a in DEV_AGENTS if a['id'] == active_agent_id), DEV_AGENTS[0])
            msg = f"[步骤 {idx}/{total}] {step} — 正在处理..."
            add_log('INFO', msg, source=active_agent['name'])
            socketio.emit('dev_task_progress', {
                'task_id': task_id,
                'step': step,
                'step_index': idx,
                'total_steps': total,
                'progress': progress,
                'agent': active_agent,
                'message': msg,
            })
            time.sleep(1.2)

        duration = (datetime.now() - dev_running_tasks[task_id]['start_time']).total_seconds()
        result_msg = f"场景 [{meta['name']}] 执行完成，耗时 {duration:.1f} 秒"
        add_log('INFO', result_msg, source='dev-orchestrator')
        history_entry = {
            'id': task_id,
            'scenario_id': scenario_id,
            'scenario_name': meta['name'],
            'start_time': dev_running_tasks[task_id]['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'duration': round(duration, 1),
            'status': 'success',
            'params': params,
            'result': result_msg,
        }
        dev_execution_history.append(history_entry)
        dev_running_tasks[task_id]['status'] = 'completed'
        socketio.emit('dev_task_completed', {
            'task_id': task_id,
            'result': result_msg,
            'history': history_entry,
        })

    except Exception as exc:  # pylint: disable=broad-except
        err_msg = f"场景执行失败: {exc}"
        add_log('ERROR', err_msg, source='dev-orchestrator')
        dev_running_tasks[task_id]['status'] = 'failed'
        socketio.emit('dev_task_failed', {'task_id': task_id, 'error': err_msg})

    finally:
        dev_running_tasks.pop(task_id, None)


# ──────────────────────────────────────────────
# REST API
# ──────────────────────────────────────────────

@app.route('/api/dashboard')
def api_dashboard():
    """获取仪表板数据"""
    metrics = get_system_metrics()
    alerts = get_active_alerts(metrics)
    agent_statuses = get_agent_statuses()
    recent_history = sorted(execution_history, key=lambda h: h['start_time'], reverse=True)[:5]

    return jsonify({
        'metrics': metrics,
        'alerts': alerts,
        'alert_count': len(alerts),
        'agents': agent_statuses,
        'running_tasks': len(running_tasks),
        'recent_history': recent_history,
    })


@app.route('/api/scenarios')
def api_scenarios():
    """获取所有可用场景"""
    return jsonify({'scenarios': SCENARIOS})


@app.route('/api/scenarios/<scenario_id>/run', methods=['POST'])
def api_run_scenario(scenario_id):
    """执行指定场景"""
    scenario = next((s for s in SCENARIOS if s['id'] == scenario_id), None)
    if not scenario:
        return jsonify({'error': '场景不存在'}), 404

    params = request.get_json(silent=True) or {}
    task_id = f"{scenario_id}_{int(time.time() * 1000)}"

    # 在后台线程中执行
    thread = threading.Thread(
        target=run_scenario_thread,
        args=(scenario_id, task_id, params),
        daemon=True,
    )
    thread.start()

    add_log('INFO', f"已触发场景: {scenario['name']} (task_id={task_id})", source='api')

    return jsonify({'task_id': task_id, 'scenario': scenario, 'status': 'started'})


@app.route('/api/logs')
def api_logs():
    """获取日志列表"""
    level_filter = request.args.get('level', 'ALL').upper()
    search = request.args.get('search', '').lower()
    limit = int(request.args.get('limit', 200))

    filtered = [
        entry for entry in log_buffer
        if (level_filter == 'ALL' or entry['level'] == level_filter)
        and (not search or search in entry['message'].lower() or search in entry['source'].lower())
    ]

    return jsonify({'logs': filtered[-limit:]})


@app.route('/api/history')
def api_history():
    """获取执行历史"""
    search = request.args.get('search', '').lower()
    status_filter = request.args.get('status', 'ALL')

    filtered = [
        h for h in execution_history
        if (status_filter == 'ALL' or h['status'] == status_filter)
        and (not search or search in h['scenario_name'].lower())
    ]

    return jsonify({
        'history': sorted(filtered, key=lambda h: h['start_time'], reverse=True),
        'total': len(filtered),
    })


@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """获取系统设置"""
    return jsonify(system_settings)


@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """更新系统设置"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    allowed_keys = set(system_settings.keys())
    for key, value in data.items():
        if key in allowed_keys:
            system_settings[key] = value

    add_log('INFO', '系统设置已更新', source='settings')
    return jsonify({'success': True, 'settings': system_settings})


@app.route('/api/metrics/history')
def api_metrics_history():
    """获取最近 20 个时间点的指标（用于趋势图）"""
    # 实际项目中从时序数据库读取；此处返回模拟数据
    import random
    points = []
    now = time.time()
    for i in range(20):
        ts = now - (19 - i) * 15
        points.append({
            'timestamp': datetime.fromtimestamp(ts).strftime('%H:%M:%S'),
            'cpu': round(random.uniform(20, 75), 1),
            'memory': round(random.uniform(40, 80), 1),
        })
    return jsonify({'points': points})


# ──────────────────────────────────────────────
# 软件开发框架 API
# ──────────────────────────────────────────────

@app.route('/api/dev/agents')
def api_dev_agents():
    """获取软件开发智能体状态"""
    return jsonify({
        'agents': _get_dev_agent_statuses(),
        'available': _DEV_SCENARIOS_AVAILABLE,
    })


@app.route('/api/dev/scenarios')
def api_dev_scenarios():
    """获取软件开发场景列表"""
    return jsonify({'scenarios': DEV_SCENARIOS_META})


@app.route('/api/dev/scenarios/<scenario_id>/run', methods=['POST'])
def api_run_dev_scenario(scenario_id):
    """执行软件开发场景"""
    meta = next((m for m in DEV_SCENARIOS_META if m['id'] == scenario_id), None)
    if not meta:
        return jsonify({'error': '场景不存在'}), 404

    params = request.get_json(silent=True) or {}
    task_id = f"dev_{scenario_id}_{int(time.time() * 1000)}"

    thread = threading.Thread(
        target=_run_dev_scenario_thread,
        args=(scenario_id, task_id, params),
        daemon=True,
    )
    thread.start()

    add_log('INFO', f"[软件开发] 已触发场景: {meta['name']} (task_id={task_id})", source='api')
    return jsonify({'task_id': task_id, 'scenario': meta, 'status': 'started'})


@app.route('/api/dev/history')
def api_dev_history():
    """获取软件开发场景执行历史"""
    search = request.args.get('search', '').lower()
    status_filter = request.args.get('status', 'ALL')
    filtered = [
        h for h in dev_execution_history
        if (status_filter == 'ALL' or h['status'] == status_filter)
        and (not search or search in h['scenario_name'].lower())
    ]
    return jsonify({
        'history': sorted(filtered, key=lambda h: h['start_time'], reverse=True),
        'total': len(filtered),
    })


@app.route('/api/dev/dashboard')
def api_dev_dashboard():
    """软件开发框架仪表板数据"""
    recent = sorted(dev_execution_history, key=lambda h: h['start_time'], reverse=True)[:5]
    return jsonify({
        'agents': _get_dev_agent_statuses(),
        'running_tasks': len(dev_running_tasks),
        'total_executed': len(dev_execution_history),
        'success_count': sum(1 for h in dev_execution_history if h['status'] == 'success'),
        'recent_history': recent,
        'available': _DEV_SCENARIOS_AVAILABLE,
    })


# ──────────────────────────────────────────────
# WebSocket 事件
# ──────────────────────────────────────────────

@socketio.on('connect')
def on_connect():
    logger.info('WebSocket 客户端已连接: %s', request.sid)
    # 发送最近 50 条日志
    emit('log_history', {'logs': log_buffer[-50:]})


@socketio.on('disconnect')
def on_disconnect():
    logger.info('WebSocket 客户端已断开: %s', request.sid)


@socketio.on('request_metrics')
def on_request_metrics():
    metrics = get_system_metrics()
    emit('metrics_update', metrics)


# ──────────────────────────────────────────────
# 启动系统日志
# ──────────────────────────────────────────────

def _seed_startup_logs():
    """系统启动时写入几条示例日志"""
    add_log('INFO',  '多智能体 DevOps / 软件开发系统 Web 界面已启动', source='system')
    add_log('INFO',  f"已加载 {len(AGENTS)} 个 DevOps 智能体，{len(DEV_AGENTS)} 个开发智能体", source='system')
    add_log('INFO',  f"软件开发场景: {'已加载 ' + str(len(DEV_SCENARIOS_META)) + ' 个' if _DEV_SCENARIOS_AVAILABLE else '模拟模式'}", source='system')
    add_log('INFO',  '所有智能体就绪，等待任务...', source='orchestrator')


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

if __name__ == '__main__':
    _seed_startup_logs()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    logger.info('启动 Web 服务，监听 http://0.0.0.0:%d', port)
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
