// Pulse Outreach - Production-Grade Frontend Application Logic

let currentTab = "overview";
let globalStatus = null;
let allRecentSends = [];
let allLeads = [];
let currentLeadsFilter = "all";
let rawLogLines = [];
let autoScrollEnabled = true;

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  fetchStatus();
  fetchResumeInfo();
  fetchConfig();
  fetchLogs();

  // Periodic Polling
  setInterval(fetchStatus, 4000);
  setInterval(() => {
    if (currentTab === "logs") fetchLogs();
  }, 3000);

  // Keyboard shortcut: Escape to close modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeEmailPreview();
    }
  });
});

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  const bg = type === "success" ? "bg-emerald-600/95 text-white border-emerald-500/40" :
             type === "error" ? "bg-rose-600/95 text-white border-rose-500/40" : 
             "bg-zinc-850/95 text-zinc-100 border-zinc-700/60";

  const iconName = type === "success" ? "check-circle" : type === "error" ? "alert-circle" : "info";

  toast.className = `${bg} backdrop-blur-xl px-4 py-3 rounded-xl shadow-2xl border text-xs font-semibold flex items-center gap-2.5 transform transition-all duration-300 translate-y-2 opacity-0 pointer-events-auto max-w-md`;
  toast.innerHTML = `<i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i><span>${message}</span>`;
  container.appendChild(toast);
  lucide.createIcons();

  requestAnimationFrame(() => {
    toast.classList.remove("translate-y-2", "opacity-0");
  });

  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Tab Switching
function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.className = "nav-item w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850 transition";
  });

  const activeContent = document.getElementById(`tab-${tabId}`);
  if (activeContent) activeContent.classList.remove("hidden");

  const activeBtn = document.getElementById(`nav-${tabId}`);
  if (activeBtn) {
    activeBtn.className = "nav-item w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-white bg-zinc-800/90 border border-zinc-700/60 shadow-sm transition";
  }

  // Update Page Title
  const titles = {
    overview: ["Overview & Fleet Telemetry", "Live outreach performance and multi-account automation."],
    leads: ["Leads Pipeline & Smart Ingestion", "Upload spreadsheets, filter duplicates, and manage targeted prospects."],
    resume: ["Resume Studio", "Active PDF attached to outgoing applications."],
    settings: ["Fleet & Delivery Config", "Configure sender accounts, spam safety limits, and intervals."],
    logs: ["Engine Telemetry & Terminal", "Real-time daemon stdout and delivery receipts."]
  };
  if (titles[tabId]) {
    document.getElementById("page-title").innerText = titles[tabId][0];
    document.getElementById("page-subtitle").innerText = titles[tabId][1];
  }

  if (tabId === "leads") fetchLeads();
  if (tabId === "resume") fetchResumeInfo();
  if (tabId === "settings") fetchConfig();
  if (tabId === "logs") fetchLogs();

  lucide.createIcons();
}

// -----------------------------------------------------------------------------
// 1. STATUS & OVERVIEW
// -----------------------------------------------------------------------------
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    globalStatus = data;

    // Metrics
    document.getElementById("metric-today-sent").innerText = data.today_sent;
    document.getElementById("metric-all-time").innerText = data.all_time_sent;
    document.getElementById("metric-queue-unsent").innerText = data.queue_unsent;
    document.getElementById("metric-queue-total").innerText = data.queue_total;
    document.getElementById("badge-unsent-leads").innerText = data.queue_unsent;

    // Progress percentage (target 50)
    const target = 50;
    const pct = Math.min(Math.round((data.today_sent / target) * 100), 100);
    document.getElementById("metric-today-progress").style.width = `${pct}%`;

    // Active inboxes count
    const activeAccs = data.accounts.filter(a => a.enabled);
    document.getElementById("metric-active-accounts").innerText = activeAccs.length;

    // Daemon pill
    const daemonPill = document.getElementById("daemon-status-pill");
    if (data.daemon_scheduled) {
      daemonPill.className = "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      daemonPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Active';
    } else {
      daemonPill.className = "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-zinc-800 text-zinc-400 border border-zinc-700";
      daemonPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-zinc-500"></span> Inactive';
    }

    // Brave CDP Pill
    const bravePill = document.getElementById("brave-status-pill");
    if (data.brave_cdp_active) {
      bravePill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Connected';
      bravePill.className = "text-emerald-400 font-medium flex items-center gap-1";
    } else {
      bravePill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Disconnected';
      bravePill.className = "text-amber-400 font-medium flex items-center gap-1";
    }

    // Engine running controls
    const btnTrigger = document.getElementById("btn-trigger-engine");
    const btnStop = document.getElementById("btn-stop-engine");
    const liveIndicator = document.getElementById("engine-live-indicator");

    if (data.outreach_running) {
      btnTrigger.classList.add("hidden");
      btnStop.classList.remove("hidden");
      btnStop.classList.add("flex");
      if (liveIndicator) {
        liveIndicator.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span><span class="text-emerald-300 font-medium">Outreach Active</span>';
      }
    } else {
      btnTrigger.classList.remove("hidden");
      btnStop.classList.add("hidden");
      btnStop.classList.remove("flex");
      if (liveIndicator) {
        liveIndicator.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-zinc-300 font-medium">Fleet Ready</span>';
      }
    }

    renderFleetGrid(data.accounts);
    allRecentSends = data.recent_sends || [];
    renderRecentSendsTable(allRecentSends);

  } catch (e) {
    console.error("Error fetching status:", e);
  }
}

