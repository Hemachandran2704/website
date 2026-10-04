/**
 * Magnus Dynamic CMS - iFrames Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadiFrames();
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById("btn-add-new").addEventListener("click", () => openModal());
  document.getElementById("modal-close-btn").addEventListener("click", () => closeModal());
  document.getElementById("modal-cancel-btn").addEventListener("click", () => closeModal());
  document.getElementById("view-modal-close-btn").addEventListener("click", () => closeViewModal());

  document.getElementById("item-form").addEventListener("submit", handleFormSubmit);

  const searchInput = document.getElementById("table-search");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => filterAndRender(), 200);
    });
  }

  const statusFilter = document.getElementById("status-filter");
  if (statusFilter) {
    statusFilter.addEventListener("change", () => loadiFrames());
  }
}

async function loadiFrames() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading iframes...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/iframes", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load iframes"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLiveIframePreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      item.url.toLowerCase().includes(searchTerm);
  });

  renderTable(filtered);
}

function renderTable(items) {
  const tableBody = document.getElementById("table-body");
  const countEl = document.getElementById("table-record-count");
  if (countEl) countEl.textContent = `Showing ${items.length} records`;

  if (items.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">
          <div class="empty-state-icon">🖥️</div>
          <div class="empty-state-title">No iFrames Found</div>
          <p>Click "+ Add iFrame" above to configure responsive embed frames.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(frame => `
    <tr>
      <td><strong>#${frame.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(frame.title)}</div>
        <small style="color: var(--text-muted);">${frame.width} &times; ${frame.height}</small>
      </td>
      <td>
        <code style="font-size: 0.8rem;">${escapeHtml(frame.url.substring(0, 45))}${frame.url.length > 45 ? '...' : ''}</code>
      </td>
      <td>
        <span class="badge" style="background: ${frame.allow_fullscreen ? '#dcfce7' : '#f1f5f9'}; color: ${frame.allow_fullscreen ? '#166534' : '#64748b'};">
          ${frame.allow_fullscreen ? 'Fullscreen' : 'No Fullscreen'}
        </span>
      </td>
      <td>
        <span class="badge badge-${frame.status}">${frame.status}</span>
      </td>
      <td><small>${frame.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewIframe(${frame.id})" title="View Frame">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${frame.can_manage ? "" : "disabled"} onclick="editIframe(${frame.id})" title="Edit Frame">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${frame.can_manage ? "" : "disabled"} onclick="deleteIframe(${frame.id})" title="Delete Frame">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLiveIframePreview() {
  const container = document.getElementById("preview-iframe-container");
  if (!container) return;

  const activeFrames = currentItems.filter(f => f.status === "active");

  if (activeFrames.length === 0) {
    container.innerHTML = "<p style='color: var(--text-muted);'>No active iframe embeds to preview.</p>";
    return;
  }

  const frame = activeFrames[0];

  container.innerHTML = `
    <div style="border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; background: #ffffff;">
      <div style="padding: 10px 16px; background: #f8fafc; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between;">
        <span style="font-weight: 600; font-size: 0.85rem;">${escapeHtml(frame.title)}</span>
        <code style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(frame.url)}</code>
      </div>
      <iframe src="${escapeHtml(frame.url)}" 
              width="${frame.width || '100%'}" 
              height="${frame.height || '380px'}" 
              ${frame.allow_fullscreen ? 'allowfullscreen' : ''} 
              style="border: none; display: block;"
              loading="lazy"
              sandbox="allow-scripts allow-same-origin allow-popups allow-forms">
      </iframe>
    </div>
  `;
}

function openModal(frame = null) {
  editingItemId = frame ? frame.id : null;
  document.getElementById("modal-title").textContent = frame ? "Edit iFrame Embed" : "Create New iFrame Embed";
  document.getElementById("iframe-title").value = frame ? frame.title : "";
  document.getElementById("iframe-url").value = frame ? frame.url : "";
  document.getElementById("iframe-width").value = frame ? frame.width : "100%";
  document.getElementById("iframe-height").value = frame ? frame.height : "400px";
  document.getElementById("iframe-fullscreen").checked = frame ? Boolean(frame.allow_fullscreen) : true;
  document.getElementById("iframe-status").value = frame ? frame.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewIframe = function(id) {
  const frame = currentItems.find(t => t.id === id);
  if (!frame) return;

  document.getElementById("view-iframe-title").textContent = frame.title;
  document.getElementById("view-iframe-id").textContent = `#${frame.id}`;
  document.getElementById("view-iframe-url").textContent = frame.url;
  document.getElementById("view-iframe-dims").textContent = `${frame.width} × ${frame.height}`;
  document.getElementById("view-iframe-status").innerHTML = `<span class="badge badge-${frame.status}">${frame.status}</span>`;
  document.getElementById("view-iframe-fullscreen").textContent = frame.allow_fullscreen ? "Allowed" : "Disabled";
  document.getElementById("view-iframe-created").textContent = frame.created_at;

  const viewFrameEl = document.getElementById("view-iframe-preview");
  viewFrameEl.src = frame.url;
  viewFrameEl.width = frame.width || "100%";
  viewFrameEl.height = frame.height || "350px";

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  const viewFrameEl = document.getElementById("view-iframe-preview");
  if (viewFrameEl) viewFrameEl.src = "";
  document.getElementById("view-modal").classList.remove("active");
}

window.editIframe = function(id) {
  const frame = currentItems.find(t => t.id === id);
  if (frame) openModal(frame);
};

window.deleteIframe = async function(id) {
  const frame = currentItems.find(t => t.id === id);
  const title = frame ? frame.title : `iFrame #${id}`;

  const confirmed = await confirmAction(`Delete iframe embed "${title}"?`, "Delete iFrame");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/iframes/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete iframe", "error");
    return;
  }

  showToast("iFrame deleted successfully", "success");
  await loadiFrames();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const title = document.getElementById("iframe-title").value.trim();
  const url = document.getElementById("iframe-url").value.trim();
  const width = document.getElementById("iframe-width").value.trim() || "100%";
  const height = document.getElementById("iframe-height").value.trim() || "400px";
  const allow_fullscreen = document.getElementById("iframe-fullscreen").checked ? 1 : 0;
  const status = document.getElementById("iframe-status").value;

  let hasError = false;
  if (!title) {
    setFieldError("iframe-title", "Title is required.");
    hasError = true;
  }
  if (!url) {
    setFieldError("iframe-url", "iFrame URL is required.");
    hasError = true;
  } else if (!url.startsWith("https://") && !url.startsWith("/")) {
    setFieldError("iframe-url", "Only secure HTTPS URLs or safe local paths are permitted for iframes.");
    hasError = true;
  }
  if (hasError) return;

  const payload = { title, url, width, height, allow_fullscreen, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/iframes/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/iframes", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save iFrame";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`iframe-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save iframe", "error");
    return;
  }

  showToast(editingItemId ? "iFrame updated successfully" : "iFrame created successfully", "success");
  closeModal();
  await loadiFrames();
}

function setFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  if (field) {
    field.classList.add("is-invalid");
    const errSpan = document.getElementById(`${fieldId}-error`);
    if (errSpan) errSpan.textContent = message;
  }
}

function clearFormErrors() {
  document.querySelectorAll(".form-control").forEach(el => el.classList.remove("is-invalid"));
  document.querySelectorAll(".form-error").forEach(el => el.textContent = "");
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
