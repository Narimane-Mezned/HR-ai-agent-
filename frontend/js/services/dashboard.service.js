import { apiFetch } from "./api.js";

export function getDashboardSummary() {
  return apiFetch("/dashboard/summary");
}