function renderFleetGrid(accounts) {
  const container = document.getElementById("accounts-fleet-grid");
  if (!container) return;

  container.innerHTML = accounts.map(acc => {
    const isReady = acc.enabled && acc.sent_today < acc.daily_limit;
    const isCapped = acc.enabled && acc.sent_today >= acc.daily_limit;
    const badgeColor = isCapped ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                       isReady ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                                 "bg-zinc-800 text-zinc-500 border-zinc-700";
    const badgeLabel = isCapped ? "Daily Cap Met" : isReady ? "Active" : "Disabled";

    return `
      <div class="glass-card rounded-2xl p-5 border border-zinc-800/80 space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <span class="w-2.5 h-2.5 rounded-full ${acc.enabled ? (isCapped ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse') : 'bg-zinc-600'}"></span>
            <span class="font-mono text-xs font-bold text-white truncate max-w-[170px]" title="${acc.account}">${acc.account}</span>
          </div>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold border ${badgeColor}">${badgeLabel}</span>
        </div>

        <div>
          <div class="flex items-baseline justify-between text-xs mb-1.5">
            <span class="text-zinc-400 font-medium">Daily Quota</span>
            <span class="font-mono font-bold text-zinc-200">${acc.sent_today} / ${acc.daily_limit} <span class="text-zinc-500 font-normal">(${acc.percent_today}%)</span></span>
          </div>
          <div class="w-full bg-zinc-800/80 rounded-full h-2 overflow-hidden">
            <div class="bg-gradient-to-r from-brand-600 to-indigo-400 h-2 rounded-full transition-all duration-500" style="width: ${acc.percent_today}%"></div>
          </div>
        </div>

        <div class="flex items-center justify-between text-[11px] text-zinc-400 pt-1 border-t border-zinc-800/60">
          <span>Brave Profile: <strong class="text-zinc-300 font-mono">u/${acc.user_index}</strong></span>
          <span>Buffer: <strong class="text-zinc-300">45-75s</strong></span>
        </div>
      </div>
    `;
  }).join("");
}

function renderRecentSendsTable(records) {
  const tbody = document.getElementById("recent-sends-tbody");
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-zinc-500 italic">No applications sent yet today.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => {
    const isSuccess = r.status === "Success";
    const statusBadge = isSuccess ?
      `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><i data-lucide="check" class="w-3 h-3"></i> Delivered</span>` :
      `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20"><i data-lucide="alert-triangle" class="w-3 h-3"></i> Retry Timeout</span>`;

    const escLead = encodeURIComponent(JSON.stringify({
      company: r.company || "Company",
      contact_name: r.name || "Hiring Team",
      email: r.email || "",
      target_role: "AI Engineering Intern",
      subject: r.subject || ""
    }));

    return `
      <tr class="hover:bg-zinc-850/40 transition">
        <td class="py-3 px-4">
          <div class="font-bold text-white">${r.company || 'Unknown'}</div>
          <div class="text-[11px] text-zinc-400">${r.name || 'Hiring Team'}</div>
        </td>
        <td class="py-3 px-4 font-mono text-zinc-300 text-xs">${r.email}</td>
        <td class="py-3 px-4 text-zinc-300 truncate max-w-xs text-xs" title="${r.subject}">${r.subject}</td>
        <td class="py-3 px-4 font-mono text-[11px] text-brand-400">${r.sender}</td>
        <td class="py-3 px-4">${statusBadge}</td>
        <td class="py-3 px-4 font-mono text-[11px] text-zinc-400 whitespace-nowrap">${r.timestamp.split(' ')[1] || r.timestamp}</td>
        <td class="py-3 px-4 text-right">
          <button onclick="previewEmail('${escLead}')" class="p-1.5 rounded-lg bg-zinc-850 hover:bg-zinc-800 text-zinc-400 hover:text-brand-300 transition" title="Preview Sent Email">
            <i data-lucide="eye" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      </tr>
    `;
  }).join("");

  lucide.createIcons();
}

