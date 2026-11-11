"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Area, Shop } from "@/types";

export default function PlansPage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [salespeople, setSalespeople] = useState<any[]>([]);
  const [shops, setShops] = useState<Shop[]>([]);
  const [loading, setLoading] = useState(true);

  // Form state
  const [selectedSp, setSelectedSp] = useState("");
  const [serviceDate, setServiceDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [selectedShopId, setSelectedShopId] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const [plansRes, spRes, shopsRes] = await Promise.all([
        api.get("/plans"),
        api.get("/users"),
        api.get("/shops"),
      ]);
      setPlans(plansRes.data);
      setSalespeople(spRes.data);
      setShops(shopsRes.data);
      if (spRes.data.length > 0 && !selectedSp) {
        setSelectedSp(spRes.data[0].membership_id);
      }
      if (shopsRes.data.length > 0 && !selectedShopId) {
        setSelectedShopId(shopsRes.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load plan data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddStop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSp || !serviceDate || !selectedShopId) return;

    setSubmitting(true);
    try {
      await api.post("/plans", {
        membership_id: selectedSp,
        service_date: serviceDate,
        stops: [{ shop_id: selectedShopId, sequence_order: plans.length + 1 }],
      });
      await fetchData();
    } catch (err) {
      console.error("Failed to add stop", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Daily Visit Plans</h1>
        <p className="text-sm text-slate-500">Schedule and assign daily route stops to sales team</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
          Schedule Daily Route Stop
        </h2>
        <form onSubmit={handleAddStop} className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Salesperson</label>
            <select
              value={selectedSp}
              onChange={(e) => setSelectedSp(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
            >
              {salespeople.map((sp) => (
                <option key={sp.membership_id} value={sp.membership_id}>
                  {sp.full_name} (@{sp.username})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Service Date</label>
            <input
              type="date"
              required
              value={serviceDate}
              onChange={(e) => setServiceDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Assigned Shop</label>
            <select
              value={selectedShopId}
              onChange={(e) => setSelectedShopId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
            >
              {shops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.city})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-green-600 py-2 font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition shadow-sm"
            >
              {submitting ? "Adding..." : "Add to Plan"}
            </button>
          </div>
        </form>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">Service Date</th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">Stop Seq</th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">Store Name</th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">Address</th>
              <th className="px-6 py-3 text-center font-semibold text-slate-500 uppercase text-xs">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">Loading visit plans...</td>
              </tr>
            ) : plans.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">No scheduled stops found.</td>
              </tr>
            ) : (
              plans.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono font-medium text-slate-700">{p.service_date}</td>
                  <td className="px-6 py-4 font-bold text-slate-800">#{p.sequence_order}</td>
                  <td className="px-6 py-4 font-medium text-slate-800">{p.shop_name}</td>
                  <td className="px-6 py-4 text-slate-500">{p.shop_address}</td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-semibold uppercase ${
                        p.status === "completed"
                          ? "bg-green-100 text-green-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {p.status}
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

