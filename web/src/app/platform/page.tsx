"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";

export default function PlatformDashboardPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New business form state
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [city, setCity] = useState("Karachi");
  const [contactName, setContactName] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchBusinesses = async () => {
    try {
      const res = await api.get("/platform/businesses");
      setBusinesses(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBusinesses();
  }, []);

  const handleCreateBusiness = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/platform/businesses", {
        business_name: name,
        business_code: code.toUpperCase(),
        city,
        contact_name: contactName,
        contact_phone: contactPhone,
        owner_email: ownerEmail,
      });

      setName("");
      setCode("");
      setContactName("");
      setContactPhone("");
      setOwnerEmail("");
      await fetchBusinesses();
    } catch (err) {
      console.error("Failed to provision business", err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Platform Super Admin</h1>
          <p className="text-sm text-slate-500">Tenant Management &amp; Provisioning</p>
        </div>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
        >
          Sign Out
        </button>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
          Provision New Distributor Tenant
        </h2>
        <form onSubmit={handleCreateBusiness} className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <input
            type="text"
            required
            placeholder="Business Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            required
            placeholder="Business Code (e.g. KHYBER)"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            required
            placeholder="City (e.g. Peshawar)"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Contact Name"
            value={contactName}
            onChange={(e) => setContactName(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Contact Phone"
            value={contactPhone}
            onChange={(e) => setContactPhone(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="email"
            placeholder="Owner Email"
            value={ownerEmail}
            onChange={(e) => setOwnerEmail(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <div className="md:col-span-3">
            <button
              type="submit"
              disabled={creating}
              className="rounded-lg bg-green-600 px-6 py-2 font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition shadow-sm"
            >
              {creating ? "Provisioning..." : "Provision Distributor"}
            </button>
          </div>
        </form>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Business
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Code
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                City
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-slate-500">
                  Loading businesses...
                </td>
              </tr>
            ) : businesses.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-slate-500">
                  No businesses provisioned.
                </td>
              </tr>
            ) : (
              businesses.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-800">{b.business_name}</td>
                  <td className="px-6 py-4 font-mono font-bold text-slate-700">{b.business_code}</td>
                  <td className="px-6 py-4 text-slate-500">{b.city}</td>
                  <td className="px-6 py-4">
                    <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800 uppercase">
                      {b.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

