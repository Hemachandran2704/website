/**
 * Magnus Dynamic CMS - Comprehensive Admin Dashboard Controller
 */

let currentUsers = [];
let currentTickets = [];
let currentDocs = [];

document.addEventListener("DOMContentLoaded", async () => {
  if (!Auth.requireAdmin()) return;
  Auth.initSidebar();

  setupNavigationTabs();
  setupEventListeners();

  // Load initial view
  await loadDashboardStats();
  await loadRecentActivities();
});

function setupNavigationTabs() {
  const links = document.querySelectorAll(".admin-tab-link");
  links.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = link.getAttribute("data-view");
      if (!targetView) return;

      // Update active nav
      document.querySelectorAll(".sidebar .nav-link").forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      // Switch view panel
      document.querySelectorAll(".admin-view-panel").forEach(p => p.style.display = "none");
      const targetPanel = document.getElementById(`view-${targetView}`);
      if (targetPanel) {
        targetPanel.style.display = "block";
      }

      // Load view data
      if (targetView === "overview") {
        loadDashboardStats();
        loadRecentActivities();
      } else if (targetView === "users") {
        loadUsers();
      } else if (targetView === "tickets") {
        loadTickets();
      } else if (targetView === "documents") {
        loadDocuments();
      } else if (targetView === "notifications") {
        loadNotificationsAndAnnouncements();
      } else if (targetView === "reports") {
        loadReports("all");
      } else if (targetView === "audit") {
        loadFullAuditLogs();
      } else if (targetView === "settings") {
        loadSystemSettings();
      }
    });
  });

}

function setupEventListeners() {
  // User Management
  const userSearch = document.getElementById("user-search");
  if (userSearch) {
    let debounce;
    userSearch.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => loadUsers(), 250);
    });
  }

  const roleFilter = document.getElementById("user-role-filter");
  if (roleFilter) roleFilter.addEventListener("change", () => loadUsers());

  const statusFilter = document.getElementById("user-status-filter");
  if (statusFilter) statusFilter.addEventListener("change", () => loadUsers());

  // Support Tickets
  const ticketStatusFilter = document.getElementById("ticket-status-filter");
  if (ticketStatusFilter) ticketStatusFilter.addEventListener("change", () => loadTickets());

  const ticketPriorityFilter = document.getElementById("ticket-priority-filter");
  if (ticketPriorityFilter) ticketPriorityFilter.addEventListener("change", () => loadTickets());

  // Documents
  const docStatusFilter = document.getElementById("doc-status-filter");
  if (docStatusFilter) docStatusFilter.addEventListener("change", () => loadDocuments());

  // Reports range filter
  const reportRangeFilter = document.getElementById("report-range-filter");
  if (reportRangeFilter) {
    reportRangeFilter.addEventListener("change", (e) => {
      const customDates = document.getElementById("report-custom-dates");
      if (customDates) customDates.style.display = e.target.value === "custom" ? "flex" : "none";
      loadReports(e.target.value);
    });
  }

  // System Settings Form
  const settingsForm = document.getElementById("system-settings-form");
  if (settingsForm) {
    settingsForm.addEventListener("submit", handleSaveSystemSettings);
  }

  // Admin Password Form
  const passwordForm = document.getElementById("admin-password-form");
  if (passwordForm) {
    passwordForm.addEventListener("submit", handleAdminPasswordChange);
  }
}

