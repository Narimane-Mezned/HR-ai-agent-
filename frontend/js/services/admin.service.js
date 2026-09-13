import { apiFetch, apiFormUrlEncoded } from "./api.js";

export async function listPendingUsers() {
  return apiFetch("/admin/pending-users");
}

export async function approveUser(username) {
  return apiFormUrlEncoded(
    `/admin/users/${encodeURIComponent(username)}/approve`,
    {},
  );
}

export async function rejectUser(username) {
  return apiFormUrlEncoded(
    `/admin/users/${encodeURIComponent(username)}/reject`,
    {},
  );
}
