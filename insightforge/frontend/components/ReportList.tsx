"use client";

import Link from "next/link";
import { Report } from "@/lib/api";

export default function ReportList({ reports }: { reports: Report[] }) {
  if (!reports.length) {
    return <p className="text-slate-600">No reports yet.</p>;
  }

  return (
    <div className="rounded-xl bg-white shadow-sm ring-1 ring-slate-200 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-3">Industry</th>
            <th className="text-left p-3">Geography</th>
            <th className="text-left p-3">Status</th>
            <th className="text-left p-3">Created</th>
            <th className="text-left p-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((report) => (
            <tr key={report.id} className="border-t border-slate-200">
              <td className="p-3">{report.industry}</td>
              <td className="p-3">{report.geography}</td>
              <td className="p-3">
                <span className="rounded-full bg-slate-200 px-2 py-1 text-xs">{report.status}</span>
                <p className="text-xs text-slate-500 mt-1">{report.progress_message}</p>
              </td>
              <td className="p-3">{new Date(report.created_at).toLocaleString()}</td>
              <td className="p-3 flex gap-2">
                <Link className="text-brand-700 underline" href={`/reports/${report.id}`}>
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
