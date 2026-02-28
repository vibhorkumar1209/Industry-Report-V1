"use client";

import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

type Props = {
  onCreated: () => void;
};

export default function ReportForm({ onCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    industry: "AI in Healthcare",
    geography: "Global",
    time_horizon: "2024-2030",
    depth: "Professional",
    include_financial_forecast: true,
    include_competitive_landscape: true,
  });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.post("/reports", form);
      onCreated();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Unable to create report");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="rounded-xl bg-white shadow-sm ring-1 ring-slate-200 p-6 space-y-4">
      <h2 className="text-xl font-semibold">Create Report</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="text-sm font-medium">
          Industry
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={form.industry}
            onChange={(e) => setForm({ ...form, industry: e.target.value })}
            required
          />
        </label>

        <label className="text-sm font-medium">
          Geography
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={form.geography}
            onChange={(e) => setForm({ ...form, geography: e.target.value })}
            required
          />
        </label>

        <label className="text-sm font-medium">
          Time horizon
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={form.time_horizon}
            onChange={(e) => setForm({ ...form, time_horizon: e.target.value })}
            required
          />
        </label>

        <label className="text-sm font-medium">
          Depth
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={form.depth}
            onChange={(e) => setForm({ ...form, depth: e.target.value })}
          >
            <option>Basic</option>
            <option>Professional</option>
            <option>Investor-grade</option>
          </select>
        </label>
      </div>

      <div className="flex flex-wrap gap-6">
        <label className="inline-flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.include_financial_forecast}
            onChange={(e) => setForm({ ...form, include_financial_forecast: e.target.checked })}
          />
          Include Financial Forecast
        </label>

        <label className="inline-flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.include_competitive_landscape}
            onChange={(e) => setForm({ ...form, include_competitive_landscape: e.target.checked })}
          />
          Include Competitive Landscape
        </label>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="rounded-md bg-brand-700 text-white px-4 py-2 disabled:opacity-50"
      >
        {loading ? "Submitting..." : "Generate Report"}
      </button>
    </form>
  );
}
