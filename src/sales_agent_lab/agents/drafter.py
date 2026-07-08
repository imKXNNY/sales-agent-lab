"""Outreach email drafting agent."""

from typing import Any

from sales_agent_lab.clients.llm import LlmClient
from sales_agent_lab.knowledge import discovery


def draft_outreach_email(lead: dict[str, Any], llm: LlmClient | None = None) -> dict[str, str]:
    """Generate a German, personalized outreach email for a qualified lead."""
    import json
    import re

    client = llm or LlmClient()
    system = (
        "Du bist ein erfahrener B2B-Verkaufsassistent für Tectara Systems. "
        "Schreibe kurze, persönliche, professionelle deutsche E-Mails. "
        "Keine Allgemeinplätze. Bezug nimm auf den konkreten Lead. "
        "Ziel: ein kurzes Gespräch vereinbaren."
    )
    user = f"""Verfasse eine Outreach-E-Mail für diesen Lead:

{json.dumps(lead, ensure_ascii=False, indent=2)}

Discovery-Call-Kontext (für Ton und Ziel):
{discovery.DISCOVERY_SUMMARY}

Gib ausschließlich gültiges JSON zurück:
{{
  "subject": "...",
  "body": "...",
  "personalization_hook": "..."
}}

Anforderungen:
- Betreff max. 60 Zeichen, keine Clickbait-Wörter.
- E-Mail max. 150 Wörter, professionell, persönlich, konkret.
- Klare Einladung zu einem 15-minütigen Gespräch.
- Deutscher Anrede, "Sie"-Form.
"""
    raw = client.complete(system, user)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"LLM did not return JSON: {raw}")
    return json.loads(match.group(0))
