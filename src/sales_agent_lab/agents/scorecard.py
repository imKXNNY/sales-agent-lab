"""Lead qualification using the ADOS scorecard."""

from typing import Any

from sales_agent_lab.clients.llm import LlmClient
from sales_agent_lab.knowledge import discovery, scorecard


def _build_prompt(lead: dict[str, Any]) -> str:
    return f"""Bewerte diesen Lead anhand des Tectara-Scorecards.

{scorecard.SCORECARD_TEXT}

Entscheidungsmatrix:
{scorecard.DECISION_MATRIX_TEXT}

Lead-Daten:
{json.dumps(lead, ensure_ascii=False, indent=2)}

Gib ausschließlich gültiges JSON zurück mit diesen Feldern:
- pain_clarity (1-5)
- budget_fit (1-5)
- decision_access (1-5)
- timeline (1-5)
- data_readiness (1-5)
- red_flags (array of strings from the scorecard list, or empty)
- total_score (float, 0.0-10.0)
- decision (one of: offer, nurture, reject)
- reasoning (string in German)
- next_action (string in German)
"""


def qualify_lead(lead: dict[str, Any], llm: LlmClient | None = None) -> dict[str, Any]:
    import json
    import re

    client = llm or LlmClient()
    system = (
        "Du bist ein erfahrener B2B-Verkaufsqualifizierer für Tectara Systems. "
        "Bewerte Leads objektiv anhand der vorgegebenen Kriterien. "
        "Antworte ausschließlich im geforderten JSON-Format."
    )
    raw = client.complete(system, _build_prompt(lead))
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"LLM did not return JSON: {raw}")
    return json.loads(match.group(0))
