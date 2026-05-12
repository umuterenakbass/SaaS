"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getSiteId, getUserRole } from "@/lib/auth-storage";

export default function ResidentLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    const siteId = getSiteId();
    const role = getUserRole();

    if (!token || !siteId) {
      router.replace("/login");
      return;
    }
    if (role !== "resident") {
      // Admin/manager yanlışlıkla gelirse dashboard'a gönder
      router.replace("/dashboard");
    }
  }, [router]);

  return <>{children}</>;
}
