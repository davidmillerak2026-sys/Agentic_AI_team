from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceItem:
    title: str
    source: str
    text: str
    score: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    name_cn: str
    name_en: str
    mission: str
    responsibilities: tuple[str, ...]
    input_signals: tuple[str, ...]
    output_artifacts: tuple[str, ...]
    required_fields: tuple[str, ...]
    research_queries: tuple[str, ...]
    handoff_targets: tuple[str, ...] = ()

    @property
    def display_name(self) -> str:
        return f"{self.name_cn} ({self.name_en})"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentTask:
    mission: str
    project_context: str = ""
    constraints: tuple[str, ...] = ()
    desired_output: str = "Give founder-ready work product."
    language: str = "zh-CN"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentRun:
    agent_id: str
    agent_name: str
    prompt: str
    output: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    required_fields: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()

    @property
    def is_contract_complete(self) -> bool:
        return not self.missing_fields

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_complete"] = self.is_contract_complete
        return value


@dataclass(frozen=True)
class TeamReport:
    mission: str
    generated_at: str
    agents: list[AgentRun]
    runtime_data: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            "# WearEdge Agent Team Report",
            "",
            f"Mission: {self.mission}",
            f"Generated at: {self.generated_at}",
            "",
            "## Runtime Blackboard",
            "",
        ]
        if not self.runtime_data:
            lines.append("- No runtime data.")
        for key, value in self.runtime_data.items():
            compact = " ".join(value.split())
            if len(compact) > 240:
                compact = compact[:237] + "..."
            lines.append(f"- **{key}**: {compact}")
        lines.extend(["", "## Agent Outputs", ""])
        for run in self.agents:
            status = "complete" if run.is_contract_complete else f"missing {', '.join(run.missing_fields)}"
            lines.extend(
                [
                    f"### {run.agent_name}",
                    "",
                    f"Contract: {status}",
                    "",
                    run.output.strip(),
                    "",
                ]
            )
            if run.evidence:
                lines.append("Evidence:")
                for item in run.evidence:
                    lines.append(f"- {item.title} ({item.source}) score={item.score:.2f}")
                lines.append("")
        return "\n".join(lines).strip() + "\n"
