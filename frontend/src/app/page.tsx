"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  useEffect(() => { router.replace("/dashboard"); }, [router]);
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0d17]">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 animate-pulse" />
    </div>
  );
}
