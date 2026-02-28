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
  metadata_json?: {
    source_count?: number;
    visuals?: {
      current_market_size_usd_billion?: number;
      cagr_percent?: number;
      historical_market_size?: Array<{ year: number; market_size_usd_billion: number }>;
      forecast_table?: Array<{ year: number; market_size_usd_billion: number }>;
      type_breakup?: Array<{ label: string; share_percent: number }>;
      player_market_share?: Array<{ label: string; share_percent: number }>;
      regional_overview?: Array<{ region: string; share_percent: number; summary: string }>;
      market_dynamics?: {
        trends?: string[];
        drivers?: string[];
        barriers?: string[];
      };
      regulatory_overview?: string[];
      key_player_profiles?: Array<{ company: string; profile: string }>;
    };
  };
  created_at: string;
};
