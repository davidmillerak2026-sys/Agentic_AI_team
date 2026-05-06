from __future__ import annotations

from datetime import datetime, timezone

from .definitions import build_default_agent_definitions
from .llm import LLMClient, create_llm
from .models import AgentDefinition, AgentRun, AgentTask, EvidenceItem, TeamReport


class RoleAgent:
    def __init__(self, definition: AgentDefinition, llm: LLMClient) -> None:
        self.definition = definition
        self.llm = llm

    def run(
        self,
        task: AgentTask,
        *,
        evidence: list[EvidenceItem] | None = None,
        runtime_data: dict[str, str] | None = None,
    ) -> AgentRun:
        evidence = evidence or []
        runtime_data = runtime_data or {}
        prompt = self.build_prompt(task, evidence=evidence, runtime_data=runtime_data)
        output = self.llm.generate(prompt).strip()
        if not output or self.llm.provider == "offline":
            output = build_deterministic_output(self.definition, task, evidence=evidence, runtime_data=runtime_data)
        missing_fields = tuple(field for field in self.definition.required_fields if field not in output)
        return AgentRun(
            agent_id=self.definition.agent_id,
            agent_name=self.definition.display_name,
            prompt=prompt,
            output=output,
            evidence=evidence,
            required_fields=self.definition.required_fields,
            missing_fields=missing_fields,
        )

    def build_prompt(
        self,
        task: AgentTask,
        *,
        evidence: list[EvidenceItem],
        runtime_data: dict[str, str],
    ) -> str:
        return "\n\n".join(
            [
                f"You are {self.definition.display_name}, one of Ryan Hui's nine AI agents.",
                f"Agent mission: {self.definition.mission}",
                "Responsibilities:\n" + "\n".join(f"- {item}" for item in self.definition.responsibilities),
                "Input signals:\n" + "\n".join(f"- {item}" for item in self.definition.input_signals),
                "Required output fields:\n" + "\n".join(f"- {item}" for item in self.definition.required_fields),
                f"Founder mission:\n{task.mission}",
                f"Project context:\n{task.project_context or 'No extra context provided.'}",
                "Constraints:\n" + "\n".join(f"- {item}" for item in task.constraints or ("Local-first and founder-ready.",)),
                f"Desired output:\n{task.desired_output}",
                f"Language: {task.language}",
                "Runtime blackboard:\n" + format_runtime_data(runtime_data),
                "Evidence:\n" + format_evidence(evidence),
                "Return compact output. Keep every required output field label verbatim.",
            ]
        )


class AgentTeam:
    def __init__(
        self,
        *,
        definitions: list[AgentDefinition] | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.definitions = definitions or build_default_agent_definitions()
        self.llm = llm or create_llm("offline")

    @classmethod
    def build(cls, *, provider: str = "offline", model: str | None = None) -> "AgentTeam":
        return cls(llm=create_llm(provider, model=model))

    def list_agents(self) -> list[AgentDefinition]:
        return list(self.definitions)

    def run_mission(
        self,
        mission: str,
        *,
        project_context: str = "",
        constraints: list[str] | tuple[str, ...] | None = None,
        desired_output: str = "Generate founder-ready work product.",
        language: str = "zh-CN",
        active_agent_ids: list[str] | tuple[str, ...] | None = None,
        evidence: list[EvidenceItem] | None = None,
    ) -> TeamReport:
        selected = self._select_agents(active_agent_ids)
        task = AgentTask(
            mission=mission,
            project_context=project_context,
            constraints=tuple(constraints or ()),
            desired_output=desired_output,
            language=language,
        )
        runtime_data: dict[str, str] = {}
        runs: list[AgentRun] = []
        for definition in selected:
            relevant_evidence = select_evidence_for_agent(definition, evidence or [])
            run = RoleAgent(definition, self.llm).run(task, evidence=relevant_evidence, runtime_data=runtime_data)
            runs.append(run)
            runtime_data[definition.agent_id] = run.output
        return TeamReport(
            mission=mission,
            generated_at=datetime.now(timezone.utc).isoformat(),
            agents=runs,
            runtime_data=runtime_data,
        )

    def _select_agents(self, active_agent_ids: list[str] | tuple[str, ...] | None) -> list[AgentDefinition]:
        if not active_agent_ids:
            return list(self.definitions)
        allowed = {agent_id.strip() for agent_id in active_agent_ids}
        selected = [definition for definition in self.definitions if definition.agent_id in allowed]
        missing = allowed.difference(definition.agent_id for definition in selected)
        if missing:
            raise ValueError(f"Unknown agent ids: {', '.join(sorted(missing))}")
        return selected


def select_evidence_for_agent(definition: AgentDefinition, evidence: list[EvidenceItem], *, limit: int = 3) -> list[EvidenceItem]:
    if not evidence:
        return []
    query = " ".join([definition.mission, *definition.research_queries]).lower()
    ranked: list[tuple[int, EvidenceItem]] = []
    for item in evidence:
        haystack = f"{item.title} {item.text}".lower()
        score = sum(1 for token in query.split() if token and token in haystack)
        ranked.append((score, item))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in ranked[:limit]]


