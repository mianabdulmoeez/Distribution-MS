"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DashboardSummary } from "@/types";

export default function DashboardOverviewPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const res = await api.get("/reports/dashboard");
        setData(res.data);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="text-slate-500">Loading daily metrics...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Operational Overview</h1>
        <p className="text-sm text-slate-500">Today&apos;s field activity &amp; orders summary</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Planned Coverage</div>
          <div className="mt-2 text-3xl font-bold text-slate-800">
            {data?.planned_coverage.coverage_percentage?.toFixed(1) || 0}%
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {data?.planned_coverage.completed_stops || 0} of {data?.planned_coverage.total_stops || 0} stops completed
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Verified Visits</div>
          <div className="mt-2 text-3xl font-bold text-green-600">
            {data?.visits.total_verified || 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">Foreground GPS verified inside radius</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Orders Placed</div>
          <div className="mt-2 text-3xl font-bold text-slate-800">
            {data?.visits.order_placed || 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {data?.visits.no_order || 0} &quot;No Order&quot; verified visits
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Awaiting Action</div>
          <div className="mt-2 text-3xl font-bold text-amber-600">
            {data?.orders_pending_confirmation || 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">Orders submitted awaiting confirmation</div>
        </div>
      </div>
    </div>
  );
}

