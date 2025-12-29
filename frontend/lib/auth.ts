import axios from "axios";

// Auth API client with credentials
const authApi = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Types
export type UserRole = "admin" | "user";
export type UserStatus = "pending" | "approved" | "rejected";

export interface User {
  id: string;
  email: string;
  name: string;
  picture_url: string | null;
  google_id: string;
  role: UserRole;
  status: UserStatus;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}

// Google OAuth URL
export function getGoogleOAuthUrl(): string {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  const redirectUri = `${window.location.origin}/login`;

  const params = new URLSearchParams({
    client_id: clientId || "",
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "consent",
  });

  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
}

// Auth API functions
export const authService = {
  // Exchange Google code for session
  async googleAuth(code: string): Promise<AuthResponse> {
    const redirectUri = `${window.location.origin}/login`;
    const response = await authApi.post("/auth/google", {
      code,
      redirect_uri: redirectUri,
    });
    return response.data;
  },

  // Get current user
  async getMe(): Promise<User> {
    const response = await authApi.get("/auth/me");
    return response.data;
  },

  // Logout
  async logout(): Promise<void> {
    await authApi.post("/auth/logout");
  },
};

// Admin API functions
export const adminService = {
  // List all users
  async listUsers(statusFilter?: UserStatus): Promise<User[]> {
    const params = statusFilter ? { status_filter: statusFilter } : {};
    const response = await authApi.get("/admin/users", { params });
    return response.data;
  },

  // Approve user
  async approveUser(userId: string): Promise<User> {
    const response = await authApi.put(`/admin/users/${userId}/approve`);
    return response.data;
  },

  // Reject user
  async rejectUser(userId: string): Promise<User> {
    const response = await authApi.put(`/admin/users/${userId}/reject`);
    return response.data;
  },

  // Delete user
  async deleteUser(userId: string): Promise<void> {
    await authApi.delete(`/admin/users/${userId}`);
  },
};

export default authApi;
