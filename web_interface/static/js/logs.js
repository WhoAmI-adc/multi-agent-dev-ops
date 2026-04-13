/**
 * logs.js — 实时日志流、过滤与导出
 */

let allLogs = [];        // 所有接收到的日志
let currentLevel = 'ALL'; // 当前级别过滤
let autoScroll = true;

// ── 颜色映射 ──
const LEVEL_COLORS = {
  INFO:    { text: '#64b5f6', label: 'bg-info'    },
  WARNING: { text: '#ffcc02', label: 'bg-warning text-dark' },
  ERROR:   { text: '#ef9a9a', label: 'bg-danger'  },
  DEBUG:   { text: '#b0bec5', label: 'bg-secondary'},
};

// ── 渲染单条日志 ──
function renderLogLine(entry) {
  const color = (LEVEL_COLORS[entry.level] || LEVEL_COLORS.INFO).text;
  const search = document.getElementById('log-search')?.value.toLowerCase() || '';
  let msg = escapeHtml(entry.message);
  if (search) {
    const re = new RegExp(escapeRegex(search), 'gi');
    msg = msg.replace(re, m => `<mark style="background:#ffe082;color:#000">${m}</mark>`);
  }
  return `<div class="log-line mb-0">` +
    `<span style="color:#78909c">${entry.timestamp}</span> ` +
    `<span class="badge ${(LEVEL_COLORS[entry.level] || LEVEL_COLORS.INFO).label}" style="font-size:.65rem">${entry.level}</span> ` +
    `<span style="color:#80cbc4">[${entry.source}]</span> ` +
    `<span style="color:${color}">${msg}</span>` +
    `</div>`;
}

// ── 刷新终端显示 ──
function renderTerminal() {
  const terminal = document.getElementById('log-terminal');
  if (!terminal) return;

  const search = document.getElementById('log-search')?.value.toLowerCase() || '';
  const filtered = allLogs.filter(e =>
    (currentLevel === 'ALL' || e.level === currentLevel) &&
    (!search || e.message.toLowerCase().includes(search) || e.source.toLowerCase().includes(search))
  );

  terminal.innerHTML = filtered.length
    ? filtered.map(renderLogLine).join('')
    : '<span class="text-muted">暂无匹配的日志</span>';

  const countEl = document.getElementById('log-count');
  if (countEl) countEl.textContent = filtered.length;

  if (autoScroll) terminal.scrollTop = terminal.scrollHeight;
}

// ── 过滤按钮点击 ──
function filterLogs(btn) {
  document.querySelectorAll('[data-level]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentLevel = btn.dataset.level;
  renderTerminal();
}

// ── 搜索框输入 ──
function applyLogFilters() {
  renderTerminal();
}

// ── 清空日志 ──
function clearLogs() {
  allLogs = [];
  renderTerminal();
  showToast('日志已清空', 'info');
}

// ── 导出日志 ──
function exportLogs() {
  const search = document.getElementById('log-search')?.value.toLowerCase() || '';
  const filtered = allLogs.filter(e =>
    (currentLevel === 'ALL' || e.level === currentLevel) &&
    (!search || e.message.toLowerCase().includes(search) || e.source.toLowerCase().includes(search))
  );
  const text = filtered.map(e => `[${e.timestamp}] [${e.level}] [${e.source}] ${e.message}`).join('\n');
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `devops_logs_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.txt`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('日志已导出', 'success');
}

// ── 工具函数 ──
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ── 页面初始化 ──
document.addEventListener('DOMContentLoaded', () => {
  // 自动滚动开关
  const scrollCheck = document.getElementById('auto-scroll');
  if (scrollCheck) scrollCheck.addEventListener('change', e => { autoScroll = e.target.checked; });

  // 初始加载历史日志
  apiFetch('/api/logs?limit=200').then(data => {
    allLogs = data.logs || [];
    renderTerminal();
  }).catch(() => {});

  // 等待 WebSocket 就绪
  setTimeout(() => {
    const sock = window._socket;
    if (!sock) return;

    const wsStatus = document.getElementById('log-ws-status');

    sock.on('connect', () => {
      if (wsStatus) { wsStatus.textContent = '已连接'; wsStatus.className = 'text-success'; }
    });
    sock.on('disconnect', () => {
      if (wsStatus) { wsStatus.textContent = '已断开'; wsStatus.className = 'text-danger'; }
    });

    // 接收历史日志（连接时服务端主动推送）
    sock.on('log_history', data => {
      allLogs = data.logs || [];
      renderTerminal();
    });

    // 实时新日志
    sock.on('new_log', entry => {
      allLogs.push(entry);
      if (allLogs.length > 1000) allLogs.shift();
      renderTerminal();
    });
  }, 500);
});
