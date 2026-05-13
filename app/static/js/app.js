/* MapSchool — Frontend JS sin dependencias.
   Contiene: API helper, Toast, Dialog, Dropdown, Schedule popover, SSE notifs. */
(() => {
  'use strict';

  // ============== AUTH STORAGE ==============
  const TokenStore = {
    get access() { return localStorage.getItem('mg_access'); },
    set access(v) { v ? localStorage.setItem('mg_access', v) : localStorage.removeItem('mg_access'); },
    get refresh() { return localStorage.getItem('mg_refresh'); },
    set refresh(v) { v ? localStorage.setItem('mg_refresh', v) : localStorage.removeItem('mg_refresh'); },
    clear() { localStorage.removeItem('mg_access'); localStorage.removeItem('mg_refresh'); },
  };

  // ============== API ==============
  async function api(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    const token = TokenStore.access;
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(path, { credentials: 'include', ...opts, headers });

    // Para endpoints que NO son los de auth: si 401, intentamos refresh una vez.
    const isAuthEndpoint = /^\/auth\/(login|web-login|web-logout|web-refresh|refresh|heartbeat)$/.test(path);
    if (res.status === 401 && !opts._retry && !isAuthEndpoint) {
      const refreshed = await tryRefreshTokens();
      if (refreshed) {
        return api(path, { ...opts, _retry: true });
      }
      // Refresh falló: la sesión está muerta. Saca al usuario.
      if (isAuthenticatedPage()) {
        forceLogout('expired');
        // throw para que el caller no procese más; forceLogout ya redirige
        const err = new Error('Sesión expirada');
        err.status = 401; throw err;
      }
    }

    let body = null;
    try { body = await res.json(); } catch (_) { body = null; }
    if (!res.ok) {
      const err = new Error((body && body.error) || res.statusText);
      err.status = res.status; err.body = body; throw err;
    }
    return body;
  }
  window.api = api;
  window.TokenStore = TokenStore;

  // ============== SESSION LIFECYCLE ==============
  const INACTIVITY_MS = 10 * 60 * 1000;          // 10 min sin eventos → logout
  const HEARTBEAT_MS  = 2  * 60 * 1000;          // ping cada 2 min para mantener viva la cookie
  const REFRESH_MS    = 12 * 60 * 1000;          // re-emitir JWT cookies antes de los 15 min de TTL
  let lastActivity = Date.now();
  let logoutInFlight = false;

  function isAuthenticatedPage() {
    return document.body && document.body.dataset.authenticated === 'true';
  }

  function markActivity() { lastActivity = Date.now(); }

  async function tryRefreshTokens() {
    // 1) Intento server-side (cookies httpOnly) — funciona si la sesión Flask
    //    aún vive aunque el access JWT haya expirado.
    try {
      const r = await fetch('/auth/web-refresh', {
        method: 'POST', credentials: 'include',
      });
      if (r.ok) return true;
    } catch (_) { /* fallthrough */ }
    // 2) Bearer + refresh token (Flutter/SPA path)
    if (TokenStore.refresh) {
      try {
        const r = await fetch('/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: TokenStore.refresh }),
        });
        if (r.ok) {
          const j = await r.json();
          TokenStore.access = j.access_token;
          if (j.refresh_token) TokenStore.refresh = j.refresh_token;
          return true;
        }
      } catch (_) { /* fallthrough */ }
    }
    return false;
  }
  window.tryRefreshTokens = tryRefreshTokens;

  function forceLogout(reason = 'expired') {
    if (logoutInFlight) return;
    logoutInFlight = true;
    TokenStore.clear();
    // Cierra el SSE para no spamear reconexiones
    if (window._mgSSE) { try { window._mgSSE.close(); } catch (_) {} window._mgSSE = null; }
    // Mensaje al usuario antes del redirect
    try { toast('Tu sesión expiró', 'warning', 'Vuelve a iniciar sesión para continuar.', 2500); } catch (_) {}
    // Mata sesión Flask + cookies en el server (fire-and-forget)
    fetch('/auth/web-logout', { method: 'POST', credentials: 'include' })
      .catch(() => {})
      .finally(() => {
        const next = encodeURIComponent(location.pathname + location.search);
        setTimeout(() => {
          location.href = `/auth/login?expired=1&reason=${reason}&next=${next}`;
        }, 700);
      });
  }
  window.forceLogout = forceLogout;

  async function heartbeat() {
    if (!isAuthenticatedPage()) return;
    // Si el usuario lleva > INACTIVITY_MS sin interactuar → logout.
    if (Date.now() - lastActivity > INACTIVITY_MS) {
      forceLogout('inactivity');
      return;
    }
    try {
      const r = await fetch('/auth/heartbeat', { credentials: 'include' });
      if (r.status === 401) forceLogout('expired');
    } catch (_) { /* offline: no actuamos */ }
  }

  async function periodicRefresh() {
    if (!isAuthenticatedPage()) return;
    if (Date.now() - lastActivity > INACTIVITY_MS) return; // inactivo: no extiendas
    const ok = await tryRefreshTokens();
    if (!ok) forceLogout('expired');
  }

  function startSessionMonitor() {
    if (!isAuthenticatedPage()) return;
    ['click', 'keydown', 'mousemove', 'scroll', 'touchstart', 'pointerdown']
      .forEach(evt => window.addEventListener(evt, markActivity, { passive: true }));
    setInterval(heartbeat, HEARTBEAT_MS);
    setInterval(periodicRefresh, REFRESH_MS);
    // Primer heartbeat rápido para validar estado al cargar
    setTimeout(heartbeat, 5000);
  }

  // ============== TOAST ==============
  function toast(title, variant = 'info', body = '', duration = 6000) {
    const wrap = document.getElementById('toast-container');
    if (!wrap) return;
    const el = document.createElement('div');
    el.className = `toast toast--${variant}`;
    el.innerHTML = `
      <div class="toast__title">${escapeHtml(title)}</div>
      ${body ? `<div class="toast__body">${escapeHtml(body)}</div>` : ''}
      <div class="toast__progress" style="animation-duration:${duration}ms"></div>
    `;
    wrap.appendChild(el);
    setTimeout(() => el.remove(), duration);
  }
  window.toast = toast;

  function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, m => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[m]));
  }

  // ============== DIALOG ==============
  document.addEventListener('click', e => {
    const open = e.target.closest('[data-dialog-open]');
    if (open) {
      e.preventDefault();
      const id = open.getAttribute('data-dialog-open');
      const dlg = document.getElementById(id);
      if (dlg) dlg.classList.add('open');
      return;
    }
    const close = e.target.closest('[data-dialog-close]') ||
                  (e.target.classList.contains('dialog-backdrop') ? e.target : null);
    if (close) {
      const dlg = close.closest('.dialog-backdrop') || close;
      if (dlg.classList.contains('dialog-backdrop')) dlg.classList.remove('open');
    }
    const dismiss = e.target.closest('[data-action="dismiss-alert"]');
    if (dismiss) dismiss.closest('.alert').remove();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.dialog-backdrop.open').forEach(d => d.classList.remove('open'));
    }
  });

  // ============== DROPDOWN ==============
  document.addEventListener('click', e => {
    const trig = e.target.closest('[data-dropdown-trigger]');
    if (trig) {
      e.preventDefault();
      const dd = trig.closest('[data-dropdown]');
      if (dd) {
        const wasOpen = dd.classList.contains('open');
        document.querySelectorAll('[data-dropdown].open').forEach(x => {
          x.classList.remove('open');
          x.querySelector('[data-dropdown-trigger]')?.setAttribute('aria-expanded', 'false');
        });
        if (!wasOpen) {
          dd.classList.add('open');
          trig.setAttribute('aria-expanded', 'true');
        }
      }
      return;
    }
    if (!e.target.closest('[data-dropdown]')) {
      document.querySelectorAll('[data-dropdown].open').forEach(x => {
        x.classList.remove('open');
        x.querySelector('[data-dropdown-trigger]')?.setAttribute('aria-expanded', 'false');
      });
    }
  });

  // ============== SCHEDULE BLOCK POPOVER ==============
  let activePopover = null;
  document.addEventListener('click', e => {
    const bloque = e.target.closest('.bloque');
    if (bloque) {
      e.preventDefault();
      e.stopPropagation();
      if (activePopover) activePopover.remove();
      const pop = document.createElement('div');
      pop.className = 'popover';
      const isConflicto = bloque.classList.contains('bloque--conflicto');
      pop.innerHTML = `
        <div class="popover__title">${escapeHtml(bloque.dataset.materia)}</div>
        <div class="popover__row">🕐 ${escapeHtml(bloque.dataset.hora)}</div>
        <div class="popover__row">📍 ${escapeHtml(bloque.dataset.salon)}</div>
        <div class="popover__row">👤 ${escapeHtml(bloque.dataset.profesor)}</div>
        ${isConflicto ? '<div class="popover__row" style="color: var(--danger); font-weight: 700;">⚠ Conflicto · revisa tu agenda</div>' : ''}
      `;
      document.body.appendChild(pop);
      const r = bloque.getBoundingClientRect();
      pop.style.position = 'fixed';
      pop.style.left = Math.min(r.right + 8, window.innerWidth - 260) + 'px';
      pop.style.top = Math.max(r.top, 80) + 'px';
      activePopover = pop;
      return;
    }
    if (activePopover && !e.target.closest('.popover')) {
      activePopover.remove(); activePopover = null;
    }
  });

  // ============== NOTIFICATIONS PANEL + SSE ==============
  function initNotifs() {
    const bell = document.getElementById('bell-btn');
    const panel = document.getElementById('notif-panel');
    if (!bell || !panel) return;
    bell.addEventListener('click', () => {
      const open = panel.classList.toggle('open');
      bell.setAttribute('aria-expanded', open ? 'true' : 'false');
      panel.setAttribute('aria-hidden', open ? 'false' : 'true');
      if (open) {
        loadNotifs();
        // Mover foco al panel para keyboard nav
        panel.querySelector('[data-action="close-notif-panel"]')?.focus();
      } else {
        bell.focus();
      }
    });
    document.querySelector('[data-action="close-notif-panel"]')?.addEventListener('click', () => {
      panel.classList.remove('open');
      bell.setAttribute('aria-expanded', 'false');
      panel.setAttribute('aria-hidden', 'true');
      bell.focus();
    });
    // Cerrar con Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && panel.classList.contains('open')) {
        panel.classList.remove('open');
        bell.setAttribute('aria-expanded', 'false');
        panel.setAttribute('aria-hidden', 'true');
        bell.focus();
      }
    });
    document.querySelector('[data-action="mark-all-read"]')?.addEventListener('click', async () => {
      try { await api('/api/v1/notificaciones/leer-todas', { method: 'POST' }); loadNotifs(); updateBadge(); }
      catch (e) { toast('No se pudieron marcar como leídas', 'danger'); }
    });
    updateBadge();
    setInterval(updateBadge, 30000);
    startSSE();
  }

  async function updateBadge() {
    if (!TokenStore.access) return;
    try {
      const r = await api('/api/v1/notificaciones?leida=false&per_page=1');
      const badge = document.getElementById('bell-badge');
      if (!badge) return;
      if (r.no_leidas > 0) {
        badge.textContent = r.no_leidas > 99 ? '99+' : r.no_leidas;
        badge.style.display = 'inline-flex';
      } else { badge.style.display = 'none'; }
    } catch (_) { /* silent */ }
  }

  async function loadNotifs() {
    const list = document.getElementById('notif-list');
    if (!list) return;
    try {
      const r = await api('/api/v1/notificaciones?per_page=20');
      if (!r.data.length) {
        list.innerHTML = '<div class="empty"><div class="empty__icon">🔔</div><div class="empty__title">Sin notificaciones</div></div>';
        return;
      }
      list.innerHTML = r.data.map(n => `
        <div class="card mb-3" style="padding: var(--s-3); ${n.leida ? 'opacity: 0.6;' : ''}">
          <div style="display:flex; justify-content: space-between; gap: var(--s-2);">
            <strong>${escapeHtml(n.titulo)}</strong>
            ${!n.leida ? '<span class="dot dot--danger"></span>' : ''}
          </div>
          ${n.cuerpo ? `<div class="b-12 mt-2 text-muted">${escapeHtml(n.cuerpo)}</div>` : ''}
          <div class="b-12 mt-2 text-soft">${formatTime(n.created_at)}</div>
          ${n.accion_url ? `<a class="b-12" href="${n.accion_url}">Abrir →</a>` : ''}
        </div>`).join('');
    } catch (e) {
      list.innerHTML = '<div class="empty"><div class="empty__title">No se pudieron cargar</div></div>';
    }
  }

  function formatTime(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const diffMin = Math.floor((Date.now() - d) / 60000);
    if (diffMin < 1) return 'Hace un momento';
    if (diffMin < 60) return `Hace ${diffMin} min`;
    if (diffMin < 1440) return `Hace ${Math.floor(diffMin / 60)} h`;
    return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
  }

  function startSSE() {
    if (!TokenStore.access) return;
    if (window._mgSSE) return;
    const src = new EventSource(`/api/v1/notificaciones/stream?token=${encodeURIComponent(TokenStore.access)}`);
    window._mgSSE = src;
    src.onmessage = e => {
      try {
        const n = JSON.parse(e.data);
        toast(n.titulo, mapVariant(n.tipo), n.cuerpo || '');
        updateBadge();
      } catch (_) {}
    };
    src.onerror = () => { src.close(); window._mgSSE = null; setTimeout(startSSE, 30000); };
  }

  function mapVariant(tipo) {
    return ({
      conflicto: 'warning', tramite: 'warning',
      calificacion: 'info', anuncio: 'info',
      horario: 'success', sistema: 'info',
    })[tipo] || 'info';
  }

  // ============== INIT ==============
  document.addEventListener('DOMContentLoaded', () => {
    initNotifs();
    initFormValidation();
    startSessionMonitor();
  });

  // ============== INLINE FORM VALIDATION ==============
  function initFormValidation() {
    document.querySelectorAll('[data-validate]').forEach(input => {
      input.addEventListener('blur', () => validateField(input));
      input.addEventListener('input', () => {
        const field = input.closest('.field');
        if (field) field.classList.remove('field--has-error');
      });
    });
  }
  function validateField(input) {
    const field = input.closest('.field');
    if (!field) return true;
    const rules = (input.dataset.validate || '').split(' ');
    const v = input.value.trim();
    let err = '';
    if (rules.includes('required') && !v) err = 'Este campo es obligatorio';
    else if (rules.includes('email') && v && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v))
      err = 'Correo inválido';
    else if (rules.includes('min8') && v.length < 8)
      err = 'Mínimo 8 caracteres';
    if (err) {
      field.classList.add('field--has-error');
      const e = field.querySelector('.field__error');
      if (e) e.textContent = err;
      return false;
    }
    field.classList.remove('field--has-error');
    return true;
  }
  window.validateField = validateField;
})();
