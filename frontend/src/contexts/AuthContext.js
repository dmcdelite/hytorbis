import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/config";

axios.defaults.withCredentials = true;

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ email: "", password: "", name: "" });
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => { checkAuth(); }, []);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setCurrentUser(response.data);
    } catch (e) { setCurrentUser(null); }
  };

  const handleLogin = async () => {
    setAuthLoading(true); setAuthError("");
    try {
      const response = await axios.post(`${API}/auth/login`, { email: authForm.email, password: authForm.password });
      setCurrentUser(response.data);
      setShowAuthDialog(false);
      setAuthForm({ email: "", password: "", name: "" });
    } catch (e) { setAuthError(e.response?.data?.detail || "Login failed"); }
    setAuthLoading(false);
  };

  const handleRegister = async () => {
    setAuthLoading(true); setAuthError("");
    try {
      const response = await axios.post(`${API}/auth/register`, { email: authForm.email, password: authForm.password, name: authForm.name });
      setCurrentUser(response.data);
      setShowAuthDialog(false);
      setAuthForm({ email: "", password: "", name: "" });
    } catch (e) { setAuthError(e.response?.data?.detail || "Registration failed"); }
    setAuthLoading(false);
  };

  const handleLogout = async () => {
    try { await axios.post(`${API}/auth/logout`); } catch (e) {}
    setCurrentUser(null);
  };

  const value = {
    currentUser, setCurrentUser,
    showAuthDialog, setShowAuthDialog, authMode, setAuthMode,
    authForm, setAuthForm, authLoading, authError, setAuthError,
    handleLogin, handleRegister, handleLogout, checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
