import React, { createContext, useContext, useState, useEffect } from "react";
import { AuthApi, UserResponse, TokenResponse } from "../api/auth";

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  register: (userData: { email: string; full_name: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  async function initializeAuth() {
    const token = localStorage.getItem("careeros_access_token");
    if (token) {
      try {
        const currentUser = await AuthApi.me();
        setUser(currentUser);
      } catch {
        // Token invalid or expired
        localStorage.removeItem("careeros_access_token");
        localStorage.removeItem("careeros_refresh_token");
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  }

  useEffect(() => {
    void initializeAuth();
  }, []);

  async function login(credentials: { email: string; password: string }) {
    const response: TokenResponse = await AuthApi.login(credentials);
    localStorage.setItem("careeros_access_token", response.access_token);
    localStorage.setItem("careeros_refresh_token", response.refresh_token);
    const currentUser = await AuthApi.me();
    setUser(currentUser);
  }

  async function register(userData: { email: string; full_name: string; password: string }) {
    // Register the user (returns user data)
    await AuthApi.register(userData);
    // Then log in to get token
    const loginResponse: TokenResponse = await AuthApi.login({
      email: userData.email,
      password: userData.password,
    });
    localStorage.setItem("careeros_access_token", loginResponse.access_token);
    localStorage.setItem("careeros_refresh_token", loginResponse.refresh_token);
    const currentUser = await AuthApi.me();
    setUser(currentUser);
  }

  async function logout() {
    try {
      await AuthApi.logout();
    } finally {
      localStorage.removeItem("careeros_access_token");
      localStorage.removeItem("careeros_refresh_token");
      setUser(null);
    }
  }

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
