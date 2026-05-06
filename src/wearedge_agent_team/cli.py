from __future__ import annotations

import argparse
import json

from .definitions import build_default_agent_definitions
from .evidence import load_evidence
from .team import AgentTeam


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WearEdge AI-native nine-agent founder team")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List all agent definitions")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON")

    run_parser = subparsers.add_parser("run", help="Run a mission through the agent team")
    run_parser.add_argument("mission", help="Founder mission or business question")
    run_parser.add_argument("--context", default="", help="Additional project context")
    run_parser.add_argument("--constraint", action="append", default=[], help="Mission constraint; can be repeated")
    run_parser.add_argument("--desired-output", default="Generate founder-ready work product.")
    run_parser.add_argument("--language", default="zh-CN")
    run_parser.add_argument("--agent", action="append", help="Run only selected agent id; repeat for multiple agents")
    run_parser.add_argument("--evidence", action="append", help="Evidence file or folder; repeat for multiple paths")
    run_parser.add_argument("--provider", default="offline", choices=["offline", "openai-compatible"])
    run_parser.add_argument("--model", help="Optional model name for provider")
    run_parser.add_argument("--json", action="store_true", help="Emit JSON")

    args = parser.parse_args(argv)

    if args.command == "list":
        definitions = build_default_agent_definitions()
        if args.json:
            print(json.dumps([definition.to_dict() for definition in definitions], ensure_ascii=False, indent=2))
        else:
            print(format_agent_table(definitions))
        return 0

    if args.command == "run":
        team = AgentTeam.build(provider=args.provider, model=args.model)
        report = team.run_mission(
            args.mission,
            project_context=args.context,
            constraints=args.constraint,
            desired_output=args.desired_output,
            language=args.language,
            active_agent_ids=args.agent,
            evidence=load_evidence(args.evidence),
        )
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(report.to_markdown())
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def format_agent_table(definitions) -> str:
    lines = [
        "| Agent | Core Mission | Output Artifacts | Handoff |",
        "| --- | --- | --- | --- |",
    ]
    for definition in definitions:
        lines.append(
            "| "
            f"{definition.display_name} | "
            f"{definition.mission} | "
            f"{', '.join(definition.output_artifacts)} | "
            f"{', '.join(definition.handoff_targets) or 'Founder'} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
