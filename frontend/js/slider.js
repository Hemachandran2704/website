/**
 * Magnus Dynamic CMS - Slider Management Admin Controller
 */

let currentItems = [];
let availableImages = [];
let editingItemId = null;
let currentSlideIndex = 0;
let autoSlideInterval = null;

document.addEventListener("DOMContentLoaded", async () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  await loadImagesList();
  await loadSliders();
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
    statusFilter.addEventListener("change", () => loadSliders());
  }

  // Slider prev/next
  const prevBtn = document.getElementById("slider-prev-btn");
  const nextBtn = document.getElementById("slider-next-btn");
  if (prevBtn) prevBtn.addEventListener("click", () => changeSlide(-1));
  if (nextBtn) nextBtn.addEventListener("click", () => changeSlide(1));
}

async function loadImagesList() {
  const res = await apiClient.get("/api/images", { status: "active" });
  if (res.success) {
    availableImages = res.data || [];
    populateImageSelect();
  }
}

function populateImageSelect() {
  const select = document.getElementById("slider-image");
  if (!select) return;
  select.innerHTML = '<option value="">-- Select an Image Asset --</option>';
  availableImages.forEach(img => {
    const opt = document.createElement("option");
    opt.value = img.id;
    opt.textContent = `${img.title} (#${img.id} - ${img.file_path})`;
    select.appendChild(opt);
  });
}

