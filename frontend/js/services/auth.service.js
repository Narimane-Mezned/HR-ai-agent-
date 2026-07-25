import { apiFormUrlEncoded } from "./api.js";

export async function login(username, password) {
  const data = await apiFormUrlEncoded("/login", { username, password });
  if (data.access_token) {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("username", username.trim().toLowerCase());
    return true;
  }
  throw new Error(data.error || "Login failed");
}

export async function register(username, password, companyName, email) {
  const data = await apiFormUrlEncoded("/register", {
    username,
    password,
    company_name: companyName,
    email: email || "",
  });
  if (data.access_token) {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("username", data.username);
    return true;
  }
  throw new Error(data.detail || "Registration failed");
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
}

export function isAuthenticated() {
  return !!localStorage.getItem("token");
}
export function currentUsername() {
  return localStorage.getItem("username") || "";
}
