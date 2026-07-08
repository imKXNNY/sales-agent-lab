# sales-agent-lab

Voice-first, human-in-the-loop AI sales agent lab for **Tectara Systems / Webton**.

Connects to **Kundenportal** (leads + drafts + approvals) and **MailOps** (email send + replies) without changing any Webton AIO source code.

## Quick start

1. Copy `.env.example` to `.env` and fill in the service tokens Kenny provides.
2. Create a virtual environment and install dependencies:

   ```bash
   uv sync
   # or
   python -m venv .venv && source .venv/bin/activate && pip install -e .
   ```

3. Run the agent CLI:

   ```bash
   sales-agent --help
   ```

## M0: Scaffold (current)

- Project structure
- Kundenportal + MailOps clients
- Agent configuration
- ADOS sales knowledge (discovery script + lead scorecard)
- `.env.example` with all required variables

## M1: Text-first outbound drafter

- Poll Kundenportal for leads with `status=new` and `min_quality`.
- Qualify leads using the ADOS scorecard via LLM structured output.
- Generate personalized German outreach emails.
- Post drafts to Kundenportal with `requires_approval: true`.

## M2: Approval → send

- Receive `draft.approved` events from Kundenportal.
- Trigger MailOps to send approved emails.
- Update lead status in Kundenportal.

## M3: Inbound replies

- React to inbound email replies (MailOps webhook or IMAP poll).
- Draft reply in Kundenportal for approval.

## M4: Voice channel

- Add Pipecat or LiveKit voice transport around the same agent core.
- Streaming ASR + VAD + streaming TTS.

## Repository

<https://github.com/imKXNNY/sales-agent-lab>
