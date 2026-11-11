"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SalespersonsPage() {
  const [salespeople, setSalespeople] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("pass123");
  const [creating, setCreating] = useState(false);

  const fetchSalespeople = async () => {
    try {
      const res = await api.get("/users");
      setSalespeople(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSalespeople();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/users", {
        full_name: fullName,
        username: username.toLowerCase(),
        phone,
        password,
      });
      setFullName("");
      setUsername("");
      setPhone("");
      await fetchSalespeople();
    } catch (err) {
      console.error("Failed to add salesperson", err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Sales Team Management</h1>
        <p className="text-sm text-slate-500">Manage field sales representatives and accounts</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
          Add New Salesperson
        </h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
          <input
            type="text"
            required
            placeholder="Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            required
            placeholder="Username (e.g. salesman1)"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Phone Number (+92...)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="password"
            placeholder="Temporary Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <div className="md:col-span-4">
            <button
              type="submit"
              disabled={creating}
              className="rounded-lg bg-green-600 px-4 py-2 font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition shadow-sm"
            >
              {creating ? "Adding..." : "Add Salesperson"}
            </button>
          </div>
        </form>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Name
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Username
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Phone
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
                  Loading sales team...
                </td>
              </tr>
            ) : salespeople.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-slate-500">
                  No salespeople registered yet.
                </td>
              </tr>
            ) : (
              salespeople.map((sp) => (
                <tr key={sp.membership_id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-800">{sp.full_name}</td>
                  <td className="px-6 py-4 font-mono text-slate-600">@{sp.username}</td>
                  <td className="px-6 py-4 text-slate-500">{sp.phone || "—"}</td>
                  <td className="px-6 py-4">
                    <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800 uppercase">
                      {sp.status}
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