// ----------------------------------------------------
// 1. Overview Section
// ----------------------------------------------------
async function loadDashboardStats() {
  const container = document.getElementById("stats-grid-container");
  if (!container) return;

  const res = await apiClient.get("/api/dashboard/stats");
  if (!res.success) {
    showToast(res.message || "Failed to load dashboard statistics", "error");
    return;
  }

  const stats = res.data;

  const cards = [
    { label: "Total Users", count: stats.total_users || 0, icon: "👥", color: "blue", view: "users", sub: `${stats.active_users || 0} active &bull; ${stats.blocked_users || 0} blocked` },
    { label: "Support Tickets", count: stats.total_tickets || 0, icon: "🎫", color: "amber", view: "tickets", sub: `${stats.open_tickets || 0} pending action` },
    { label: "Documents", count: stats.total_documents || 0, icon: "📄", color: "purple", view: "documents", sub: `${stats.pending_documents || 0} pending review` },
    { label: "Dynamic Modules", count: 17, icon: "⚙️", color: "green", url: "/frontend/pages/multiple-tabs.html", sub: "17 active sub-modules" },
    { label: "Total Tabs", count: stats.total_tabs || 0, icon: "📑", color: "blue", url: "/frontend/pages/multiple-tabs.html", sub: "Configured tabs" },
    { label: "Images Library", count: stats.total_images || 0, icon: "🖼️", color: "purple", url: "/frontend/pages/images.html", sub: "Uploaded assets" },
    { label: "Dynamic Forms", count: stats.total_forms || 0, icon: "📋", color: "rose", url: "/frontend/pages/form-manager.html", sub: `${stats.total_submissions || 0} submissions` },
    { label: "System Alerts", count: stats.total_notifications || 0, icon: "🔔", color: "cyan", view: "notifications", sub: "Active broadcasts" }
  ];

  container.innerHTML = cards.map(c => `
    <div class="stat-card" style="cursor: pointer;" onclick="${c.view ? `switchAdminTab('${c.view}')` : `window.location.href='${c.url}'`}">
      <div class="stat-icon stat-icon-${c.color}">
        <span>${c.icon}</span>
      </div>
      <div class="stat-details">
        <span class="stat-count">${c.count}</span>
        <span class="stat-label">${c.label}</span>
        ${c.sub ? `<span style="font-size: 0.725rem; color: var(--text-muted); margin-top: 2px;">${c.sub}</span>` : ''}
      </div>
    </div>
  `).join("");
}

window.switchAdminTab = function(viewName) {
  const link = document.querySelector(`.admin-tab-link[data-view="${viewName}"]`);
  if (link) {
    link.click();
  }
};

async function loadRecentActivities() {
  const container = document.getElementById("recent-activities-feed");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Loading audit logs...</span></div>';

  const res = await apiClient.get("/api/audit-logs", { limit: 8 });
  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load audit logs"}</p></div>`;
    return;
  }

  const logs = res.data.items || [];
  if (logs.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">No Audit Logs Yet</div>
        <p>Activity logs will populate as actions are performed across modules.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = logs.map(log => `
    <div class="audit-item">
      <div>
        <span class="audit-badge audit-badge-${log.action}">${log.action}</span>
        <span class="audit-module">[${log.module}]</span>
        <span class="audit-desc">${escapeHtml(log.description || "System action")}</span>
      </div>
      <div class="audit-meta">
        <span>${escapeHtml(log.user_name || log.user_email || "System")} &bull; ${log.created_at}</span>
      </div>
    </div>
  `).join("");
}

// ----------------------------------------------------
// 2. User Management Section
// ----------------------------------------------------
async function loadUsers() {
  const tbody = document.getElementById("users-table-body");
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading users...</span></td></tr>';

  const search = document.getElementById("user-search")?.value || "";
  const role = document.getElementById("user-role-filter")?.value || "";
  const status = document.getElementById("user-status-filter")?.value || "";

  const res = await apiClient.get("/api/users", { search, role, status, limit: 50 });
  if (!res.success) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load users"}</p></td></tr>`;
    return;
  }

  currentUsers = res.data.items || [];
  const countEl = document.getElementById("users-count");
  if (countEl) countEl.textContent = `Total: ${res.data.total || currentUsers.length} users`;

  if (currentUsers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><p>No users matching filters found.</p></td></tr>';
    return;
  }

  tbody.innerHTML = currentUsers.map(u => `
    <tr>
      <td><strong>#${u.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(u.name)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(u.email)}</small>
      </td>
      <td>
        <span class="badge ${u.role === 'admin' ? 'badge-primary' : 'badge-neutral'}" style="text-transform: uppercase;">
          ${u.role}
        </span>
      </td>
      <td>
        <span class="badge badge-${u.status === 'active' ? 'active' : (u.status === 'blocked' ? 'danger' : 'inactive')}">
          ${u.status}
        </span>
      </td>
      <td><small>${u.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-outline" onclick="openEditUserModal(${u.id})" title="Edit User Details">✏️ Edit</button>
          ${u.status === 'active' 
            ? `<button class="btn btn-sm btn-outline" onclick="toggleUserStatus(${u.id}, 'inactive')" title="Deactivate">⏸️ Deactivate</button>
               <button class="btn btn-sm btn-danger" onclick="toggleUserStatus(${u.id}, 'blocked')" title="Block User">🚫 Block</button>`
            : `<button class="btn btn-sm btn-primary" onclick="toggleUserStatus(${u.id}, 'active')" title="Activate">✅ Activate</button>`
          }
        </div>
      </td>
    </tr>
  `).join("");
}