function filterRecentSends() {
  const q = document.getElementById("filter-recent-sends").value.toLowerCase();
  const filtered = allRecentSends.filter(r =>
    (r.company && r.company.toLowerCase().includes(q)) ||
    (r.email && r.email.toLowerCase().includes(q)) ||
    (r.name && r.name.toLowerCase().includes(q)) ||
    (r.subject && r.subject.toLowerCase().includes(q))
  );
  renderRecentSendsTable(filtered);
}

// -----------------------------------------------------------------------------
// 2. LEADS MANAGEMENT
// -----------------------------------------------------------------------------
async function fetchLeads() {
  try {
    const res = await fetch("/api/leads?limit=300");
    if (!res.ok) return;
    const data = await res.json();
    allLeads = data.leads || [];

    // Update filter counts
    const totalCount = allLeads.length;
    const sentCount = allLeads.filter(l => l.is_sent).length;
    const queuedCount = totalCount - sentCount;

    document.getElementById("count-all").innerText = totalCount;
    document.getElementById("count-queued").innerText = queuedCount;
    document.getElementById("count-sent").innerText = sentCount;

    applyLeadsFilterAndRender();
  } catch (e) {
    console.error("Error fetching leads:", e);
  }
}

function setLeadsFilter(filterType) {
  currentLeadsFilter = filterType;
  ["all", "queued", "sent"].forEach(t => {
    const btn = document.getElementById(`btn-filter-${t}`);
    if (btn) {
      if (t === filterType) {
        btn.className = "px-2.5 py-1 rounded-md font-semibold text-white bg-zinc-800 transition";
      } else {
        btn.className = "px-2.5 py-1 rounded-md font-semibold text-zinc-400 hover:text-white transition";
      }
    }
  });
  applyLeadsFilterAndRender();
}

function applyLeadsFilterAndRender() {
  const q = (document.getElementById("filter-leads-input")?.value || "").toLowerCase();
  let list = allLeads;

  if (currentLeadsFilter === "queued") {
    list = list.filter(l => !l.is_sent);
  } else if (currentLeadsFilter === "sent") {
    list = list.filter(l => l.is_sent);
  }

  if (q) {
    list = list.filter(l =>
      (l.company && l.company.toLowerCase().includes(q)) ||
      (l.email && l.email.toLowerCase().includes(q)) ||
      (l.contact_name && l.contact_name.toLowerCase().includes(q)) ||
      (l.target_role && l.target_role.toLowerCase().includes(q))
    );
  }

  renderLeadsTable(list);
}

function filterLeadsTable() {
  applyLeadsFilterAndRender();
}

function renderLeadsTable(leads) {
  const tbody = document.getElementById("leads-tbody");
  if (!tbody) return;

  if (!leads || leads.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-zinc-500 italic">No leads match the selected criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = leads.map(l => {
    const statusChip = l.is_sent ?
      `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Delivered</span>` :
      `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700">Queued</span>`;

    const escLead = encodeURIComponent(JSON.stringify(l));

    return `
      <tr class="hover:bg-zinc-850/40 transition">
        <td class="py-3 px-4 font-mono text-[11px] text-zinc-400">${l.priority}</td>
        <td class="py-3 px-4 font-bold text-white">${l.company}</td>
        <td class="py-3 px-4 text-zinc-300">${l.contact_name}</td>
        <td class="py-3 px-4 font-mono text-zinc-300 text-xs">${l.email}</td>
        <td class="py-3 px-4 text-zinc-400 text-xs">${l.target_role}</td>
        <td class="py-3 px-4">${statusChip}</td>
        <td class="py-3 px-4 text-right">
          <div class="flex items-center justify-end gap-1.5">
            <button onclick="previewEmail('${escLead}')" class="p-1.5 rounded-lg bg-zinc-850 hover:bg-zinc-800 text-zinc-400 hover:text-brand-300 transition" title="Preview Email">
              <i data-lucide="eye" class="w-3.5 h-3.5"></i>
            </button>
            ${!l.is_sent ? `
              <button onclick="deleteLead('${l.email}')" class="p-1.5 rounded-lg bg-zinc-850 hover:bg-rose-500/20 text-zinc-400 hover:text-rose-400 transition" title="Delete lead">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join("");

  lucide.createIcons();
}

// Drag & Drop Handlers
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById("dropzone").classList.add("border-brand-500", "bg-brand-500/10");
}

