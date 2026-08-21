/**
 * Authentication and User Identity Types for Feynman Tutor AI.
 */

export type Role = "student" | "content_admin" | "sys_admin";

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: Role;
  targetExam?: string;
  avatarUrl?: string;
  createdAt?: string;
}

export interface AuthTokens {
  accessToken: string;
  tokenType: string;
  expiresIn?: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  fullName: string;
  targetExam?: string;
  role?: Role;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  setError: (error: string | null) => void;
  setLoading: (isLoading: boolean) => void;
}
