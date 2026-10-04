/**
 * Magnus Dynamic CMS - User Dashboard Controller
 */

let myOverviewData = {};
let myTickets = [];
let myDocuments = [];
let mySchedules = [];
let myFavorites = [];

document.addEventListener("DOMContentLoaded", async () => {
  const isAuthed = await Auth.checkAuth();
  if (!isAuthed) return;

  setupUserSidebar();
  setupUserNavigation();
  setupUserFormListeners();

  // Load initial view
  await loadUserOverview();
});

function setupUserSidebar() {
  const user = apiClient.getUser();
  if (user) {
    const nameEl = document.getElementById("sidebar-user-name");
    const roleEl = document.getElementById("sidebar-user-role");
    const avatarEl = document.getElementById("sidebar-user-avatar");
    if (nameEl) nameEl.textContent = user.name || user.email;
    if (roleEl) roleEl.textContent = "USER";
    if (avatarEl) avatarEl.textContent = (user.name || user.email || "U").charAt(0).toUpperCase();

  }

  const logoutBtn = document.getElementById("sidebar-logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => Auth.logout());
  }

  const mobileToggle = document.getElementById("mobile-menu-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", () => sidebar.classList.toggle("mobile-open"));
  }

  const moreGroup = document.getElementById("nav-more-group");
  const moreToggle = moreGroup?.querySelector(".nav-group-header");
  if (moreToggle) {
    moreToggle.addEventListener("click", () => moreGroup.classList.toggle("open"));
  }
}

function setupUserNavigation() {
  const tabLinks = document.querySelectorAll(".user-tab-link");
  tabLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = link.getAttribute("data-view");
      if (!targetView) return;

      document.querySelectorAll(".sidebar .nav-link").forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      document.querySelectorAll(".user-view-panel").forEach(p => p.style.display = "none");
      const targetPanel = document.getElementById(`user-view-${targetView}`);
      if (targetPanel) targetPanel.style.display = "block";

      const titleEl = document.getElementById("user-page-title");
      const breadcrumbEl = document.getElementById("user-breadcrumb-curr");
      if (titleEl) titleEl.textContent = link.textContent.trim().replace(/^[^\s]+\s*/, '');
      if (breadcrumbEl) breadcrumbEl.textContent = link.textContent.trim().replace(/^[^\s]+\s*/, '');

      // Load view data
      if (targetView === "overview") loadUserOverview();
      else if (targetView === "profile") loadUserProfile();
      else if (targetView === "activities") loadUserActivities();
      else if (targetView === "notifications") loadUserNotifications();
      else if (targetView === "schedules") loadUserSchedules();
      else if (targetView === "documents") loadUserDocuments();
      else if (targetView === "reports") loadUserReports();
      else if (targetView === "favorites") loadUserFavorites();
      else if (targetView === "support") loadUserTickets();
      else if (targetView === "settings") loadUserSettings();
      else if (targetView === "security") loadUserSecurity();
    });
  });
}

function setupUserFormListeners() {
  // Profile update form
  const profileForm = document.getElementById("user-profile-form");
  if (profileForm) {
    profileForm.addEventListener("submit", handleUpdateUserProfile);
  }

  // Password change form
  const passForm = document.getElementById("user-security-password-form");
  if (passForm) {
    passForm.addEventListener("submit", handleUserPasswordChange);
  }

  // Settings update form
  const settingsForm = document.getElementById("user-prefs-form");
  if (settingsForm) {
    settingsForm.addEventListener("submit", handleSaveUserSettings);
  }

  // New ticket form
  const ticketForm = document.getElementById("new-ticket-form");
  if (ticketForm) {
    ticketForm.addEventListener("submit", handleCreateTicket);
  }

  // Upload document form
  const docForm = document.getElementById("upload-doc-form");
  if (docForm) {
    docForm.addEventListener("submit", handleUploadDocument);
  }

  // New schedule event form
  const schedForm = document.getElementById("new-schedule-form");
  if (schedForm) {
    schedForm.addEventListener("submit", handleCreateSchedule);
  }

  // New favorite form
  const favForm = document.getElementById("new-favorite-form");
  if (favForm) {
    favForm.addEventListener("submit", handleCreateFavorite);
  }
}