async function loadSliders() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading sliders...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/sliders", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load sliders"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  renderLiveSliderPreview();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      (item.description && item.description.toLowerCase().includes(searchTerm)) ||
      (item.image_title && item.image_title.toLowerCase().includes(searchTerm));
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
          <div class="empty-state-icon">🎞️</div>
          <div class="empty-state-title">No Slider Slides Found</div>
          <p>Click "+ Add Slider Slide" above to create an interactive slide.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(slide => `
    <tr>
      <td><strong>#${slide.id}</strong></td>
      <td style="width: 70px;">
        <img src="${slide.image_url}" alt="${escapeHtml(slide.alt_text || slide.title)}" 
             style="width: 54px; height: 38px; object-fit: cover; border-radius: 4px; border: 1px solid var(--border-color);" 
             onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'54\\' height=\\'38\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'%23f1f5f9\\'/><text x=\\'50%\\' y=\\'50%\\' dominant-baseline=\\'middle\\' text-anchor=\\'middle\\' font-size=\\'10\\' fill=\\'%2394a3b8\\'>Img</text></svg>'"/>
      </td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(slide.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(slide.description || '')}</small>
      </td>
      <td><span style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(slide.image_title || 'Image #' + slide.image_id)}</span></td>
      <td>
        <span class="badge badge-${slide.status}">${slide.status}</span>
        <small style="color: var(--text-light); margin-left: 6px;">Order: ${slide.display_order}</small>
      </td>
      <td><small>${slide.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewSlide(${slide.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${slide.can_manage ? "" : "disabled"} onclick="editSlide(${slide.id})" title="Edit Slide">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${slide.can_manage ? "" : "disabled"} onclick="deleteSlide(${slide.id})" title="Delete Slide">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLiveSliderPreview() {
  const container = document.getElementById("slider-slides-container");
  const dotsContainer = document.getElementById("slider-dots-container");
  if (!container || !dotsContainer) return;

  const activeSlides = currentItems.filter(s => s.status === "active");

  if (activeSlides.length === 0) {
    container.innerHTML = "<div style='padding: 40px; text-align: center; color: var(--text-muted);'>No active slider records found.</div>";
    dotsContainer.innerHTML = "";
    clearInterval(autoSlideInterval);
    return;
  }

  currentSlideIndex = 0;

  container.innerHTML = activeSlides.map((slide, idx) => `
    <div class="slider-slide-item" style="display: ${idx === 0 ? 'block' : 'none'}; position: relative; border-radius: 8px; overflow: hidden; background: #000; height: 320px;">
      <img src="${slide.image_url}" alt="${escapeHtml(slide.alt_text || slide.title)}" 
           style="width: 100%; height: 100%; object-fit: cover; opacity: 0.85;" />
      <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 24px; background: linear-gradient(transparent, rgba(15, 23, 42, 0.9)); color: #ffffff;">
        <h3 style="color: #ffffff; font-size: 1.35rem; margin-bottom: 6px;">${escapeHtml(slide.title)}</h3>
        <p style="color: #e2e8f0; font-size: 0.875rem;">${escapeHtml(slide.description || '')}</p>
      </div>
    </div>
  `).join("");

  dotsContainer.innerHTML = activeSlides.map((_, idx) => `
    <button class="slider-dot-btn ${idx === 0 ? 'active' : ''}" 
            style="width: 10px; height: 10px; border-radius: 50%; border: none; background: ${idx === 0 ? 'var(--primary)' : '#cbd5e1'}; cursor: pointer; transition: var(--transition);" 
            onclick="goToSlide(${idx})"></button>
  `).join("");

  // Auto slide setup
  clearInterval(autoSlideInterval);
  if (activeSlides.length > 1) {
    autoSlideInterval = setInterval(() => {
      changeSlide(1);
    }, 4500);
  }
}

function changeSlide(direction) {
  const activeSlides = currentItems.filter(s => s.status === "active");
  if (activeSlides.length <= 1) return;

  currentSlideIndex = (currentSlideIndex + direction + activeSlides.length) % activeSlides.length;
  updateSlideDisplay();
}

window.goToSlide = function(index) {
  currentSlideIndex = index;
  updateSlideDisplay();
};

function updateSlideDisplay() {
  const slides = document.querySelectorAll(".slider-slide-item");
  const dots = document.querySelectorAll(".slider-dot-btn");

  slides.forEach((slide, idx) => {
    slide.style.display = idx === currentSlideIndex ? "block" : "none";
  });

  dots.forEach((dot, idx) => {
    dot.style.background = idx === currentSlideIndex ? "var(--primary)" : "#cbd5e1";
  });
}

function openModal(slide = null) {
  editingItemId = slide ? slide.id : null;
  populateImageSelect();

  document.getElementById("modal-title").textContent = slide ? "Edit Slider Slide" : "Create New Slider Slide";
  document.getElementById("slider-title").value = slide ? slide.title : "";
  document.getElementById("slider-description").value = slide ? (slide.description || "") : "";
  document.getElementById("slider-image").value = slide ? slide.image_id : "";
  document.getElementById("slider-order").value = slide ? slide.display_order : 0;
  document.getElementById("slider-status").value = slide ? slide.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewSlide = function(id) {
  const slide = currentItems.find(t => t.id === id);
  if (!slide) return;

  document.getElementById("view-slide-img").src = slide.image_url;
  document.getElementById("view-slide-title").textContent = slide.title;
  document.getElementById("view-slide-id").textContent = `#${slide.id}`;
  document.getElementById("view-slide-status").innerHTML = `<span class="badge badge-${slide.status}">${slide.status}</span>`;
  document.getElementById("view-slide-order").textContent = slide.display_order;
  document.getElementById("view-slide-desc").textContent = slide.description || "No description provided.";
  document.getElementById("view-slide-image-ref").textContent = `${slide.image_title || 'Image #' + slide.image_id} (${slide.file_path})`;
  document.getElementById("view-slide-created").textContent = slide.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editSlide = function(id) {
  const slide = currentItems.find(t => t.id === id);
  if (slide) openModal(slide);
};

window.deleteSlide = async function(id) {
  const slide = currentItems.find(t => t.id === id);
  const title = slide ? slide.title : `Slide #${id}`;

  const confirmed = await confirmAction(`Delete slider slide "${title}"?`, "Delete Slide");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/sliders/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete slider slide", "error");
    return;
  }

  showToast("Slide deleted successfully", "success");
  await loadSliders();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const title = document.getElementById("slider-title").value.trim();
  const description = document.getElementById("slider-description").value.trim();
  const image_id = document.getElementById("slider-image").value;
  const display_order = parseInt(document.getElementById("slider-order").value || 0);
  const status = document.getElementById("slider-status").value;

  let hasError = false;
  if (!title) {
    setFieldError("slider-title", "Title is required.");
    hasError = true;
  }
  if (!image_id) {
    setFieldError("slider-image", "Please select an associated image.");
    hasError = true;
  }
  if (hasError) return;

  const payload = {
    title,
    description,
    image_id: parseInt(image_id),
    display_order,
    status
  };

  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/sliders/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/sliders", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Slide";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`slider-${key}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save slide", "error");
    return;
  }

  showToast(editingItemId ? "Slide updated successfully" : "Slide created successfully", "success");
  closeModal();
  await loadSliders();
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
