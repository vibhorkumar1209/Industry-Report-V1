"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, Report } from "@/lib/api";

const sections = [
  "Executive Summary",
  "Market Overview",
  "Competitive Landscape",
  "Financial Forecast Table (5-year)",
  "Risks & Sensitivity",
];

export default function ReportDetailPage() {
  const params = useParams<{ id: string }>();
  const reportId = useMemo(() => Number(params.id), [params.id]);
  const [report, setReport] = useState<Report | null>(null);
  const [selectedSection, setSelectedSection] = useState(sections[0]);

  async function load() {
    const { data } = await api.get(`/reports/${reportId}`);
    setReport(data);
  }

  useEffect(() => {
    if (!reportId) return;
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [reportId]);

  async function regenerateSection() {
    await api.post(`/reports/${reportId}/regenerate-section`, { section_name: selectedSection });
    await load();
  }

  if (!report) return <p>Loading...</p>;

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{report.industry} Report</h1>
          <p className="text-slate-600">{report.geography} | {report.time_horizon} | {report.depth}</p>
          <p className="text-sm text-slate-500 mt-1">Status: {report.status} ({report.progress_message})</p>
        </div>
        <div className="flex gap-3">
          <Link href="/" className="text-brand-700 underline">Back</Link>
          <a
            href={`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/reports/${report.id}/pdf`}
            className="rounded-md bg-brand-700 text-white px-3 py-2"
          >
            Download PDF
          </a>
        </div>
      </div>

      <div className="rounded-xl bg-white shadow-sm ring-1 ring-slate-200 p-4 flex gap-2 items-center">
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
          value={selectedSection}
          onChange={(e) => setSelectedSection(e.target.value)}
        >
          {sections.map((s) => <option key={s}>{s}</option>)}
        </select>
        <button onClick={regenerateSection} className="rounded-md bg-slate-900 text-white px-3 py-2">
          Regenerate Section
        </button>
      </div>

      <article className="rounded-xl bg-white shadow-sm ring-1 ring-slate-200 p-6">
        <pre className="whitespace-pre-wrap text-sm leading-6">{report.markdown_content || "Report not ready yet."}</pre>
      </article>
    </section>
  );
}