// ----------------------------------------------------
// 1. User Overview Section
// ----------------------------------------------------
async function loadUserOverview() {
  const container = document.getElementById("user-overview-stats-grid");
  if (!container) return;

  const res = await apiClient.get("/api/user/overview");
  if (!res.success) {
    showToast(res.message || "Failed to load overview", "error");
    return;
  }

  myOverviewData = res.data || {};
  const user = apiClient.getUser();

  const welcomeName = document.getElementById("overview-welcome-name");
  if (welcomeName) welcomeName.textContent = user ? user.name : "User";

  const cards = [
    { label: "Open Support Tickets", count: myOverviewData.open_tickets || 0, icon: "🎫", color: "amber", view: "support", sub: `${myOverviewData.my_tickets || 0} total tickets` },
    { label: "My Documents", count: myOverviewData.my_documents || 0, icon: "📄", color: "purple", view: "documents", sub: `${myOverviewData.approved_documents || 0} approved` },
    { label: "Calendar Schedules", count: myOverviewData.my_schedules || 0, icon: "📅", color: "blue", view: "schedules", sub: "Upcoming events" },
    { label: "Saved Favorites", count: myOverviewData.my_favorites || 0, icon: "⭐", color: "green", view: "favorites", sub: "Quick access shortcuts" }
  ];

  container.innerHTML = cards.map(c => `
    <div class="stat-card" style="cursor: pointer;" onclick="switchUserTab('${c.view}')">
      <div class="stat-icon stat-icon-${c.color}"><span>${c.icon}</span></div>
      <div class="stat-details">
        <span class="stat-count">${c.count}</span>
        <span class="stat-label">${c.label}</span>
        <span style="font-size: 0.725rem; color: var(--text-muted); margin-top: 2px;">${c.sub}</span>
      </div>
    </div>
  `).join("");

  // Announcements banner
  const annContainer = document.getElementById("overview-announcements-banner");
  if (annContainer && myOverviewData.announcements && myOverviewData.announcements.length > 0) {
    annContainer.innerHTML = myOverviewData.announcements.map(a => `
      <div style="padding: 12px 16px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; margin-bottom: 10px; display: flex; align-items: flex-start; gap: 12px;">
        <span style="font-size: 1.25rem;">📢</span>
        <div>
          <strong style="color: #1e3a8a; font-size: 0.95rem;">${escapeHtml(a.title)}</strong>
          <p style="font-size: 0.85rem; color: #1e40af; margin-top: 2px;">${escapeHtml(a.message)}</p>
        </div>
      </div>
    `).join("");
    annContainer.style.display = "block";
  }

  // Recent activities list
  const actContainer = document.getElementById("overview-recent-activities");
  if (actContainer) {
    const acts = myOverviewData.recent_activities || [];
    if (acts.length === 0) {
      actContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No recent activities logged yet.</p>';
    } else {
      actContainer.innerHTML = acts.map(a => `
        <div class="audit-item">
          <div>
            <span class="audit-badge audit-badge-${a.action}">${a.action}</span>
            <span class="audit-module">[${a.module}]</span>
            <span class="audit-desc">${escapeHtml(a.description || "Personal action")}</span>
          </div>
          <div class="audit-meta">
            <span>${a.created_at}</span>
          </div>
        </div>
      `).join("");
    }
  }
}

window.switchUserTab = function(viewName) {
  const link = document.querySelector(`.user-tab-link[data-view="${viewName}"]`);
  if (link) link.click();
};

