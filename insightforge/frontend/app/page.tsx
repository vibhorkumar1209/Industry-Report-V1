"use client";

import { useCallback, useEffect, useState } from "react";
import ReportForm from "@/components/ReportForm";
import ReportList from "@/components/ReportList";
import { api, Report } from "@/lib/api";

export default function HomePage() {
  const [reports, setReports] = useState<Report[]>([]);

  const loadReports = useCallback(async () => {
    const { data } = await api.get("/reports");
    setReports(data);
  }, []);

  useEffect(() => {
    loadReports();
    const id = setInterval(loadReports, 5000);
    return () => clearInterval(id);
  }, [loadReports]);

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">InsightForge AI</h1>
        <p className="text-slate-600">Automated Industry Intelligence Platform</p>
      </header>

      <ReportForm onCreated={loadReports} />

      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Generated Reports</h2>
        <ReportList reports={reports} />
      </div>
    </section>
  );
}
