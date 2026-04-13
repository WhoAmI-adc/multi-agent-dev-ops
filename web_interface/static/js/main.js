/**
 * main.js — 通用工具函数与 WebSocket 初始化
 */

// ── WebSocket 连接 ──
let socket = null;

function initSocket() {
  socket = io({ transports: ['websocket', 'polling'] });

  socket.on('connect', () => {
    updateWsStatus(true);
    console.log('WebSocket 已连接:', socket.id);
  });

  socket.on('disconnect', () => {
    updateWsStatus(false);
    console.warn('WebSocket 已断开');
  });

  // 将 new_log 事件暴露给各页面（由各页面监听）
  return socket;
}

function updateWsStatus(online) {
  const el = document.getElementById('ws-status');
  if (!el) return;
  el.className = online ? 'badge bg-success me-1' : 'badge bg-danger me-1';
  el.innerHTML = `<i class="fas fa-circle me-1" style="font-size:.6rem"></i>${online ? '在线' : '离线'}`;
}

// ── Toast 通知 ──
function showToast(message, type = 'info') {
  const toast = document.getElementById('globalToast');
  const msgEl = document.getElementById('toastMessage');
  if (!toast || !msgEl) return;

  msgEl.textContent = message;
  // 重置颜色类
  toast.className = toast.className.replace(/bg-\S+/g, '').trim();
  const colorMap = { success: 'bg-success', danger: 'bg-danger', warning: 'bg-warning', info: 'bg-primary' };
  toast.classList.add('text-white', colorMap[type] || 'bg-primary');

  bootstrap.Toast.getOrCreateInstance(toast, { delay: 3000 }).show();
}

// ── 通用 Fetch 封装 ──
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('API 请求失败:', url, err);
    showToast(`请求失败: ${err.message}`, 'danger');
    throw err;
  }
}

// ── 格式化时间 ──
function formatDuration(seconds) {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

// ── 状态徽章 HTML ──
function statusBadge(status) {
  const map = {
    success: ['bg-success', '成功'],
    failed:  ['bg-danger',  '失败'],
    running: ['bg-primary progress-bar-animated', '运行中'],
  };
  const [cls, text] = map[status] || ['bg-secondary', status];
  return `<span class="badge ${cls}">${text}</span>`;
}

// ── 页面加载完成后初始化 WebSocket ──
document.addEventListener('DOMContentLoaded', () => {
  window._socket = initSocket();
});
