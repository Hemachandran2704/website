/**
 * Magnus Dynamic CMS - Reports Controller
 */

let currentReportData = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.requireAdmin()) return;
  Auth.initSidebar();

  loadReportsSummary();
  document.getElementById("btn-refresh-reports")?.addEventListener("click", loadReportsSummary);
  document.getElementById("reports-filter-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    loadReportsSummary();
  });
  document.getElementById("report-range")?.addEventListener("change", toggleCustomReportDates);
  document.getElementById("report-activity-search")?.addEventListener("input", filterRecentActivities);
  document.getElementById("btn-export-report")?.addEventListener("click", exportReportCsv);
});

function toggleCustomReportDates() {
  const customDates = document.getElementById("report-custom-dates");
  if (customDates) {
    customDates.style.display = document.getElementById("report-range").value === "custom" ? "flex" : "none";
  }
}

async function loadReportsSummary() {
  const statsContainer = document.getElementById("reports-stats-grid");
  const notifContainer = document.getElementById("notif-type-breakdown-container");
  const actionContainer = document.getElementById("action-breakdown-container");
  const recentTableBody = document.getElementById("recent-activities-table-body");

  const range = document.getElementById("report-range")?.value || "all";
  const params = { range };
  if (range === "custom") {
    const startDate = document.getElementById("report-start-date")?.value || "";
    const endDate = document.getElementById("report-end-date")?.value || "";
    if (!startDate || (endDate && endDate < startDate)) {
      showToast("Choose a valid custom date range.", "error");
      return;
    }
    params.start_date = startDate;
    params.end_date = endDate;
  }

  const res = await apiClient.get("/api/reports/summary", params);
  if (!res.success) {
    showToast(res.message || "Failed to load database reports", "error");
    return;
  }

  const data = res.data || {};
  currentReportData = data;

  // 1. Render Metrics Cards
  const cards = [
    { label: "Total Users", count: data.total_users || 0, icon: "👥", color: "blue" },
    { label: "Total Content", count: data.total_content || 0, icon: "📝", color: "indigo" },
    { label: "Total Media", count: data.total_media || 0, icon: "📁", color: "purple" },
    { label: "Total Forms", count: data.total_forms || 0, icon: "📋", color: "green" },
    { label: "Form Submissions", count: data.total_form_submissions || 0, icon: "📥", color: "amber" },
    { label: "Total Notifications", count: data.total_notifications || 0, icon: "🔔", color: "rose" },
    { label: "Total Tabs", count: data.total_tabs || 0, icon: "📑", color: "cyan" },
    { label: "Activity Logs", count: data.total_activity_logs || 0, icon: "📜", color: "blue" }
  ];

  statsContainer.innerHTML = cards.map(c => `
    <div class="stat-card">
      <div class="stat-icon stat-icon-${c.color}">
        <span>${c.icon}</span>
      </div>
      <div class="stat-details">
        <span class="stat-count">${c.count}</span>
        <span class="stat-label">${c.label}</span>
      </div>
    </div>
  `).join("");

  // 2. Render Notification Type Breakdown
  const notifs = data.notification_type_breakdown || [];
  if (notifs.length === 0) {
    notifContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No notifications recorded.</p>';
  } else {
    notifContainer.innerHTML = `
      <table style="width: 100%; border-collapse: collapse; font-size: 0.875rem;">
        <tbody>
          ${notifs.map(n => `
            <tr style="border-bottom: 1px solid var(--border-color);">
              <td style="padding: 8px 0; text-transform: capitalize; font-weight: 600;">${escapeHtml(n.type)}</td>
              <td style="padding: 8px 0; text-align: right;"><span class="badge" style="background:#f1f5f9; color:#334155;">${n.count} entries</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  // 3. Render Action Breakdown
  const actions = data.action_breakdown || [];
  if (actions.length === 0) {
    actionContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No actions recorded.</p>';
  } else {
    actionContainer.innerHTML = `
      <table style="width: 100%; border-collapse: collapse; font-size: 0.875rem;">
        <tbody>
          ${actions.map(a => `
            <tr style="border-bottom: 1px solid var(--border-color);">
              <td style="padding: 8px 0; font-weight: 600;">${escapeHtml(a.action)}</td>
              <td style="padding: 8px 0; text-align: right;"><span class="badge badge-active">${a.count} actions</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  // 4. Render Recent Activities Table
  const recents = data.recent_activities || [];
  if (recents.length === 0) {
    recentTableBody.innerHTML = '<tr><td colspan="6" class="empty-state"><p>No recent activity logs.</p></td></tr>';
  } else {
    recentTableBody.innerHTML = recents.map(r => `
      <tr>
        <td><strong>#${r.id}</strong></td>
        <td><span class="badge badge-active">${escapeHtml(r.action)}</span></td>
        <td><span style="font-weight: 600; color: #475569;">[${escapeHtml(r.module)}]</span></td>
        <td>${escapeHtml(r.description || "System action")}</td>
        <td><small style="font-weight: 600;">${escapeHtml(r.user_name || "System")}</small></td>
        <td><small style="color: var(--text-light);">${r.created_at}</small></td>
      </tr>
    `).join("");
  }
  filterRecentActivities();
}

function filterRecentActivities() {
  const query = (document.getElementById("report-activity-search")?.value || "").trim().toLowerCase();
  document.querySelectorAll("#recent-activities-table-body tr").forEach(row => {
    row.hidden = !row.textContent.toLowerCase().includes(query);
  });
}

function exportReportCsv() {
  if (!currentReportData) {
    showToast("There is no report data to export.", "error");
    return;
  }

  const rows = [["Metric", "Value"]];
  [
    ["Total Users", "total_users"],
    ["New Users", "new_users"],
    ["Active Users", "active_users"],
    ["Inactive Users", "inactive_users"],
    ["Total Content", "total_content"],
    ["Total Media", "total_media"],
    ["Total Forms", "total_forms"],
    ["Form Submissions", "total_form_submissions"],
    ["Total Notifications", "total_notifications"],
    ["Activity Logs", "total_activity_logs"]
  ].forEach(([label, key]) => rows.push([label, currentReportData[key] ?? 0]));

  rows.push([], ["Notification Type", "Count"]);
  (currentReportData.notification_type_breakdown || []).forEach(item => rows.push([item.type, item.count]));
  rows.push([], ["Action", "Count"]);
  (currentReportData.action_breakdown || []).forEach(item => rows.push([item.action, item.count]));
  rows.push([], ["Recent Activity ID", "Action", "Module", "Description", "User", "Date"]);
  (currentReportData.recent_activities || []).forEach(item => {
    rows.push([item.id, item.action, item.module, item.description || "", item.user_name || "System", item.created_at]);
  });

  const csv = rows.map(row => row.map(value => `"${String(value ?? "").replace(/"/g, '""')}"`).join(",")).join("\r\n");
  const blobUrl = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = `magnus-report-${document.getElementById("report-range")?.value || "all"}.csv`;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
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
