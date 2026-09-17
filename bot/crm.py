import json
from aiohttp import web
from bot.database import Database

CRM_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Miwa CRM • Fans & Ventes</title>
  <style>
    :root {
      --bg: #0d0f14;
      --card-bg: #161a23;
      --card-border: #232936;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --primary: #8b5cf6;
      --primary-hover: #7c3aed;
      --gold: #f59e0b;
      --green: #10b981;
      --red: #ef4444;
      --blue: #3b82f6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; padding: 24px 16px; }
    .container { max-width: 1200px; margin: 0 auto; }
    
    /* Header */
    .header { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 24px; }
    .header h1 { font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
    .header .subtitle { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
    .header-stats { display: flex; gap: 12px; }
    .stat-pill { background: var(--card-bg); border: 1px solid var(--card-border); padding: 8px 16px; border-radius: 12px; font-size: 13px; display: flex; align-items: center; gap: 8px; }
    .stat-pill strong { color: var(--gold); font-size: 16px; }

    /* Control Bar */
    .controls { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; align-items: center; justify-content: space-between; }
    .search-box { position: relative; flex: 1; min-width: 250px; max-width: 400px; }
    .search-box input { width: 100%; background: var(--card-bg); border: 1px solid var(--card-border); color: var(--text); padding: 10px 14px 10px 36px; border-radius: 10px; font-size: 14px; outline: none; transition: 0.2s; }
    .search-box input:focus { border-color: var(--primary); }
    .search-box svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); width: 16px; height: 16px; fill: var(--text-muted); }

    .tag-filters { display: flex; flex-wrap: wrap; gap: 8px; }
    .filter-btn { background: var(--card-bg); border: 1px solid var(--card-border); color: var(--text-muted); padding: 7px 14px; border-radius: 20px; font-size: 13px; cursor: pointer; transition: 0.2s; }
    .filter-btn:hover, .filter-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

    /* Table */
    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th { padding: 14px 18px; color: var(--text-muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--card-border); background: rgba(0,0,0,0.2); }
    td { padding: 14px 18px; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 14px; vertical-align: middle; }
    tr.fan-row { cursor: context-menu; transition: background 0.15s; }
    tr.fan-row:hover { background: rgba(139, 92, 246, 0.07); }

    .fan-info { display: flex; align-items: center; gap: 12px; }
    .avatar { width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #ec4899); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px; color: white; flex-shrink: 0; }
    .fan-name { font-weight: 600; color: var(--text); }
    .fan-username { font-size: 12px; color: var(--text-muted); }
    .fan-username a { color: var(--primary); text-decoration: none; }
    .fan-username a:hover { text-decoration: underline; }

    /* Badges */
    .tag-badge { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; cursor: pointer; }
    .tag-VIP { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .tag-Acheteur { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .tag-Chaud { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .tag-Relance { background: rgba(234, 179, 8, 0.15); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.3); }
    .tag-Curieux { background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }
    .tag-Nouveau { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

    .stars-badge { color: var(--gold); font-weight: 700; display: inline-flex; align-items: center; gap: 4px; }
    .seniority { font-size: 13px; color: var(--text); }
    .seniority-sub { font-size: 11px; color: var(--text-muted); }

    .btn-action { background: rgba(255,255,255,0.06); border: 1px solid var(--card-border); color: var(--text); padding: 6px 12px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: 0.2s; }
    .btn-action:hover { background: var(--primary); color: white; }

    /* Custom Right-Click Context Menu */
    .context-menu {
      position: absolute;
      background: #1e2430;
      border: 1px solid #2f3747;
      border-radius: 10px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.6);
      width: 220px;
      z-index: 1000;
      display: none;
      overflow: hidden;
      padding: 6px 0;
    }
    .context-item {
      padding: 9px 16px;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      color: var(--text);
      transition: background 0.15s;
    }
    .context-item:hover { background: var(--primary); color: white; }
    .context-divider { height: 1px; background: #2f3747; margin: 4px 0; }
    .context-header { padding: 6px 16px; font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; }

    /* Modal */
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.75); backdrop-filter: blur(4px); z-index: 2000; display: none; align-items: center; justify-content: center; padding: 16px; }
    .modal { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; width: 100%; max-width: 540px; max-height: 90vh; overflow-y: auto; padding: 24px; position: relative; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
    .modal-close { position: absolute; top: 18px; right: 18px; background: none; border: none; color: var(--text-muted); font-size: 24px; cursor: pointer; }
    .modal-close:hover { color: white; }

    .modal-fan-head { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border); }
    .modal-avatar { width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #ec4899); display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; color: white; }

    .highlight-card { background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(59, 130, 246, 0.1)); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 16px; margin-bottom: 20px; }
    .highlight-title { font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--primary); font-weight: 700; margin-bottom: 6px; }
    .highlight-main { font-size: 18px; font-weight: 700; color: white; margin-bottom: 4px; }
    .highlight-sub { font-size: 13px; color: var(--text-muted); }

    .modal-section { margin-bottom: 20px; }
    .modal-section h4 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 10px; }

    .tag-selector { display: flex; flex-wrap: wrap; gap: 8px; }
    .tag-opt { padding: 6px 12px; border-radius: 8px; font-size: 12px; cursor: pointer; border: 1px solid var(--card-border); background: rgba(255,255,255,0.04); transition: 0.2s; }
    .tag-opt.selected { border-color: var(--primary); background: var(--primary); color: white; }

    textarea.notes-input { width: 100%; background: #0f1219; border: 1px solid var(--card-border); border-radius: 10px; padding: 12px; color: white; font-size: 13px; resize: vertical; min-height: 80px; outline: none; margin-bottom: 8px; }
    textarea.notes-input:focus { border-color: var(--primary); }

    .purchases-list { max-height: 160px; overflow-y: auto; border: 1px solid var(--card-border); border-radius: 10px; padding: 8px; }
    .purchase-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 13px; }
    .purchase-item:last-child { border-bottom: none; }

    .toast { position: fixed; bottom: 20px; right: 20px; background: var(--primary); color: white; padding: 12px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 3000; display: none; }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <div>
        <h1>👑 Miwa CRM • Gestion des Fans</h1>
        <div class="subtitle">Triez vos fans par étiquette • <strong>Clic droit sur un fan</strong> pour voir son ancienneté & infos</div>
      </div>
      <div class="header-stats">
        <div class="stat-pill">👥 Total fans : <strong id="stat-total">0</strong></div>
        <div class="stat-pill">⭐ Étoiles encaissées : <strong id="stat-stars">0</strong></div>
      </div>
    </div>

    <!-- Controls -->
    <div class="controls">
      <div class="search-box">
        <svg viewBox="0 0 24 24"><path d="M10 2a8 8 0 015.293 14.707l4.5 4.5a1 1 0 01-1.414 1.414l-4.5-4.5A8 8 0 1110 2zm0 2a6 6 0 100 12 6 6 0 000-12z"/></svg>
        <input type="text" id="search-input" placeholder="Rechercher par pseudo, prénom ou ID Telegram..." oninput="filterFans()">
      </div>
      <div class="tag-filters">
        <button class="filter-btn active" data-tag="all" onclick="setFilter('all', this)">Tous (<span id="count-all">0</span>)</button>
        <button class="filter-btn" data-tag="VIP" onclick="setFilter('VIP', this)">👑 VIP (<span id="count-VIP">0</span>)</button>
        <button class="filter-btn" data-tag="Acheteur" onclick="setFilter('Acheteur', this)">💰 Acheteur (<span id="count-Acheteur">0</span>)</button>
        <button class="filter-btn" data-tag="Chaud" onclick="setFilter('Chaud', this)">🔥 Chaud (<span id="count-Chaud">0</span>)</button>
        <button class="filter-btn" data-tag="Relance" onclick="setFilter('Relance', this)">⏳ À relancer (<span id="count-Relance">0</span>)</button>
        <button class="filter-btn" data-tag="Curieux" onclick="setFilter('Curieux', this)">👀 Curieux (<span id="count-Curieux">0</span>)</button>
        <button class="filter-btn" data-tag="Nouveau" onclick="setFilter('Nouveau', this)">🆕 Nouveau (<span id="count-Nouveau">0</span>)</button>
      </div>
    </div>

    <!-- Table -->
    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Fan / Client</th>
            <th>ID Telegram</th>
            <th>Étiquette</th>
            <th>Ancienneté (Depuis quand ?)</th>
            <th>Dépenses ⭐</th>
            <th>Achats</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="fans-tbody">
          <tr><td colspan="7" style="text-align:center; padding: 40px; color: var(--text-muted);">Chargement des fans...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Custom Right Click Context Menu -->
  <div class="context-menu" id="context-menu">
    <div class="context-header" id="context-fan-name">Options du fan</div>
    <div class="context-item" onclick="openFanModalFromContext()">
      <span>ℹ️</span> <strong>Voir les infos détaillées</strong>
    </div>
    <div class="context-item" onclick="openTelegramChat()">
      <span>💬</span> Ouvrir chat Telegram
    </div>
    <div class="context-item" onclick="copyFanId()">
      <span>📋</span> Copier l'ID
    </div>
    <div class="context-divider"></div>
    <div class="context-header">Changer l'étiquette</div>
    <div class="context-item" onclick="setFanTagFromContext('VIP')">👑 Mettre en VIP</div>
    <div class="context-item" onclick="setFanTagFromContext('Acheteur')">💰 Mettre en Acheteur</div>
    <div class="context-item" onclick="setFanTagFromContext('Chaud')">🔥 Mettre en Chaud</div>
    <div class="context-item" onclick="setFanTagFromContext('Relance')">⏳ Mettre en À relancer</div>
    <div class="context-item" onclick="setFanTagFromContext('Curieux')">👀 Mettre en Curieux</div>
  </div>

  <!-- Modal Fiche Détaillée -->
  <div class="modal-overlay" id="fan-modal" onclick="closeModal(event)">
    <div class="modal" onclick="event.stopPropagation()">
      <button class="modal-close" onclick="closeModalDirect()">&times;</button>
      
      <div class="modal-fan-head">
        <div class="modal-avatar" id="m-avatar">M</div>
        <div>
          <h2 id="m-name" style="font-size: 20px;">Nom du Fan</h2>
          <div id="m-username" style="color: var(--primary); font-size: 14px;">@username</div>
          <div id="m-id" style="color: var(--text-muted); font-size: 12px; margin-top: 2px;">ID: 123456789</div>
        </div>
      </div>

      <!-- Ancienneté Card -->
      <div class="highlight-card">
        <div class="highlight-title">⏳ Ancienneté & Présence</div>
        <div class="highlight-main" id="m-seniority">Présent depuis 9 jours</div>
        <div class="highlight-sub" id="m-joined-date">Arrivé le 8 septembre 2026 à 20:03</div>
      </div>

      <!-- Étiquette Selector -->
      <div class="modal-section">
        <h4>Étiquette du fan</h4>
        <div class="tag-selector" id="m-tag-selector">
          <div class="tag-opt" data-tag="VIP" onclick="selectModalTag('VIP')">👑 VIP</div>
          <div class="tag-opt" data-tag="Acheteur" onclick="selectModalTag('Acheteur')">💰 Acheteur</div>
          <div class="tag-opt" data-tag="Chaud" onclick="selectModalTag('Chaud')">🔥 Chaud</div>
          <div class="tag-opt" data-tag="Relance" onclick="selectModalTag('Relance')">⏳ À relancer</div>
          <div class="tag-opt" data-tag="Curieux" onclick="selectModalTag('Curieux')">👀 Curieux</div>
          <div class="tag-opt" data-tag="Nouveau" onclick="selectModalTag('Nouveau')">🆕 Nouveau</div>
        </div>
      </div>

      <!-- Purchases History -->
      <div class="modal-section">
        <h4>Historique des achats (<span id="m-purchases-count">0</span>) • <span style="color: var(--gold);" id="m-total-stars">0 ⭐</span></h4>
        <div class="purchases-list" id="m-purchases-list">
          <div style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 12px;">Aucun média acheté pour le moment.</div>
        </div>
      </div>

      <!-- Notes internes pour le chatter -->
      <div class="modal-section">
        <h4>Notes internes pour les chatteurs</h4>
        <textarea class="notes-input" id="m-notes" placeholder="Ex: Aime les photos en robe, paie rapidement, étudiant..."></textarea>
        <button class="btn-action" style="background: var(--primary); color: white; width: 100%; padding: 10px;" onclick="saveFanNotes()">💾 Enregistrer la note</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast">Notification</div>

  <script>
    let allFans = [];
    let currentFilter = 'all';
    let selectedFanId = null;

    async function loadFans() {
      try {
        const res = await fetch('/api/fans');
        allFans = await res.json();
        updateStats();
        renderTable();
      } catch (e) {
        console.error("Erreur chargement fans", e);
      }
    }

    function calculateSeniority(joinedAtStr) {
      if (!joinedAtStr) return { main: "Date inconnue", sub: "" };
      const joinedDate = new Date(joinedAtStr.replace(' ', 'T'));
      const now = new Date();
      const diffMs = now - joinedDate;
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

      let main = "";
      if (diffDays <= 0) {
        main = diffHours <= 1 ? "Arrivé il y a moins d'1h" : `Arrivé il y a ${diffHours}h (Aujourd'hui)`;
      } else if (diffDays === 1) {
        main = "Présent depuis hier (1 jour)";
      } else {
        main = `Présent depuis ${diffDays} jours`;
      }

      const options = { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' };
      const sub = `Premier contact : ${joinedDate.toLocaleDateString('fr-FR', options)}`;
      return { main, sub, days: diffDays };
    }

    function updateStats() {
      let totalStars = 0;
      const counts = { all: allFans.length, VIP: 0, Acheteur: 0, Chaud: 0, Relance: 0, Curieux: 0, Nouveau: 0 };

      allFans.forEach(f => {
        totalStars += f.total_stars || 0;
        const tag = f.tag || 'Nouveau';
        if (counts[tag] !== undefined) counts[tag]++;
        else counts.Nouveau++;
      });

      document.getElementById('stat-total').textContent = allFans.length;
      document.getElementById('stat-stars').textContent = totalStars.toLocaleString('fr-FR');

      for (let k in counts) {
        const el = document.getElementById('count-' + k);
        if (el) el.textContent = counts[k];
      }
    }

    function renderTable() {
      const tbody = document.getElementById('fans-tbody');
      const search = document.getElementById('search-input').value.toLowerCase().trim();

      const filtered = allFans.filter(f => {
        if (currentFilter !== 'all' && (f.tag || 'Nouveau') !== currentFilter) return false;
        if (search) {
          const name = (f.first_name || '').toLowerCase();
          const user = (f.username || '').toLowerCase();
          const id = String(f.user_id);
          return name.includes(search) || user.includes(search) || id.includes(search);
        }
        return true;
      });

      if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 40px; color: var(--text-muted);">Aucun fan ne correspond aux critères.</td></tr>`;
        return;
      }

      tbody.innerHTML = filtered.map(f => {
        const seniority = calculateSeniority(f.joined_at);
        const tag = f.tag || 'Nouveau';
        const initial = (f.first_name || f.username || '?')[0].toUpperCase();
        const userDisplay = f.username ? `@${f.username}` : `(Pas de pseudo)`;
        const link = f.username ? `https://t.me/${f.username}` : `tg://user?id=${f.user_id}`;

        return `
          <tr class="fan-row" data-id="${f.user_id}" oncontextmenu="handleContextMenu(event, ${f.user_id})" onclick="openFanModal(${f.user_id})">
            <td>
              <div class="fan-info">
                <div class="avatar">${initial}</div>
                <div>
                  <div class="fan-name">${f.first_name || 'Fan Telegram'}</div>
                  <div class="fan-username"><a href="${link}" target="_blank" onclick="event.stopPropagation()">${userDisplay}</a></div>
                </div>
              </div>
            </td>
            <td><code style="color:var(--text-muted); cursor:pointer;" title="Cliquer pour copier" onclick="event.stopPropagation(); navigator.clipboard.writeText('${f.user_id}'); showToast('ID copié !');">${f.user_id}</code></td>
            <td>
              <span class="tag-badge tag-${tag}" onclick="event.stopPropagation(); cycleTag(${f.user_id})">${getTagIcon(tag)} ${tag}</span>
            </td>
            <td>
              <div class="seniority">⏳ ${seniority.main}</div>
              <div class="seniority-sub">${seniority.sub}</div>
            </td>
            <td><span class="stars-badge">⭐ ${f.total_stars || 0}</span></td>
            <td><strong>${f.purchases_count || 0}</strong></td>
            <td>
              <button class="btn-action" onclick="event.stopPropagation(); openFanModal(${f.user_id})">ℹ️ Fiche</button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function getTagIcon(tag) {
      switch(tag) {
        case 'VIP': return '👑';
        case 'Acheteur': return '💰';
        case 'Chaud': return '🔥';
        case 'Relance': return '⏳';
        case 'Curieux': return '👀';
        default: return '🆕';
      }
    }

    function setFilter(tag, btn) {
      currentFilter = tag;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderTable();
    }

    function filterFans() {
      renderTable();
    }

    /* Right-Click Context Menu Logic */
    const contextMenu = document.getElementById('context-menu');

    function handleContextMenu(e, userId) {
      e.preventDefault();
      selectedFanId = userId;
      const fan = allFans.find(f => f.user_id === userId);
      if (fan) {
        document.getElementById('context-fan-name').textContent = fan.first_name || fan.username || `Fan ${fan.user_id}`;
      }

      contextMenu.style.display = 'block';
      let x = e.pageX;
      let y = e.pageY;
      if (x + 230 > window.innerWidth) x = window.innerWidth - 240;
      contextMenu.style.left = x + 'px';
      contextMenu.style.top = y + 'px';
    }

    document.addEventListener('click', () => {
      contextMenu.style.display = 'none';
    });

    async function setFanTag(userId, newTag) {
      const res = await fetch(`/api/fans/${userId}/tag`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tag: newTag })
      });
      if (res.ok) {
        const f = allFans.find(x => x.user_id === userId);
        if (f) f.tag = newTag;
        updateStats();
        renderTable();
        showToast(`Étiquette changée en ${getTagIcon(newTag)} ${newTag}`);
      }
    }

    function setFanTagFromContext(newTag) {
      if (selectedFanId) setFanTag(selectedFanId, newTag);
      contextMenu.style.display = 'none';
    }

    function cycleTag(userId) {
      const order = ['VIP', 'Acheteur', 'Chaud', 'Relance', 'Curieux', 'Nouveau'];
      const f = allFans.find(x => x.user_id === userId);
      const current = f ? (f.tag || 'Nouveau') : 'Nouveau';
      const next = order[(order.indexOf(current) + 1) % order.length];
      setFanTag(userId, next);
    }

    function openTelegramChat() {
      if (!selectedFanId) return;
      const f = allFans.find(x => x.user_id === selectedFanId);
      if (f && f.username) {
        window.open(`https://t.me/${f.username}`, '_blank');
      } else {
        window.open(`tg://user?id=${selectedFanId}`, '_blank');
      }
      contextMenu.style.display = 'none';
    }

    function copyFanId() {
      if (selectedFanId) {
        navigator.clipboard.writeText(String(selectedFanId));
        showToast('ID Telegram copié !');
      }
      contextMenu.style.display = 'none';
    }

    function openFanModalFromContext() {
      contextMenu.style.display = 'none';
      if (selectedFanId) openFanModal(selectedFanId);
    }

    /* Modal Logic */
    async function openFanModal(userId) {
      selectedFanId = userId;
      const res = await fetch(`/api/fans/${userId}`);
      if (!res.ok) return;
      const fan = await res.json();

      document.getElementById('m-avatar').textContent = (fan.first_name || fan.username || '?')[0].toUpperCase();
      document.getElementById('m-name').textContent = fan.first_name || 'Fan Telegram';
      document.getElementById('m-username').textContent = fan.username ? `@${fan.username}` : '(Pas de pseudo)';
      document.getElementById('m-id').textContent = `ID Telegram : ${fan.user_id}`;

      const seniority = calculateSeniority(fan.joined_at);
      document.getElementById('m-seniority').textContent = seniority.main;
      document.getElementById('m-joined-date').textContent = seniority.sub;

      // Tag selector
      const curTag = fan.tag || 'Nouveau';
      document.querySelectorAll('#m-tag-selector .tag-opt').forEach(opt => {
        opt.classList.toggle('selected', opt.dataset.tag === curTag);
      });

      // Purchases
      document.getElementById('m-purchases-count').textContent = fan.purchases ? fan.purchases.length : 0;
      document.getElementById('m-total-stars').textContent = `${fan.total_stars || 0} ⭐`;

      const pList = document.getElementById('m-purchases-list');
      if (fan.purchases && fan.purchases.length > 0) {
        pList.innerHTML = fan.purchases.map(p => `
          <div class="purchase-item">
            <div><strong>📸 ${p.title}</strong><div style="font-size:11px;color:var(--text-muted);">${p.purchased_at}</div></div>
            <div style="color:var(--gold);font-weight:700;">${p.star_count} ⭐</div>
          </div>
        `).join('');
      } else {
        pList.innerHTML = `<div style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 12px;">Aucun média débloqué pour l'instant.</div>`;
      }

      // Notes
      document.getElementById('m-notes').value = fan.notes || '';

      document.getElementById('fan-modal').style.display = 'flex';
    }

    function selectModalTag(tag) {
      if (!selectedFanId) return;
      setFanTag(selectedFanId, tag);
      document.querySelectorAll('#m-tag-selector .tag-opt').forEach(opt => {
        opt.classList.toggle('selected', opt.dataset.tag === tag);
      });
    }

    async function saveFanNotes() {
      if (!selectedFanId) return;
      const notes = document.getElementById('m-notes').value;
      const res = await fetch(`/api/fans/${selectedFanId}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes })
      });
      if (res.ok) {
        const f = allFans.find(x => x.user_id === selectedFanId);
        if (f) f.notes = notes;
        showToast('Notes enregistrées !');
      }
    }

    function closeModalDirect() {
      document.getElementById('fan-modal').style.display = 'none';
    }
    function closeModal(e) {
      if (e.target.id === 'fan-modal') closeModalDirect();
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 2200);
    }

    // Init
    loadFans();
  </script>
</body>
</html>
"""

def setup_crm_routes(app: web.Application, db: Database):
    """Enregistre les routes de la plateforme CRM."""

    async def crm_view(request):
        return web.Response(text=CRM_HTML, content_type="text/html")

    async def api_fans_list(request):
        fans = await db.get_all_fans_with_stats()
        return web.json_response(fans)

    async def api_fan_detail(request):
        user_id = int(request.match_info["user_id"])
        fan = await db.get_fan_details(user_id)
        if not fan:
            return web.json_response({"error": "Fan non trouvé"}, status=404)
        return web.json_response(fan)

    async def api_update_tag(request):
        user_id = int(request.match_info["user_id"])
        data = await request.json()
        tag = data.get("tag", "Nouveau")
        success = await db.update_fan_tag(user_id, tag)
        return web.json_response({"success": success})

    async def api_update_notes(request):
        user_id = int(request.match_info["user_id"])
        data = await request.json()
        notes = data.get("notes", "")
        success = await db.update_fan_notes(user_id, notes)
        return web.json_response({"success": success})

    app.router.add_get("/", crm_view)
    app.router.add_get("/crm", crm_view)
    app.router.add_get("/api/fans", api_fans_list)
    app.router.add_get("/api/fans/{user_id}", api_fan_detail)
    app.router.add_post("/api/fans/{user_id}/tag", api_update_tag)
    app.router.add_post("/api/fans/{user_id}/notes", api_update_notes)
