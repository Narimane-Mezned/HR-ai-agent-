import {
  listPendingUsers,
  approveUser,
  rejectUser,
} from "../services/admin.service.js";
import { logout } from "../services/auth.service.js";

export function renderAdminPage(onLogout) {
  const screen = document.getElementById("login-screen");
  document.getElementById("app-screen").style.display = "none";
  screen.style.display = "flex";

  screen.innerHTML = `
    <div id="login-box" style="max-width:560px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <h2 style="margin:0;">Pending account approvals</h2>
        <button id="admin-logout" class="secondary">Log out</button>
      </div>
      <div id="admin-list"></div>
    </div>
  `;

  document.getElementById("admin-logout").addEventListener("click", () => {
    logout();
    onLogout();
  });

  loadPendingUsers();

  async function loadPendingUsers() {
    const listEl = document.getElementById("admin-list");
    listEl.innerHTML = `<p style="font-size:13px; color:#888;">Loading...</p>`;
    try {
      const users = await listPendingUsers();
      if (users.length === 0) {
        listEl.innerHTML = `<p style="font-size:13px; color:#888;">No pending accounts.</p>`;
        return;
      }
      listEl.innerHTML = users
        .map(
          (u) => `
        <div class="pending-user-row" style="border:1px solid #e5e5e5; border-radius:8px; padding:12px; margin-bottom:10px;">
          <div><strong>${u.username}</strong> &mdash; ${u.company_name || "(no company)"}</div>
          <div style="font-size:13px; color:#555;">${u.email || "(no email)"}</div>
          <div style="font-size:12px; color:${u.email_verified ? "#2a7a2a" : "#a00"}; margin:4px 0 8px;">
            ${u.email_verified ? "Email verified" : "Email not verified yet"}
          </div>
          <button type="button" class="primary approve-btn" data-username="${u.username}">Approve</button>
          <button type="button" class="secondary reject-btn" data-username="${u.username}">Reject</button>
        </div>
      `,
        )
        .join("");

      listEl.querySelectorAll(".approve-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          btn.disabled = true;
          await approveUser(btn.dataset.username);
          loadPendingUsers();
        });
      });
      listEl.querySelectorAll(".reject-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          btn.disabled = true;
          await rejectUser(btn.dataset.username);
          loadPendingUsers();
        });
      });
    } catch (err) {
      listEl.innerHTML = `<p class="error-text">${err.message}</p>`;
    }
  }
}
