"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Order } from "@/types";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchOrders = async () => {
    try {
      const res = await api.get("/orders");
      setOrders(res.data);
    } catch (err) {
      console.error("Failed to load orders", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleConfirm = async (orderId: string) => {
    try {
      await api.post(`/orders/${orderId}/confirm`, { notes: "Confirmed from distributor web dashboard" });
      await fetchOrders();
    } catch (err) {
      console.error("Failed to confirm order", err);
    }
  };

  const handleDispatch = async (orderId: string) => {
    try {
      await api.post(`/orders/${orderId}/dispatch`, { dispatch_reference: "WEB-DISP-01" });
      await fetchOrders();
    } catch (err) {
      console.error("Failed to dispatch order", err);
    }
  };

  const handleDeliver = async (orderId: string) => {
    try {
      await api.post(`/orders/${orderId}/deliver`, { recipient: "Store Owner" });
      await fetchOrders();
    } catch (err) {
      console.error("Failed to mark delivered", err);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Orders Inbox</h1>
        <p className="text-sm text-slate-500">Review field visits, confirm quantities, and manage dispatch</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Store
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Origin
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Total (PKR)
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Status
              </th>
              <th className="px-6 py-3 text-right font-semibold text-slate-500 uppercase text-xs">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">
                  Loading orders...
                </td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">
                  No orders received yet.
                </td>
              </tr>
            ) : (
              orders.map((o) => (
                <tr key={o.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-800">{o.shop_name}</div>
                    <div className="text-xs text-slate-500">{o.shop_address}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="capitalize text-slate-600">{o.origin}</span>
                  </td>
                  <td className="px-6 py-4 font-semibold text-slate-800">
                    Rs. {o.total_amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-semibold uppercase ${
                        o.status === "delivered"
                          ? "bg-green-100 text-green-800"
                          : o.status === "submitted"
                          ? "bg-amber-100 text-amber-800"
                          : o.status === "dispatched"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {o.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {o.status === "submitted" && (
                      <button
                        onClick={() => handleConfirm(o.id)}
                        className="rounded bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-700 transition"
                      >
                        Confirm
                      </button>
                    )}
                    {o.status === "confirmed" && (
                      <button
                        onClick={() => handleDispatch(o.id)}
                        className="rounded bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-700 transition"
                      >
                        Dispatch
                      </button>
                    )}
                    {o.status === "dispatched" && (
                      <button
                        onClick={() => handleDeliver(o.id)}
                        className="rounded bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-700 transition"
                      >
                        Mark Delivered
                      </button>
                    )}
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

