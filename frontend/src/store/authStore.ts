import { create } from "zustand";

interface AuthState {
  token: string | null;
  role: string | null;
  username: string | null;
  login: (token: string, role: string, username: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem("token"),
  role: localStorage.getItem("role"),
  username: localStorage.getItem("username"),
  login: (token, role, username) => {
    localStorage.setItem("token", token);
    localStorage.setItem("role", role);
    localStorage.setItem("username", username);
    set({ token, role, username });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    set({ token: null, role: null, username: null });
  },
  isAuthenticated: () => {
    return !!get().token;
  },
}));
