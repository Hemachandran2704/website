/**
 * Magnus Dynamic CMS - Form Manager Controller
 */

let currentForms = [];
let editingFormId = null;
let activeTestingFormId = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!Auth.requireAdmin()) return;
  Auth.initSidebar();

  loadForms();
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById("btn-add-new").addEventListener("click", () => openModal());
  document.getElementById("modal-close-btn").addEventListener("click", () => closeModal());
  document.getElementById("modal-cancel-btn").addEventListener("click", () => closeModal());
  document.getElementById("btn-add-field").addEventListener("click", () => addFieldRow());

  document.getElementById("btn-view-all-subs").addEventListener("click", () => viewSubmissions(null));
  document.getElementById("submissions-modal-close-btn").addEventListener("click", () => closeSubmissionsModal());
  document.getElementById("preview-modal-close-btn").addEventListener("click", () => closePreviewModal());

  document.getElementById("item-form").addEventListener("submit", handleFormSubmit);
  document.getElementById("public-submit-form").addEventListener("submit", handleTestFormSubmit);

  const searchInput = document.getElementById("table-search");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => filterAndRender(), 200);
    });
  }

  const statusFilter = document.getElementById("status-filter");
  if (statusFilter) {
    statusFilter.addEventListener("change", () => loadForms());
  }
}

async function loadForms() {
  const tableBody = document.getElementById("table-body");
  tableBody.innerHTML = '<tr><td colspan="7" class="loading-container"><span class="spinner"></span><span>Loading dynamic forms...</span></td></tr>';

  const status = document.getElementById("status-filter").value;
  const res = await apiClient.get("/api/forms", { status });

  if (!res.success) {
    tableBody.innerHTML = `<tr><td colspan="7" class="empty-state"><p>${res.message || "Failed to load forms"}</p></td></tr>`;
    return;
  }

  currentForms = res.data || [];
  filterAndRender();
}

function filterAndRender() {
  const searchTerm = (document.getElementById("table-search")?.value || "").toLowerCase().trim();

  const filtered = currentForms.filter(item => {
    return !searchTerm ||
      item.title.toLowerCase().includes(searchTerm) ||
      (item.description && item.description.toLowerCase().includes(searchTerm));
  });

  renderTable(filtered);
}