// ----------------------------------------------------
// 2. User Profile Section
// ----------------------------------------------------
async function loadUserProfile() {
  const res = await apiClient.get("/api/user/profile");
  if (!res.success) {
    showToast(res.message || "Failed to load profile", "error");
    return;
  }

  const p = res.data;
  if (document.getElementById("prof-name")) document.getElementById("prof-name").value = p.name || "";
  if (document.getElementById("prof-email")) document.getElementById("prof-email").value = p.email || "";
  if (document.getElementById("prof-phone")) document.getElementById("prof-phone").value = p.phone || "";
  if (document.getElementById("prof-dept")) document.getElementById("prof-dept").value = p.department || "";
  if (document.getElementById("prof-bio")) document.getElementById("prof-bio").value = p.bio || "";
  if (document.getElementById("prof-registered")) document.getElementById("prof-registered").textContent = p.created_at || "—";
}

async function handleUpdateUserProfile(e) {
  e.preventDefault();
  const name = document.getElementById("prof-name").value.trim();
  const phone = document.getElementById("prof-phone").value.trim();
  const department = document.getElementById("prof-dept").value.trim();
  const bio = document.getElementById("prof-bio").value.trim();

  if (!name) {
    showToast("Full name is required", "error");
    return;
  }

  const res = await apiClient.put("/api/user/profile", { name, phone, department, bio });
  if (res.success) {
    showToast("Profile updated successfully", "success");
    // Update local storage user name
    const curr = apiClient.getUser();
    if (curr) {
      curr.name = name;
      apiClient.setUser(curr);
      setupUserSidebar();
    }
  } else {
    showToast(res.message || "Failed to update profile", "error");
  }
}

// ----------------------------------------------------
// 3. User Activities Section
// ----------------------------------------------------
async function loadUserActivities() {
  const container = document.getElementById("user-activities-list");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Loading your activity logs...</span></div>';

  const res = await apiClient.get("/api/user/activities");
  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load activities"}</p></div>`;
    return;
  }

  const items = res.data.items || [];
  if (items.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No activity logs recorded yet.</p></div>';
    return;
  }

  container.innerHTML = items.map(a => `
    <div class="audit-item">
      <div>
        <span class="audit-badge audit-badge-${a.action}">${a.action}</span>
        <span class="audit-module">[${a.module}]</span>
        <span class="audit-desc">${escapeHtml(a.description || "Activity")}</span>
      </div>
      <div class="audit-meta">
        <span>${a.created_at}</span>
      </div>
    </div>
  `).join("");
}

// ----------------------------------------------------
// 4. User Notifications Section
// ----------------------------------------------------
async function loadUserNotifications() {
  const container = document.getElementById("user-notifications-list");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Loading notifications...</span></div>';

  const res = await apiClient.get("/api/notifications");
  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load notifications"}</p></div>`;
    return;
  }

  const items = res.data || [];
  if (items.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>You have no notifications at this time.</p></div>';
    return;
  }

  container.innerHTML = items.map(n => `
    <div class="audit-item" style="border-left: 4px solid var(--${n.type === 'alert' || n.type === 'warning' ? 'danger' : 'primary'});">
      <div>
        <div style="font-weight: 600; font-size: 0.95rem;">
          ${escapeHtml(n.title)} 
          <span class="badge badge-${n.type}">${n.type}</span>
          ${n.status === 'read' ? '<span class="badge" style="background:#f1f5f9; color:#64748b;">Read</span>' : ''}
        </div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">${escapeHtml(n.message)}</p>
      </div>
      <div class="audit-meta">
        <span>${n.created_at}</span>
        ${n.status !== 'read' ? `<button class="btn btn-sm btn-outline" style="margin-left: 8px;" onclick="markNotificationRead(${n.id})">Mark as Read</button>` : ''}
      </div>
    </div>
  `).join("");
}

window.markNotificationRead = async function(notifId) {
  const res = await apiClient.put(`/api/notifications/${notifId}/read`);
  if (res.success) {
    showToast("Marked as read", "success");
    loadUserNotifications();
  }
};

