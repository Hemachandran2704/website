/**
 * Magnus Dynamic CMS - Media Manager Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.requireAdmin()) return;
  Auth.initSidebar();

  loadMedia();
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
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => filterAndRender(), 200);
    });
  }

  const categoryFilter = document.getElementById("category-filter");
  if (categoryFilter) {
    categoryFilter.addEventListener("change", () => filterAndRender());
  }

  const statusFilter = document.getElementById("status-filter");
  if (statusFilter) {
    statusFilter.addEventListener("change", () => loadMedia());
  }
}

async function loadMedia() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="8" class="loading-container"><span class="spinner"></span><span>Loading media assets...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/media", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="8" class="empty-state"><p>${res.message || "Failed to load media"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const category = (document.getElementById("category-filter")?.value || "all").toLowerCase();

  const filtered = currentItems.filter(item => {
    const matchSearch = !searchTerm ||
      item.file_name.toLowerCase().includes(searchTerm) ||
      (item.description && item.description.toLowerCase().includes(searchTerm)) ||
      (item.category && item.category.toLowerCase().includes(searchTerm));
    
    const matchCategory = category === "all" || (item.category && item.category.toLowerCase() === category);
    return matchSearch && matchCategory;
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
        <td colspan="8" class="empty-state">
          <div class="empty-state-icon">📁</div>
          <div class="empty-state-title">No Media Assets Found</div>
          <p>Click "Upload Media Asset" above to store your files in the system.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(item => `
    <tr>
      <td><strong>#${item.id}</strong></td>
      <td>
        <img src="${item.url}" alt="${escapeHtml(item.file_name)}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; border: 1px solid var(--border-color); background: #f8fafc;" onerror="this.src='/uploads/sample_cloud.webp'">
      </td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(item.file_name)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(item.description || "—")}</small>
      </td>
      <td><code>${escapeHtml(item.file_type || "image")}</code></td>
      <td><span class="badge" style="background:#f1f5f9; color:#334155;">${escapeHtml(item.category || "General")}</span></td>
      <td><span class="badge badge-${item.status}">${item.status}</span></td>
      <td><small>${item.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewMedia(${item.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" onclick="editMedia(${item.id})" title="Edit Metadata">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" onclick="deleteMedia(${item.id}, '${escapeHtml(item.file_name)}')" title="Delete">🗑️</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function openModal(item = null) {
  editingItemId = item ? item.id : null;
  const modal = document.getElementById("crud-modal");
  const titleEl = document.getElementById("modal-title");
  const errorEl = document.getElementById("form-error");
  const fileReq = document.getElementById("file-required-mark");

  errorEl.style.display = "none";
  errorEl.textContent = "";

  if (item) {
    titleEl.textContent = `Edit Media Metadata #${item.id}`;
    document.getElementById("media-name").value = item.file_name;
    document.getElementById("media-category").value = item.category || "General";
    document.getElementById("media-desc").value = item.description || "";
    document.getElementById("media-status").value = item.status;
    fileReq.style.display = "none";
  } else {
    titleEl.textContent = "Upload Media Asset";
    document.getElementById("item-form").reset();
    document.getElementById("media-category").value = "General";
    document.getElementById("media-status").value = "active";
    fileReq.style.display = "inline";
  }

  modal.classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const errorEl = document.getElementById("form-error");
  const submitBtn = document.getElementById("modal-submit-btn");
  const fileInput = document.getElementById("media-file");

  errorEl.style.display = "none";

  if (!editingItemId && (!fileInput.files || fileInput.files.length === 0)) {
    errorEl.textContent = "Please select a file to upload.";
    errorEl.style.display = "block";
    return;
  }

  const formData = new FormData();
  if (fileInput.files && fileInput.files.length > 0) {
    formData.append("media_file", fileInput.files[0]);
  }
  
  formData.append("file_name", document.getElementById("media-name").value.trim());
  formData.append("category", document.getElementById("media-category").value.trim() || "General");
  formData.append("description", document.getElementById("media-desc").value.trim());
  formData.append("status", document.getElementById("media-status").value);

  submitBtn.disabled = true;
  submitBtn.textContent = "Uploading / Saving...";

  let res;
  if (editingItemId) {
    res = await apiClient.upload(`/api/media/${editingItemId}`, formData, "PUT");
  } else {
    res = await apiClient.upload("/api/media", formData);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Media";

  if (!res.success) {
    errorEl.textContent = res.message || "Operation failed.";
    errorEl.style.display = "block";
    return;
  }

  showToast(editingItemId ? "Media metadata updated!" : "Media asset uploaded successfully!", "success");
  closeModal();
  await loadMedia();
}

function viewMedia(id) {
  const item = currentItems.find(i => i.id === id);
  if (!item) return;

  const modal = document.getElementById("view-modal");
  const body = document.getElementById("view-modal-body");
  document.getElementById("view-modal-title").textContent = `Media #${item.id}: ${item.file_name}`;

  body.innerHTML = `
    <div style="text-align: center; margin-bottom: 20px; background: #0f172a; padding: 16px; border-radius: 8px;">
      <img src="${item.url}" alt="${escapeHtml(item.file_name)}" style="max-height: 240px; max-width: 100%; object-fit: contain;" onerror="this.src='/uploads/sample_cloud.webp'">
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">File Name</span>
      <span class="view-detail-value font-weight-bold">${escapeHtml(item.file_name)}</span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Direct URL</span>
      <span class="view-detail-value"><a href="${item.url}" target="_blank" style="color: var(--primary);">${item.url}</a></span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Category</span>
      <span class="view-detail-value"><span class="badge" style="background:#f1f5f9; color:#334155;">${escapeHtml(item.category || "General")}</span></span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">File Type / Status</span>
      <span class="view-detail-value">
        <code>${escapeHtml(item.file_type || "image")}</code>
        <span class="badge badge-${item.status}" style="margin-left: 8px;">${item.status}</span>
      </span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Description</span>
      <span class="view-detail-value">${escapeHtml(item.description || "—")}</span>
    </div>
    <div class="view-detail-row">
      <span class="view-detail-label">Uploaded Date</span>
      <span class="view-detail-value">${item.created_at}</span>
    </div>
  `;

  modal.classList.add("active");
}

function editMedia(id) {
  const item = currentItems.find(i => i.id === id);
  if (item) openModal(item);
}

async function deleteMedia(id, fileName) {
  const confirmed = await confirmAction(
    `Are you sure you want to permanently delete media asset "${fileName}" (#${id})?`,
    "Delete Media"
  );
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/media/${id}`);
  if (res.success) {
    showToast("Media asset deleted successfully.", "success");
    await loadMedia();
  } else {
    showToast(res.message || "Failed to delete media asset.", "error");
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
