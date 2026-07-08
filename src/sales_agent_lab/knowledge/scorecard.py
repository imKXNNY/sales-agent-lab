"""Tectara lead scorecard knowledge for LLM prompts."""

SCORECARD_TEXT = """
Scorecard (Rate 1-5 pro Dimension, Total = Sum / 25 * 10, max 10.0):
1. Pain Clarity: 1=vague/just looking, 3=problem described but not quantified, 5=quantified pain (€/hours/revenue).
2. Budget Fit: 1=no budget, 3=budget exists but not allocated, 5=budget available, ready to deploy.
3. Decision Access: 1=no DM access, 3=DM will review proposal, 5=DM on call, engaged, can decide.
4. Timeline: 1=no timeline, 3=3-6 months, 5=this month/yesterday.
5. Data Readiness: 1=no data/unwilling, 3=accessible needs cleaning, 5=ready, documented, access available.

Threshold: ≥8.0 / 10 is qualified.
"""

DECISION_MATRIX_TEXT = """
Decision Matrix:
- Score ≥8.0 + 0 red flags → Offer (60-min deep-dive diagnosis).
- Score 6.0–7.9 + 0 red flags → Nurture (case study + 14-day follow-up).
- Score 6.0–7.9 + 1 red flag → Nurture/watch, re-qualify in 30 days.
- Score <6.0 + ≥2 red flags → Reject.
- Any score + ≥3 red flags → Hard reject.
- Red flag *Unrealistic expectations* or *No clear problem* → Reject regardless of score.
"""
