/**
 * AISYS Frontend Application Engine
 * Drives all functional workflows, mock hardware simulations, and real-time audio/visual events.
 */

const App = {
  state: {
    token: null,
    user: null,
    activeTab: 'dashboard',
    lastGateAlarm: null,
    inventoryAuditId: null
  },

  async init() {
    console.log("AISYS Frontend Initializing...");
    this.bindEvents();
    // Default guest session or restore session
    const savedToken = localStorage.getItem("aisys_token");
    if (savedToken) {
      this.state.token = savedToken;
      await this.verifySession();
    } else {
      // Auto login as admin for demonstration ease
      await this.demoSmartCardLogin('SC-ADMIN-001');
    }
    this.navigate('dashboard');
    this.refreshDashboard();
  },

  bindEvents() {
    // Navigation items
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        const target = item.getAttribute('data-target');
        this.navigate(target);
      });
    });

    // Sound initializer on first click
    document.body.addEventListener('click', () => {
      window.audioManager.init();
    }, { once: true });
  },

  navigate(tabName) {
    this.state.activeTab = tabName;
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-target') === tabName);
    });
    document.querySelectorAll('.view-section').forEach(el => {
      el.classList.toggle('active', el.id === `view-${tabName}`);
    });

    if (tabName === 'dashboard') this.refreshDashboard();
    if (tabName === 'catalog') this.searchCatalog();
    if (tabName === 'bookshelf') this.loadBookshelf();
    if (tabName === 'gate') this.loadGateEvents();
    if (tabName === 'migration') this.loadMigrationBatches();
    if (tabName === 'admin') this.loadAdminDiagnostics();
  },

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.state.token) {
      headers['Authorization'] = `Bearer ${this.state.token}`;
    }
    return headers;
  },

  // ================= AUTHENTICATION & SMART CARD =================
  async demoSmartCardLogin(uid) {
    try {
      const res = await fetch('/api/auth/smart-card-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smart_card_uid: uid })
      });
      const data = await res.json();
      if (res.ok) {
        this.state.token = data.token;
        this.state.user = data;
        localStorage.setItem("aisys_token", data.token);
        document.getElementById("user-display-name").innerText = `${data.full_name} (${data.role})`;
        window.audioManager.playSuccessBeep();
      } else {
        alert("Smart Card Login Failed: " + data.detail);
      }
    } catch (e) {
      console.error("Login error:", e);
    }
  },

  async verifySession() {
    try {
      const res = await fetch('/api/auth/me', { headers: this.getHeaders() });
      if (res.ok) {
        const user = await res.json();
        this.state.user = user;
        document.getElementById("user-display-name").innerText = `${user.full_name} (${user.role})`;
      } else {
        this.logout();
      }
    } catch (e) {
      this.logout();
    }
  },

  logout() {
    this.state.token = null;
    this.state.user = null;
    localStorage.removeItem("aisys_token");
    document.getElementById("user-display-name").innerText = "Not Authenticated";
    this.demoSmartCardLogin('SC-ADMIN-001'); // reset
  },

  // ================= DASHBOARD & REPORTS =================
  async refreshDashboard() {
    try {
      const res = await fetch('/api/reports/dashboard', { headers: this.getHeaders() });
      const data = await res.json();

      document.getElementById('stat-total-titles').innerText = data.catalog.total_titles;
      document.getElementById('stat-total-items').innerText = data.catalog.total_items;
      document.getElementById('stat-tagged-items').innerText = `${data.catalog.tagged_items} (${data.catalog.tagging_percentage}%)`;
      document.getElementById('stat-active-loans').innerText = data.circulation.active_loans;
      document.getElementById('stat-members').innerText = data.patrons.total_members;
      document.getElementById('stat-gate-alarms').innerText = data.security.alarm_violations;
      document.getElementById('stat-footfall').innerText = data.security.footfall_count;

      // Populate recent alarms table
      const tbody = document.getElementById('dashboard-alarms-tbody');
      tbody.innerHTML = '';
      data.security.recent_alarms.forEach(al => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${al.timestamp}</strong></td>
          <td><span class="badge badge-red">ALARM</span></td>
          <td>${al.accession_number || 'N/A'}</td>
          <td>${al.item_title || 'Unknown'}</td>
          <td>${al.cctv_image_path ? `<a href="${al.cctv_image_path}" target="_blank" class="btn btn-secondary btn-sm">View CCTV</a>` : 'N/A'}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error("Dashboard error:", e);
    }
  },

  // ================= CATALOG & SEARCH =================
  async searchCatalog() {
    const q = document.getElementById('catalog-search-input').value;
    try {
      const res = await fetch(`/api/catalog/search?q=${encodeURIComponent(q)}&limit=25`, { headers: this.getHeaders() });
      const data = await res.json();

      const tbody = document.getElementById('catalog-results-tbody');
      tbody.innerHTML = '';
      data.results.forEach(b => {
        const tr = document.createElement('tr');
        const refBadge = b.is_reference ? '<span class="badge badge-red">Reference Only</span>' : '<span class="badge badge-green">Lendable</span>';
        tr.innerHTML = `
          <td><strong>${b.id}</strong></td>
          <td><strong>${b.title}</strong><br><small style="color:#64748b">${b.author} | Call: ${b.call_number}</small></td>
          <td>${b.virtual_shelf}</td>
          <td>${refBadge}</td>
          <td>${b.available_copies} / ${b.total_copies} (Tagged: ${b.tagged_copies})</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="App.previewSpineLabel(${b.id})">Spine Label</button>
            <button class="btn btn-primary btn-sm" onclick="App.selectItemForTagging('${b.call_number}')">Tag Copy</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error("Search error:", e);
    }
  },

  async previewSpineLabel(bibId) {
    try {
      const res = await fetch(`/api/catalog/bibliographic/${bibId}`, { headers: this.getHeaders() });
      const bib = await res.json();
      if (bib.items && bib.items.length > 0) {
        const labelRes = await fetch(`/api/catalog/spine-label/${bib.items[0].id}`, { headers: this.getHeaders() });
        const labelData = await labelRes.json();
        const container = document.getElementById('spine-label-preview-modal');
        document.getElementById('spine-svg-render').innerHTML = labelData.svg_label;
        container.style.display = 'block';
      } else {
        alert("This title has no physical accession items yet.");
      }
    } catch (e) {
      alert("Error loading spine label: " + e);
    }
  },

  // ================= CIRCULATION =================
  async handleCheckout() {
    const memberId = document.getElementById('circ-member-input').value.trim();
    const itemId = document.getElementById('circ-item-input').value.trim();
    const resultBox = document.getElementById('circ-result-box');

    try {
      const res = await fetch('/api/circulation/checkout', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ member_identifier: memberId, item_identifier: itemId })
      });
      const data = await res.json();

      if (res.ok) {
        window.audioManager.playSuccessBeep();
        resultBox.innerHTML = `
          <div class="card" style="border-left: 4px solid var(--success); background:#f0fdf4;">
            <strong style="color:var(--success);">Check-Out Successful!</strong>
            <p>${data.message}</p>
            <small>Transaction ID: ${data.transaction_id} | Due Date: ${data.due_date} | RFID EAS Disarmed (0x01)</small>
          </div>
        `;
      } else {
        window.audioManager.playErrorBuzz();
        resultBox.innerHTML = `
          <div class="card" style="border-left: 4px solid var(--danger); background:#fef2f2;">
            <strong style="color:var(--danger);">Circulation Policy Rejection!</strong>
            <p>${data.detail}</p>
          </div>
        `;
      }
    } catch (e) {
      window.audioManager.playErrorBuzz();
      resultBox.innerHTML = `<div class="card" style="border-left:4px solid var(--danger)">Error: ${e}</div>`;
    }
  },

  async handleCheckin() {
    const itemId = document.getElementById('circ-return-input').value.trim();
    const resultBox = document.getElementById('circ-result-box');

    try {
      const res = await fetch('/api/circulation/checkin', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ item_identifier: itemId })
      });
      const data = await res.json();

      if (res.ok) {
        window.audioManager.playSuccessBeep();
        resultBox.innerHTML = `
          <div class="card" style="border-left: 4px solid var(--success); background:#f0fdf4;">
            <strong style="color:var(--success);">Item Return Accepted!</strong>
            <p>${data.message}</p>
            <small>Shelf Destination: <strong>${data.shelf_destination}</strong> | EAS Bit Armed (0x00) | Fines Assessed: $${data.fine_assessed.toFixed(2)}</small>
          </div>
        `;
      } else {
        window.audioManager.playErrorBuzz();
        resultBox.innerHTML = `<div class="card" style="border-left:4px solid var(--danger)">${data.detail}</div>`;
      }
    } catch (e) {
      window.audioManager.playErrorBuzz();
      resultBox.innerHTML = `<div class="card" style="border-left:4px solid var(--danger)">Error: ${e}</div>`;
    }
  },

  // ================= RFID STAFF STATION & TAGGING =================
  async handleTagBinding() {
    const itemId = document.getElementById('tag-item-id').value.trim();
    const tagUid = document.getElementById('tag-rfid-uid').value.trim();
    const resBox = document.getElementById('tagging-result-box');

    try {
      const res = await fetch('/api/rfid/tag-item', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ item_identifier: itemId, tag_uid: tagUid })
      });
      const data = await res.json();

      if (res.ok) {
        window.audioManager.playSuccessBeep();
        resBox.innerHTML = `
          <div class="card" style="border-left: 4px solid var(--success); background:#f0fdf4;">
            <strong style="color:var(--success);">Tagging Confirmed!</strong>
            <p>${data.message}</p>
            <small>Tag UID: <code>${data.tag_uid}</code> | Memory Format: ${data.memory_format} | EAS Armed (0x00)</small>
          </div>
        `;
      } else {
        window.audioManager.playErrorBuzz();
        resBox.innerHTML = `<div class="card" style="border-left: 4px solid var(--danger); background:#fef2f2;">${data.detail}</div>`;
      }
    } catch (e) {
      resBox.innerHTML = `<div class="card">Error: ${e}</div>`;
    }
  },

  // ================= HANDHELD INVENTORY =================
  async startShelfAudit() {
    const name = document.getElementById('inv-audit-name').value.trim();
    const shelf = document.getElementById('inv-shelf-target').value.trim();

    try {
      const res = await fetch('/api/inventory/start-audit', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ audit_name: name, shelf_target: shelf })
      });
      const data = await res.json();
      if (res.ok) {
        this.state.inventoryAuditId = data.audit_id;
        document.getElementById('inv-active-audit-indicator').innerText = `Active Audit #${data.audit_id} (${shelf})`;
        document.getElementById('inv-burst-section').style.display = 'block';
        alert(`Audit Session #${data.audit_id} initialized on ${shelf}. Wave the handheld wand to scan.`);
      }
    } catch (e) {
      alert("Error starting audit: " + e);
    }
  },

  async triggerInventoryBurst(scenarioType) {
    if (!this.state.inventoryAuditId) {
      alert("Please start an inventory audit session first.");
      return;
    }
    const currentShelf = document.getElementById('inv-shelf-target').value.trim();

    // Prepare simulated tag bursts
    let tags = [];
    if (scenarioType === 'correct') {
      tags = ["E00401509988A101", "E00401509988A102"]; // Introduction to Algorithms on Shelf-A-01
    } else if (scenarioType === 'misplaced') {
      tags = ["E00401509988A301"]; // Artificial Intelligence (belongs on Shelf-A-02, scanned here!)
    } else if (scenarioType === 'mixed') {
      tags = ["E00401509988A101", "E00401509988A401", "UNKNOWN-TAG-9999"];
    }

    try {
      const res = await fetch('/api/inventory/scan-burst', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          audit_id: this.state.inventoryAuditId,
          current_shelf: currentShelf,
          scanned_tag_uids: tags
        })
      });
      const data = await res.json();

      const tbody = document.getElementById('inv-events-tbody');
      data.items.forEach(it => {
        // Play appropriate sound
        if (it.status === 'CORRECT') window.audioManager.playSuccessBeep();
        else if (it.status === 'MISPLACED') window.audioManager.playWarningDoublePulse();
        else window.audioManager.playErrorBuzz();

        const tr = document.createElement('tr');
        const badge = it.status === 'CORRECT' ? '<span class="badge badge-green">CORRECT</span>' :
                      (it.status === 'MISPLACED' ? '<span class="badge badge-yellow">MISPLACED</span>' : '<span class="badge badge-red">UNKNOWN</span>');
        tr.innerHTML = `
          <td><code>${it.tag_uid}</code></td>
          <td><strong>${it.title}</strong></td>
          <td>${it.assigned_shelf}</td>
          <td>${it.scanned_shelf}</td>
          <td>${badge}</td>
        `;
        tbody.prepend(tr);
      });
    } catch (e) {
      console.error("Burst error:", e);
    }
  },

  async finalizeAudit() {
    if (!this.state.inventoryAuditId) return;
    try {
      const res = await fetch(`/api/inventory/finalize-audit/${this.state.inventoryAuditId}`, {
        method: 'POST',
        headers: this.getHeaders()
      });
      const data = await res.json();
      alert(`Audit Finalized!\nExpected: ${data.total_expected}\nScanned: ${data.total_scanned}\nCorrect: ${data.correct_count}\nMisplaced: ${data.misplaced_count}\nMissing: ${data.missing_count}`);
      this.state.inventoryAuditId = null;
      document.getElementById('inv-active-audit-indicator').innerText = 'None';
      document.getElementById('inv-burst-section').style.display = 'none';
    } catch (e) {
      alert("Error finalizing audit: " + e);
    }
  },

  // ================= SECURITY GATE =================
  async simulateGatePassage(tagUid, rawEas) {
    const gateCard = document.getElementById('gate-status-card');
    try {
      const res = await fetch('/api/gate/passage', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          gate_id: 'GATE-01',
          detected_tag_uid: tagUid,
          raw_eas_bit: rawEas
        })
      });
      const data = await res.json();

      if (data.alarm) {
        window.audioManager.playGateAlarm();
        gateCard.classList.add('alarm-flash');
        setTimeout(() => gateCard.classList.remove('alarm-flash'), 4000);

        document.getElementById('gate-alarm-alert-box').innerHTML = `
          <div class="card" style="border: 2px solid var(--danger); background:#fef2f2;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:var(--danger); font-size:1.1rem;">SIREN & STROBE ACTIVE! UNAUTHORIZED ITEM REMOVAL</strong>
              <span class="badge badge-red">EAS 0x00 VIOLATION</span>
            </div>
            <p style="margin-top:0.5rem;">Accession: <strong>${data.accession_number}</strong> | Title: <strong>${data.item_title}</strong></p>
            <p><small>Alert email queued to security. CCTV evidence snapshot captured below.</small></p>
            <div style="margin-top:0.75rem;">
              <img src="${data.cctv_image_path}" style="max-width:100%; border-radius:6px; border:1px solid #cbd5e1;" />
            </div>
          </div>
        `;
      } else {
        window.audioManager.playSuccessBeep();
        document.getElementById('gate-alarm-alert-box').innerHTML = `
          <div class="card" style="border-left: 4px solid var(--success); background:#f0fdf4;">
            <strong style="color:var(--success);">Passage Authorized</strong>
            <p>${data.message}</p>
          </div>
        `;
      }
      this.loadGateEvents();
    } catch (e) {
      console.error("Gate error:", e);
    }
  },

  async loadGateEvents() {
    try {
      const res = await fetch('/api/gate/events?limit=15', { headers: this.getHeaders() });
      const data = await res.json();
      const tbody = document.getElementById('gate-events-tbody');
      tbody.innerHTML = '';
      data.forEach(ev => {
        const tr = document.createElement('tr');
        const badge = ev.event_type === 'ALARM' ? '<span class="badge badge-red">ALARM</span>' : '<span class="badge badge-green">PASS</span>';
        tr.innerHTML = `
          <td>${ev.timestamp}</td>
          <td>${ev.gate_id}</td>
          <td>${badge}</td>
          <td>${ev.accession_number || 'N/A'}</td>
          <td>${ev.item_title || 'N/A'}</td>
          <td>${ev.cctv_image_path ? `<a href="/api/gate/cctv/${ev.cctv_image_path.split('/').pop()}" target="_blank" class="btn btn-secondary btn-sm">CCTV</a>` : ''}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error("Gate events error:", e);
    }
  },

  // ================= MIGRATION WIZARD =================
  async generate20kDataset() {
    const statusBox = document.getElementById('migration-status-box');
    statusBox.innerText = "Generating synthetic 20,000 record dataset (valid, invalid, duplicate)...";
    try {
      // Ingest local file
      const res = await fetch('/api/migration/ingest-local', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ filepath: 'data/sample_import_20000.csv' })
      });
      const data = await res.json();
      if (res.ok) {
        statusBox.innerHTML = `
          <div class="card" style="border-left:4px solid var(--primary); background:#f0f9ff;">
            <strong>Batch Staged: ${data.batch_id}</strong>
            <p>Ingested ${data.total_rows_ingested} records into staging table.</p>
            <p><small>Pre-migration hot backup stored at: <code>${data.pre_migration_backup}</code></small></p>
            <button class="btn btn-primary" onclick="App.validateBatch('${data.batch_id}')">Run Validation & Profile</button>
          </div>
        `;
        this.loadMigrationBatches();
      } else {
        statusBox.innerText = "Error: " + data.detail;
      }
    } catch (e) {
      statusBox.innerText = "Error generating dataset: " + e;
    }
  },

  async validateBatch(batchId) {
    const statusBox = document.getElementById('migration-status-box');
    statusBox.innerText = `Validating and deduplicating batch ${batchId}...`;
    try {
      const res = await fetch(`/api/migration/validate/${batchId}`, {
        method: 'POST',
        headers: this.getHeaders()
      });
      const data = await res.json();

      statusBox.innerHTML = `
        <div class="card" style="border-left:4px solid var(--secondary); background:#f0fdfa;">
          <strong style="font-size:1.1rem; color:var(--secondary);">Reconciliation Report - Batch ${data.batch_id}</strong>
          <div class="grid-4" style="margin:1rem 0;">
            <div class="card"><strong>Total Rows:</strong> ${data.total_rows_profiled}</div>
            <div class="card"><strong style="color:var(--success);">Valid Rows:</strong> ${data.valid_records}</div>
            <div class="card"><strong style="color:var(--danger);">Invalid Rows:</strong> ${data.invalid_records}</div>
            <div class="card"><strong style="color:var(--warning);">Duplicates:</strong> ${data.duplicate_records}</div>
          </div>
          <p>Checksum match: <strong>${data.reconciliation_checksum_match ? '100% RECONCILED' : 'MISMATCH'}</strong></p>
          <div style="margin-top:1rem; display:flex; gap:0.75rem;">
            <button class="btn btn-success" onclick="App.commitBatch('${data.batch_id}')">Commit Valid Records to Database</button>
            <button class="btn btn-danger" onclick="App.rollbackBatch('${data.batch_id}')">Atomic Rollback</button>
          </div>
        </div>
      `;
      this.loadMigrationBatches();
    } catch (e) {
      statusBox.innerText = "Validation error: " + e;
    }
  },

  async commitBatch(batchId) {
    const statusBox = document.getElementById('migration-status-box');
    statusBox.innerText = `Committing valid records into production tables...`;
    try {
      const res = await fetch(`/api/migration/commit/${batchId}`, {
        method: 'POST',
        headers: this.getHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        window.audioManager.playSuccessBeep();
        statusBox.innerHTML = `
          <div class="card" style="border-left:4px solid var(--success); background:#f0fdf4;">
            <strong style="color:var(--success); font-size:1.1rem;">Migration Committed Successfully!</strong>
            <p>Migrated <strong>${data.migrated_records}</strong> records with real-time FTS5 search indexing.</p>
            <div style="margin-top:0.75rem;">
              <button class="btn btn-danger" onclick="App.rollbackBatch('${data.batch_id}')">Test Atomic Rollback</button>
            </div>
          </div>
        `;
        this.loadMigrationBatches();
        this.refreshDashboard();
      } else {
        alert("Commit failed: " + data.detail);
      }
    } catch (e) {
      alert("Error committing: " + e);
    }
  },

  async rollbackBatch(batchId) {
    if (!confirm(`Are you sure you want to execute an atomic rollback for batch ${batchId}?`)) return;
    const statusBox = document.getElementById('migration-status-box');
    statusBox.innerText = `Rolling back batch ${batchId}...`;
    try {
      const res = await fetch(`/api/migration/rollback/${batchId}`, {
        method: 'POST',
        headers: this.getHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        window.audioManager.playSuccessBeep();
        statusBox.innerHTML = `
          <div class="card" style="border-left:4px solid var(--danger); background:#fef2f2;">
            <strong style="color:var(--danger);">Rollback Complete!</strong>
            <p>${data.message}</p>
            <small>Purged ${data.deleted_items} items and ${data.deleted_bibliographic_records} titles. Pre-existing records intact.</small>
          </div>
        `;
        this.loadMigrationBatches();
        this.refreshDashboard();
      }
    } catch (e) {
      alert("Rollback error: " + e);
    }
  },

  async loadMigrationBatches() {
    try {
      const res = await fetch('/api/migration/batches', { headers: this.getHeaders() });
      const data = await res.json();
      const tbody = document.getElementById('migration-batches-tbody');
      tbody.innerHTML = '';
      data.forEach(b => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${b.batch_id}</strong></td>
          <td>${b.filename}</td>
          <td>${b.total_rows}</td>
          <td><span class="badge badge-green">${b.valid_rows}</span></td>
          <td><span class="badge badge-red">${b.invalid_rows}</span></td>
          <td><span class="badge badge-yellow">${b.duplicate_rows}</span></td>
          <td><strong>${b.status}</strong></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="App.validateBatch('${b.batch_id}')">Validate</button>
            <button class="btn btn-danger btn-sm" onclick="App.rollbackBatch('${b.batch_id}')">Rollback</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error("Batches error:", e);
    }
  },

  // ================= ADMIN & OPERATIONS =================
  async loadAdminDiagnostics() {
    try {
      const healthRes = await fetch('/api/admin/health', { headers: this.getHeaders() });
      const health = await healthRes.json();
      document.getElementById('admin-health-display').innerText = JSON.stringify(health, null, 2);

      const verRes = await fetch('/api/admin/version', { headers: this.getHeaders() });
      const ver = await verRes.json();
      document.getElementById('admin-version-display').innerText = `${ver.application_name} v${ver.version} (Schema: ${ver.schema_version})`;

      const auditRes = await fetch('/api/admin/audit-logs?limit=15', { headers: this.getHeaders() });
      const logs = await auditRes.json();
      const tbody = document.getElementById('admin-audit-tbody');
      tbody.innerHTML = '';
      logs.forEach(l => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><small>${l.timestamp}</small></td>
          <td><strong>${l.action}</strong></td>
          <td>${l.entity} (${l.entity_id || 'N/A'})</td>
          <td>${l.username || 'System'}</td>
          <td><small>${l.details || ''}</small></td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error("Admin error:", e);
    }
  },

  async triggerHotBackup() {
    try {
      const res = await fetch('/api/admin/backup', { method: 'POST', headers: this.getHeaders() });
      const data = await res.json();
      if (res.ok) {
        alert(`Hot Backup Created Successfully!\nFile: ${data.manifest.backup_file}\nSHA-256: ${data.manifest.sha256}`);
        this.loadAdminDiagnostics();
      }
    } catch (e) {
      alert("Backup error: " + e);
    }
  },

  async applyOfflineUpdate() {
    try {
      const res = await fetch('/api/admin/apply-update', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ version: '1.1.0' })
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Offline Update v1.1.0 Applied!\nSnapshot: ${data.snapshot_path}`);
        this.loadAdminDiagnostics();
      }
    } catch (e) {
      alert("Update error: " + e);
    }
  },

  async rollbackOfflineUpdate() {
    try {
      const res = await fetch('/api/admin/rollback-update', {
        method: 'POST',
        headers: this.getHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Offline Update Rolled Back!\nRestored to: v${data.rolled_back_to_version}`);
        this.loadAdminDiagnostics();
      }
    } catch (e) {
      alert("Rollback error: " + e);
    }
  },

  // ================= VIRTUAL BOOKSHELF =================
  async loadBookshelf() {
    try {
      const res = await fetch('/api/catalog/bookshelf', { headers: this.getHeaders() });
      const data = await res.json();
      const container = document.getElementById('bookshelf-container');
      container.innerHTML = '';

      // Group by shelf
      const shelves = {};
      data.forEach(item => {
        const shelf = item.virtual_shelf || 'Shelf-General';
        if (!shelves[shelf]) shelves[shelf] = [];
        shelves[shelf].push(item);
      });

      const colors = ['#1e40af', '#047857', '#b91c1c', '#7c3aed', '#b45309', '#0369a1'];

      for (const [shelfName, items] of Object.entries(shelves)) {
        const titleEl = document.createElement('h3');
        titleEl.style.margin = '1rem 0 0.5rem 0';
        titleEl.innerText = `${shelfName} (${items.length} items)`;
        container.appendChild(titleEl);

        const shelfDiv = document.createElement('div');
        shelfDiv.className = 'bookshelf-shelf';

        items.forEach((it, idx) => {
          const spine = document.createElement('div');
          spine.className = 'book-spine';
          spine.style.backgroundColor = colors[idx % colors.length];
          spine.title = `${it.title} | Call: ${it.call_number} | Status: ${it.status}`;
          spine.innerText = `${it.title.slice(0, 16)} (${it.call_number})`;
          shelfDiv.appendChild(spine);
        });

        container.appendChild(shelfDiv);
      }
    } catch (e) {
      console.error("Bookshelf error:", e);
    }
  }
};

window.App = App;
document.addEventListener('DOMContentLoaded', () => App.init());
