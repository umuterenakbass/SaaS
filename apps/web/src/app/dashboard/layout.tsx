"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getAccessToken, getSiteId, getUserRole } from "@/lib/auth-storage";

// Sakin rolünün erişebileceği dashboard alt rotaları
const RESIDENT_ALLOWED_PATHS = ["/dashboard/portal"];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = getAccessToken();
    const siteId = getSiteId();
    const role = getUserRole();

    if (!token || !siteId) {
      router.replace("/login");
      return;
    }

    // Sakin rolü yalnızca izin verilen sayfalara erişebilir
    if (role === "resident" && !RESIDENT_ALLOWED_PATHS.includes(pathname)) {
      router.replace("/dashboard/portal");
    }
  }, [router, pathname]);

  return <>{children}</>;
}
