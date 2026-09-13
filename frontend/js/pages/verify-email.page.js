import { verifyEmail } from "../services/auth.service.js";

export function renderVerifyEmailPage(token, onDone) {
  const screen = document.getElementById("login-screen");
  screen.style.display = "flex";

  if (!token) {
    screen.innerHTML = `
      <div id="login-box">
        <h2>HR AI Agent</h2>
        <p class="error-text">This verification link is missing its token. Please check the link in your email.</p>
        <button id="back-to-login" class="secondary full">Back to Log In</button>
      </div>
    `;
    document.getElementById("back-to-login").addEventListener("click", onDone);
    return;
  }

  screen.innerHTML = `
    <div id="login-box">
      <h2>Verifying your email...</h2>
    </div>
  `;

  verifyEmail(token)
    .then((result) => {
      screen.innerHTML = `
        <div id="login-box">
          <h2>Email verified</h2>
          <p>${result.message}</p>
          <button id="go-to-login" class="primary full">Go to Log In</button>
        </div>
      `;
      document.getElementById("go-to-login").addEventListener("click", onDone);
    })
    .catch((err) => {
      screen.innerHTML = `
        <div id="login-box">
          <h2>HR AI Agent</h2>
          <p class="error-text">${err.message}</p>
          <button id="back-to-login" class="secondary full">Back to Log In</button>
        </div>
      `;
      document
        .getElementById("back-to-login")
        .addEventListener("click", onDone);
    });
}
