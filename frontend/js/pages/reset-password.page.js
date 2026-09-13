import { resetPassword } from "../services/auth.service.js";

function getPasswordError(password) {
  if (password.length < 8)
    return "Password must be at least 8 characters long.";
  if (!/\d/.test(password)) return "Password must contain at least one number.";
  return null;
}

export function renderResetPasswordPage(token, onDone) {
  const screen = document.getElementById("login-screen");
  screen.style.display = "flex";

  if (!token) {
    screen.innerHTML = `
      <div id="login-box">
        <h2>HR AI Agent</h2>
        <p class="error-text">This reset link is missing its token. Please request a new one from the login page.</p>
        <button id="back-to-login" class="secondary full">Back to Log In</button>
      </div>
    `;
    document.getElementById("back-to-login").addEventListener("click", onDone);
    return;
  }

  screen.innerHTML = `
    <div id="login-box">
      <h2>Reset your password</h2>
      <form id="reset-form">
        <div class="password-field">
          <input id="rp-password" type="password" placeholder="New password" required>
        </div>
        <small style="color:#888; font-size:12px; display:block; margin-top:-8px;">Min. 8 characters, at least 1 number</small>
        <button type="submit" class="primary full">Set new password</button>
      </form>
      <div id="reset-error" class="error-text"></div>
    </div>
  `;

  const errorEl = document.getElementById("reset-error");

  document
    .getElementById("reset-form")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      errorEl.innerText = "";
      const password = document.getElementById("rp-password").value;
      const passwordError = getPasswordError(password);
      if (passwordError) {
        errorEl.innerText = passwordError;
        return;
      }
      try {
        await resetPassword(token, password);
        screen.innerHTML = `
        <div id="login-box">
          <h2>Password updated</h2>
          <p>You can now log in with your new password.</p>
          <button id="go-to-login" class="primary full">Go to Log In</button>
        </div>
      `;
        document
          .getElementById("go-to-login")
          .addEventListener("click", onDone);
      } catch (err) {
        errorEl.innerText = err.message;
      }
    });
}
