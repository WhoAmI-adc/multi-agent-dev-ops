/**
 * scenarios.js — 场景列表加载与执行
 */

let currentTaskId = null;

// ── 场景颜色主题 ──
const SCENARIO_COLORS = {
  deployment:   { border: '#1565c0', badge: 'bg-primary' },
  diagnosis:    { border: '#c62828', badge: 'bg-danger'  },
  optimization: { border: '#f57f17', badge: 'bg-warning text-dark' },
  monitoring:   { border: '#2e7d32', badge: 'bg-success' },
};

// ── 加载场景卡片 ──
async function loadScenarios() {
  const container = document.getElementById('scenario-cards');
  try {
    const data = await apiFetch('/api/scenarios');
    renderScenarioCards(data.scenarios);
  } catch (e) {
    container.innerHTML = '<div class="col-12 text-center text-danger">加载场景失败</div>';
  }
}

function renderScenarioCards(scenarios) {
  const container = document.getElementById('scenario-cards');
  container.innerHTML = scenarios.map(s => {
    const theme = SCENARIO_COLORS[s.id] || { border: '#607d8b', badge: 'bg-secondary' };
    const agentBadges = s.agents.map(a => `<span class="badge bg-light text-dark border me-1">${agentLabel(a)}</span>`).join('');
    const stepsList = s.steps.slice(0, 4).map(st => `<li>${st}</li>`).join('');
    const moreSteps = s.steps.length > 4 ? `<li class="text-muted">+${s.steps.length - 4} 步...</li>` : '';

    return `
      <div class="col-12 col-md-6">
        <div class="card border-0 shadow-sm h-100 scenario-card" style="border-left:4px solid ${theme.border}!important">
          <div class="card-body d-flex flex-column">
            <div class="d-flex align-items-start mb-2">
              <div class="me-3 fs-2"><i class="${s.icon}" style="color:${theme.border}"></i></div>
              <div>
                <h5 class="card-title mb-1">${s.name}</h5>
                <span class="badge ${theme.badge} mb-1">${s.expected_duration}</span>
              </div>
            </div>
            <p class="card-text text-muted small mb-2">${s.description}</p>
            <div class="mb-2">
              <div class="small text-muted mb-1">参与智能体：</div>
              ${agentBadges}
            </div>
            <div class="mb-3 flex-grow-1">
              <div class="small text-muted mb-1">执行步骤：</div>
              <ol class="ps-3 mb-0 small text-muted">${stepsList}${moreSteps}</ol>
            </div>
            <button class="btn btn-primary btn-sm w-100" id="btn-${s.id}"
                    onclick="runScenario('${s.id}', '${s.name}')">
              <i class="fas fa-play me-1"></i>执行场景
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function agentLabel(agentId) {
  const labels = {
    monitor_agent: '监控专家', log_analyzer_agent: '日志分析师',
    diagnosis_agent: '诊断专家', remediation_agent: '修复专家',
    deploy_agent: '部署专家',
  };
  return labels[agentId] || agentId;
}

// ── 执行场景 ──
async function runScenario(scenarioId, scenarioName) {
  const btn = document.getElementById(`btn-${scenarioId}`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>启动中...';
  }

  try {
    const data = await apiFetch(`/api/scenarios/${scenarioId}/run`, { method: 'POST', body: '{}' });
    currentTaskId = data.task_id;
    showExecutionPanel(scenarioName);
    showToast(`场景「${scenarioName}」已启动`, 'info');
  } catch (e) {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-play me-1"></i>执行场景';
    }
  }
}

// ── 执行面板 ──
function showExecutionPanel(scenarioName) {
  const panel = document.getElementById('execution-panel');
  panel.style.setProperty('display', 'block', 'important');
  panel.scrollIntoView({ behavior: 'smooth' });

  document.getElementById('exec-scenario-name').textContent = scenarioName;
  document.getElementById('exec-progress-bar').style.width = '0%';
  document.getElementById('exec-progress-pct').textContent = '0%';
  document.getElementById('exec-current-step').textContent = '准备中...';
  document.getElementById('agent-dialog-body').innerHTML = '<span class="text-muted">等待智能体响应...</span>';
  document.getElementById('exec-result').style.display = 'none';
}

function closeExecutionPanel() {
  const panel = document.getElementById('execution-panel');
  panel.style.setProperty('display', 'none', 'important');
  resetButtons();
}

function resetButtons() {
  document.querySelectorAll('[id^="btn-"]').forEach(btn => {
    const id = btn.id.replace('btn-', '');
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-play me-1"></i>执行场景';
  });
}

function appendDialog(agent, message, type = 'info') {
  const body = document.getElementById('agent-dialog-body');
  const colors = { info: '#64b5f6', warn: '#ffcc02', error: '#ef9a9a', success: '#a5d6a7' };
  const color = colors[type] || colors.info;
  const line = document.createElement('div');
  line.className = 'mb-1';
  line.innerHTML = `<span style="color:#90caf9">[${new Date().toLocaleTimeString()}]</span> `
    + `<span style="color:${color}" class="fw-bold">${agent}:</span> `
    + `<span>${message}</span>`;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

// ── WebSocket 事件处理 ──
document.addEventListener('DOMContentLoaded', () => {
  loadScenarios();

  // 等待 main.js 初始化 socket
  setTimeout(() => {
    const sock = window._socket;
    if (!sock) return;

    sock.on('task_progress', data => {
      if (data.task_id !== currentTaskId) return;
      const pct = data.progress + '%';
      document.getElementById('exec-progress-bar').style.width = pct;
      document.getElementById('exec-progress-pct').textContent = pct;
      document.getElementById('exec-current-step').textContent = data.step;
      appendDialog(data.agent.name, data.message);
    });

    sock.on('task_completed', data => {
      if (data.task_id !== currentTaskId) return;
      document.getElementById('exec-progress-bar').style.width = '100%';
      document.getElementById('exec-progress-pct').textContent = '100%';
      document.getElementById('exec-current-step').textContent = '执行完成';
      appendDialog('系统', data.result, 'success');

      const resultEl = document.getElementById('exec-result');
      resultEl.style.display = 'block';
      document.getElementById('exec-result-alert').className = 'alert alert-success mb-0';
      document.getElementById('exec-result-alert').innerHTML = `<i class="fas fa-check-circle me-2"></i>${data.result}`;

      document.querySelector('.card-header .fa-cog').classList.remove('fa-spin');
      resetButtons();
      showToast('场景执行成功！', 'success');
    });

    sock.on('task_failed', data => {
      if (data.task_id !== currentTaskId) return;
      appendDialog('系统', `执行失败: ${data.error}`, 'error');
      const resultEl = document.getElementById('exec-result');
      resultEl.style.display = 'block';
      document.getElementById('exec-result-alert').className = 'alert alert-danger mb-0';
      document.getElementById('exec-result-alert').innerHTML = `<i class="fas fa-times-circle me-2"></i>${data.error}`;
      resetButtons();
      showToast('场景执行失败', 'danger');
    });
  }, 500);
});
