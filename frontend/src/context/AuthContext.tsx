// src/types/user.ts

export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string;
  national_id: string;
  phone_number: string;
  groups: string[];
  roles: string;
  photo_url: string | null;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface RegisterData {
  username: string;
  password: string;
  full_name: string;
  national_id: string;
  phone_number: string;
  email: string;
}

export interface RegisterResponse {
  user: RegisterData;
  token: string;
}

export interface RolesResponse {
  username: string;
  roles: string[];
}

// frontend/src/context/AuthContext.tsx
import {
  createContext,
  useState,
  useContext,
  useEffect,
  ReactNode,
} from "react";

// import { User, LoginResponse } from "../types/user";

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, userData: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
  userRoles: string[];
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [userRoles, setUserRoles] = useState<string[]>([]);

  // Load token and user from localStorage on initial render
  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("user");

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser) as User;
        setToken(storedToken);
        setUser(parsedUser);
        setUserRoles(parsedUser.groups || []);
        console.log("✅ Loaded user from storage:", parsedUser.username);
      } catch (e) {
        console.error("Failed to parse stored user:", e);
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
      }
    }
  }, []);

  const login = (newToken: string, userData: User) => {
    console.log(
      "📝 Login called with token:",
      newToken.substring(0, 10) + "...",
    );
    console.log("📝 User data:", userData);

    // Save to state
    setToken(newToken);
    setUser(userData);
    setUserRoles(userData.groups || []);

    // Save to localStorage
    localStorage.setItem("access_token", newToken);
    localStorage.setItem("user", JSON.stringify(userData));

    console.log("✅ Login successful - token saved");
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setUserRoles([]);
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    console.log("👋 Logged out");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        userRoles,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
