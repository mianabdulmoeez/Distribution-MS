"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const navItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Areas & Routes", href: "/dashboard/areas" },
    { label: "Sales Team", href: "/dashboard/salespersons" },
    { label: "Shops Directory", href: "/dashboard/shops" },
    { label: "Visit Plans", href: "/dashboard/plans" },
    { label: "Products Catalog", href: "/dashboard/products" },
    { label: "Orders Inbox", href: "/dashboard/orders" },
    { label: "Reports & Exports", href: "/dashboard/reports" },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between">
        <div>
          <div className="p-6 border-b border-slate-200">
            <h2 className="text-lg font-bold text-slate-800">
              {user?.business_name || "Distributor Portal"}
            </h2>
            <span className="inline-block mt-1 rounded bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">
              {user?.business_code || "DMS"}
            </span>
          </div>
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block rounded-lg px-3 py-2 text-sm font-medium transition ${
                    active
                      ? "bg-green-50 text-green-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-slate-200">
          <div className="text-xs text-slate-500 mb-2">
            Logged in as <span className="font-semibold text-slate-700">{user?.full_name}</span>
          </div>
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="w-full rounded-md border border-slate-300 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-8 overflow-y-auto">{children}</main>
    </div>
  );
}

