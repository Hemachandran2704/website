/**
 * Magnus Dynamic CMS - Authentication & Session Management
 */

const Auth = {
  async checkAuth() {
    const token = apiClient.getToken();
    const user = apiClient.getUser();

    // Verify session with backend if either token or cookie exists
    try {
      const res = await apiClient.get("/api/auth/me");
      if (res.success && res.data) {
        apiClient.setUser(res.data);
        this.renderUserInfo(res.data);
        return true;
      }
    } catch (e) {
      console.warn("Auth verification error:", e);
    }

    if (!token && !user) {
      apiClient.clearAuth();
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      return false;
    }

    if (user) {
      this.renderUserInfo(user);
    }
    return true;
  },

  requireAdmin() {
    return this.checkAuth();
  },

  renderUserInfo(user) {
    const nameEl = document.getElementById("sidebar-user-name");
    const roleEl = document.getElementById("sidebar-user-role");
    const avatarEl = document.getElementById("sidebar-user-avatar");
    const brandRoleEl = document.getElementById("sidebar-brand-role");

    if (nameEl) nameEl.textContent = user.name || user.email;
    if (roleEl) roleEl.textContent = "USER";
    if (brandRoleEl) brandRoleEl.textContent = "USER";
    if (avatarEl) {
      const initial = (user.name || user.email || "U").charAt(0).toUpperCase();
      avatarEl.textContent = initial;
    }
  },

  async logout() {
    const confirmed = await confirmAction("Are you sure you want to log out of your session?", "Sign Out");
    if (!confirmed) return;

    try {
      await apiClient.post("/api/auth/logout");
    } catch (e) {
      console.warn("Logout request failed:", e);
    } finally {
      apiClient.clearAuth();
      showToast("You have been signed out.", "info");
      setTimeout(() => {
        window.location.href = "/login";
      }, 300);
    }
  },

  async initLoginPage() {
    const loginForm = document.getElementById("login-form");
    if (!loginForm) return;
    if (loginForm.dataset.initialized === "true") return;
    loginForm.dataset.initialized = "true";

    const params = new URLSearchParams(window.location.search);
    if (params.get("registered") === "1") {
      const errorBox = document.getElementById("login-error");
      if (errorBox) {
        errorBox.textContent = "Account created. Please sign in.";
        errorBox.style.display = "block";
        errorBox.style.background = "#dcfce7";
        errorBox.style.borderColor = "#86efac";
      }
    }

    

    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const errorBox = document.getElementById("login-error");
    const submitBtn = document.getElementById("login-submit-btn");

    // 1. Independent controlled states for email and password
    let emailState = emailInput ? emailInput.value : "";
    let passwordState = passwordInput ? passwordInput.value : "";
    let isSubmitting = false;

    // 2. Controlled event bindings for email input
    if (emailInput) {
      const handleEmailChange = (e) => {
        emailState = e.target.value;
      };
      emailInput.addEventListener("input", handleEmailChange);
      emailInput.addEventListener("change", handleEmailChange);
      emailInput.addEventListener("paste", (e) => {
        // Allow native paste to current field, then update state
        setTimeout(() => {
          emailState = emailInput.value;
        }, 0);
      });
    }

    // 3. Controlled event bindings for password input
    if (passwordInput) {
      const handlePasswordChange = (e) => {
        passwordState = e.target.value;
      };
      passwordInput.addEventListener("input", handlePasswordChange);
      passwordInput.addEventListener("change", handlePasswordChange);
      passwordInput.addEventListener("paste", (e) => {
        setTimeout(() => {
          passwordState = passwordInput.value;
        }, 0);
      });
    }

    // 4. Global prefill helper to update controlled states and DOM values
    window.fillCreds = function(email, password) {
      if (emailInput) {
        emailInput.value = email;
        emailState = email;
      }
      if (passwordInput) {
        passwordInput.value = password;
        passwordState = password;
      }
      if (errorBox) {
        errorBox.style.display = "none";
        errorBox.textContent = "";
      }
    };

    // 5. Form submission handler
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (isSubmitting) return;

      if (errorBox) {
        errorBox.textContent = "";
        errorBox.style.display = "none";
      }

      // Read current values from controlled states (or fallback to element values)
      const email = (emailState || (emailInput ? emailInput.value : "")).trim();
      const password = passwordState || (passwordInput ? passwordInput.value : "");

      // 6. Validation
      if (!email && !password) {
        if (errorBox) {
          errorBox.textContent = "Please enter your email address and password.";
          errorBox.style.display = "block";
        }
        if (emailInput) emailInput.focus();
        return;
      }

      if (!email) {
        if (errorBox) {
          errorBox.textContent = "Please enter your email address.";
          errorBox.style.display = "block";
        }
        if (emailInput) emailInput.focus();
        return;
      }

      if (!password) {
        if (errorBox) {
          errorBox.textContent = "Please enter your password.";
          errorBox.style.display = "block";
        }
        if (passwordInput) passwordInput.focus();
        return;
      }

      // 7. Execute Login API call with loading state
      isSubmitting = true;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px;"></span> Authenticating...';
      }

      try {
        const res = await apiClient.post("/api/auth/login", { email, password });

        if (!res.success) {
          isSubmitting = false;
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Sign In";
          }
          if (errorBox) {
            errorBox.textContent = res.message || (res.errors && res.errors.email) || "Invalid credentials provided. Please check your email and password.";
            errorBox.style.display = "block";
          }
          return;
        }

        // 8. Handle successful login
        if (res.data && res.data.token) {
          apiClient.setToken(res.data.token);
        }
        if (res.data && res.data.user) {
          apiClient.setUser(res.data.user);
        }

        showToast(`Welcome back, ${res.data.user.name || "User"}!`, "success");

        // 9. Redirect to requested URL or dashboard
        const urlParams = new URLSearchParams(window.location.search);
        const redirectUrl = urlParams.get("redirect");

        setTimeout(() => {
          if (redirectUrl && !redirectUrl.includes("login")) {
            window.location.href = redirectUrl;
          } else {
            window.location.href = "/dashboard";
          }
        }, 300);

      } catch (err) {
        isSubmitting = false;
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = "Sign In";
        }
        if (errorBox) {
          errorBox.textContent = "A network error occurred while connecting to the server. Please try again.";
          errorBox.style.display = "block";
        }
        console.error("Login submission error:", err);
      }
    });
  },

  async initRegisterPage() {
    const registerForm = document.getElementById("register-form");
    if (!registerForm) return;
    if (registerForm.dataset.initialized === "true") return;
    registerForm.dataset.initialized = "true";

    // Check if user already has an active session
    const token = apiClient.getToken();
    const existingUser = apiClient.getUser();
    if (token || existingUser) {
      try {
        const res = await apiClient.get("/api/auth/me");
        if (res.success && res.data) {
          apiClient.setUser(res.data);
          window.location.href = "/dashboard";
          return;
        }
      } catch (e) {
        apiClient.clearAuth();
      }
    }

    const nameInput = document.getElementById("name");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirm_password");
    const errorBox = document.getElementById("register-error");
    const submitBtn = document.getElementById("register-submit-btn");

    // 1. Independent controlled states for each registration field
    let nameState = nameInput ? nameInput.value : "";
    let emailState = emailInput ? emailInput.value : "";
    let passwordState = passwordInput ? passwordInput.value : "";
    let confirmPasswordState = confirmPasswordInput ? confirmPasswordInput.value : "";
    let isSubmitting = false;

    // 2. Stable event bindings without recreating or unmounting inputs
    if (nameInput) {
      const handleNameChange = (e) => {
        nameState = e.target.value;
      };
      nameInput.addEventListener("input", handleNameChange);
      nameInput.addEventListener("change", handleNameChange);
      nameInput.addEventListener("paste", (e) => {
        setTimeout(() => { nameState = nameInput.value; }, 0);
      });
    }

    if (emailInput) {
      const handleEmailChange = (e) => {
        emailState = e.target.value;
      };
      emailInput.addEventListener("input", handleEmailChange);
      emailInput.addEventListener("change", handleEmailChange);
      emailInput.addEventListener("paste", (e) => {
        setTimeout(() => { emailState = emailInput.value; }, 0);
      });
    }

    if (passwordInput) {
      const handlePasswordChange = (e) => {
        passwordState = e.target.value;
      };
      passwordInput.addEventListener("input", handlePasswordChange);
      passwordInput.addEventListener("change", handlePasswordChange);
      passwordInput.addEventListener("paste", (e) => {
        setTimeout(() => { passwordState = passwordInput.value; }, 0);
      });
    }

    if (confirmPasswordInput) {
      const handleConfirmPasswordChange = (e) => {
        confirmPasswordState = e.target.value;
      };
      confirmPasswordInput.addEventListener("input", handleConfirmPasswordChange);
      confirmPasswordInput.addEventListener("change", handleConfirmPasswordChange);
      confirmPasswordInput.addEventListener("paste", (e) => {
        setTimeout(() => { confirmPasswordState = confirmPasswordInput.value; }, 0);
      });
    }

    // 3. Form submission handler
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (isSubmitting) return;

      if (errorBox) {
        errorBox.textContent = "";
        errorBox.style.display = "none";
      }

      // Read values from controlled state
      const name = (nameState || (nameInput ? nameInput.value : "")).trim();
      const email = (emailState || (emailInput ? emailInput.value : "")).trim();
      const password = passwordState || (passwordInput ? passwordInput.value : "");
      const confirm_password = confirmPasswordState || (confirmPasswordInput ? confirmPasswordInput.value : "");

      // 4. Client-side field validation
      if (!name) {
        if (errorBox) {
          errorBox.textContent = "Please enter your full name.";
          errorBox.style.display = "block";
        }
        if (nameInput) nameInput.focus();
        return;
      }

      if (!email) {
        if (errorBox) {
          errorBox.textContent = "Please enter your email address.";
          errorBox.style.display = "block";
        }
        if (emailInput) emailInput.focus();
        return;
      }

      if (!password) {
        if (errorBox) {
          errorBox.textContent = "Please enter a password.";
          errorBox.style.display = "block";
        }
        if (passwordInput) passwordInput.focus();
        return;
      }

      if (password.length < 6) {
        if (errorBox) {
          errorBox.textContent = "Password must be at least 6 characters long.";
          errorBox.style.display = "block";
        }
        if (passwordInput) passwordInput.focus();
        return;
      }

      if (password !== confirm_password) {
        if (errorBox) {
          errorBox.textContent = "Passwords do not match. Please re-enter matching passwords.";
          errorBox.style.display = "block";
        }
        if (confirmPasswordInput) confirmPasswordInput.focus();
        return;
      }

      // 5. Submit to backend API
      isSubmitting = true;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px;"></span> Creating Account...';
      }

      try {
        const res = await apiClient.post("/api/auth/register", {
          name,
          email,
          password,
          confirm_password
        });

        if (!res.success) {
          isSubmitting = false;
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "Create Account";
          }
          if (errorBox) {
            errorBox.textContent = res.message || (res.errors && (res.errors.email || res.errors.name || res.errors.password)) || "Registration failed. Please check your details.";
            errorBox.style.display = "block";
          }
          return;
        }

        // Registration creates the account; the user signs in separately.
        setTimeout(() => {
          window.location.href = "/login?registered=1";
        }, 400);

      } catch (err) {
        isSubmitting = false;
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = "Create Account";
        }
        if (errorBox) {
          errorBox.textContent = "A network error occurred during registration. Please try again.";
          errorBox.style.display = "block";
        }
        console.error("Register submission error:", err);
      }
    });
  },

  initSidebar() {
    // Highlight active link
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll(".sidebar .nav-link");
    let inMoreMenu = false;

    links.forEach(link => {
      const href = link.getAttribute("href");
      if (href && (currentPath.endsWith(href) || currentPath.includes(href.replace("/frontend/", "")))) {
        link.classList.add("active");
        if (link.closest(".nav-submenu")) {
          inMoreMenu = true;
        }
      }
    });

    // Auto open "More" group if currently inside a More subpage
    const moreGroup = document.getElementById("nav-more-group");
    if (moreGroup) {
      if (inMoreMenu || currentPath.includes("/pages/")) {
        moreGroup.classList.add("open");
      }
      const toggle = moreGroup.querySelector(".nav-group-header");
      if (toggle) {
        toggle.addEventListener("click", () => {
          moreGroup.classList.toggle("open");
        });
      }

    }

    // Logout button handler
    const logoutBtn = document.getElementById("sidebar-logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => this.logout());
    }

    // Mobile sidebar toggle
    const mobileToggle = document.getElementById("mobile-menu-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (mobileToggle && sidebar) {
      mobileToggle.addEventListener("click", () => {
        sidebar.classList.toggle("mobile-open");
      });
    }
  }
};
