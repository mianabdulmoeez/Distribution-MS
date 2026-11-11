"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth";

export default function Home() {
  const router = useRouter();
  const { user, initAuth } = useAuthStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    if (!user) {
      router.push("/login");
    } else if (user.is_platform_admin) {
      router.push("/platform");
    } else {
      router.push("/dashboard");
    }
  }, [user, router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center font-semibold text-slate-600">Loading DMS...</div>
    </div>
  );
}

