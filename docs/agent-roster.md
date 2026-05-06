# Agent Roster

The team has nine stable agents. Each agent has required fields because founder work needs reusable contracts, not loose chat output.

| Agent ID | Required Fields | Typical Artifact |
| --- | --- | --- |
| `research` | `Insight`, `Evidence`, `Risk`, `NextAction` | market brief, competitor matrix |
| `algorithm` | `ModelPlan`, `LatencyBudget`, `SchemaContract`, `EvalMetric` | model benchmark, schema contract |
| `architecture` | `ComponentMap`, `DataFlow`, `FailureMode`, `IntegrationPoint` | architecture doc, API gateway spec |
| `fullstack` | `BuildPlan`, `Endpoint`, `TestCase`, `DemoPath` | CLI/API/demo/test plan |
| `hardware` | `BOMRisk`, `PowerBudget`, `ThermalPlan`, `ManufacturingNextStep` | BOM and DFM checklist |
| `productization` | `UseCase`, `Workflow`, `AcceptanceMetric`, `HumanApproval` | PoC scope and workflow map |
| `compliance` | `ComplianceScope`, `SafetyBoundary`, `AuditLog`, `ApprovalGate` | security and safety review |
| `sales` | `CustomerPain`, `ROIModel`, `PoCScope`, `FollowUp` | proposal and customer-success plan |
| `media` | `Narrative`, `ProofPoint`, `Audience`, `CallToAction` | launch post, pitch narrative |

## Suggested Operating Cadence

1. `research`, `productization`, and `sales` run first to choose the right customer pain.
2. `algorithm`, `architecture`, `hardware`, and `compliance` run next to decide what can be delivered safely.
3. `fullstack` creates the runnable demo path.
4. `media` turns the progress into GitHub, pitch, and customer-facing narratives.
