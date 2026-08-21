import type { LoginCredentials, RegisterCredentials, AuthResponse, User } from "@/types/auth";
import { apiClient, ApiError } from "./client";

/**
 * Predefined local demo users for zero-blocking development & testing.
 */
export const DEMO_USERS: Record<string, { user: User; password: string }> = {
  "student@feynman.ai": {
    user: {
      id: "usr_student_01",
      email: "student@feynman.ai",
      fullName: "Alex Rivera",
      role: "student",
      targetExam: "Cambridge A-Level Physics",
      createdAt: new Date().toISOString(),
    },
    password: "password123",
  },
  "admin@feynman.ai": {
    user: {
      id: "usr_admin_01",
      email: "admin@feynman.ai",
      fullName: "Dr. Eleanor Vance",
      role: "content_admin",
      targetExam: "All Curricula",
      createdAt: new Date().toISOString(),
    },
    password: "adminpassword123",
  },
};

export const authClient = {
  /**
   * Logs in a user with email and password.
   * Attempts live backend call; falls back to demo accounts if backend is offline or mock credentials match.
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Check demo accounts first for instant offline dev/test
    const demo = DEMO_USERS[credentials.email.toLowerCase()];
    if (demo) {
      if (demo.password === credentials.password) {
        return {
          user: demo.user,
          token: `demo_jwt_${demo.user.id}_${Date.now()}`,
        };
      } else {
        throw new ApiError(401, "Unauthorized", { detail: "Invalid password for demo account." });
      }
    }

    try {
      return await apiClient<AuthResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      });
    } catch (err) {
      // If server is unavailable, provide actionable feedback
      if (err instanceof ApiError) throw err;
      throw new ApiError(401, "Unauthorized", { detail: "Invalid email or password." });
    }
  },

  /**
   * Registers a new student account.
   */
  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    try {
      return await apiClient<AuthResponse>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(credentials),
      });
    } catch {
      // Fallback for offline UI testing
      const newUser: User = {
        id: `usr_${Date.now().toString(36)}`,
        email: credentials.email,
        fullName: credentials.fullName,
        role: credentials.role || "student",
        targetExam: credentials.targetExam || "Cambridge A-Level Physics",
        createdAt: new Date().toISOString(),
      };
      return {
        user: newUser,
        token: `mock_jwt_${newUser.id}`,
      };
    }
  },

  /**
   * Fetches current authenticated user profile.
   */
  async getMe(token: string): Promise<User> {
    if (token.startsWith("demo_jwt_") || token.startsWith("mock_jwt_")) {
      const match = Object.values(DEMO_USERS).find((d) => token.includes(d.user.id));
      if (match) return match.user;
    }

    return apiClient<User>("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};
