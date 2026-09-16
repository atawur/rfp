"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { userService } from "@/services/userService";
import { useToast } from "@/context/ToastContext";
import { Sparkles, LogIn, UserPlus, Lock, Mail, User as UserIcon, Loader2, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { success, error } = useToast();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setLoading(true);
    try {
      await login(email.trim(), password);
      success("Logged in successfully! Welcome back.");
      router.push("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed";
      error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) return;

    setLoading(true);
    try {
      await userService.createUser({
        name: name.trim(),
        email: email.trim(),
        password,
        status: "active",
      });
      success("Account registered! Logging in...");
      await login(email.trim(), password);
      router.push("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed";
      error(msg);
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAdmin = () => {
    setEmail("admin@example.com");
    setPassword("adminpassword123!");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "clamp(16px, 4vw, 24px)",
      }}
    >
      <div
        className="glass-card animate-fade-in"
        style={{
          width: "100%",
          maxWidth: "460px",
          padding: "clamp(22px, 5vw, 36px)",
          background: "rgba(17, 24, 39, 0.85)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "16px",
          boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.8)",
          position: "relative",
        }}
      >
        {/* Brand Header */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px auto",
              boxShadow: "0 0 25px rgba(99, 102, 241, 0.5)",
            }}
          >
            <Sparkles size={28} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 800, color: "#ffffff", letterSpacing: "-0.02em" }}>
            RFP<span style={{ color: "var(--accent-cyan)" }}>INTELLECT</span>
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "4px" }}>
            Autonomous Procurement Intelligence Platform
          </p>
        </div>

        {/* Tab switch */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            background: "rgba(255, 255, 255, 0.04)",
            padding: "4px",
            borderRadius: "10px",
            marginBottom: "24px",
            border: "1px solid var(--border-subtle)",
          }}
        >
          <button
            type="button"
            onClick={() => setMode("login")}
            style={{
              padding: "8px",
              borderRadius: "8px",
              fontSize: "0.85rem",
              fontWeight: 600,
              backgroundColor: mode === "login" ? "rgba(99, 102, 241, 0.25)" : "transparent",
              color: mode === "login" ? "#ffffff" : "var(--text-muted)",
              border: mode === "login" ? "1px solid rgba(99, 102, 241, 0.4)" : "none",
              transition: "all 0.15s ease",
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            style={{
              padding: "8px",
              borderRadius: "8px",
              fontSize: "0.85rem",
              fontWeight: 600,
              backgroundColor: mode === "register" ? "rgba(99, 102, 241, 0.25)" : "transparent",
              color: mode === "register" ? "#ffffff" : "var(--text-muted)",
              border: mode === "register" ? "1px solid rgba(99, 102, 241, 0.4)" : "none",
              transition: "all 0.15s ease",
            }}
          >
            Create Account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={mode === "login" ? handleLogin : handleRegister} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {mode === "register" && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="register-name">Full Name</label>
              <div style={{ position: "relative" }}>
                <UserIcon size={16} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                <input
                  id="register-name"
                  type="text"
                  required
                  placeholder="Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="form-control"
                  style={{ paddingLeft: "40px" }}
                />
              </div>
            </div>
          )}

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" htmlFor="auth-email">Email Address</label>
            <div style={{ position: "relative" }}>
              <Mail size={16} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
              <input
                id="auth-email"
                type="email"
                required
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-control"
                style={{ paddingLeft: "40px" }}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" htmlFor="auth-password">Password</label>
            <div style={{ position: "relative" }}>
              <Lock size={16} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
              <input
                id="auth-password"
                type="password"
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-control"
                style={{ paddingLeft: "40px" }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: "100%", padding: "12px", marginTop: "8px" }}
          >
            {loading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : mode === "login" ? (
              <>
                <LogIn size={18} />
                <span>Sign In to Platform</span>
              </>
            ) : (
              <>
                <UserPlus size={18} />
                <span>Register & Continue</span>
              </>
            )}
          </button>
        </form>

        {/* Quick Demo Credentials Auto-Fill */}
        {mode === "login" && (
          <div style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "8px" }}>
              Instant Verification & Quick Testing:
            </span>
            <button
              type="button"
              onClick={fillDemoAdmin}
              style={{
                fontSize: "0.75rem",
                color: "var(--accent-cyan)",
                background: "rgba(6, 182, 212, 0.1)",
                border: "1px solid rgba(6, 182, 212, 0.25)",
                padding: "6px 12px",
                borderRadius: "6px",
                fontWeight: 600,
              }}
            >
              Fill Admin Credentials (admin@example.com)
            </button>
          </div>
        )}

        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <Link href="/" style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <span>Skip to Dashboard</span>
            <ArrowRight size={12} />
          </Link>
        </div>
      </div>
    </div>
  );
}
