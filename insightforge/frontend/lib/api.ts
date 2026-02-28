import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
});

export type Report = {
  id: number;
  industry: string;
  geography: string;
  time_horizon: string;
  depth: "Basic" | "Professional" | "Investor-grade";
  include_financial_forecast: boolean;
  include_competitive_landscape: boolean;
  status: "Queued" | "Running" | "Complete" | "Failed";
  progress_message: string;
  markdown_content: string;
  created_at: string;
};