// ----------------------------------------------------
// 5. User Calendar Schedules Section
// ----------------------------------------------------
async function loadUserSchedules() {
  const container = document.getElementById("user-schedules-list");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Loading your schedule...</span></div>';

  const res = await apiClient.get("/api/user/schedules");
  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load schedules"}</p></div>`;
    return;
  }

  mySchedules = res.data || [];
  if (mySchedules.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No schedule events planned yet. Click "+ Add Schedule Event" above.</p></div>';
    return;
  }

  container.innerHTML = mySchedules.map(s => `
    <div style="padding: 16px; background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-weight: 700; font-size: 1rem; color: var(--text-main);">${escapeHtml(s.title)}</div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">${escapeHtml(s.description || 'No description provided')}</p>
        <div style="margin-top: 6px; font-size: 0.8rem; color: var(--primary); font-weight: 600;">
          📅 ${s.event_date} at ${s.event_time}
        </div>
      </div>
      <button class="btn btn-sm btn-outline" style="color: #ef4444;" onclick="deleteScheduleEvent(${s.id})">🗑️ Delete</button>
    </div>
  `).join("");
}

window.openNewScheduleModal = function() {
  document.getElementById("schedule-modal")?.classList.add("active");
};

window.closeNewScheduleModal = function() {
  document.getElementById("schedule-modal")?.classList.remove("active");
};

async function handleCreateSchedule(e) {
  e.preventDefault();
  const title = document.getElementById("sched-title").value.trim();
  const description = document.getElementById("sched-desc").value.trim();
  const event_date = document.getElementById("sched-date").value;
  const event_time = document.getElementById("sched-time").value || "09:00";

  if (!title || !event_date) {
    showToast("Event title and date are required", "error");
    return;
  }

  const res = await apiClient.post("/api/user/schedules", { title, description, event_date, event_time });
  if (res.success) {
    showToast("Event added to calendar", "success");
    closeNewScheduleModal();
    document.getElementById("new-schedule-form")?.reset();
    loadUserSchedules();
  } else {
    showToast(res.message || "Failed to add event", "error");
  }
}

window.deleteScheduleEvent = async function(schedId) {
  const confirmed = await confirmAction("Delete this schedule event?", "Confirm Delete");
  if (!confirmed) return;
  const res = await apiClient.delete(`/api/user/schedules/${schedId}`);
  if (res.success) {
    showToast("Event deleted", "success");
    loadUserSchedules();
  }
};

// ----------------------------------------------------
// 6. User Documents Section
// ----------------------------------------------------
async function loadUserDocuments() {
  const tbody = document.getElementById("user-documents-table-body");
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading documents...</span></td></tr>';

  const res = await apiClient.get("/api/documents");
  if (!res.success) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load documents"}</p></td></tr>`;
    return;
  }

  myDocuments = res.data || [];
  if (myDocuments.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><p>No documents uploaded yet. Click "+ Upload New Document" above.</p></td></tr>';
    return;
  }

  tbody.innerHTML = myDocuments.map(d => `
    <tr>
      <td><strong>#${d.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(d.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(d.category)}</small>
        ${d.review_notes ? `<div style="font-size:0.775rem; color:#b91c1c; margin-top:2px;">Notes: ${escapeHtml(d.review_notes)}</div>` : ''}
      </td>
      <td><code>${escapeHtml(d.file_name)}</code></td>
      <td><span class="badge" style="background:#f1f5f9; color:#475569;">${d.file_size || '150 KB'}</span></td>
      <td>
        <span class="badge badge-${d.status === 'approved' ? 'success' : (d.status === 'rejected' ? 'danger' : 'warning')}">
          ${d.status}
        </span>
      </td>
      <td>
        <div class="table-actions">
          <a href="${d.download_url}" target="_blank" class="btn btn-sm btn-outline">⬇️ Download</a>
          ${d.status === 'pending' ? `<button class="btn btn-sm btn-danger" onclick="deleteUserDoc(${d.id})">🗑️</button>` : ''}
        </div>
      </td>
    </tr>
  `).join("");
}

window.openUploadDocModal = function() {
  document.getElementById("upload-doc-modal")?.classList.add("active");
};

window.closeUploadDocModal = function() {
  document.getElementById("upload-doc-modal")?.classList.remove("active");
};

async function handleUploadDocument(e) {
  e.preventDefault();
  const form = document.getElementById("upload-doc-form");
  const formData = new FormData(form);

  const res = await apiClient.upload("/api/documents", formData);
  if (res.success) {
    showToast("Document submitted for review", "success");
    closeUploadDocModal();
    form.reset();
    loadUserDocuments();
  } else {
    showToast(res.message || "Failed to upload document", "error");
  }
}