def format_evidence(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "No evidence provided."
    sections: list[str] = []
    for idx, item in enumerate(evidence, start=1):
        compact = " ".join(item.text.split())
        sections.append(f"[E{idx}] {item.title}\nSource: {item.source}\nScore: {item.score:.2f}\nText: {compact[:1000]}")
    return "\n\n---\n\n".join(sections)


def format_runtime_data(runtime_data: dict[str, str]) -> str:
    if not runtime_data:
        return "No prior agent output."
    lines: list[str] = []
    for key, value in runtime_data.items():
        compact = " ".join(value.split())
        if len(compact) > 500:
            compact = compact[:497] + "..."
        lines.append(f"- {key}: {compact}")
    return "\n".join(lines)


def build_deterministic_output(
    definition: AgentDefinition,
    task: AgentTask,
    *,
    evidence: list[EvidenceItem],
    runtime_data: dict[str, str],
) -> str:
    evidence_line = "；".join(item.title for item in evidence[:3]) or "暂无证据文件，使用角色默认工业假设"
    handoff_line = "、".join(definition.handoff_targets) or "Founder"
    lines = [
        f"Agent: {definition.display_name}",
        f"Mission: {definition.mission}",
        f"Evidence: {evidence_line}",
    ]
    for field in definition.required_fields:
        lines.append(f"{field}: {recommendation_for_field(field, definition, task, evidence_line, runtime_data)}")
    lines.append(f"Handoff: {handoff_line}")
    return "\n".join(lines)


def recommendation_for_field(
    field: str,
    definition: AgentDefinition,
    task: AgentTask,
    evidence_line: str,
    runtime_data: dict[str, str],
) -> str:
    upstream = "、".join(runtime_data.keys()) or "暂无上游 Agent 输出"
    recommendations = {
        "Insight": f"围绕“{task.mission}”优先验证可本地离线、可进厂、可形成 ROI 的工业 Agent 场景。",
        "Evidence": f"参考证据：{evidence_line}。",
        "Risk": "最大风险是只有叙事，没有现场数据、验收指标、安全边界和客户确认。",
        "NextAction": "选择一个灯塔场景，补齐数据样例、验收指标和端侧运行脚本。",
        "ModelPlan": "采用本地优先 RAG + 可替换 LLM provider，先保证可解释引用，再逐步接入 VLM 和量化推理。",
        "LatencyBudget": "把检索、结构化输出、AR 渲染和音频播报分段计时，PoC 阶段先锁定 15W-25W 供电约束。",
        "SchemaContract": "每个下游动作必须有 required_fields、缺失字段重试和人工确认门。",
        "EvalMetric": "用召回率、引用覆盖率、字段完整率、首 token 延迟和人工复核通过率评估。",
        "ComponentMap": "端侧算力大脑负责模型和流程，AR/音频负责感知交互，网关负责企业系统边界。",
        "DataFlow": f"从 {upstream} 汇聚结果进入黑板，再交给执行、销售或传播 Agent。",
        "FailureMode": "网络不可用、模型字段缺失、硬件过热、现场噪音和 SOP 版本错误都必须有降级策略。",
        "IntegrationPoint": "优先接入文档知识库、工单系统和只读 MES 数据，再评估 PLC 控制动作。",
        "BuildPlan": "先交付 CLI 与 Markdown/JSON 报告，再扩展 FastAPI、任务队列和操作员控制台。",
        "Endpoint": "建议暴露 /agents、/missions、/runs/{id}、/evidence 和 /reports。",
        "TestCase": "覆盖 9 Agent 完整性、字段契约、非法 agent id、证据加载和 Markdown/JSON 输出。",
        "DemoPath": "README 快速开始 -> list -> run -> selected agents -> evidence -> JSON report。",
        "BOMRisk": "优先确认边缘模块供货稳定性、AR 眼镜工业防护等级和电池热插拔方案。",
        "PowerBudget": "将模型推理、无线链路、显示、音频和散热风扇拆分到独立功耗预算。",
        "ThermalPlan": "腰包级边缘盒子需要导热路径、降频策略和连续班次温升测试。",
        "ManufacturingNextStep": "建立 DFM checklist，把原型线束、接口和散热方案转成可装配版本。",
        "UseCase": "优先选择 AR 实时质检、盲操排障、模拟仪表 OCR 或动态安全预警中的一个闭环。",
        "Workflow": "现场输入 -> RAG/视觉/规则并发 -> Schema 校验 -> 人工确认 -> 工单或 AR/音频输出。",
        "AcceptanceMetric": "定义节拍时间、误报率、漏检率、人工节省时间和一次通过率。",
        "HumanApproval": "安全、停机、放行和参数写入动作必须保留人工确认。",
        "ComplianceScope": "限定为本地离线推理、现场知识库、最小权限日志审计和受控系统接入。",
        "SafetyBoundary": "Agent 可建议和预警，不应绕过安全联锁或直接执行高风险控制。",
        "AuditLog": "记录输入、证据、模型输出、字段校验、人工确认和下游动作。",
        "ApprovalGate": "进厂前需要客户 IT、安全、设备、质量和生产负责人共同确认。",
        "CustomerPain": "从停机损失、返工成本、巡检效率和老师傅经验断层中选择最强痛点。",
        "ROIModel": "按减少停机分钟、减少误检漏检、缩短维修时间和减少培训成本计算。",
        "PoCScope": "PoC 必须限制在一个产线、一个设备族或一个质检工位内闭环。",
        "FollowUp": "每次试点后沉淀问题清单、数据缺口、下一版 Demo 和采购路径。",
        "Narrative": "Ryan Hui 以 AI-Native Solo Founder 模式，用 9 个 Agent 搭建工业公司的最小作战系统。",
        "ProofPoint": "用独立 GitHub repo、可运行 CLI、样例证据、README 和测试结果证明进展。",
        "Audience": "分别面向工厂负责人、设备工程师、投资人和开发者调整表达。",
        "CallToAction": "邀请灯塔客户提供 SOP/日志样例，启动本地离线 PoC。",
    }
    return recommendations.get(field, f"{definition.name_cn} should produce {field} for {task.mission}.")
