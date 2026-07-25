export const API_BASE = "";

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(API_BASE + path, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.hash = "#login";
  }

  let data;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const message =
      (data && (data.detail || data.error)) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export function apiForm(path, formData) {
  return apiFetch(path, { method: "POST", body: formData });
}

export function apiFormUrlEncoded(path, dataObj, method = "POST") {
  return apiFetch(path, {
    method,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(dataObj),
  });
}
export async function apiFormPut(path, formData) {
  return apiFetch(path, { method: "PUT", body: formData });
}