window.deleteUserDoc = async function(docId) {
  const confirmed = await confirmAction("Delete this pending document?", "Confirm Delete");
  if (!confirmed) return;
  const res = await apiClient.delete(`/api/documents/${docId}`);
  if (res.success) {
    showToast("Document removed", "success");
    loadUserDocuments();
  }
};

// ----------------------------------------------------
// 7. User Personal Reports Section
// ----------------------------------------------------
async function loadUserReports() {
  const container = document.getElementById("user-reports-container");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Compiling your personal activity metrics...</span></div>';

  const res = await apiClient.get("/api/reports/user");
  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load reports"}</p></div>`;
    return;
  }

  const r = res.data;
  container.innerHTML = `
    <div class="stats-grid" style="margin-bottom: 24px;">
      <div class="stat-card">
        <div class="stat-icon stat-icon-amber"><span>🎫</span></div>
        <div class="stat-details">
          <span class="stat-count">${r.total_tickets || 0}</span>
          <span class="stat-label">Support Tickets (${r.resolved_tickets || 0} Resolved)</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-purple"><span>📄</span></div>
        <div class="stat-details">
          <span class="stat-count">${r.total_documents || 0}</span>
          <span class="stat-label">Documents (${r.approved_documents || 0} Approved)</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon-blue"><span>📜</span></div>
        <div class="stat-details">
          <span class="stat-count">${r.total_activities || 0}</span>
          <span class="stat-label">Total Activities Performed</span>
        </div>
      </div>
    </div>

    <div class="table-card" style="padding: 20px;">
      <h3 style="font-size: 1rem; margin-bottom: 12px;">Activity Type Breakdown</h3>
      <div style="display:flex; flex-direction:column; gap: 8px;">
        ${(r.action_breakdown && r.action_breakdown.length > 0) ? r.action_breakdown.map(a => `
          <div style="display:flex; justify-content:space-between; font-size:0.875rem; border-bottom:1px solid #f1f5f9; padding-bottom:4px;">
            <span class="badge audit-badge-${a.action}">${a.action}</span>
            <strong>${a.count} actions</strong>
          </div>
        `).join("") : '<p style="color:var(--text-muted); font-size:0.85rem;">No activity records logged.</p>'}
      </div>
    </div>
  `;
}

// ----------------------------------------------------
// 8. User Favorites Section
// ----------------------------------------------------
async function loadUserFavorites() {
  const container = document.getElementById("user-favorites-list");
  if (!container) return;

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Loading saved favorites...</span></div>';

  const res = await apiClient.get("/api/user/favorites");
  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load favorites"}</p></div>`;
    return;
  }

  myFavorites = res.data || [];
  if (myFavorites.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No saved favorites yet. Click "+ Bookmark Item" above.</p></div>';
    return;
  }

  container.innerHTML = myFavorites.map(f => `
    <div style="padding: 16px; background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-weight: 700; font-size: 1rem; color: var(--text-main);">⭐ ${escapeHtml(f.title)}</div>
        <code style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(f.url)}</code>
      </div>
      <div style="display:flex; gap: 8px;">
        <a href="${f.url}" class="btn btn-sm btn-outline">Visit Link ↗</a>
        <button class="btn btn-sm btn-danger" onclick="deleteFavorite(${f.id})">🗑️</button>
      </div>
    </div>
  `).join("");
}

window.openNewFavoriteModal = function() {
  document.getElementById("favorite-modal")?.classList.add("active");
};

window.closeNewFavoriteModal = function() {
  document.getElementById("favorite-modal")?.classList.remove("active");
};

