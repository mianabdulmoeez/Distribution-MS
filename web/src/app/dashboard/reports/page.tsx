"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ReportsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSummary() {
      try {
        const res = await api.get("/reports/weekly-summary");
        setSummary(res.data);
      } catch (err) {
        console.error("Failed to load weekly summary", err);
      } finally {
        setLoading(false);
      }
    }
    fetchSummary();
  }, []);

  const handleExportCsv = () => {
    const token = localStorage.getItem("dms_access_token");
    window.open(`http://localhost:8000/api/v1/reports/export/csv?token=${token}`, "_blank");
  };

  if (loading) {
    return <div className="text-slate-500">Loading weekly summary reports...</div>;
  }

  const m = summary?.metrics;
  const ob = m?.outcome_breakdown;
  const ot = m?.order_totals;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Weekly Reports &amp; Reconciliation</h1>
          <p className="text-sm text-slate-500">
            Period: {summary?.period?.start_date} to {summary?.period?.end_date} ({summary?.period?.timezone})
          </p>
        </div>
        <button
          onClick={handleExportCsv}
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 transition shadow-sm"
        >
          Export CSV Report
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Planned Route Coverage</div>
          <div className="mt-2 text-3xl font-bold text-slate-800">{m?.planned_coverage_pct ?? 0}%</div>
          <div className="mt-1 text-xs text-slate-500">
            {m?.verified_completed_stops || 0} completed of {m?.total_assigned_stops || 0} assigned
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Verified Visits Count</div>
          <div className="mt-2 text-3xl font-bold text-green-600">{m?.distinct_verified_visits || 0}</div>
          <div className="mt-1 text-xs text-slate-500">
            {ob?.order_placed || 0} Orders, {ob?.no_order || 0} No-Order
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Field Conversion Rate</div>
          <div className="mt-2 text-3xl font-bold text-slate-800">{m?.field_conversion_pct ?? 0}%</div>
          <div className="mt-1 text-xs text-slate-500">
            Orders from verified field visits / Total visits
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
          Visit Outcomes Breakdown
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Order Placed</div>
            <div className="text-xl font-bold text-slate-800 mt-1">{ob?.order_placed || 0}</div>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">No Order Verified</div>
            <div className="text-xl font-bold text-slate-800 mt-1">{ob?.no_order || 0}</div>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Shop Closed</div>
            <div className="text-xl font-bold text-slate-800 mt-1">{ob?.shop_closed || 0}</div>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Contact Unavailable</div>
            <div className="text-xl font-bold text-slate-800 mt-1">{ob?.contact_unavailable || 0}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

