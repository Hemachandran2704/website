/**
 * Magnus Dynamic CMS - Image Management Admin Controller
 */

let currentItems = [];
let editingItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  loadImages();
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById("btn-add-new").addEventListener("click", () => openModal());
  document.getElementById("modal-close-btn").addEventListener("click", () => closeModal());
  document.getElementById("modal-cancel-btn").addEventListener("click", () => closeModal());
  document.getElementById("view-modal-close-btn").addEventListener("click", () => closeViewModal());

  document.getElementById("item-form").addEventListener("submit", handleFormSubmit);

  // File input change preview
  const fileInput = document.getElementById("image-file");
  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      const previewImg = document.getElementById("file-preview-img");
      const previewText = document.getElementById("file-upload-prompt-text");
      if (file) {
        const reader = new FileReader();
        reader.onload = (re) => {
          previewImg.src = re.target.result;
          previewImg.style.display = "block";
          if (previewText) previewText.textContent = `Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
        };
        reader.readAsDataURL(file);
      }
    });
  }

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
    statusFilter.addEventListener("change", () => loadImages());
  }
}

async function loadImages() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading image gallery...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/images", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load images"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLiveGalleryPreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      (item.description && item.description.toLowerCase().includes(searchTerm)) ||
      (item.category && item.category.toLowerCase().includes(searchTerm)) ||
      (item.alt_text && item.alt_text.toLowerCase().includes(searchTerm));
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
          <div class="empty-state-icon">🖼️</div>
          <div class="empty-state-title">No Images Found</div>
          <p>Click "+ Upload New Image" above to add image assets to your repository.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(img => `
    <tr>
      <td><strong>#${img.id}</strong></td>
      <td style="width: 70px;">
        <img src="${img.image_url}" alt="${escapeHtml(img.alt_text || img.title)}" 
             style="width: 54px; height: 38px; object-fit: cover; border-radius: 4px; border: 1px solid var(--border-color);" 
             onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'54\\' height=\\'38\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'%23f1f5f9\\'/><text x=\\'50%\\' y=\\'50%\\' dominant-baseline=\\'middle\\' text-anchor=\\'middle\\' font-size=\\'10\\' fill=\\'%2394a3b8\\'>Img</text></svg>'"/>
      </td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(img.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(img.alt_text || 'No alt text')}</small>
      </td>
      <td><span class="badge" style="background: #f1f5f9; color: #475569;">${escapeHtml(img.category || 'General')}</span></td>
      <td>
        <span class="badge badge-${img.status}">${img.status}</span>
      </td>
      <td><small>${img.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewImage(${img.id})" title="View Image">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${img.can_manage ? "" : "disabled"} onclick="editImage(${img.id})" title="Edit Details">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${img.can_manage ? "" : "disabled"} onclick="deleteImage(${img.id})" title="Delete Image">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLiveGalleryPreview() {
  const gallery = document.getElementById("preview-image-gallery");
  if (!gallery) return;

  const activeImages = currentItems.filter(i => i.status === "active");

  if (activeImages.length === 0) {
    gallery.innerHTML = "<p style='color: var(--text-muted);'>No active images available in library.</p>";
    return;
  }

  gallery.innerHTML = activeImages.map(img => `
    <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; box-shadow: var(--shadow-sm);">
      <img src="${img.image_url}" alt="${escapeHtml(img.alt_text || img.title)}" 
           style="width: 100%; height: 120px; object-fit: cover;" />
      <div style="padding: 10px;">
        <div style="font-weight: 600; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(img.title)}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(img.category || 'General')}</div>
      </div>
    </div>
  `).join("");
}

function openModal(img = null) {
  editingItemId = img ? img.id : null;
  document.getElementById("modal-title").textContent = img ? "Edit Image Metadata" : "Upload New Image";
  document.getElementById("image-title").value = img ? img.title : "";
  document.getElementById("image-description").value = img ? (img.description || "") : "";
  document.getElementById("image-alt-text").value = img ? (img.alt_text || "") : "";
  document.getElementById("image-category").value = img ? (img.category || "General") : "General";
  document.getElementById("image-status").value = img ? img.status : "active";

  const previewImg = document.getElementById("file-preview-img");
  const promptText = document.getElementById("file-upload-prompt-text");
  const fileInput = document.getElementById("image-file");
  fileInput.value = "";

  if (img) {
    previewImg.src = img.image_url;
    previewImg.style.display = "block";
    promptText.textContent = "Click to select a replacement image (or keep current)";
  } else {
    previewImg.src = "";
    previewImg.style.display = "none";
    promptText.textContent = "Click to browse or drop image here (JPG, PNG, WebP up to 5MB)";
  }

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewImage = function(id) {
  const img = currentItems.find(t => t.id === id);
  if (!img) return;

  document.getElementById("view-image-preview").src = img.image_url;
  document.getElementById("view-image-title").textContent = img.title;
  document.getElementById("view-image-id").textContent = `#${img.id}`;
  document.getElementById("view-image-category").textContent = img.category || "General";
  document.getElementById("view-image-alt").textContent = img.alt_text || "None";
  document.getElementById("view-image-path").textContent = img.file_path;
  document.getElementById("view-image-status").innerHTML = `<span class="badge badge-${img.status}">${img.status}</span>`;
  document.getElementById("view-image-desc").textContent = img.description || "No description provided.";
  document.getElementById("view-image-created").textContent = img.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editImage = function(id) {
  const img = currentItems.find(t => t.id === id);
  if (img) openModal(img);
};

window.deleteImage = async function(id) {
  const img = currentItems.find(t => t.id === id);
  const title = img ? img.title : `Image #${id}`;

  const confirmed = await confirmAction(`Delete image "${title}" and its local file? Any sliders referencing this image may be affected.`, "Delete Image");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/images/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete image", "error");
    return;
  }

  showToast("Image deleted successfully", "success");
  await loadImages();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const title = document.getElementById("image-title").value.trim();
  const description = document.getElementById("image-description").value.trim();
  const alt_text = document.getElementById("image-alt-text").value.trim();
  const category = document.getElementById("image-category").value.trim();
  const status = document.getElementById("image-status").value;
  const fileInput = document.getElementById("image-file");

  let hasError = false;
  if (!title) {
    setFieldError("image-title", "Title is required.");
    hasError = true;
  }

  if (!editingItemId && (!fileInput.files || fileInput.files.length === 0)) {
    setFieldError("image-file", "Please select an image file to upload.");
    hasError = true;
  }
  if (hasError) return;

  const formData = new FormData();
  formData.append("title", title);
  formData.append("description", description);
  formData.append("alt_text", alt_text);
  formData.append("category", category);
  formData.append("status", status);

  if (fileInput.files && fileInput.files[0]) {
    formData.append("image_file", fileInput.files[0]);
  }

  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Uploading...';

  let res;
  if (editingItemId) {
    res = await apiClient.upload(`/api/images/${editingItemId}`, formData, "PUT");
  } else {
    res = await apiClient.upload("/api/images", formData, "POST");
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Image";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`image-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save image", "error");
    return;
  }

  showToast(editingItemId ? "Image metadata updated successfully" : "Image uploaded successfully", "success");
  closeModal();
  await loadImages();
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
