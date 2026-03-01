from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from app.config import settings
from app.market_intel.contracts import AGENT_ORDER, AgentRunResult, ExecutionMode, ResearchScope
from app.market_intel.engines import ClaudeApiExecutionEngine, ClaudeSaaSExecutionEngine
from app.market_intel.prompts import build_agent_prompt_packets
from app.market_intel.report_builder import build_word_style_report
from app.market_intel.segmentation import check_dimension_coverage, reconcile_dimension_totals
from app.market_intel.validation import detect_weak_citations, merge_and_score_citations


class MultiAgentMarketIntelOrchestrator:
    def __init__(self, scope: ResearchScope) -> None:
        self.scope = scope

    def prepare(self) -> dict:
        packets = build_agent_prompt_packets(self.scope)
        return {
            "scope": asdict(self.scope),
            "mode": ExecutionMode.SAAS.value,
            "orchestrator_agent": "active",
            "parallel_sessions_required": len(packets),
            "agent_prompt_packets": [
                {
                    "agent_name": p.agent_name,
                    "objective": p.objective,
                    "prompt": p.prompt,
                    "expected_output_contract": p.expected_output_contract,
                }
                for p in packets
            ],
            "instructions": [
                "Open one Claude web session per agent packet.",
                "Paste prompt and enforce strict JSON output.",
                "Submit all agent outputs to /api/market-intel/compose.",
            ],
        }

    def run(self, mode: ExecutionMode) -> dict:
        packets = build_agent_prompt_packets(self.scope)
        if mode == ExecutionMode.SAAS:
            engine = ClaudeSaaSExecutionEngine()
        else:
            engine = ClaudeApiExecutionEngine()

        results = engine.execute(packets)
        payloads = {result.agent_name: result.payload for result in results}

        if mode == ExecutionMode.SAAS:
            return {
                "status": "awaiting_manual_agent_outputs",
                "scope": asdict(self.scope),
                "agent_outputs": payloads,
                "next_step": "POST consolidated JSON payloads to /api/market-intel/compose",
            }

        return self.compose(payloads)

    def compose(self, agent_payloads: dict[str, dict]) -> dict:
        normalized = {name: agent_payloads.get(name, {}) for name in AGENT_ORDER}

        market = normalized.get("market_sizing", {})
        segmentation = normalized.get("segmentation", {})
        coverage = check_dimension_coverage(segmentation)

        historical = market.get("historical_market", [])
        overall_by_year = {
            str(row.get("year")): float(row.get("market_size_usd_bn", 0.0) or 0.0)
            for row in historical
            if row.get("year") is not None
        }
        reconciliation_flags = reconcile_dimension_totals(segmentation, overall_by_year)

        credibility_rows = merge_and_score_citations(normalized)
        weak_citations = detect_weak_citations(credibility_rows)

        validation_payload = normalized.setdefault("validation_credibility", {})
        validation_payload.setdefault("source_credibility", credibility_rows)
        validation_payload.setdefault("weak_citations", weak_citations)
        validation_payload.setdefault("estimation_logic_flags", [])

        segmentation["coverage_check"] = coverage
        segmentation["reconciliation_flags"] = reconciliation_flags

        markdown = build_word_style_report(self.scope, normalized, credibility_rows)
        artifact_path = self._write_artifact(markdown)

        return {
            "status": "complete",
            "scope": asdict(self.scope),
            "mode": "composed",
            "coverage_check": coverage,
            "reconciliation_flags": reconciliation_flags,
            "weak_citations": weak_citations,
            "report_markdown": markdown,
            "report_path": str(artifact_path),
            "architecture_notes": {
                "current_mode": "Claude SaaS parallel sessions or Claude API",
                "replaceability": "Execution engine interface keeps prompts and orchestration unchanged.",
                "web_layer": "Citation scoring and filtering remain engine-agnostic.",
                "segmentation_logic": "Dimension list is centralized and industry-dynamic.",
            },
        }

    def _write_artifact(self, markdown: str) -> Path:
        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"market_intel_{self.scope.industry.lower().replace(' ', '_')}_{self.scope.geography.lower().replace(' ', '_')}_{self.scope.end_year}.md"
        target = reports_dir / filename
        target.write_text(markdown, encoding="utf-8")
        return target
