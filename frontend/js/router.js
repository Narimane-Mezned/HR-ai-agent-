import {
  isAuthenticated,
  currentUsername,
  isAdmin,
  logout,
} from "./services/auth.service.js";
import { renderLoginPage } from "./pages/login.page.js";
import { renderResetPasswordPage } from "./pages/reset-password.page.js";
import { renderVerifyEmailPage } from "./pages/verify-email.page.js";
import { renderAdminPage } from "./pages/admin.page.js";
import { renderDashboardPage } from "./pages/dashboard.page.js";
import { renderScreeningPage } from "./pages/screening.page.js";
import { renderMatchingPage } from "./pages/matching.page.js";
import { renderCommunicationPage } from "./pages/communication.page.js";
import {
  renderSchedulingPage,
  initScheduleModal,
} from "./pages/scheduling.page.js";
import { renderSidebar } from "./components/sidebar.js";
import { renderOnboardingPage } from "./pages/onboarding.page.js";

const ROUTES = {
  dashboard: renderDashboardPage,
  screening: renderScreeningPage,
  matching: renderMatchingPage,
  communication: renderCommunicationPage,
  scheduling: renderSchedulingPage,
  onboarding: renderOnboardingPage,
};

let modalInitialized = false;
let isNavigating = false;

async function navigate(tabKey) {
  if (isNavigating) return;
  isNavigating = true;
  try {
    if (!isAuthenticated()) {
      showLogin();
      return;
    }
    document
      .querySelectorAll(".view")
      .forEach((v) => (v.style.display = "none"));
    document.getElementById("view-" + tabKey).style.display = "block";
    renderSidebar(
      tabKey,
      (key) => {
        window.location.hash = "#" + key;
      },
      () => {
        logout();
        showLogin();
      },
      currentUsername(),
    );
    await ROUTES[tabKey]();
  } catch (err) {
    console.error(err);
  } finally {
    isNavigating = false;
  }
}

function parseHashToken() {
  const hash = window.location.hash; // "#reset-password?token=..." or "#verify-email?token=..."
  const queryIndex = hash.indexOf("?");
  if (queryIndex === -1) return null;
  return new URLSearchParams(hash.slice(queryIndex + 1)).get("token");
}

function handleHashChange() {
  if (window.location.hash.startsWith("#reset-password")) {
    showResetPassword(parseHashToken());
    return;
  }
  if (window.location.hash.startsWith("#verify-email")) {
    showVerifyEmail(parseHashToken());
    return;
  }
  if (!isAuthenticated()) {
    if (window.location.hash !== "#login") showLogin();
    return;
  }
  if (isAdmin()) {
    showAdmin();
    return;
  }
  const tabKey = window.location.hash.replace("#", "");
  navigate(ROUTES[tabKey] ? tabKey : "dashboard");
}

window.addEventListener("hashchange", handleHashChange);

export function showApp() {
  if (isAdmin()) {
    showAdmin();
    return;
  }

  document.getElementById("login-screen").style.display = "none";
  document.getElementById("app-screen").style.display = "flex";

  if (!modalInitialized) {
    initScheduleModal();
    modalInitialized = true;
  }

  const requestedTab = window.location.hash.replace("#", "");
  const targetTab = ROUTES[requestedTab] ? requestedTab : "dashboard";
  if (window.location.hash === "#" + targetTab) {
    navigate(targetTab);
  } else {
    window.location.hash = "#" + targetTab;
  }
}

export function showAdmin() {
  renderAdminPage(() => {
    window.location.hash = "#login";
    showLogin();
  });
}

export function showLogin() {
  document.getElementById("app-screen").style.display = "none";
  renderLoginPage(showApp);
}

export function showResetPassword(token) {
  document.getElementById("app-screen").style.display = "none";
  renderResetPasswordPage(token, () => {
    window.location.hash = "#login";
    showLogin();
  });
}

export function showVerifyEmail(token) {
  document.getElementById("app-screen").style.display = "none";
  renderVerifyEmailPage(token, () => {
    window.location.hash = "#login";
    showLogin();
  });
}

export function startApp() {
  if (window.location.hash.startsWith("#reset-password")) {
    showResetPassword(parseHashToken());
    return;
  }
  if (window.location.hash.startsWith("#verify-email")) {
    showVerifyEmail(parseHashToken());
    return;
  }
  isAuthenticated() ? showApp() : showLogin();
}