window.openAddUserModal = function() {
  const modal = document.getElementById("user-modal");
  if (!modal) return;
  document.getElementById("user-modal-title").textContent = "Add New User";
  document.getElementById("user-form-id").value = "";
  document.getElementById("user-form-name").value = "";
  document.getElementById("user-form-email").value = "";
  document.getElementById("user-form-password").value = "";
  document.getElementById("user-form-password-group").style.display = "block";
  document.getElementById("user-form-role").value = "user";
  document.getElementById("user-form-status").value = "active";
  modal.classList.add("active");
};

window.openEditUserModal = async function(userId) {
  const modal = document.getElementById("user-modal");
  if (!modal) return;

  const res = await apiClient.get(`/api/users/${userId}`);
  if (!res.success) {
    showToast(res.message || "Failed to load user details", "error");
    return;
  }

  const u = res.data;
  document.getElementById("user-modal-title").textContent = `Edit User: ${u.name}`;
  document.getElementById("user-form-id").value = u.id;
  document.getElementById("user-form-name").value = u.name;
  document.getElementById("user-form-email").value = u.email;
  document.getElementById("user-form-password").value = "";
  document.getElementById("user-form-password-group").style.display = "block";
  document.getElementById("user-form-role").value = u.role;
  document.getElementById("user-form-status").value = u.status;
  modal.classList.add("active");
};

window.closeUserModal = function() {
  document.getElementById("user-modal")?.classList.remove("active");
};

window.handleSaveUser = async function(e) {
  e.preventDefault();
  const id = document.getElementById("user-form-id").value;
  const name = document.getElementById("user-form-name").value.trim();
  const email = document.getElementById("user-form-email").value.trim();
  const password = document.getElementById("user-form-password").value;
  const role = document.getElementById("user-form-role").value;
  const status = document.getElementById("user-form-status").value;

  if (!name || !email) {
    showToast("Name and email are required.", "error");
    return;
  }

  let res;
  if (id) {
    // Update
    const payload = { name, email, role, status };
    if (password) payload.password = password;
    res = await apiClient.put(`/api/users/${id}`, payload);
  } else {
    // Create
    if (!password || password.length < 6) {
      showToast("Password must be at least 6 characters.", "error");
      return;
    }
    res = await apiClient.post("/api/users", { name, email, password, role, status });
  }

  if (res.success) {
    showToast(res.message || "User saved successfully", "success");
    closeUserModal();
    loadUsers();
  } else {
    showToast(res.message || "Failed to save user", "error");
  }
};

window.toggleUserStatus = async function(userId, newStatus) {
  const confirmed = await confirmAction(`Are you sure you want to change user status to '${newStatus}'?`, "Confirm Status Change");
  if (!confirmed) return;

  const res = await apiClient.put(`/api/users/${userId}/status`, { status: newStatus });
  if (res.success) {
    showToast(`User status updated to ${newStatus}`, "success");
    loadUsers();
  } else {
    showToast(res.message || "Failed to update status", "error");
  }
};

// ----------------------------------------------------
// 3. Support Tickets Section
// ----------------------------------------------------
async function loadTickets() {
  const tbody = document.getElementById("tickets-table-body");
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading support tickets...</span></td></tr>';

  const status = document.getElementById("ticket-status-filter")?.value || "";
  const priority = document.getElementById("ticket-priority-filter")?.value || "";

  const res = await apiClient.get("/api/tickets", { status, priority });
  if (!res.success) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load tickets"}</p></td></tr>`;
    return;
  }

  currentTickets = res.data || [];
  if (currentTickets.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><p>No support tickets found.</p></td></tr>';
    return;
  }

  tbody.innerHTML = currentTickets.map(t => `
    <tr>
      <td><strong>#${t.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(t.subject)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(t.user_name || t.user_email || 'User')} &bull; ${escapeHtml(t.category)}</small>
      </td>
      <td>
        <span class="badge badge-${t.priority === 'urgent' || t.priority === 'high' ? 'danger' : 'neutral'}">
          ${t.priority}
        </span>
      </td>
      <td>
        <span class="badge badge-${t.status === 'open' ? 'active' : (t.status === 'resolved' ? 'success' : 'neutral')}">
          ${t.status}
        </span>
      </td>
      <td><span class="badge" style="background: #f1f5f9; color: #475569;">💬 ${t.reply_count || 0}</span></td>
      <td><small>${t.created_at}</small></td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="openTicketThreadModal(${t.id})">🔍 View & Reply</button>
      </td>
    </tr>
  `).join("");
}

