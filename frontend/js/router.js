import {
  isAuthenticated,
  currentUsername,
  logout,
} from "./services/auth.service.js";
import { renderLoginPage } from "./pages/login.page.js";
import { renderDashboardPage } from "./pages/dashboard.page.js";
import { renderScreeningPage } from "./pages/screening.page.js";
import { renderMatchingPage } from "./pages/matching.page.js";
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

function handleHashChange() {
  if (!isAuthenticated()) {
    if (window.location.hash !== "#login") showLogin();
    return;
  }
  const tabKey = window.location.hash.replace("#", "");
  navigate(ROUTES[tabKey] ? tabKey : "dashboard");
}

window.addEventListener("hashchange", handleHashChange);

export function showApp() {
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

export function showLogin() {
  document.getElementById("app-screen").style.display = "none";
  renderLoginPage(showApp);
}

export function startApp() {
  isAuthenticated() ? showApp() : showLogin();
}
