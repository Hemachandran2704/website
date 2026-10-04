/**
 * Magnus Dynamic CMS - CSS Properties Admin Controller
 */

let currentItems = [];
let editingItemId = null;

const ALLOWED_CSS_PROPERTIES = [
  "font-size",
  "font-weight",
  "color",
  "background-color",
  "border-radius",
  "padding",
  "margin",
  "width",
  "height",
  "opacity",
  "display",
  "text-align"
];

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.checkAuth()) return;
  Auth.initSidebar();

  populateAllowedPropertiesDropdown();
  loadCssProperties();
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
    statusFilter.addEventListener("change", () => loadCssProperties());
  }
}

function populateAllowedPropertiesDropdown() {
  const select = document.getElementById("css-property-name");
  if (!select) return;
  select.innerHTML = '<option value="">-- Select Whitelisted Property --</option>';
  ALLOWED_CSS_PROPERTIES.forEach(prop => {
    const opt = document.createElement("option");
    opt.value = prop;
    opt.textContent = prop;
    select.appendChild(opt);
  });
}

async function loadCssProperties() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="6" class="loading-container"><span class="spinner"></span><span>Loading CSS rules...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/css-properties", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="6" class="empty-state"><p>${res.message || "Failed to load CSS properties"}</p></td></tr>`;
    return;
  }

  currentItems = res.data || [];
  filterAndRender();
  applyDynamicStylesLive();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();
  const filtered = currentItems.filter(item => {
    return !searchTerm ||
      item.property_name.toLowerCase().includes(searchTerm) ||
      item.property_value.toLowerCase().includes(searchTerm) ||
      item.selector.toLowerCase().includes(searchTerm);
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
        <td colspan="6" class="empty-state">
          <div class="empty-state-icon">🎨</div>
          <div class="empty-state-title">No CSS Properties Found</div>
          <p>Click "+ Add CSS Property" above to define safe styling rules.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(prop => `
    <tr>
      <td><strong>#${prop.id}</strong></td>
      <td><code>${escapeHtml(prop.selector)}</code></td>
      <td>
        <span style="font-weight: 600; color: var(--primary);">${escapeHtml(prop.property_name)}</span>
      </td>
      <td><code>${escapeHtml(prop.property_value)}</code></td>
      <td>
        <span class="badge badge-${prop.status}">${prop.status}</span>
      </td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="viewProperty(${prop.id})" title="View Details">👁️ View</button>
          <button class="btn btn-sm btn-action-edit" ${prop.can_manage ? "" : "disabled"} onclick="editProperty(${prop.id})" title="Edit Property">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" ${prop.can_manage ? "" : "disabled"} onclick="deleteProperty(${prop.id})" title="Delete Property">🗑️ Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function applyDynamicStylesLive() {
  let styleTag = document.getElementById("dynamic-cms-styles");
  if (!styleTag) {
    styleTag = document.createElement("style");
    styleTag.id = "dynamic-cms-styles";
    document.head.appendChild(styleTag);
  }

  const activeProps = currentItems.filter(p => p.status === "active");
  const rules = activeProps.map(p => {
    return `${p.selector} { ${p.property_name}: ${p.property_value} !important; }`;
  }).join("\n");

  styleTag.textContent = rules;
}

function openModal(prop = null) {
  editingItemId = prop ? prop.id : null;
  document.getElementById("modal-title").textContent = prop ? "Edit CSS Property" : "Add CSS Property";
  document.getElementById("css-selector").value = prop ? prop.selector : "";
  document.getElementById("css-property-name").value = prop ? prop.property_name : "";
  document.getElementById("css-property-value").value = prop ? prop.property_value : "";
  document.getElementById("css-status").value = prop ? prop.status : "active";

  clearFormErrors();
  document.getElementById("crud-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingItemId = null;
}

window.viewProperty = function(id) {
  const prop = currentItems.find(t => t.id === id);
  if (!prop) return;

  document.getElementById("view-css-selector").textContent = prop.selector;
  document.getElementById("view-css-id").textContent = `#${prop.id}`;
  document.getElementById("view-css-prop").textContent = prop.property_name;
  document.getElementById("view-css-val").textContent = prop.property_value;
  document.getElementById("view-css-status").innerHTML = `<span class="badge badge-${prop.status}">${prop.status}</span>`;
  document.getElementById("view-css-rule").textContent = `${prop.selector} {\n  ${prop.property_name}: ${prop.property_value};\n}`;
  document.getElementById("view-css-created").textContent = prop.created_at;

  document.getElementById("view-modal").classList.add("active");
};

function closeViewModal() {
  document.getElementById("view-modal").classList.remove("active");
}

window.editProperty = function(id) {
  const prop = currentItems.find(t => t.id === id);
  if (prop) openModal(prop);
};

window.deleteProperty = async function(id) {
  const prop = currentItems.find(t => t.id === id);
  const name = prop ? `${prop.selector} { ${prop.property_name} }` : `Property #${id}`;

  const confirmed = await confirmAction(`Delete CSS rule "${name}"?`, "Delete CSS Property");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/css-properties/${id}`);
  if (!res.success) {
    showToast(res.message || "Failed to delete property", "error");
    return;
  }

  showToast("Property deleted successfully", "success");
  await loadCssProperties();
};

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const selector = document.getElementById("css-selector").value.trim();
  const property_name = document.getElementById("css-property-name").value.trim();
  const property_value = document.getElementById("css-property-value").value.trim();
  const status = document.getElementById("css-status").value;

  let hasError = false;
  if (!selector) {
    setFieldError("css-selector", "Selector is required (e.g. .dynamic-card).");
    hasError = true;
  }
  if (!property_name) {
    setFieldError("css-property-name", "Property name is required.");
    hasError = true;
  }
  if (!property_value) {
    setFieldError("css-property-value", "Property value is required (e.g. 12px or #f00).");
    hasError = true;
  }
  if (hasError) return;

  const payload = { selector, property_name, property_value, status };
  const submitBtn = document.getElementById("modal-submit-btn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px;"></span> Saving...';

  let res;
  if (editingItemId) {
    res = await apiClient.put(`/api/css-properties/${editingItemId}`, payload);
  } else {
    res = await apiClient.post("/api/css-properties", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Property";

  if (!res.success) {
    if (res.errors) {
      Object.keys(res.errors).forEach(key => {
        setFieldError(`css-${key.replace('_', '-')}`, res.errors[key]);
      });
    }
    showToast(res.message || "Failed to save CSS property", "error");
    return;
  }

  showToast(editingItemId ? "CSS property updated successfully" : "CSS property created successfully", "success");
  closeModal();
  await loadCssProperties();
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