function renderTable(items) {
  const tableBody = document.getElementById("table-body");
  const countEl = document.getElementById("table-record-count");
  if (countEl) countEl.textContent = `Showing ${items.length} forms`;

  if (items.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-title">No Dynamic Forms Found</div>
          <p>Click "+ Create New Form" above to build your first dynamic form.</p>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(form => `
    <tr>
      <td><strong>#${form.id}</strong></td>
      <td>
        <div style="font-weight: 600;">${escapeHtml(form.title)}</div>
        <small style="color: var(--text-muted);">${escapeHtml(form.description || "—")}</small>
      </td>
      <td><span class="badge" style="background:#f1f5f9; color:#334155;">${form.field_count || 0} fields</span></td>
      <td>
        <button class="btn btn-sm btn-outline" onclick="viewSubmissions(${form.id})" style="padding: 3px 8px; font-size: 0.8rem;">
          📥 ${form.submission_count || 0} Responses
        </button>
      </td>
      <td><span class="badge badge-${form.status}">${form.status}</span></td>
      <td><small>${form.created_at}</small></td>
      <td>
        <div class="table-actions">
          <button class="btn btn-sm btn-action-view" onclick="testForm(${form.id})" title="Fill / Test Form">🧪 Test</button>
          <button class="btn btn-sm btn-action-edit" onclick="editForm(${form.id})" title="Edit Form & Fields">✏️ Edit</button>
          <button class="btn btn-sm btn-action-delete" onclick="deleteForm(${form.id}, '${escapeHtml(form.title)}')" title="Delete Form">🗑️</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function addFieldRow(field = null) {
  const container = document.getElementById("fields-builder-container");
  const rowId = "fld_" + Math.random().toString(36).substr(2, 9);
  
  const div = document.createElement("div");
  div.id = rowId;
  div.style.cssText = "background: #f8fafc; border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; position: relative;";

  div.innerHTML = `
    <button type="button" onclick="document.getElementById('${rowId}').remove()" style="position: absolute; right: 8px; top: 8px; background: none; border: none; color: #ef4444; font-size: 1.1rem; cursor: pointer;">&times;</button>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 8px;">
      <div>
        <label style="font-size: 0.8rem; font-weight: 600; display: block; margin-bottom: 2px;">Field Label <span style="color:#ef4444;">*</span></label>
        <input type="text" class="form-control fld-label" placeholder="e.g. Email Address" value="${field ? escapeHtml(field.field_label) : ''}" required>
      </div>
      <div>
        <label style="font-size: 0.8rem; font-weight: 600; display: block; margin-bottom: 2px;">Field Type <span style="color:#ef4444;">*</span></label>
        <select class="form-control fld-type" onchange="toggleFieldOptions(this)">
          <option value="text" ${field && field.field_type === 'text' ? 'selected' : ''}>Text Input</option>
          <option value="email" ${field && field.field_type === 'email' ? 'selected' : ''}>Email Input</option>
          <option value="phone" ${field && field.field_type === 'phone' ? 'selected' : ''}>Phone Input</option>
          <option value="textarea" ${field && field.field_type === 'textarea' ? 'selected' : ''}>Text Area (Message)</option>
          <option value="dropdown" ${field && field.field_type === 'dropdown' ? 'selected' : ''}>Dropdown Menu</option>
          <option value="radio" ${field && field.field_type === 'radio' ? 'selected' : ''}>Radio Buttons</option>
          <option value="checkbox" ${field && field.field_type === 'checkbox' ? 'selected' : ''}>Checkbox</option>
        </select>
      </div>
    </div>
    <div class="fld-options-box" style="margin-bottom: 8px; display: ${field && ['dropdown', 'radio', 'checkbox'].includes(field.field_type) ? 'block' : 'none'};">
      <label style="font-size: 0.8rem; font-weight: 600; display: block; margin-bottom: 2px;">Choices / Options (Comma-separated)</label>
      <input type="text" class="form-control fld-options" placeholder="e.g. Sales, Support, Billing" value="${field ? escapeHtml(field.options || '') : ''}">
    </div>
    <div style="display: flex; align-items: center; gap: 16px;">
      <label style="font-size: 0.8rem; display: flex; align-items: center; gap: 6px; cursor: pointer;">
        <input type="checkbox" class="fld-required" ${field && field.is_required ? 'checked' : ''}> Required field
      </label>
    </div>
  `;

  container.appendChild(div);
}

function toggleFieldOptions(selectEl) {
  const parent = selectEl.closest("div[id^='fld_']");
  const optionsBox = parent.querySelector(".fld-options-box");
  if (['dropdown', 'radio', 'checkbox'].includes(selectEl.value)) {
    optionsBox.style.display = "block";
  } else {
    optionsBox.style.display = "none";
  }
}

async function openModal(formId = null) {
  editingFormId = formId;
  const modal = document.getElementById("crud-modal");
  const titleEl = document.getElementById("modal-title");
  const errorEl = document.getElementById("form-error");
  const container = document.getElementById("fields-builder-container");

  errorEl.style.display = "none";
  container.innerHTML = "";

  if (formId) {
    titleEl.textContent = `Edit Form #${formId}`;
    const res = await apiClient.get(`/api/forms/${formId}`);
    if (res.success && res.data) {
      const f = res.data;
      document.getElementById("form-title").value = f.title;
      document.getElementById("form-desc").value = f.description || "";
      document.getElementById("form-status").value = f.status;

      if (f.fields && f.fields.length > 0) {
        f.fields.forEach(fld => addFieldRow(fld));
      } else {
        addFieldRow();
      }
    }
  } else {
    titleEl.textContent = "Create Dynamic Form";
    document.getElementById("item-form").reset();
    document.getElementById("form-status").value = "active";
    // Add default fields
    addFieldRow({ field_label: "Your Full Name", field_type: "text", is_required: 1 });
    addFieldRow({ field_label: "Your Email Address", field_type: "email", is_required: 1 });
    addFieldRow({ field_label: "Your Message", field_type: "textarea", is_required: 1 });
  }

  modal.classList.add("active");
}

function closeModal() {
  document.getElementById("crud-modal").classList.remove("active");
  editingFormId = null;
}

function closePreviewModal() {
  document.getElementById("preview-form-modal").classList.remove("active");
  activeTestingFormId = null;
}

function closeSubmissionsModal() {
  document.getElementById("submissions-modal").classList.remove("active");
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const errorEl = document.getElementById("form-error");
  const submitBtn = document.getElementById("modal-submit-btn");

  errorEl.style.display = "none";

  // Collect field rows
  const fieldRows = document.querySelectorAll("#fields-builder-container > div");
  const fields = [];

  fieldRows.forEach((row, idx) => {
    const label = row.querySelector(".fld-label")?.value.trim();
    const type = row.querySelector(".fld-type")?.value || "text";
    const options = row.querySelector(".fld-options")?.value.trim() || "";
    const isRequired = row.querySelector(".fld-required")?.checked ? 1 : 0;
    const name = label ? label.toLowerCase().replace(/[^a-z0-9_]/g, "_").replace(/_+/g, "_") : `field_${idx+1}`;

    if (label) {
      fields.push({
        field_label: label,
        field_name: name,
        field_type: type,
        options: options,
        is_required: isRequired,
        display_order: idx + 1
      });
    }
  });

  const payload = {
    title: document.getElementById("form-title").value.trim(),
    description: document.getElementById("form-desc").value.trim(),
    status: document.getElementById("form-status").value,
    fields: fields
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  let res;
  if (editingFormId) {
    res = await apiClient.put(`/api/forms/${editingFormId}`, payload);
  } else {
    res = await apiClient.post("/api/forms", payload);
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Save Form";

  if (!res.success) {
    errorEl.textContent = res.message || "Operation failed.";
    if (res.errors) {
      errorEl.textContent += " " + Object.values(res.errors).join(" ");
    }
    errorEl.style.display = "block";
    return;
  }

  showToast(editingFormId ? "Form updated successfully!" : "Form created successfully!", "success");
  closeModal();
  await loadForms();
}

async function testForm(formId) {
  activeTestingFormId = formId;
  const res = await apiClient.get(`/api/forms/${formId}`);
  if (!res.success || !res.data) {
    showToast("Failed to load form details", "error");
    return;
  }

  const f = res.data;
  const modal = document.getElementById("preview-form-modal");
  const body = document.getElementById("preview-form-fields-body");
  document.getElementById("preview-modal-title").textContent = `Test: ${f.title}`;

  let html = '';
  if (f.description) {
    html += `<p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 16px;">${escapeHtml(f.description)}</p>`;
  }

  if (!f.fields || f.fields.length === 0) {
    html += '<p style="color: #94a3b8;">No fields configured in this form.</p>';
  } else {
    f.fields.forEach(fld => {
      html += `<div class="form-group">`;
      html += `<label class="form-label">${escapeHtml(fld.field_label)} ${fld.is_required ? '<span class="required">*</span>' : ''}</label>`;

      if (fld.field_type === 'textarea') {
        html += `<textarea name="${fld.field_name}" class="form-control" rows="3" ${fld.is_required ? 'required' : ''}></textarea>`;
      } else if (fld.field_type === 'dropdown') {
        const opts = (fld.options || "").split(",").map(o => o.trim()).filter(Boolean);
        html += `<select name="${fld.field_name}" class="form-control" ${fld.is_required ? 'required' : ''}>`;
        html += `<option value="">-- Please Select --</option>`;
        opts.forEach(opt => html += `<option value="${escapeHtml(opt)}">${escapeHtml(opt)}</option>`);
        html += `</select>`;
      } else if (fld.field_type === 'radio') {
        const opts = (fld.options || "").split(",").map(o => o.trim()).filter(Boolean);
        html += `<div style="display: flex; gap: 14px; flex-wrap: wrap;">`;
        opts.forEach((opt, idx) => {
          html += `
            <label style="font-size: 0.9rem; display: flex; align-items: center; gap: 6px;">
              <input type="radio" name="${fld.field_name}" value="${escapeHtml(opt)}" ${fld.is_required && idx===0 ? 'required' : ''}> ${escapeHtml(opt)}
            </label>
          `;
        });
        html += `</div>`;
      } else if (fld.field_type === 'checkbox') {
        html += `
          <label style="font-size: 0.9rem; display: flex; align-items: center; gap: 6px;">
            <input type="checkbox" name="${fld.field_name}" value="Yes" ${fld.is_required ? 'required' : ''}> ${escapeHtml(fld.options || 'Confirm / Agree')}
          </label>
        `;
      } else {
        const inputId = `preview_input_${fld.id || Math.random().toString(36).substr(2, 6)}_${fld.field_name}`;
        html += `<input type="${fld.field_type === 'email' ? 'email' : (fld.field_type === 'phone' ? 'tel' : 'text')}" id="${inputId}" name="${fld.field_name}" class="form-control" ${fld.is_required ? 'required' : ''} autocomplete="off" spellcheck="false">`;
      }

      html += `</div>`;
    });
  }

  body.innerHTML = html;
  modal.classList.add("active");
}

async function handleTestFormSubmit(e) {
  e.preventDefault();
  if (!activeTestingFormId) return;

  const formEl = document.getElementById("public-submit-form");
  const formData = new FormData(formEl);
  const data = {};
  formData.forEach((val, key) => data[key] = val);

  const btn = document.getElementById("btn-submit-preview-form");
  btn.disabled = true;
  btn.textContent = "Submitting Response...";

  const res = await apiClient.post(`/api/forms/${activeTestingFormId}/submit`, data);
  btn.disabled = false;
  btn.textContent = "Submit Form Response";

  if (!res.success) {
    showToast(res.message || "Failed to submit form.", "error");
    return;
  }

  showToast("Form response submitted and saved to MySQL!", "success");
  closePreviewModal();
  await loadForms();
}

async function viewSubmissions(formId = null) {
  const modal = document.getElementById("submissions-modal");
  const container = document.getElementById("submissions-content-container");
  document.getElementById("submissions-modal-title").textContent = formId ? `Submissions for Form #${formId}` : "All Form Submissions";

  container.innerHTML = '<div class="loading-container"><span class="spinner"></span><span>Loading responses...</span></div>';
  modal.classList.add("active");

  const url = formId ? `/api/forms/${formId}/submissions` : "/api/forms/submissions";
  const res = await apiClient.get(url);

  if (!res.success) {
    container.innerHTML = `<div class="empty-state"><p>${res.message || "Failed to load submissions"}</p></div>`;
    return;
  }

  const items = res.data || [];
  if (items.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📥</div>
        <div class="empty-state-title">No Submissions Recorded Yet</div>
        <p>Use the "Test" button to fill out the form and submit responses.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = items.map(sub => `
    <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px; padding: 14px; margin-bottom: 12px; box-shadow: var(--shadow-sm);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid var(--border-color); padding-bottom: 6px;">
        <div>
          <span style="font-weight: 700; color: var(--text-main);">Submission #${sub.id}</span>
          <span class="badge" style="background:#f1f5f9; color:#475569; margin-left: 8px;">${escapeHtml(sub.form_title || 'Form')}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <small style="color: var(--text-muted);">${sub.created_at}</small>
          <button class="btn btn-sm btn-action-delete" onclick="deleteSubmission(${sub.id}, ${formId})" title="Delete Response" style="padding: 2px 6px;">🗑️</button>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px;">
        ${Object.entries(sub.parsed_data || {}).map(([k, v]) => `
          <div style="background: #f8fafc; padding: 6px 10px; border-radius: 4px;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">${escapeHtml(k)}</div>
            <div style="font-size: 0.875rem; font-weight: 600; color: var(--text-main); word-break: break-word;">${escapeHtml(v)}</div>
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");
}

async function deleteSubmission(subId, formId) {
  const confirmed = await confirmAction(`Delete submission record #${subId}?`, "Delete Response");
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/forms/submissions/${subId}`);
  if (res.success) {
    showToast("Submission deleted successfully.", "success");
    await viewSubmissions(formId);
    await loadForms();
  } else {
    showToast(res.message || "Failed to delete submission.", "error");
  }
}

function editForm(id) {
  openModal(id);
}

async function deleteForm(id, title) {
  const confirmed = await confirmAction(
    `Are you sure you want to permanently delete dynamic form "${title}" (#${id}) and all its submissions?`,
    "Delete Form"
  );
  if (!confirmed) return;

  const res = await apiClient.delete(`/api/forms/${id}`);
  if (res.success) {
    showToast("Form deleted successfully.", "success");
    await loadForms();
  } else {
    showToast(res.message || "Failed to delete form.", "error");
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
