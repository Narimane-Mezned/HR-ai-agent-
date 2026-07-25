const TABS = [
  { key: "dashboard", label: "Dashboard" },
  { key: "screening", label: "Screening" },
  { key: "matching", label: "Matching" },
  { key: "scheduling", label: "Scheduling" },
];

export function renderSidebar(activeKey, onNavigate, onLogout, username) {
  const nav = document.getElementById("tabs");
  nav.innerHTML = "";
  TABS.forEach((tab) => {
    const div = document.createElement("div");
    div.className = "tab" + (tab.key === activeKey ? " active" : "");
    div.innerText = tab.label;
    div.onclick = () => onNavigate(tab.key);
    nav.appendChild(div);
  });
  document.getElementById("sidebar-username").innerText = username;
  document.getElementById("logout-btn").onclick = onLogout;
}
