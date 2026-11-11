"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Area } from "@/types";

export default function AreasPage() {
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchAreas = async () => {
    try {
      const res = await api.get("/areas");
      setAreas(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAreas();
  }, []);

  const handleCreateArea = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    setCreating(true);
    try {
      await api.post("/areas", { name, description });
      setName("");
      setDescription("");
      await fetchAreas();
    } catch (err) {
      console.error("Failed to create area", err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Areas &amp; Territories</h1>
        <p className="text-sm text-slate-500">Define distribution territories and routes</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
          Add New Area
        </h2>
        <form onSubmit={handleCreateArea} className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            type="text"
            required
            placeholder="Area Name (e.g. Saddar Market)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Description / Route"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-green-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={creating}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition"
          >
            {creating ? "Adding..." : "Add Area"}
          </button>
        </form>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                Area Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-sm">
            {loading ? (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-center text-slate-500">
                  Loading areas...
                </td>
              </tr>
            ) : areas.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-center text-slate-500">
                  No areas defined yet.
                </td>
              </tr>
            ) : (
              areas.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-800">{a.name}</td>
                  <td className="px-6 py-4 text-slate-500">{a.description || "—"}</td>
                  <td className="px-6 py-4">
                    <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                      Active
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