window.openTicketThreadModal = async function(ticketId) {
  const modal = document.getElementById("ticket-thread-modal");
  if (!modal) return;

  const res = await apiClient.get(`/api/tickets/${ticketId}`);
  if (!res.success) {
    showToast(res.message || "Failed to load ticket conversation", "error");
    return;
  }

  const t = res.data;
  document.getElementById("ticket-modal-subject").textContent = `#${t.id}: ${t.subject}`;
  document.getElementById("ticket-modal-user").textContent = `${t.user_name} (${t.user_email})`;
  document.getElementById("ticket-modal-status-select").value = t.status;
  document.getElementById("ticket-modal-id").value = t.id;

  const threadContainer = document.getElementById("ticket-messages-thread");
  let threadHtml = `
    <div style="padding: 14px; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 12px;">
      <div style="display:flex; justify-content:space-between; margin-bottom: 6px;">
        <strong>${escapeHtml(t.user_name)} (Initial Query)</strong>
        <small style="color:var(--text-muted);">${t.created_at}</small>
      </div>
      <p style="white-space:pre-line; color:var(--text-main); font-size:0.9rem;">${escapeHtml(t.message)}</p>
    </div>
  `;

  if (t.replies && t.replies.length > 0) {
    threadHtml += t.replies.map(r => `
      <div style="padding: 12px 14px; border-radius: 8px; margin-bottom: 10px; border: 1px solid ${r.is_admin ? '#bfdbfe' : 'var(--border-color)'}; background: ${r.is_admin ? '#eff6ff' : '#ffffff'}; margin-left: ${r.is_admin ? '20px' : '0'};">
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
          <strong style="color: ${r.is_admin ? 'var(--primary)' : 'inherit'};">
            ${r.is_admin ? '🛡️ Admin Support' : `👤 ${escapeHtml(r.user_name || 'User')}`}
          </strong>
          <small style="color:var(--text-muted);">${r.created_at}</small>
        </div>
        <p style="white-space:pre-line; font-size:0.875rem; color:var(--text-main);">${escapeHtml(r.message)}</p>
      </div>
    `).join("");
  }

  threadContainer.innerHTML = threadHtml;
  document.getElementById("ticket-reply-input").value = "";
  modal.classList.add("active");
};

window.closeTicketThreadModal = function() {
  document.getElementById("ticket-thread-modal")?.classList.remove("active");
};

window.handleSendTicketReply = async function(e) {
  e.preventDefault();
  const ticketId = document.getElementById("ticket-modal-id").value;
  const message = document.getElementById("ticket-reply-input").value.trim();

  if (!message) {
    showToast("Please enter a reply message.", "error");
    return;
  }

  const res = await apiClient.post(`/api/tickets/${ticketId}/reply`, { message });
  if (res.success) {
    showToast("Reply sent successfully", "success");
    openTicketThreadModal(ticketId);
    loadTickets();
  } else {
    showToast(res.message || "Failed to send reply", "error");
  }
};

window.handleUpdateTicketStatus = async function() {
  const ticketId = document.getElementById("ticket-modal-id").value;
  const status = document.getElementById("ticket-modal-status-select").value;

  const res = await apiClient.put(`/api/tickets/${ticketId}/status`, { status });
  if (res.success) {
    showToast(`Ticket status updated to ${status}`, "success");
    loadTickets();
  } else {
    showToast(res.message || "Failed to update status", "error");
  }
};

