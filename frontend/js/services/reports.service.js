import { apiFetch } from "./api.js";

export function getReportSummary() {
  return apiFetch("/reports/summary");
}
