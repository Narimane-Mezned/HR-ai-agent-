import { apiFormUrlEncoded } from "./api.js";

export async function login(username, password) {
  const data = await apiFormUrlEncoded("/login", { username, password });
  if (data.access_token) {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("username", username.trim().toLowerCase());
    localStorage.setItem("is_admin", data.is_admin ? "1" : "0");
    return true;
  }
  throw new Error(data.error || "Login failed");
}

export async function register(username, password, companyName, email) {
  return apiFormUrlEncoded("/register", {
    username,
    password,
    company_name: companyName,
    email,
  });
}

export async function verifyEmail(token) {
  return apiFormUrlEncoded("/verify-email", { token });
}

export async function forgotPassword(username) {
  return apiFormUrlEncoded("/forgot-password", { username });
}

export async function resetPassword(token, newPassword) {
  return apiFormUrlEncoded("/reset-password", {
    token,
    new_password: newPassword,
  });
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  localStorage.removeItem("is_admin");
}

export function isAuthenticated() {
  return !!localStorage.getItem("token");
}
export function currentUsername() {
  return localStorage.getItem("username") || "";
}
export function isAdmin() {
  return localStorage.getItem("is_admin") === "1";
}