// ----------------------------------------------------
// 4. Documents Section
// ----------------------------------------------------
async function loadDocuments() {
  const tbody = document.getElementById("documents-table-body");
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading documents...</span></td></tr>';

  const status = document.getElementById("doc-status-filter")?.value || "";
  const res = await apiClient.get("/api/documents", { status });
  if (!res.success) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load documents"}</p></td></tr>`;
    return;
  }

  currentDocs = res.data || [];
  if (currentDocs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><p>No documents found.</p></td></tr>';
    return;
  }

  tbody.innerHTML = currentDocs.map(d => `
    <tr>
      <td><strong>#${d.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(d.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(d.user_name || d.user_email || 'User')} &bull; ${escapeHtml(d.category)}</small>
      </td>
      <td><code>${escapeHtml(d.file_name)}</code></td>
      <td><span class="badge" style="background:#f1f5f9; color:#475569;">${d.file_size || '150 KB'}</span></td>
      <td>
        <span class="badge badge-${d.status === 'approved' ? 'success' : (d.status === 'rejected' ? 'danger' : 'warning')}">
          ${d.status}
        </span>
      </td>
      <td><small>${d.created_at}</small></td>
      <td>
        <div class="table-actions">
          <a href="${d.download_url}" target="_blank" class="btn btn-sm btn-outline" title="Download / Preview">⬇️ View</a>
          <button class="btn btn-sm btn-primary" onclick="openReviewDocModal(${d.id}, '${escapeHtml(d.title)}', '${d.status}', '${escapeHtml(d.review_notes || '')}')" title="Review Document">⚖️ Review</button>
        </div>
      </td>
    </tr>
  `).join("");
}

window.openReviewDocModal = function(docId, title, currentStatus, notes) {
  const modal = document.getElementById("review-doc-modal");
  if (!modal) return;
  document.getElementById("review-doc-id").value = docId;
  document.getElementById("review-doc-title").textContent = title;
  document.getElementById("review-doc-status").value = currentStatus;
  document.getElementById("review-doc-notes").value = notes;
  modal.classList.add("active");
};

window.closeReviewDocModal = function() {
  document.getElementById("review-doc-modal")?.classList.remove("active");
};

window.handleSaveDocReview = async function(e) {
  e.preventDefault();
  const docId = document.getElementById("review-doc-id").value;
  const status = document.getElementById("review-doc-status").value;
  const review_notes = document.getElementById("review-doc-notes").value.trim();

  const res = await apiClient.put(`/api/documents/${docId}/status`, { status, review_notes });
  if (res.success) {
    showToast(`Document marked as ${status}`, "success");
    closeReviewDocModal();
    loadDocuments();
  } else {
    showToast(res.message || "Failed to update review", "error");
  }
};

// ----------------------------------------------------
// 5. Notifications & Announcements Section
// ----------------------------------------------------
async function loadNotificationsAndAnnouncements() {
  // Load Notifications
  const notifsContainer = document.getElementById("admin-notifs-list");
  if (notifsContainer) {
    const res = await apiClient.get("/api/notifications");
    if (res.success && res.data) {
      notifsContainer.innerHTML = res.data.map(n => `
        <div class="audit-item" style="border-left: 4px solid var(--${n.type === 'alert' || n.type === 'warning' ? 'danger' : 'primary'});">
          <div>
            <div style="font-weight: 600; font-size: 0.95rem;">${escapeHtml(n.title)} <span class="badge badge-${n.type}">${n.type}</span></div>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">${escapeHtml(n.message)}</p>
          </div>
          <div class="audit-meta">
            <span>${n.created_at}</span>
            <button class="btn btn-sm btn-outline" style="margin-left: 8px; color: #ef4444;" onclick="deleteNotification(${n.id})">🗑️</button>
          </div>
        </div>
      `).join("");
    }
  }

  // Load Announcements
  const annContainer = document.getElementById("admin-announcements-list");
  if (annContainer) {
    const res2 = await apiClient.get("/api/announcements");
    if (res2.success && res2.data) {
      annContainer.innerHTML = res2.data.map(a => `
        <div style="padding: 14px; background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 10px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size: 0.95rem;">${escapeHtml(a.title)}</strong>
            <div>
              <span class="badge badge-${a.priority === 'high' ? 'danger' : 'neutral'}">${a.priority}</span>
              <button class="btn btn-sm btn-outline" style="color: #ef4444; padding: 2px 6px;" onclick="deleteAnnouncement(${a.id})">🗑️</button>
            </div>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 6px;">${escapeHtml(a.message)}</p>
          <small style="color: var(--text-muted);">Target: ${a.target_role} &bull; ${a.created_at}</small>
        </div>
      `).join("");
    }
  }
}

