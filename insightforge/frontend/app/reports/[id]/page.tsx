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

const chartPalette = ["#0f766e", "#0369a1", "#1d4ed8", "#7c3aed", "#b45309", "#0e7490"];

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-gradient-to-br from-slate-900 to-slate-700 text-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-slate-200">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function LineTrendChart({
  title,
  data,
}: {
  title: string;
  data: Array<{ year: number; market_size_usd_billion: number }>;
}) {
  if (!data.length) return null;

  const width = 720;
  const height = 280;
  const padding = 40;
  const maxY = Math.max(...data.map((d) => d.market_size_usd_billion), 1);
  const minY = Math.min(...data.map((d) => d.market_size_usd_billion), 0);
  const ySpan = Math.max(maxY - minY, 1);

  const points = data
    .map((d, idx) => {
      const x = padding + (idx * (width - padding * 2)) / Math.max(data.length - 1, 1);
      const y = height - padding - ((d.market_size_usd_billion - minY) / ySpan) * (height - padding * 2);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="rounded-xl bg-white p-4 ring-1 ring-slate-200 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <svg viewBox={`0 0 ${width} ${height}`} className="mt-3 w-full">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#94a3b8" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#94a3b8" />
        <polyline fill="none" stroke="#0f766e" strokeWidth="3" points={points} />
        {data.map((d, idx) => {
          const x = padding + (idx * (width - padding * 2)) / Math.max(data.length - 1, 1);
          const y = height - padding - ((d.market_size_usd_billion - minY) / ySpan) * (height - padding * 2);
          return (
            <g key={`${d.year}-${idx}`}>
              <circle cx={x} cy={y} r="4" fill="#0f766e" />
              <text x={x} y={height - 12} textAnchor="middle" fontSize="10" fill="#334155">
                {d.year}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function BreakdownBars({
  title,
  rows,
  labelKey,
}: {
  title: string;
  rows: Array<Record<string, string | number>>;
  labelKey: string;
}) {
  if (!rows.length) return null;
  return (
    <div className="rounded-xl bg-white p-4 ring-1 ring-slate-200 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <div className="mt-4 space-y-3">
        {rows.map((row, idx) => {
          const label = String(row[labelKey]);
          const share = Number(row.share_percent || 0);
          return (
            <div key={`${label}-${idx}`}>
              <div className="flex justify-between text-xs text-slate-700">
                <span>{label}</span>
                <span>{share}%</span>
              </div>
              <div className="mt-1 h-2.5 rounded-full bg-slate-100">
                <div
                  className="h-2.5 rounded-full"
                  style={{ width: `${share}%`, backgroundColor: chartPalette[idx % chartPalette.length] }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ShareDonut({ rows }: { rows: Array<{ label: string; share_percent: number }> }) {
  if (!rows.length) return null;

  let start = 0;
  const segments = rows.map((row, idx) => {
    const end = start + row.share_percent;
    const color = chartPalette[idx % chartPalette.length];
    const segment = `${color} ${start}% ${end}%`;
    start = end;
    return segment;
  });

  return (
    <div className="rounded-xl bg-white p-4 ring-1 ring-slate-200 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">Player Market Share Mix</h3>
      <div className="mt-4 flex items-center gap-6">
        <div
          className="h-40 w-40 rounded-full"
          style={{ background: `conic-gradient(${segments.join(", ")})` }}
        />
        <div className="space-y-2 text-xs text-slate-700">
          {rows.map((row, idx) => (
            <div className="flex items-center gap-2" key={row.label}>
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: chartPalette[idx % chartPalette.length] }} />
              <span>{row.label}</span>
              <span className="font-semibold">{row.share_percent}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function BulletPanel({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="rounded-xl bg-white p-4 ring-1 ring-slate-200 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <ul className="mt-3 space-y-1 text-sm text-slate-700 list-disc pl-5">
        {items.map((item, idx) => (
          <li key={`${title}-${idx}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

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

  const visuals = report.metadata_json?.visuals;
  const historical = visuals?.historical_market_size || [];
  const forecast = visuals?.forecast_table || [];
  const mergedSeries = [
    ...historical,
    ...forecast.filter((f) => !historical.find((h) => h.year === f.year)),
  ];

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard label="Current Market Size" value={`USD ${visuals?.current_market_size_usd_billion || 0}B`} />
        <MetricCard label="Growth Rate" value={`${visuals?.cagr_percent || 0}% CAGR`} />
        <MetricCard label="Research Sources" value={`${report.metadata_json?.source_count || 0}`} />
      </div>

      {visuals && (
        <>
          <LineTrendChart title="Historical to Forecast Market Size" data={mergedSeries} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BreakdownBars
              title="Market Size Breakup by Type"
              rows={(visuals.type_breakup || []).map((r) => ({ ...r }))}
              labelKey="label"
            />
            <ShareDonut rows={visuals.player_market_share || []} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BreakdownBars
              title="Regional / Country Overview by Share"
              rows={(visuals.regional_overview || []).map((r) => ({ label: r.region, share_percent: r.share_percent }))}
              labelKey="label"
            />
            <div className="rounded-xl bg-white p-4 ring-1 ring-slate-200 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900">Regional Commentary</h3>
              <div className="mt-3 space-y-2 text-sm text-slate-700">
                {(visuals.regional_overview || []).map((r) => (
                  <p key={r.region}>
                    <span className="font-semibold">{r.region} ({r.share_percent}%): </span>
                    {r.summary}
                  </p>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <BulletPanel title="Market Trends" items={visuals.market_dynamics?.trends || []} />
            <BulletPanel title="Market Drivers" items={visuals.market_dynamics?.drivers || []} />
            <BulletPanel title="Market Barriers" items={visuals.market_dynamics?.barriers || []} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BulletPanel title="Regulatory Overview" items={visuals.regulatory_overview || []} />
            <div className="rounded-xl bg-white p-4 ring-1 ring-slate-200 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900">Key Player Profiles</h3>
              <div className="mt-3 space-y-2 text-sm text-slate-700">
                {(visuals.key_player_profiles || []).map((profile) => (
                  <p key={profile.company}>
                    <span className="font-semibold">{profile.company}: </span>
                    {profile.profile}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

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
        <h2 className="text-lg font-semibold mb-3">Full Narrative Report</h2>
        <pre className="whitespace-pre-wrap text-sm leading-6">{report.markdown_content || "Report not ready yet."}</pre>
      </article>
    </section>
  );
}
