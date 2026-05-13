"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ResidentHomePage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/dashboard/portal");
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50">
      <p className="text-sm text-zinc-500">Yönlendiriliyor…</p>
    </div>
  );
}
