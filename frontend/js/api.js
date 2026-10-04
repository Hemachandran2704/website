/**
 * Magnus Dynamic CMS - Central API Client & UI Utilities
 */

const API_BASE_URL = window.location.origin;

const apiClient = {
  getToken() {
    return localStorage.getItem("magnus_token");
  },

  setToken(token) {
    localStorage.setItem("magnus_token", token);
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem("magnus_user") || "null");
    } catch (e) {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("magnus_user", JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem("magnus_token");
    localStorage.removeItem("magnus_user");
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
    const headers = options.headers || {};

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!options.isFormData && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      credentials: options.credentials || "same-origin",
      headers
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({
        success: false,
        message: "Failed to parse response JSON from server",
        errors: {}
      }));

      // Handle Unauthorized on protected pages (do not redirect when submitting auth forms or on auth pages)
      if (response.status === 401) {
        const isAuthApi = endpoint.includes("/auth/");
        const isAuthPage = /login|register|signup/i.test(window.location.pathname);
        if (!isAuthApi && !isAuthPage) {
          this.clearAuth();
          window.location.href = "/login?session=expired";
        }
      }

      if (!response.ok) {
        return {
          success: false,
          status: response.status,
          message: data.message || `Request failed with status ${response.status}`,
          errors: data.errors || {},
          data: null
        };
      }

      return {
        success: true,
        status: response.status,
        message: data.message || "Success",
        data: data.data || {},
        errors: null
      };
    } catch (error) {
      console.error("Network or API Error:", error);
      return {
        success: false,
        status: 0,
        message: "Unable to connect to server. Please ensure the backend is running.",
        errors: { network: error.message },
        data: null
      };
    }
  },

  get(endpoint, params = {}) {
    let url = endpoint;
    const query = new URLSearchParams();
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
        query.append(k, params[k]);
      }
    });
    const qs = query.toString();
    if (qs) {
      url += (url.includes("?") ? "&" : "?") + qs;
    }
    return this.request(url, { method: "GET" });
  },

  post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(data)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  },

  upload(endpoint, formData, method = "POST") {
    return this.request(endpoint, {
      method,
      body: formData,
      isFormData: true
    });
  }
};

/**
 * Toast Notification Dispatcher
 */
function showToast(message, type = "info", duration = 3500) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Modal Confirmation Dialog
 */
function confirmAction(message, title = "Confirm Operation") {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay active";
    overlay.style.zIndex = "99999";
    overlay.innerHTML = `
      <div class="modal-container" style="max-width: 440px;">
        <div class="modal-header">
          <h3 class="modal-title">${title}</h3>
          <button class="modal-close-btn" id="modal-cancel-x">&times;</button>
        </div>
        <div class="modal-body">
          <p style="color: var(--text-main); font-size: 0.95rem;">${message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" id="modal-btn-cancel">Cancel</button>
          <button class="btn btn-danger" id="modal-btn-confirm">Confirm</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const cleanup = (val) => {
      overlay.remove();
      resolve(val);
    };

    overlay.querySelector("#modal-btn-confirm").addEventListener("click", () => cleanup(true));
    overlay.querySelector("#modal-btn-cancel").addEventListener("click", () => cleanup(false));
    overlay.querySelector("#modal-cancel-x").addEventListener("click", () => cleanup(false));
  });
}
