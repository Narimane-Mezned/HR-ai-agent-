import { login, register } from "../services/auth.service.js";

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

  function showLoginForm() {
    errorEl.innerText = "";
    formArea.innerHTML = `
      <form id="login-form">
        <input id="li-username" placeholder="Username" required autocomplete="username">
        <input id="li-password" type="password" placeholder="Password" required autocomplete="current-password">
        <button type="submit" class="primary full">Log In</button>
      </form>
    `;
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
          errorEl.innerText = err.message;
        }
      });
  }

  function showRegisterForm() {
    errorEl.innerText = "";
    formArea.innerHTML = `
      <form id="register-form">
        <input id="re-username" placeholder="Username" required>
        <input id="re-password" type="password" placeholder="Password" required>
        <input id="re-company" placeholder="Company name" required>
        <input id="re-email" type="email" placeholder="Email (optional)">
        <button type="submit" class="primary full">Create account</button>
      </form>
    `;
    document
      .getElementById("register-form")
      .addEventListener("submit", async (e) => {
        e.preventDefault();
        errorEl.innerText = "";
        try {
          await register(
            document.getElementById("re-username").value,
            document.getElementById("re-password").value,
            document.getElementById("re-company").value,
            document.getElementById("re-email").value,
          );
          onSuccess();
        } catch (err) {
          errorEl.innerText = err.message;
        }
      });
  }

  document
    .getElementById("show-login")
    .addEventListener("click", showLoginForm);
  document
    .getElementById("show-register")
    .addEventListener("click", showRegisterForm);

  showLoginForm(); // default view
}
