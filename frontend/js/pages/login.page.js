import { login, register, forgotPassword } from "../services/auth.service.js";

const EYE_OPEN = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
const EYE_CLOSED = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a18.5 18.5 0 0 1 5.06-5.94M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;

function attachPasswordToggle(toggleId, inputId) {
  const toggle = document.getElementById(toggleId);
  const input = document.getElementById(inputId);
  toggle.innerHTML = EYE_OPEN;
  toggle.addEventListener("click", () => {
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    toggle.innerHTML = isHidden ? EYE_CLOSED : EYE_OPEN;
    toggle.setAttribute(
      "aria-label",
      isHidden ? "Hide password" : "Show password",
    );
  });
}

function getPasswordError(password) {
  if (password.length < 8)
    return "Password must be at least 8 characters long.";
  if (!/\d/.test(password)) return "Password must contain at least one number.";
  return null;
}

export function renderLoginPage(onSuccess) {
  const screen = document.getElementById("login-screen");
  screen.style.display = "flex";
  screen.innerHTML = `
    <div id="login-box">
      <h2>HR AI Agent</h2>
      <div id="mode-buttons" style="display:flex; gap:8px; margin-bottom:16px;">
        <button id="show-login" class="secondary full">Log In</button>
        <button id="show-register" class="primary full">Register</button>
      </div>
      <div id="form-area"></div>
      <div id="login-error" class="error-text"></div>
    </div>
  `;

  const formArea = document.getElementById("form-area");
  const errorEl = document.getElementById("login-error");

  let rateLimitTimer = null;

  function showRateLimitCountdown(seconds) {
    if (rateLimitTimer) clearInterval(rateLimitTimer);
    let remaining = Math.max(1, Math.round(seconds));
    errorEl.innerText = `Too many attempts. Try again in ${remaining}s...`;
    rateLimitTimer = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(rateLimitTimer);
        rateLimitTimer = null;
        errorEl.innerText = "";
      } else {
        errorEl.innerText = `Too many attempts. Try again in ${remaining}s...`;
      }
    }, 1000);
  }

  function showError(err) {
    if (typeof err.retryAfter === "number") {
      showRateLimitCountdown(err.retryAfter);
    } else {
      if (rateLimitTimer) {
        clearInterval(rateLimitTimer);
        rateLimitTimer = null;
      }
      errorEl.innerText = err.message;
    }
  }

  function showLoginForm() {
    errorEl.innerText = "";
    formArea.innerHTML = `
      <form id="login-form">
        <input id="li-username" placeholder="Username" required autocomplete="username">
        <div class="password-field">
          <input id="li-password" type="password" placeholder="Password" required autocomplete="current-password">
          <button type="button" id="li-password-toggle" class="password-toggle" aria-label="Show password"></button>
        </div>
        <button type="submit" class="primary full">Log In</button>
      </form>
      <div style="text-align:center; margin-top:10px;">
        <a href="#" id="show-forgot-password" style="font-size:13px;">Forgot password?</a>
      </div>
    `;
    attachPasswordToggle("li-password-toggle", "li-password");
    document
      .getElementById("login-form")
      .addEventListener("submit", async (e) => {
        e.preventDefault();
        errorEl.innerText = "";
        try {
          await login(
            document.getElementById("li-username").value,
            document.getElementById("li-password").value,
          );
          onSuccess();
        } catch (err) {
          showError(err);
        }
      });
    document
      .getElementById("show-forgot-password")
      .addEventListener("click", async (e) => {
        e.preventDefault();
        await triggerForgotPassword();
      });
  }

  function showRegisterForm() {
    errorEl.innerText = "";
    formArea.innerHTML = `
      <form id="register-form">
        <input id="re-username" placeholder="Username" required>
        <div class="password-field">
          <input id="re-password" type="password" placeholder="Password" required>
          <button type="button" id="re-password-toggle" class="password-toggle" aria-label="Show password"></button>
        </div>
        <small style="color:#888; font-size:12px; display:block; margin-top:-8px;">Min. 8 characters, at least 1 number</small>
        <input id="re-company" placeholder="Company name" required>
        <input id="re-email" type="email" placeholder="Email" required>
        <button type="submit" class="primary full">Create account</button>
      </form>
    `;
    attachPasswordToggle("re-password-toggle", "re-password");
    document
      .getElementById("register-form")
      .addEventListener("submit", async (e) => {
        e.preventDefault();
        errorEl.innerText = "";
        const password = document.getElementById("re-password").value;
        const passwordError = getPasswordError(password);
        if (passwordError) {
          errorEl.innerText = passwordError;
          return;
        }
        try {
          const result = await register(
            document.getElementById("re-username").value,
            password,
            document.getElementById("re-company").value,
            document.getElementById("re-email").value,
          );
          formArea.innerHTML = `
            <p style="font-size:13px;">${result.message}</p>
            <div style="text-align:center; margin-top:10px;">
              <a href="#" id="back-to-login-after-register" style="font-size:13px;">Back to Log In</a>
            </div>
          `;
          document
            .getElementById("back-to-login-after-register")
            .addEventListener("click", (e2) => {
              e2.preventDefault();
              showLoginForm();
            });
        } catch (err) {
          showError(err);
        }
      });
  }

  async function triggerForgotPassword() {
    errorEl.innerText = "";
    const username = (
      document.getElementById("li-username")?.value || ""
    ).trim();
    if (!username) {
      errorEl.innerText =
        'Type your username above first, then click "Forgot password?"';
      return;
    }
    formArea.innerHTML = `<p style="font-size:13px; color:#888;">Sending reset link...</p>`;
    try {
      const result = await forgotPassword(username);
      formArea.innerHTML = `
        <p style="font-size:13px;">${result.message}</p>
        <div style="text-align:center; margin-top:10px;">
          <a href="#" id="back-to-login-link" style="font-size:13px;">Back to Log In</a>
        </div>
      `;
      document
        .getElementById("back-to-login-link")
        .addEventListener("click", (e) => {
          e.preventDefault();
          showLoginForm();
        });
    } catch (err) {
      showLoginForm();
      showError(err);
    }
  }

  document
    .getElementById("show-login")
    .addEventListener("click", showLoginForm);
  document
    .getElementById("show-register")
    .addEventListener("click", showRegisterForm);

  showLoginForm();
}
