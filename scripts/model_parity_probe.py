"""Run the same bounded real-model probes through Tau and pinned Pi."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from time import monotonic
from typing import Any, cast

from tau_agent.loop import run_agent_loop
from tau_agent.messages import AgentMessage, TextContent, UserMessage
from tau_agent.provider import CancellationToken, ModelProvider
from tau_agent.provider_events import AssistantMessageEvent
from tau_agent.tools import AgentTool, AgentToolResult, ToolUpdateCallback
from tau_agent.types import JSONValue
from tau_ai.env import OpenAICompatibleConfig
from tau_ai.openai_compatible import OpenAICompatibleProvider


class RecordingProvider:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider
        self.calls: list[dict[str, Any]] = []

    def stream_response(
        self,
        *,
        model: str,
        system: str,
        messages: list[AgentMessage],
        tools: list[AgentTool],
        signal: CancellationToken | None = None,
        session_id: str | None = None,
    ) -> AsyncIterator[AssistantMessageEvent]:
        self.calls.append(
            {
                "model": model,
                "system": system,
                "messages": [
                    message.model_dump(by_alias=True, mode="json") for message in messages
                ],
                "tools": [tool.name for tool in tools],
                "sessionId": session_id,
            }
        )
        return self.provider.stream_response(
            model=model,
            system=system,
            messages=messages,
            tools=tools,
            signal=signal,
            session_id=session_id,
        )


async def _tau_probe(
    scenario: str,
    *,
    api_key: str,
    base_url: str,
    model: str,
    output: Path,
) -> None:
    provider = OpenAICompatibleProvider(
        OpenAICompatibleConfig(
            api_key=api_key,
            base_url=base_url,
            reasoning_effort="high",
            thinking_format="openai",
            compat={"supportsReasoningEffort": True},
            provider_name="commandcode",
            timeout_seconds=120,
            max_retries=0,
            max_tokens=2048,
            infer_api_from_model=False,
        )
    )
    recording = RecordingProvider(provider)
    tool_scenario = scenario == "tool"

    async def multiply(
        tool_call_id: str,
        arguments: Mapping[str, JSONValue],
        signal: CancellationToken | None = None,
        on_update: ToolUpdateCallback | None = None,
    ) -> AgentToolResult:
        del tool_call_id, signal, on_update
        a = cast(int, arguments["a"])
        b = cast(int, arguments["b"])
        return AgentToolResult(
            content=[TextContent(text=str(a * b))], details={"a": a, "b": b}
        )

    tools = (
        [
            AgentTool(
                name="multiply",
                label="Multiply",
                description="Multiply two integers.",
                parameters={
                    "type": "object",
                    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                    "required": ["a", "b"],
                    "additionalProperties": False,
                },
                execute_fn=multiply,
            )
        ]
        if tool_scenario
        else []
    )
    system = (
        "You are a deterministic harness probe. You must call multiply exactly once for "
        "multiplication, then answer with its result."
        if tool_scenario
        else "Reply exactly PONG."
    )
    prompt = (
        "Use multiply to calculate 17 * 23, then state the result."
        if tool_scenario
        else "Reply exactly PONG."
    )
    messages: list[AgentMessage] = []
    prompt_message = UserMessage(content=prompt)
    events: list[dict[str, Any]] = []
    turns = 0

    def stop_after_three(_context: object) -> bool:
        nonlocal turns
        turns += 1
        return turns >= 3

    started = monotonic()
    try:
        async for event in run_agent_loop(
            provider=recording,
            model=model,
            system=system,
            messages=messages,
            tools=tools,
            prompts=[prompt_message],
            should_stop_after_turn=stop_after_three,
            session_id=f"parity-{scenario}",
        ):
            events.append(
                {
                    "atMs": (monotonic() - started) * 1000,
                    "event": event.model_dump(by_alias=True, mode="json"),
                }
            )
        receipt: dict[str, Any] = {
            "identity": {
                "entrant": "tau",
                "scenario": scenario,
                "model": model,
                "baseUrl": base_url,
                "reasoning": "high",
            },
            "durationMs": (monotonic() - started) * 1000,
            "events": events,
            "providerCalls": recording.calls,
            "coverage": {"providerInputLayer": "provider-neutral-context"},
            "messages": [message.model_dump(by_alias=True, mode="json") for message in messages],
        }
    except Exception as exc:  # noqa: BLE001 - receipt must survive a provider failure
        receipt = {
            "identity": {"entrant": "tau", "scenario": scenario, "model": model},
            "durationMs": (monotonic() - started) * 1000,
            "events": events,
            "providerCalls": recording.calls,
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    finally:
        await provider.aclose()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pi-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--only", choices=("all", "tau", "pi"), default="all")
    parser.add_argument("--scenario", choices=("all", "plain", "tool"), default="all")
    return parser.parse_args()


async def main() -> int:
    args = _arguments()
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    model = os.environ.get("LLM_MODEL")
    if not api_key or not base_url or not model:
        raise RuntimeError("LLM_API_KEY, LLM_BASE_URL, and LLM_MODEL are required")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    async def run_tau(scenario: str) -> None:
        await _tau_probe(
            scenario,
            api_key=api_key,
            base_url=base_url,
            model=model,
            output=args.output_dir / f"tau-{scenario}.json",
        )

    def run_pi(scenario: str) -> None:
        completed = subprocess.run(
            [
                node,
                str(tsx),
                str(script),
                scenario,
                str(args.output_dir / f"pi-{scenario}.json"),
            ],
            cwd=args.pi_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if completed.returncode:
            failure = {
                "identity": {"entrant": "pi", "scenario": scenario, "model": model},
                "error": {
                    "returnCode": completed.returncode,
                    "stderr": completed.stderr[-8000:],
                },
            }
            (args.output_dir / f"pi-{scenario}.json").write_text(
                json.dumps(failure, indent=2), encoding="utf-8"
            )

    environment = os.environ.copy()
    node = "node.exe" if os.name == "nt" else "node"
    tsx = args.pi_root / "node_modules" / "tsx" / "dist" / "cli.mjs"
    script = Path(__file__).with_name("pi_model_probe.ts")
    schedule = (("tau", "plain"), ("pi", "plain"), ("pi", "tool"), ("tau", "tool"))
    for entrant, scenario in schedule:
        if args.only not in {"all", entrant}:
            continue
        if args.scenario not in {"all", scenario}:
            continue
        if entrant == "tau":
            await run_tau(scenario)
        else:
            run_pi(scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