function handleDragLeave(e) {
  e.preventDefault();
  document.getElementById("dropzone").classList.remove("border-brand-500", "bg-brand-500/10");
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById("dropzone").classList.remove("border-brand-500", "bg-brand-500/10");
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    uploadLeadsFile(e.dataTransfer.files[0]);
  }
}

async function uploadLeadsFile(file) {
  if (!file) return;
  const statusEl = document.getElementById("upload-status");
  statusEl.classList.remove("hidden");
  statusEl.innerHTML = `<span class="animate-spin mr-2">⏳</span> Ingesting and deduplicating <strong>${file.name}</strong>...`;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/leads/upload", {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    if (res.ok) {
      statusEl.innerHTML = `✅ Successfully imported <strong>${result.added_count} leads</strong>! (Filtered ${result.duplicates_filtered} duplicates)`;
      showToast(`Imported ${result.added_count} new leads!`, "success");
      fetchLeads();
      fetchStatus();
    } else {
      statusEl.innerHTML = `❌ Error: ${result.detail || "Upload failed."}`;
      showToast(result.detail || "Upload error", "error");
    }
  } catch (e) {
    statusEl.innerHTML = `❌ Upload failed: ${e.message}`;
    showToast(e.message, "error");
  }
}

async function submitManualLead() {
  const company = document.getElementById("manual-company").value.trim();
  const name = document.getElementById("manual-name").value.trim();
  const email = document.getElementById("manual-email").value.trim();
  const role = document.getElementById("manual-role").value.trim();

  if (!email || !company) {
    showToast("Please provide both Company and Email.", "error");
    return;
  }

  try {
    const res = await fetch("/api/leads/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company, contact_name: name, email, target_role: role })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Added ${company} to queue!`, "success");
      document.getElementById("manual-company").value = "";
      document.getElementById("manual-name").value = "";
      document.getElementById("manual-email").value = "";
      fetchLeads();
      fetchStatus();
    } else {
      showToast(data.detail || "Failed to add lead", "error");
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function deleteLead(email) {
  if (!confirm(`Remove ${email} from active queue?`)) return;
  try {
    const res = await fetch(`/api/leads/${encodeURIComponent(email)}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Lead removed from queue.", "info");
      fetchLeads();
      fetchStatus();
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function cleanSentLeads() {
  if (!confirm("Purge already-contacted leads from queue file?")) return;
  try {
    const res = await fetch("/api/leads/clean-sent", { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      showToast(`Purged ${data.removed_count} sent leads! (${data.remaining_count} remaining)`, "success");
      fetchLeads();
      fetchStatus();
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function clearAllLeads() {
  if (!confirm("⚠️ Are you sure you want to completely clear the outreach queue?")) return;
  try {
    const res = await fetch("/api/leads/clear-all", { method: "POST" });
    if (res.ok) {
      showToast("Queue successfully reset.", "info");
      fetchLeads();
      fetchStatus();
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

// -----------------------------------------------------------------------------
// 3. EMAIL PREVIEW MODAL
// -----------------------------------------------------------------------------
async function previewEmail(encodedLead) {
  try {
    const lead = JSON.parse(decodeURIComponent(encodedLead));
    const res = await fetch("/api/leads/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lead)
    });
    if (!res.ok) throw new Error("Could not generate email preview");
    const data = await res.json();

    document.getElementById("preview-modal-to").innerText = data.recipient;
    document.getElementById("preview-modal-recipient").innerText = `${data.name} • ${lead.company || 'Hiring Team'}`;
    document.getElementById("preview-modal-subject").innerText = data.subject;
    document.getElementById("preview-modal-body").innerText = data.body;

    const modal = document.getElementById("email-preview-modal");
    const card = document.getElementById("email-preview-card");
    modal.classList.remove("hidden");
    requestAnimationFrame(() => {
      card.classList.remove("scale-95", "opacity-0");
    });
    lucide.createIcons();
  } catch (e) {
    showToast(e.message, "error");
  }
}

function closeEmailPreview() {
  const modal = document.getElementById("email-preview-modal");
  const card = document.getElementById("email-preview-card");
  if (!modal) return;
  card.classList.add("scale-95", "opacity-0");
  setTimeout(() => {
    modal.classList.add("hidden");
  }, 200);
}

function copyModalSubject() {
  const subj = document.getElementById("preview-modal-subject").innerText;
  navigator.clipboard.writeText(subj);
  showToast("Subject copied to clipboard!", "success");
}

// -----------------------------------------------------------------------------
// 4. RESUME STUDIO
// -----------------------------------------------------------------------------
async function fetchResumeInfo() {
  try {
    const res = await fetch("/api/resume");
    if (!res.ok) return;
    const data = await res.json();
    if (data.exists) {
      document.getElementById("resume-filename").innerText = data.filename;
      document.getElementById("resume-size").innerText = `${data.size_kb} KB`;
      document.getElementById("resume-mtime").innerText = data.last_modified;
      document.getElementById("resume-md5").innerText = data.md5;
    }
  } catch (e) {
    console.error(e);
  }
}

async function uploadResumeFile(file) {
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);

  try {
    showToast("Uploading new resume PDF...", "info");
    const res = await fetch("/api/resume/upload", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      showToast("Resume updated successfully! Backup created.", "success");
      fetchResumeInfo();
      const frame = document.getElementById("resume-preview-frame");
      if (frame) frame.src = `/api/resume/view?t=${Date.now()}`;
    } else {
      const err = await res.json();
      showToast(err.detail || "Upload failed", "error");
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

// -----------------------------------------------------------------------------
// 5. FLEET SETTINGS
// -----------------------------------------------------------------------------
let settingsAccountsCache = [];

async function fetchConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) return;
    const cfg = await res.json();

    document.getElementById("setting-min-delay").value = cfg.delays?.min_seconds || 45;
    document.getElementById("setting-max-delay").value = cfg.delays?.max_seconds || 75;
    document.getElementById("setting-desktop-notifs").checked = cfg.desktop_notifications !== false;

    settingsAccountsCache = cfg.accounts || [];
    renderSettingsAccounts();
  } catch (e) {
    console.error(e);
  }
}

function renderSettingsAccounts() {
  const container = document.getElementById("settings-accounts-container");
  if (!container) return;

  container.innerHTML = settingsAccountsCache.map((acc, idx) => `
    <div class="p-4 rounded-xl bg-zinc-900 border border-zinc-800 space-y-3 relative group">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-3">
          <input type="checkbox" id="cfg-acc-en-${idx}" ${acc.enabled ? 'checked' : ''} onchange="settingsAccountsCache[${idx}].enabled = this.checked" class="w-4 h-4 rounded border-zinc-700 text-brand-600 focus:ring-brand-500 bg-zinc-950">
          <input type="email" id="cfg-acc-email-${idx}" value="${acc.account}" onchange="settingsAccountsCache[${idx}].account = this.value" class="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-white font-mono w-60 focus:outline-none focus:border-brand-500">
        </div>
        <div class="flex items-center gap-2 text-xs text-zinc-400">
          <span>Brave Profile:</span>
          <input type="number" id="cfg-acc-idx-${idx}" min="0" max="20" value="${acc.user_index}" onchange="settingsAccountsCache[${idx}].user_index = parseInt(this.value, 10)" class="w-16 bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1 text-xs text-white font-mono text-center focus:outline-none focus:border-brand-500">
          <button onclick="removeAccountRow(${idx})" class="p-1 hover:bg-rose-500/20 text-zinc-500 hover:text-rose-400 rounded transition ml-2" title="Remove Account">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>

      <div class="flex items-center justify-between text-xs pt-1">
        <span class="text-zinc-400">Daily Cold Email Cap</span>
        <div class="flex items-center gap-3">
          <input type="range" id="cfg-acc-lim-${idx}" min="5" max="50" value="${acc.daily_limit}" oninput="document.getElementById('cfg-acc-lim-val-${idx}').innerText = this.value; settingsAccountsCache[${idx}].daily_limit = parseInt(this.value, 10)" class="w-48 accent-brand-500">
          <span id="cfg-acc-lim-val-${idx}" class="font-mono font-bold text-white w-8">${acc.daily_limit}</span>
        </div>
      </div>
    </div>
  `).join("");

  lucide.createIcons();
}

function addNewAccountRow() {
  settingsAccountsCache.push({
    account: "new_inbox@gmail.com",
    user_index: 0,
    daily_limit: 25,
    enabled: true
  });
  renderSettingsAccounts();
}

function removeAccountRow(idx) {
  settingsAccountsCache.splice(idx, 1);
  renderSettingsAccounts();
}

async function saveFleetSettings() {
  const cfg = await (await fetch("/api/config")).json();

  const payload = {
    accounts: settingsAccountsCache,
    cdp_port: cfg.cdp_port || 9222,
    leads_file: "todays_outreach_queue.csv",
    log_file: "emails_sent.csv",
    resume_filename: "Rajat_Murhe_Resume.pdf",
    delays: {
      min_seconds: parseInt(document.getElementById("setting-min-delay").value, 10),
      max_seconds: parseInt(document.getElementById("setting-max-delay").value, 10)
    },
    schedule: cfg.schedule || { hour: 9, minute: 30, weekdays_only: true },
    desktop_notifications: document.getElementById("setting-desktop-notifs").checked
  };

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast("Fleet settings saved successfully!", "success");
      fetchStatus();
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

// -----------------------------------------------------------------------------
// 6. ENGINE CONTROL & LOGS
// -----------------------------------------------------------------------------
async function triggerOutreachNow() {
  if (!confirm("Start cold outreach batch immediately across enabled inboxes?")) return;
  try {
    const res = await fetch("/api/outreach/start", { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      showToast("Outreach Engine started in background!", "success");
      switchTab("logs");
      fetchStatus();
    } else {
      showToast(data.message || "Failed to start", "error");
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function stopOutreach() {
  if (!confirm("Terminate running outreach engine?")) return;
  try {
    const res = await fetch("/api/outreach/stop", { method: "POST" });
    if (res.ok) {
      showToast("Engine safely terminated.", "info");
      fetchStatus();
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function fetchLogs() {
  try {
    const res = await fetch("/api/logs");
    if (!res.ok) return;
    const data = await res.json();
    rawLogLines = data.lines || [];
    renderLogs();
  } catch (e) {
    console.error(e);
  }
}

function filterLogs() {
  renderLogs();
}

function renderLogs() {
  const terminal = document.getElementById("terminal-body");
  if (!terminal) return;

  const q = (document.getElementById("filter-logs-input")?.value || "").toLowerCase();
  let lines = rawLogLines;
  if (q) {
    lines = lines.filter(l => l.toLowerCase().includes(q));
  }

  if (!lines || lines.length === 0) {
    terminal.innerHTML = `<div class="text-zinc-500 italic">No log entries found.</div>`;
    return;
  }

  terminal.innerHTML = lines.map(l => {
    let color = "text-zinc-300";
    if (l.includes("[ERROR]") || l.includes("Error") || l.includes("Failed")) color = "text-rose-400 font-semibold";
    else if (l.includes("[WARNING]") || l.includes("Warning")) color = "text-amber-400";
    else if (l.includes("✅") || l.includes("Delivered") || l.includes("Success")) color = "text-emerald-400 font-semibold";
    else if (l.includes("▶️") || l.includes("Starting") || l.includes("Progress")) color = "text-brand-300";

    return `<div class="${color}">${l}</div>`;
  }).join("");

  if (autoScrollEnabled) {
    terminal.scrollTop = terminal.scrollHeight;
  }
}

function toggleAutoScroll() {
  autoScrollEnabled = !autoScrollEnabled;
  const btn = document.getElementById("btn-autoscroll");
  if (btn) {
    if (autoScrollEnabled) {
      btn.className = "px-2.5 py-1 rounded text-[11px] font-mono border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 flex items-center gap-1";
      btn.innerHTML = '<i data-lucide="chevrons-down" class="w-3.5 h-3.5"></i> <span>Auto-Scroll: ON</span>';
    } else {
      btn.className = "px-2.5 py-1 rounded text-[11px] font-mono border border-zinc-700 bg-zinc-800 text-zinc-400 flex items-center gap-1";
      btn.innerHTML = '<i data-lucide="pause" class="w-3.5 h-3.5"></i> <span>Auto-Scroll: OFF</span>';
    }
    lucide.createIcons();
  }
}

function copyLogs() {
  const text = rawLogLines.join("\n");
  navigator.clipboard.writeText(text);
  showToast("All logs copied to clipboard!", "success");
}

function refreshData() {
  fetchStatus();
  fetchResumeInfo();
  fetchConfig();
  fetchLogs();
  showToast("Live telemetry refreshed", "info");
}
