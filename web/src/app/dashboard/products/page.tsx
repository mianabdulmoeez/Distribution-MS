"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Product } from "@/types";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // New product form
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [unit, setUnit] = useState("pack");
  const [pricePkr, setPricePkr] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // CSV Import state
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [importing, setImporting] = useState(false);

  const fetchProducts = async () => {
    try {
      const res = await api.get("/products");
      setProducts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !sku || !pricePkr) return;
    setSubmitting(true);
    try {
      await api.post("/products", {
        name,
        sku: sku.toUpperCase(),
        unit,
        price_pkr: parseFloat(pricePkr),
      });
      setName("");
      setSku("");
      setPricePkr("");
      await fetchProducts();
    } catch (err) {
      console.error("Failed to add product", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePreviewCsv = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;
    setImporting(true);
    const formData = new FormData();
    formData.append("file", csvFile);

    try {
      const res = await api.post("/products/import/preview", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPreviewData(res.data);
    } catch (err) {
      console.error("Failed to preview product CSV", err);
    } finally {
      setImporting(false);
    }
  };

  const handleCommitCsv = async () => {
    if (!previewData?.valid_preview) return;
    setImporting(true);
    const validRows = previewData.valid_preview.map((v: any) => v.row);

    try {
      await api.post("/products/import/commit", { valid_rows: validRows });
      setPreviewData(null);
      setCsvFile(null);
      await fetchProducts();
    } catch (err) {
      console.error("Failed to commit product CSV", err);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Product Catalog</h1>
        <p className="text-sm text-slate-500">Manage SKUs, selling units, and PKR pricing</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Manual Product Add */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
            Add New Product
          </h2>
          <form onSubmit={handleCreate} className="space-y-3 text-sm">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Product Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Tapal Danedar Tea 400g"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">SKU</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. TAPAL-400G"
                  value={sku}
                  onChange={(e) => setSku(e.target.value.toUpperCase())}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Unit</label>
                <select
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
                >
                  <option value="pack">Pack</option>
                  <option value="piece">Piece</option>
                  <option value="carton">Carton</option>
                  <option value="box">Box</option>
                  <option value="bottle">Bottle</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">PKR Price</label>
              <input
                type="number"
                step="0.01"
                required
                placeholder="e.g. 650.00"
                value={pricePkr}
                onChange={(e) => setPricePkr(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-green-600 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-green-600 py-2 font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition shadow-sm"
            >
              {submitting ? "Saving..." : "Add Product"}
            </button>
          </form>
        </div>

        {/* Bulk CSV Import */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-600 mb-4">
            Bulk CSV Import
          </h2>
          <form onSubmit={handlePreviewCsv} className="space-y-4 text-sm">
            <p className="text-xs text-slate-500">
              CSV file headers must be: <code className="bg-slate-100 p-1 rounded font-mono">name,sku,unit,price_pkr</code>
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
            />
            <button
              type="submit"
              disabled={!csvFile || importing}
              className="w-full rounded-lg border border-green-600 py-2 font-semibold text-green-700 hover:bg-green-50 disabled:opacity-50 transition shadow-sm"
            >
              {importing ? "Validating..." : "Preview CSV Import"}
            </button>
          </form>

          {previewData && (
            <div className="mt-4 pt-4 border-t border-slate-200 space-y-3">
              <div className="text-xs flex justify-between">
                <span className="text-green-700 font-semibold">{previewData.valid_count} Valid Rows</span>
                <span className="text-red-600 font-semibold">{previewData.invalid_count} Invalid Rows</span>
              </div>
              {previewData.valid_count > 0 && (
                <button
                  type="button"
                  onClick={handleCommitCsv}
                  disabled={importing}
                  className="w-full rounded-lg bg-green-600 py-2 font-semibold text-white hover:bg-green-700 disabled:opacity-50 transition shadow-sm"
                >
                  {importing ? "Importing..." : `Confirm & Activate ${previewData.valid_count} Products`}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Catalog Table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">Product Name</th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">SKU</th>
              <th className="px-6 py-3 text-left font-semibold text-slate-500 uppercase text-xs">Selling Unit</th>
              <th className="px-6 py-3 text-right font-semibold text-slate-500 uppercase text-xs">Price (PKR)</th>
              <th className="px-6 py-3 text-center font-semibold text-slate-500 uppercase text-xs">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">Loading catalog...</td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-slate-500">No products configured.</td>
              </tr>
            ) : (
              products.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-slate-800">{p.name}</td>
                  <td className="px-6 py-4 font-mono text-slate-600">{p.sku}</td>
                  <td className="px-6 py-4 capitalize text-slate-600">{p.unit}</td>
                  <td className="px-6 py-4 text-right font-semibold text-slate-800">
                    Rs. {p.price_pkr.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">
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