window.openNewAnnouncementModal = function() {
  document.getElementById("announcement-modal")?.classList.add("active");
};

window.closeNewAnnouncementModal = function() {
  document.getElementById("announcement-modal")?.classList.remove("active");
};

window.handleSaveAnnouncement = async function(e) {
  e.preventDefault();
  const title = document.getElementById("ann-title").value.trim();
  const message = document.getElementById("ann-message").value.trim();
  const priority = document.getElementById("ann-priority").value;
  const target_role = document.getElementById("ann-target").value;

  if (!title || !message) {
    showToast("Title and message are required", "error");
    return;
  }

  const res = await apiClient.post("/api/announcements", { title, message, priority, target_role });
  if (res.success) {
    showToast("Announcement published successfully", "success");
    closeNewAnnouncementModal();
    loadNotificationsAndAnnouncements();
  } else {
    showToast(res.message || "Failed to publish announcement", "error");
  }
};

window.deleteAnnouncement = async function(annId) {
  const confirmed = await confirmAction("Delete this announcement?", "Confirm Delete");
  if (!confirmed) return;
  const res = await apiClient.delete(`/api/announcements/${annId}`);
  if (res.success) {
    showToast("Announcement deleted", "success");
    loadNotificationsAndAnnouncements();
  }
};

window.deleteNotification = async function(notifId) {
  const confirmed = await confirmAction("Delete this notification?", "Confirm Delete");
  if (!confirmed) return;
  const res = await apiClient.delete(`/api/notifications/${notifId}`);
  if (res.success) {
    showToast("Notification deleted", "success");
    loadNotificationsAndAnnouncements();
  }
};

// ----------------------------------------------------
// 6. Reports & Analytics Section
// ----------------------------------------------------
async function loadReports(range = "all") {
  const container = document.getElementById("reports-data-container");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Aggregating analytics data...</span></div>';

  const params = { range };
  if (range === "custom") {
    params.start_date = document.getElementById("report-start-date")?.value || "";
    params.end_date = document.getElementById("report-end-date")?.value || "";
  }

  const res = await apiClient.get("/api/reports/summary", params);
  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load reports"}</p></div>`;
    return;
  }

  const r = res.data;
  container.innerHTML = `
    <div class="stats-grid" style="margin-bottom: 24px;">
      <div class="stat-card">
        <div class="stat-icon stat-icon-blue"><span>👥</span></div>
        <div class="stat-details">
          <span class="stat-count">${r.total_users || 0}</span>
          <span class="stat-label">Total Users (${r.new_users || 0} in range)</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-green"><span>✅</span></div>
        <div class="stat-details">
          <span class="stat-count">${r.active_users || 0}</span>
          <span class="stat-label">Active Users</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-amber"><span>🎫</span></div>
        <div class="stat-details">
          <span class="stat-count">${r.total_tickets || 0}</span>
          <span class="stat-label">Support Tickets (${r.open_tickets || 0} Open)</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-purple"><span>📄</span></div>
        <div class="stat-details">
          <span class="stat-count">${r.total_documents || 0}</span>
          <span class="stat-label">Documents (${r.pending_documents || 0} Pending)</span>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px;">
      <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; padding: 20px;">
        <h3 style="font-size: 1rem; margin-bottom: 12px;">Activity Actions Breakdown</h3>
        <div style="display:flex; flex-direction:column; gap: 8px;">
          ${(r.action_breakdown && r.action_breakdown.length > 0) ? r.action_breakdown.map(a => `
            <div style="display:flex; justify-content:space-between; font-size:0.875rem; border-bottom:1px solid #f1f5f9; padding-bottom:4px;">
              <span class="badge audit-badge-${a.action}">${a.action}</span>
              <strong>${a.count} events</strong>
            </div>
          `).join("") : '<p style="color:var(--text-muted); font-size:0.85rem;">No activity records for this range.</p>'}
        </div>
      </div>

      <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; padding: 20px;">
        <h3 style="font-size: 1rem; margin-bottom: 12px;">Ticket Status Breakdown</h3>
        <div style="display:flex; flex-direction:column; gap: 8px;">
          ${(r.ticket_status_breakdown && r.ticket_status_breakdown.length > 0) ? r.ticket_status_breakdown.map(ts => `
            <div style="display:flex; justify-content:space-between; font-size:0.875rem; border-bottom:1px solid #f1f5f9; padding-bottom:4px;">
              <span class="badge badge-${ts.status}">${ts.status}</span>
              <strong>${ts.count} tickets</strong>
            </div>
          `).join("") : '<p style="color:var(--text-muted); font-size:0.85rem;">No tickets recorded.</p>'}
        </div>
      </div>
    </div>
  `;
}

