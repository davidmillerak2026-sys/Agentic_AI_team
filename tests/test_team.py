from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wearedge_agent_team.definitions import build_default_agent_definitions
from wearedge_agent_team.evidence import load_evidence
from wearedge_agent_team.team import AgentTeam


class AgentTeamTests(unittest.TestCase):
    def test_default_team_has_nine_unique_agents(self) -> None:
        definitions = build_default_agent_definitions()

        self.assertEqual(len(definitions), 9)
        self.assertEqual(len({definition.agent_id for definition in definitions}), 9)
        self.assertIn("research", {definition.agent_id for definition in definitions})
        self.assertIn("media", {definition.agent_id for definition in definitions})

    def test_selected_agents_complete_contracts(self) -> None:
        team = AgentTeam()
        evidence = load_evidence([str(ROOT / "examples" / "wear-edge-context.md")])

        report = team.run_mission(
            "为 WearEdge Pro 准备工业 AR 质检 PoC",
            active_agent_ids=["research", "productization", "sales"],
            evidence=evidence,
        )

        self.assertEqual(len(report.agents), 3)
        self.assertTrue(all(run.is_contract_complete for run in report.agents))
        self.assertIn("ROIModel", report.runtime_data["sales"])

    def test_unknown_agent_id_is_rejected(self) -> None:
        team = AgentTeam()

        with self.assertRaises(ValueError):
            team.run_mission("demo", active_agent_ids=["unknown"])


if __name__ == "__main__":
    unittest.main()