async function handleCreateFavorite(e) {
  e.preventDefault();
  const title = document.getElementById("fav-title").value.trim();
  const url = document.getElementById("fav-url").value.trim();
  const category = document.getElementById("fav-category").value;

  if (!title || !url) {
    showToast("Title and URL are required", "error");
    return;
  }

  const res = await apiClient.post("/api/user/favorites", { title, url, category });
  if (res.success) {
    showToast("Bookmark added to favorites", "success");
    closeNewFavoriteModal();
    document.getElementById("new-favorite-form")?.reset();
    loadUserFavorites();
  } else {
    showToast(res.message || "Failed to save favorite", "error");
  }
}

window.deleteFavorite = async function(favId) {
  const confirmed = await confirmAction("Remove from favorites?", "Confirm Delete");
  if (!confirmed) return;
  const res = await apiClient.delete(`/api/user/favorites/${favId}`);
  if (res.success) {
    showToast("Bookmark removed", "success");
    loadUserFavorites();
  }
};

// ----------------------------------------------------
// 9. Support Tickets Section
// ----------------------------------------------------
async function loadUserTickets() {
  const tbody = document.getElementById("user-tickets-table-body");
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading your tickets...</span></td></tr>';

  const res = await apiClient.get("/api/tickets");
  if (!res.success) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load tickets"}</p></td></tr>`;
    return;
  }

  myTickets = res.data || [];
  if (myTickets.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><p>You haven\'t opened any support tickets. Click "+ Open Support Ticket" above.</p></td></tr>';
    return;
  }

  tbody.innerHTML = myTickets.map(t => `
    <tr>
      <td><strong>#${t.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(t.subject)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(t.category)}</small>
      </td>
      <td><span class="badge badge-${t.priority === 'urgent' || t.priority === 'high' ? 'danger' : 'neutral'}">${t.priority}</span></td>
      <td><span class="badge badge-${t.status === 'open' ? 'active' : (t.status === 'resolved' ? 'success' : 'neutral')}">${t.status}</span></td>
      <td><small>${t.created_at}</small></td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="openUserTicketThreadModal(${t.id})">🔍 View Conversation</button>
      </td>
    </tr>
  `).join("");
}

window.openNewTicketModal = function() {
  document.getElementById("new-ticket-modal")?.classList.add("active");
};

window.closeNewTicketModal = function() {
  document.getElementById("new-ticket-modal")?.classList.remove("active");
};

async function handleCreateTicket(e) {
  e.preventDefault();
  const subject = document.getElementById("ticket-subj").value.trim();
  const category = document.getElementById("ticket-cat").value;
  const priority = document.getElementById("ticket-pri").value;
  const message = document.getElementById("ticket-msg").value.trim();

  if (!subject || !message) {
    showToast("Subject and message are required", "error");
    return;
  }

  const res = await apiClient.post("/api/tickets", { subject, category, priority, message });
  if (res.success) {
    showToast("Support ticket opened successfully", "success");
    closeNewTicketModal();
    document.getElementById("new-ticket-form")?.reset();
    loadUserTickets();
  } else {
    showToast(res.message || "Failed to open ticket", "error");
  }
}

window.openUserTicketThreadModal = async function(ticketId) {
  const modal = document.getElementById("user-ticket-thread-modal");
  if (!modal) return;

  const res = await apiClient.get(`/api/tickets/${ticketId}`);
  if (!res.success) {
    showToast(res.message || "Failed to load ticket", "error");
    return;
  }

  const t = res.data;
  document.getElementById("user-thread-subj").textContent = `#${t.id}: ${t.subject}`;
  document.getElementById("user-thread-id").value = t.id;

  const threadContainer = document.getElementById("user-thread-messages");
  let threadHtml = `
    <div style="padding: 14px; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 12px;">
      <div style="display:flex; justify-content:space-between; margin-bottom: 6px;">
        <strong>You (Initial Inquiry)</strong>
        <small style="color:var(--text-muted);">${t.created_at}</small>
      </div>
      <p style="white-space:pre-line; color:var(--text-main); font-size:0.9rem;">${escapeHtml(t.message)}</p>
    </div>
  `;

  if (t.replies && t.replies.length > 0) {
    threadHtml += t.replies.map(r => `
      <div style="padding: 12px 14px; border-radius: 8px; margin-bottom: 10px; border: 1px solid ${r.is_admin ? '#bfdbfe' : 'var(--border-color)'}; background: ${r.is_admin ? '#eff6ff' : '#ffffff'}; margin-left: ${r.is_admin ? '0' : '20px'};">
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
          <strong style="color: ${r.is_admin ? 'var(--primary)' : 'inherit'};">
            ${r.is_admin ? '🛡️ Administrator Support Reply' : '👤 You'}
          </strong>
          <small style="color:var(--text-muted);">${r.created_at}</small>
        </div>
        <p style="white-space:pre-line; font-size:0.875rem; color:var(--text-main);">${escapeHtml(r.message)}</p>
      </div>
    `).join("");
  }

  threadContainer.innerHTML = threadHtml;
  document.getElementById("user-thread-reply-input").value = "";
  modal.classList.add("active");
};

