/**
 * dashboard.js — 仪表板实时刷新与图表
 */

let perfChart = null;
const chartLabels = [];
const chartCpu = [];
const chartMem = [];
const MAX_CHART_POINTS = 20;

// ── 初始化性能图表 ──
function initPerfChart() {
  const ctx = document.getElementById('performanceChart');
  if (!ctx) return;

  perfChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartLabels,
      datasets: [
        {
          label: 'CPU %',
          data: chartCpu,
          borderColor: '#1565c0',
          backgroundColor: 'rgba(21,101,192,.1)',
          tension: .4,
          fill: true,
          pointRadius: 2,
        },
        {
          label: '内存 %',
          data: chartMem,
          borderColor: '#2e7d32',
          backgroundColor: 'rgba(46,125,50,.08)',
          tension: .4,
          fill: true,
          pointRadius: 2,
        },
      ],
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } },
      scales: {
        y: { min: 0, max: 100, ticks: { font: { size: 10 }, callback: v => v + '%' } },
        x: { ticks: { font: { size: 10 }, maxTicksLimit: 8 } },
      },
    },
  });
}

function pushChartPoint(timestamp, cpu, memory) {
  chartLabels.push(timestamp);
  chartCpu.push(cpu);
  chartMem.push(memory);
  if (chartLabels.length > MAX_CHART_POINTS) {
    chartLabels.shift(); chartCpu.shift(); chartMem.shift();
  }
  if (perfChart) perfChart.update();
}

// ── 更新指标卡片 ──
function updateMetricCards(metrics) {
  setText('cpu-value',   metrics.cpu_percent + '%');
  setText('mem-value',   metrics.memory_percent + '%');
  setText('disk-value',  metrics.disk_percent + '%');
  setText('mem-detail',  `${metrics.memory_used_gb} / ${metrics.memory_total_gb} GB`);
  setText('disk-detail', `${metrics.disk_used_gb} / ${metrics.disk_total_gb} GB`);
  setText('lastRefresh', metrics.timestamp);

  setBar('cpu-bar',  metrics.cpu_percent,    80);
  setBar('mem-bar',  metrics.memory_percent, 85, 'bg-success', 'bg-warning', 'bg-danger');
  setBar('disk-bar', metrics.disk_percent,   90, 'bg-warning', 'bg-warning', 'bg-danger');

  pushChartPoint(metrics.timestamp, metrics.cpu_percent, metrics.memory_percent);
}

function setBar(id, value, warnAt, ...colors) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.width = value + '%';
  if (colors.length) {
    el.className = el.className.replace(/bg-\S+/g, '').trim();
    el.classList.add(value >= warnAt ? (colors[2] || 'bg-danger') : (colors[0] || 'bg-primary'));
  }
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ── 更新智能体状态 ──
function updateAgents(agents) {
  const el = document.getElementById('agents-list');
  if (!el) return;
  const statusLabel = { online: '就绪', busy: '忙碌', offline: '离线' };
  el.innerHTML = agents.map(a => `
    <div class="agent-item">
      <div class="agent-icon"><i class="${a.icon}"></i></div>
      <div class="flex-grow-1">
        <div class="fw-semibold" style="font-size:.85rem">${a.name}</div>
        <div class="text-muted" style="font-size:.75rem">${a.role}</div>
      </div>
      <span class="badge ${a.status === 'online' ? 'bg-success' : a.status === 'busy' ? 'bg-warning text-dark' : 'bg-secondary'} me-2">${statusLabel[a.status] || a.status}</span>
      <div class="agent-status-dot ${a.status}"></div>
    </div>
  `).join('');
}

// ── 更新告警 ──
function updateAlerts(alerts, count) {
  setText('alerts-count', count);
  const el = document.getElementById('alerts-list');
  if (!el) return;
  if (!alerts.length) {
    el.innerHTML = '<p class="text-muted text-center small py-2 mb-0"><i class="fas fa-check-circle text-success me-1"></i>无告警</p>';
    return;
  }
  el.innerHTML = alerts.map(a =>
    `<div class="alert-item ${a.level}"><i class="fas fa-exclamation-circle me-2"></i>${a.message}</div>`
  ).join('');
}

// ── 更新最近活动 ──
function updateRecentHistory(list) {
  const tbody = document.getElementById('recent-history');
  if (!tbody) return;
  if (!list || list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">暂无记录</td></tr>';
    return;
  }
  tbody.innerHTML = list.map(h => `
    <tr>
      <td>${h.scenario_name}</td>
      <td>${statusBadge(h.status)}</td>
      <td><small class="text-muted">${h.start_time}</small></td>
      <td><small>${h.duration}s</small></td>
    </tr>
  `).join('');
}

// ── 主刷新函数 ──
async function refreshDashboard() {
  try {
    const data = await apiFetch('/api/dashboard');
    updateMetricCards(data.metrics);
    updateAgents(data.agents);
    updateAlerts(data.alerts, data.alert_count);
    updateRecentHistory(data.recent_history);
    setText('tasks-value', data.running_tasks);
  } catch (e) {
    // 错误已由 apiFetch 处理
  }
}

// ── 页面初始化 ──
document.addEventListener('DOMContentLoaded', () => {
  initPerfChart();
  refreshDashboard();
  // 每 5 秒刷新一次（可从设置读取）
  setInterval(refreshDashboard, 5000);
});
