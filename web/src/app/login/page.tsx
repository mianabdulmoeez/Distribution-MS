"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [isPlatformAdmin, setIsPlatformAdmin] = useState(false);
  const [businessCode, setBusinessCode] = useState("ALNOOR");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isPlatformAdmin) {
        const res = await api.post("/auth/login/platform", { username, password });
        login(res.data.access_token, res.data.user);
        router.push("/platform");
      } else {
        const res = await api.post("/auth/login", {
          business_code: businessCode.toUpperCase(),
          username,
          password,
        });
        login(res.data.access_token, res.data.user);
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Authentication failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg border border-slate-200">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-slate-800">DMS Portal</h1>
          <p className="text-sm text-slate-500 mt-1">Distribution Management SaaS</p>
        </div>

        <div className="flex rounded-lg bg-slate-100 p-1 mb-6">
          <button
            type="button"
            className={`flex-1 py-1.5 text-sm font-medium rounded-md transition ${
              !isPlatformAdmin ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-900"
            }`}
            onClick={() => {
              setIsPlatformAdmin(false);
              setUsername("admin");
              setPassword("admin123");
            }}
          >
            Distributor Login
          </button>
          <button
            type="button"
            className={`flex-1 py-1.5 text-sm font-medium rounded-md transition ${
              isPlatformAdmin ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-900"
            }`}
            onClick={() => {
              setIsPlatformAdmin(true);
              setUsername("superadmin@dms.pk");
              setPassword("admin123");
            }}
          >
            Super Admin
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700 border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          {!isPlatformAdmin && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Business Code
              </label>
              <input
                type="text"
                required
                value={businessCode}
                onChange={(e) => setBusinessCode(e.target.value.toUpperCase())}
                placeholder="e.g. ALNOOR"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-green-600 focus:outline-none"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              {isPlatformAdmin ? "Super Admin Email" : "Username"}
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-green-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-green-600 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-green-600 py-2.5 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition shadow-sm"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