window.closeUserTicketThreadModal = function() {
  document.getElementById("user-ticket-thread-modal")?.classList.remove("active");
};

window.handleSendUserTicketReply = async function(e) {
  e.preventDefault();
  const ticketId = document.getElementById("user-thread-id").value;
  const message = document.getElementById("user-thread-reply-input").value.trim();

  if (!message) {
    showToast("Please enter a reply message", "error");
    return;
  }

  const res = await apiClient.post(`/api/tickets/${ticketId}/reply`, { message });
  if (res.success) {
    showToast("Reply sent", "success");
    openUserTicketThreadModal(ticketId);
    loadUserTickets();
  } else {
    showToast(res.message || "Failed to send reply", "error");
  }
};

// ----------------------------------------------------
// 10. User Settings Section
// ----------------------------------------------------
async function loadUserSettings() {
  const res = await apiClient.get("/api/settings/user");
  if (res.success && res.data) {
    const s = res.data;
    if (document.getElementById("pref-email-notifs")) document.getElementById("pref-email-notifs").checked = s.email_notifications === 1;
    if (document.getElementById("pref-sec-alerts")) document.getElementById("pref-sec-alerts").checked = s.security_alerts === 1;
    if (document.getElementById("pref-digest")) document.getElementById("pref-digest").checked = s.activity_digest === 1;
    if (document.getElementById("pref-lang")) document.getElementById("pref-lang").value = s.language || "en";
    if (document.getElementById("pref-theme")) document.getElementById("pref-theme").value = s.appearance || "light";
  }
}

async function handleSaveUserSettings(e) {
  e.preventDefault();
  const payload = {
    email_notifications: document.getElementById("pref-email-notifs")?.checked ? 1 : 0,
    security_alerts: document.getElementById("pref-sec-alerts")?.checked ? 1 : 0,
    activity_digest: document.getElementById("pref-digest")?.checked ? 1 : 0,
    language: document.getElementById("pref-lang")?.value || "en",
    appearance: document.getElementById("pref-theme")?.value || "light"
  };

  const res = await apiClient.put("/api/settings/user", payload);
  if (res.success) {
    showToast("Preferences saved successfully", "success");
  } else {
    showToast(res.message || "Failed to save preferences", "error");
  }
}

// ----------------------------------------------------
// 11. Security Section
// ----------------------------------------------------
function loadUserSecurity() {
  document.getElementById("user-security-password-form")?.reset();
}

async function handleUserPasswordChange(e) {
  e.preventDefault();
  const current_password = document.getElementById("user-curr-pass").value;
  const new_password = document.getElementById("user-new-pass").value;
  const confirm_password = document.getElementById("user-conf-pass").value;

  if (!current_password || !new_password) {
    showToast("Please enter current and new password", "error");
    return;
  }
  if (new_password.length < 6) {
    showToast("Password must be at least 6 characters long", "error");
    return;
  }
  if (new_password !== confirm_password) {
    showToast("New passwords do not match", "error");
    return;
  }

  const res = await apiClient.put("/api/user/password", { current_password, new_password, confirm_password });
  if (res.success) {
    showToast("Password changed successfully", "success");
    document.getElementById("user-security-password-form")?.reset();
  } else {
    showToast(res.message || "Failed to update password", "error");
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
