import { create } from "zustand";
import { User } from "../types";

interface AuthState {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  initAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  login: (token, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("dms_access_token", token);
      localStorage.setItem("dms_user", JSON.stringify(user));
    }
    set({ token, user });
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("dms_access_token");
      localStorage.removeItem("dms_user");
    }
    set({ token: null, user: null });
  },
  initAuth: () => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("dms_access_token");
      const userStr = localStorage.getItem("dms_user");
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr);
          set({ token, user });
        } catch {
          // ignore
        }
      }
    }
  },
}));

