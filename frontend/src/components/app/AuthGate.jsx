import { useState } from "react";
import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LogIn, UserCircle, Loader2, Sparkles, Map, Users, Wand2 } from "lucide-react";

export function AuthGate() {
  const ctx = useApp();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    ctx.setAuthForm(form);

    if (mode === "login") {
      ctx.authForm.email = form.email;
      ctx.authForm.password = form.password;
      try {
        const axios = (await import("axios")).default;
        const { API } = await import("@/config");
        const response = await axios.post(`${API}/auth/login`, { email: form.email, password: form.password }, { withCredentials: true });
        ctx.checkAuth();
      } catch (e) {
        setError(e.response?.data?.detail || "Login failed");
      }
    } else {
      try {
        const axios = (await import("axios")).default;
        const { API } = await import("@/config");
        const response = await axios.post(`${API}/auth/register`, { email: form.email, password: form.password, name: form.name }, { withCredentials: true });
        ctx.checkAuth();
      } catch (e) {
        setError(e.response?.data?.detail || "Registration failed");
      }
    }
    setLoading(false);
  };

  return (
    <div className="auth-gate" data-testid="auth-gate">
      <div className="auth-gate-bg">
        <div className="auth-gate-grid" />
      </div>

      <div className="auth-gate-content">
        <div className="auth-gate-hero">
          <img src="/hytorbis-logo.png" alt="Hyt Orbis" className="auth-gate-logo" />
          <h1 className="auth-gate-title">Hyt Orbis</h1>
          <p className="auth-gate-subtitle">World Builder</p>

          <div className="auth-gate-features">
            <div className="auth-gate-feature">
              <Map size={20} />
              <span>Build worlds up to 512x512</span>
            </div>
            <div className="auth-gate-feature">
              <Wand2 size={20} />
              <span>AI-powered world generation</span>
            </div>
            <div className="auth-gate-feature">
              <Users size={20} />
              <span>Real-time collaboration</span>
            </div>
            <div className="auth-gate-feature">
              <Sparkles size={20} />
              <span>Export in multiple formats</span>
            </div>
          </div>
        </div>

        <div className="auth-gate-card" data-testid="auth-gate-card">
          <h2 className="auth-gate-card-title">
            {mode === "login" ? "Welcome Back" : "Create Account"}
          </h2>
          <p className="auth-gate-card-desc">
            {mode === "login" ? "Sign in to start building" : "Join and start creating worlds"}
          </p>

          {error && <div className="auth-gate-error" data-testid="auth-gate-error">{error}</div>}

          <form onSubmit={handleSubmit} className="auth-gate-form">
            {mode === "register" && (
              <div className="form-group">
                <Label>Name</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Your name"
                  data-testid="auth-gate-name"
                />
              </div>
            )}
            <div className="form-group">
              <Label>Email</Label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
                required
                data-testid="auth-gate-email"
              />
            </div>
            <div className="form-group">
              <Label>Password</Label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Enter password"
                required
                data-testid="auth-gate-password"
              />
            </div>
            <Button type="submit" disabled={loading || !form.email || !form.password} className="auth-gate-submit" data-testid="auth-gate-submit">
              {loading ? <Loader2 className="animate-spin" size={16} /> : mode === "login" ? <LogIn size={16} /> : <UserCircle size={16} />}
              {mode === "login" ? "Sign In" : "Create Account"}
            </Button>
          </form>

          <div className="auth-gate-switch">
            {mode === "login" ? (
              <span>New here? <button type="button" className="link-btn" onClick={() => { setMode("register"); setError(""); }} data-testid="auth-gate-switch-register">Create an account</button></span>
            ) : (
              <span>Already have an account? <button type="button" className="link-btn" onClick={() => { setMode("login"); setError(""); }} data-testid="auth-gate-switch-login">Sign in</button></span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
