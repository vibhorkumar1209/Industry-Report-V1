from __future__ import annotations

import json
from abc import ABC, abstractmethod

from anthropic import Anthropic

from app.config import settings
from app.market_intel.contracts import AgentPromptPacket, AgentRunResult


class BaseExecutionEngine(ABC):
    @abstractmethod
    def execute(self, packets: list[AgentPromptPacket]) -> list[AgentRunResult]:
        raise NotImplementedError


class ClaudeSaaSExecutionEngine(BaseExecutionEngine):
    """
    SaaS mode intentionally does not automate browser login.
    It emits session-ready prompt packets for parallel manual Claude web runs.
    """

    def execute(self, packets: list[AgentPromptPacket]) -> list[AgentRunResult]:
        results = []
        for packet in packets:
            results.append(
                AgentRunResult(
                    agent_name=packet.agent_name,
                    payload={
                        "status": "pending_manual_saas_execution",
                        "session_instructions": (
                            "Open a separate Claude web session for this agent, paste `prompt`, "
                            "and copy JSON output back into the compose step."
                        ),
                        "prompt": packet.prompt,
                        "expected_output_contract": packet.expected_output_contract,
                    },
                )
            )
        return results


class ClaudeApiExecutionEngine(BaseExecutionEngine):
    def __init__(self) -> None:
        self.client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

    def execute(self, packets: list[AgentPromptPacket]) -> list[AgentRunResult]:
        if not self.client:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured for API mode.")

        results: list[AgentRunResult] = []
        for packet in packets:
            prompt = (
                f"{packet.prompt}\n\n"
                "Output JSON only and ensure the structure matches this contract exactly:\n"
                f"{json.dumps(packet.expected_output_contract)}"
            )
            response = self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=4000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "\n".join(block.text for block in response.content if getattr(block, "text", None)).strip()
            parsed = _extract_json_object(text)
            results.append(AgentRunResult(agent_name=packet.agent_name, payload=parsed))
        return results


def _extract_json_object(raw: str) -> dict:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        candidate = raw[start : end + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return {"raw_output": raw, "parse_error": "Could not parse valid JSON object."}