// ----------------------------------------------------
// 7. Full Audit Logs Section
// ----------------------------------------------------
async function loadFullAuditLogs() {
  const container = document.getElementById("full-audit-feed");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Loading audit trail...</span></div>';

  const moduleFilter = document.getElementById("audit-module-filter")?.value || "";
  const res = await apiClient.get("/api/audit-logs", { limit: 50, module: moduleFilter });

  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load audit logs"}</p></div>`;
    return;
  }

  const logs = res.data.items || [];
  if (logs.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No audit events match criteria.</p></div>';
    return;
  }

  container.innerHTML = logs.map(log => `
    <div class="audit-item">
      <div>
        <span class="audit-badge audit-badge-${log.action}">${log.action}</span>
        <span class="audit-module">[${log.module}]</span>
        <span class="audit-desc">${escapeHtml(log.description || "System action")}</span>
      </div>
      <div class="audit-meta">
        <span>${escapeHtml(log.user_name || log.user_email || "System")} &bull; ${log.created_at}</span>
      </div>
    </div>
  `).join("");
}

// ----------------------------------------------------
// 8. System Settings Section
// ----------------------------------------------------
async function loadSystemSettings() {
  const res = await apiClient.get("/api/settings/system");
  if (res.success && res.data && res.data.map) {
    const m = res.data.map;
    if (document.getElementById("sys-site-name")) document.getElementById("sys-site-name").value = m.site_name || "Magnus Dynamic CMS";
    if (document.getElementById("sys-allow-reg")) document.getElementById("sys-allow-reg").checked = m.allow_registration === "true";
    if (document.getElementById("sys-session-timeout")) document.getElementById("sys-session-timeout").value = m.session_timeout_hours || "24";
    if (document.getElementById("sys-maintenance")) document.getElementById("sys-maintenance").checked = m.maintenance_mode === "true";
    if (document.getElementById("sys-max-upload")) document.getElementById("sys-max-upload").value = m.max_upload_size_mb || "5";
  }
}

async function handleSaveSystemSettings(e) {
  e.preventDefault();
  const payload = {
    site_name: document.getElementById("sys-site-name")?.value.trim() || "Magnus Dynamic CMS",
    allow_registration: document.getElementById("sys-allow-reg")?.checked ? "true" : "false",
    session_timeout_hours: document.getElementById("sys-session-timeout")?.value || "24",
    maintenance_mode: document.getElementById("sys-maintenance")?.checked ? "true" : "false",
    max_upload_size_mb: document.getElementById("sys-max-upload")?.value || "5"
  };

  const res = await apiClient.put("/api/settings/system", payload);
  if (res.success) {
    showToast("System settings saved successfully", "success");
  } else {
    showToast(res.message || "Failed to update settings", "error");
  }
}

async function handleAdminPasswordChange(e) {
  e.preventDefault();
  const current_password = document.getElementById("admin-curr-pass").value;
  const new_password = document.getElementById("admin-new-pass").value;
  const confirm_password = document.getElementById("admin-conf-pass").value;

  if (!current_password || !new_password) {
    showToast("Please enter current and new password", "error");
    return;
  }
  if (new_password.length < 6) {
    showToast("Password must be at least 6 characters", "error");
    return;
  }
  if (new_password !== confirm_password) {
    showToast("New passwords do not match", "error");
    return;
  }

  const res = await apiClient.put("/api/user/password", { current_password, new_password, confirm_password });
  if (res.success) {
    showToast("Password updated successfully", "success");
    document.getElementById("admin-password-form")?.reset();
  } else {
    showToast(res.message || "Failed to change password", "error");
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
