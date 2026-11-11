"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Area, Shop } from "@/types";

export default function ShopsPage() {
  const [shops, setShops] = useState<Shop[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);

  // New shop modal/form state
  const [name, setName] = useState("");
  const [areaId, setAreaId] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("Karachi");
  const [lat, setLat] = useState("24.8607");
  const [lng, setLng] = useState("67.0011");
  const [entrancePin, setEntrancePin] = useState("1234");
  const [contactPerson, setContactPerson] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchShopsAndAreas = async () => {
    try {
      const [shopsRes, areasRes] = await Promise.all([
        api.get("/shops"),
        api.get("/areas"),
      ]);
      setShops(shopsRes.data);
      setAreas(areasRes.data);
      if (areasRes.data.length > 0 && !areaId) {
        setAreaId(areasRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShopsAndAreas();
  }, []);

  const handleCreateShop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !areaId || !address || !entrancePin) return;

    setSubmitting(true);
    try {
      await api.post("/shops", {
        area_id: areaId,
        name,
        address,
        city,
        entrance_lat: parseFloat(lat),
        entrance_lng: parseFloat(lng),
        entrance_pin: entrancePin,
        contact_person: contactPerson || null,
        contact_phone: contactPhone || null,
        radius_meters: 10.0,
      });

      setName("");
      setAddress("");
      setContactPerson("");
      setContactPhone("");
      await fetchShopsAndAreas();
    } catch (err) {
      console.error("Failed to create shop", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Shops Directory</h1>
        <p className="text-sm text-slate-500">Manage approved retail stores with entrance pins</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
          Register Approved Store
        </h2>
        <form onSubmit={handleCreateShop} className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
          <input
            type="text"
            required
            placeholder="Shop Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <select
            value={areaId}
            onChange={(e) => setAreaId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          >
            {areas.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
          <input
            type="text"
            required
            placeholder="Address / Landmark"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            required
            placeholder="Entrance PIN (e.g. 1234)"
            value={entrancePin}
            onChange={(e) => setEntrancePin(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Latitude (e.g. 24.8607)"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Longitude (e.g. 67.0011)"
            value={lng}
            onChange={(e) => setLng(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Contact Person"
            value={contactPerson}
            onChange={(e) => setContactPerson(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-green-600 px-4 py-2 font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition shadow-sm"
          >
            {submitting ? "Saving..." : "Register Store"}
          </button>
        </form>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Store Name
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Address &amp; City
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Entrance PIN
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Radius
              </th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">
                  Loading shops directory...
                </td>
              </tr>
            ) : shops.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">
                  No shops registered yet.
                </td>
              </tr>
            ) : (
              shops.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-800">{s.name}</td>
                  <td className="px-6 py-4 text-slate-500">
                    {s.address}, {s.city}
                  </td>
                  <td className="px-6 py-4 font-mono font-bold text-green-700">
                    {s.entrance_pin}
                  </td>
                  <td className="px-6 py-4 text-slate-500">{s.radius_meters}m</td>
                  <td className="px-6 py-4">
                    <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">
                      Approved
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

