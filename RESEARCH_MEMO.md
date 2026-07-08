# Sales Agent Lab — Research Memo & Plan

**Project:** `sales-agent-lab` (Tectara Systems internal)  
**Goal:** Build a voice-first, human-in-the-loop AI sales entity that connects to Kundenportal / MailOps / LeadPilot without changing Webton AIO source code.  
**Date:** 2026-07-08  
**Status:** Research complete → ready to scaffold M0/M1

---

## 1. Current state

### Existing POC: `TEC-247-salesgpt-supertonic`
- **Stack:** local Whisper STT :9000 → SalesGPT :8000 → local Supertonic TTS :8001
- **Language:** German sales script, branded “Tectara Systems”
- **Verdict:** “concept proofed” but never validated end-to-end because SalesGPT needs `OPENAI_API_KEY`.
- **Architecture:** turn-based batch pipeline. STT waits for full utterance, then LLM, then TTS. This **will** feel slow and robotic.
- **Value to harvest:** German prompt, 7-stage conversation flow, objection handling, and Supertonic/Whisper as voice plumbing.

### ADOS sales assets (better harvest material)
- `~/.openclaw/workspace/projects/webton/webton-ados/docs/sales/discovery-call-script.md`
  - 15–20 min discovery call phases: Opening, 7 qualification questions, anti-ICP red flags, closing/next-step routing.
- `~/.openclaw/workspace/projects/webton/webton-ados/docs/sales/lead-scorecard.md`
  - 5-dimension scorecard (Pain, Budget, Decision Access, Timeline, Data Readiness) with threshold ≥8.0/10.
  - Decision matrix: Offer / Nurture / Reject based on score + red flags.
- **These are far more useful than the SalesGPT prompt** because they map directly to your ICP, qualification, and routing logic.

### Current ecosystem (from repo inspection)
- **Kundenportal** already exposes AIO routes:
  - `POST /api/aio/drafts` — create draft (idempotent on `request_id`)
  - `POST /api/aio/approvals/decide` — approve/reject draft
  - `GET /api/aio/drafts` — list drafts with `tenant_id`, `status`, `kind`, `limit`
  - `POST /api/aio/leads` — create lead
  - `GET /api/aio/leads` — list leads (filter by `status`, `min_quality`, `from`, `to`)
  - `POST /api/aio/leads/{id}/outreach` — create a pre-built outreach draft for a lead
  - `POST /api/aio/core/webhooks/ingest` — ingest external AIO events (HMAC-signed)
- **MailOps** service:
  - `POST /v1/mailops/send/raw` — send raw email (requires `MAILOPS_SERVICE_TOKEN`)
  - `POST /v1/mailops/send/approved-draft` — queue approved draft for send
  - Webhook delivery on `sent` / `failed` / `retrying` to configured endpoints
- **LeadPilot** currently emits results via n8n webhook (`/webhook/pcs-results-bridge`), not directly to Kundenportal.
- **AIO contracts** define standard `draft.created`, `draft.approved`, `lead.created`, `lead.batch_created` event envelopes.

### LLM available locally
- `qwen3.5:9b` (6.6 GB) — best local chat model candidate for dev/testing
- `hf.co/OBLITERATUS/Gemma-4-12B-OBLITERATED:Q8_0` (12 GB) — stronger but heavier
- Cloud aliases: `qwen3.5:cloud`, `minimax-m2.7:cloud` — for faster production use via existing subscriptions
- Embedding models already present (qwen3-embedding, nomic-embed-text, etc.)

---

## 2. Key research findings

### 2.1 Voice UX: turn-based vs. streaming
- **Turn-based (Whisper → LLM → TTS):** serial latency 1–3s, no interruption, feels robotic.
- **Natural conversation tolerance:** ~500–800 ms silence before it feels awkward.
- **Streaming architecture (minimum for natural voice):**
  - Streaming ASR (faster-whisper / WhisperLive / Deepgram / Azure)
  - VAD (Silero / PyAnnote / WebRTC) for end-of-turn and interruption detection
  - Streaming LLM output to TTS
  - Phrase-level / sentence-level TTS (Piper / Coqui / Supertonic if streaming-capable)
  - Audio ducking/interruption: stop AI audio when user starts speaking
- **Recommended open-source voice stacks:** **Pipecat** or **LiveKit Agents**.
  - Both support streaming ASR/TTS, interruptions, turn-taking, and connect to Ollama/OpenAI-compatible LLMs.
  - LiveKit: stronger transport/WebRTC.
  - Pipecat: simpler telephony integration.

### 2.2 SalesGPT alternatives

| Framework | Type | German | Local LLM | Voice | Verdict |
|---|---|---|---|---|---|
| **Pipecat** | Open-source, self-host | Yes | Yes (Ollama/OpenAI-compatible) | Native real-time | **Best for voice-first custom agent** |
| **LiveKit Agents** | Open-source, self-host | Yes | Yes | Native real-time | **Best transport/low latency** |
| **Vapi / Bland / Retell** | SaaS | Yes | Limited | Native real-time | Fast but locked-in; avoid for lab |
| **LangGraph / LangChain** | Open-source, self-host | Via prompt | Yes | No native | Best for complex stateful conversation logic |
| **CrewAI** | Open-source, self-host | Via LLM | Yes | No native | Good for multi-agent research tasks |
| **Dify** | Open-source, self-host | UI yes | Yes | Chat only | Good backend app builder, not phone voice |
| **n8n** | Open-source, self-host | UI yes | Via HTTP nodes | No native | Best glue/integration layer |

**Conclusion:** Ditch SalesGPT. Build the core agent with **LangGraph** (stateful conversation + tools) or a lightweight custom Python service, and add **Pipecat** or **LiveKit** for voice.

### 2.3 B2B outbound best practices
- **Draft-first, always.** No auto-send on first cold email.
- **Personalize** with one real business signal.
- **Clear opt-out** in every email, honor immediately.
- **German B2B compliance:** target business roles with professional relevance; document legitimate interest; provide sender ID, address, unsubscribe; avoid misleading subjects; maintain suppression list.
- **CRM status chain:** New → Qualified → Drafted → Pending Approval → Approved → Sent → Opened → Replied → Meeting Booked → Opportunity / Disqualified / Nurture.
- **Top 5 dos:** human approval before first send, personalize, clear opt-out, auto-sync CRM, continuous re-scoring.
- **Top 5 don’ts:** auto-send cold emails, buy/scrape bulk lists, misleading subject lines, ignore opt-outs, let CRM drift.

---

## 3. Recommended architecture

### Design principles
1. **No changes to Webton AIO / Kundenportal source code.** Use existing AIO contracts, API routes, and webhooks.
2. **Kundenportal is the source of truth for leads and drafts.** Pull leads from it, push drafts into it, react to approvals via webhook or poll.
3. **Text-first outbound now; voice as a channel layer later.** The same agent core serves both.
4. **Local LLM for dev/testing; cloud subscription for client-facing voice.**

### High-level flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Lead Sources   │────▶│   Kundenportal   │◀────│  sales-agent-lab │
│  LeadPilot      │     │  (leads, drafts, │     │  (this project)  │
│  lead-gen-crm   │     │   approvals)     │     │                  │
│  manual CSV     │     │                  │     │  • qualifies     │
│                 │     │                  │     │  • drafts        │
└─────────────────┘     └────────┬─────────┘     │  • listens       │
                                   │              │  • sends via     │
                                   │ approve      │    MailOps       │
                                   ▼              └────────┬─────────┘
                          ┌─────────────────┐              │
                          │  MailOps sends  │◀─────────────┘
                          │  email / logs   │
                          └─────────────────┘
```

### Component responsibilities
- **`sales-agent-lab` service:**
  - Poll Kundenportal for `new`/`qualified` leads (or ingest `lead.created` events via webhook).
  - Run qualification scoring using ADOS scorecard rules.
  - Generate personalized outreach/reply drafts.
  - POST drafts to Kundenportal (`kind: email_followup` or `email_outreach`).
  - Poll or receive webhook for `draft.approved` events.
  - Trigger MailOps to send approved drafts.
  - Update lead status in Kundenportal after send/reply.
- **Kundenportal:**
  - Stores leads and drafts.
  - Provides AIO Inbox UI for approval.
  - Emits `draft.approved` / `draft.rejected` events.
- **MailOps:**
  - Sends actual emails and logs them.
  - Webhooks back status updates.
- **Voice layer (future):**
  - Pipecat or LiveKit wrapper around the same agent core.
  - Real-time call handling with streaming ASR/TTS.

---

## 4. Concrete integration endpoints

### Create draft in Kundenportal
```
POST https://webton-kundenportal.vercel.app/api/aio/drafts
Authorization: Bearer <KUNDENPORTAL_SERVICE_TOKEN>
Content-Type: application/json

{
  "tenant_id": "tenant:01JWEBTON001",
  "request_id": "sales-agent-lab:outreach:lead-123:2026-07-08",
  "kind": "email_followup",
  "status": "proposed",
  "title": "Outreach: Firma XYZ",
  "content": {
    "format": "plain",
    "body": "Hallo Herr Muster, ..."
  },
  "targets": [
    {
      "type": "email",
      "to": ["max@example.com"],
      "subject": "Kurze Frage zu Firma XYZ"
    }
  ],
  "related": {
    "lead_id": "lead-123"
  },
  "policy": {
    "requires_approval": true,
    "approval_group": "admins",
    "mode": "draft_only"
  },
  "actor_id": "sales-agent-lab",
  "actor_type": "agent",
  "trace_id": "trc:sales-agent-lab:2026-07-08-001"
}
```

### Approve / reject draft
```
POST https://webton-kundenportal.vercel.app/api/aio/approvals/decide
Authorization: Bearer <KUNDENPORTAL_SERVICE_TOKEN>

{
  "tenant_id": "tenant:01JWEBTON001",
  "draft_id": "draft-uuid",
  "decision": "approved"
}
```

### Send approved email via MailOps
```
POST https://mailops.webton.at/v1/mailops/send/approved-draft
Authorization: Bearer <MAILOPS_SERVICE_TOKEN>

{
  "tenant_id": "tenant:01JWEBTON001",
  "draft_id": "draft-uuid",
  "send_mode": "auto_after_approval"
}
```

### List leads
```
GET https://webton-kundenportal.vercel.app/api/aio/leads?tenant_id=...&status=new&min_quality=7&limit=50
Authorization: Bearer <KUNDENPORTAL_SERVICE_TOKEN>
```

### Webhook ingest (for `draft.approved` events from Kundenportal)
```
POST https://<sales-agent-lab>/webhooks/kundenportal
Content-Type: application/json

{
  "event_id": "...",
  "event_type": "draft.approved",
  "event_version": "v1",
  "tenant_id": "...",
  "actor": { ... },
  "trace_id": "...",
  "request_id": "...",
  "timestamp": "...",
  "source": { "app": "kundenportal", "capability": "core.workflows.trigger", "capability_version": "v1" },
  "data": { "draft_id": "...", "decision": "approved", "next_action": "send_stub" }
}
```

---

## 5. Phased build plan

### M0: Harvest & scaffold (this session)
- Create repo `~/.openclaw/workspace/projects/tectara/sales-agent-lab` and GitHub repo `imKXNNY/sales-agent-lab`.
- Copy ADOS discovery script + scorecard into agent prompt/knowledge.
- Define agent tools: `lead_list`, `lead_get`, `draft_create`, `draft_get`, `mailops_send`, `lead_status_update`.
- Configure LLM client: Ollama (`qwen3.5:9b`) with OpenAI-compatible base URL.

### M1: Text-first outbound drafter
- Cron or scheduled loop that fetches Kundenportal leads with `status=new` and `min_quality`.
- Score/qualify each lead using ADOS scorecard rules via LLM + structured output.
- For qualified leads, generate personalized outreach email (German).
- POST draft to Kundenportal with `requires_approval: true`.
- No sending yet.

### M2: Approval → send
- Add webhook endpoint `/webhooks/kundenportal` to receive `draft.approved` events.
- On approval, call MailOps to send the email.
- Update lead status to `outreach_sent` in Kundenportal.
- Add basic reply detection: poll MailOps inbound threads or listen for MailOps webhook.

### M3: Inbound replies
- On new inbound reply (from MailOps webhook or IMAP sync), load thread context.
- Draft reply in Kundenportal for approval.
- On approval, send.

### M4: Voice channel (future)
- Add Pipecat or LiveKit wrapper around the same agent core.
- Streaming ASR + VAD + streaming TTS.
- Use cloud LLM for low latency; local Ollama remains dev fallback.

---

## 6. Open questions before M0/M1 start

1. **Tenant ID:** Which Kundenportal tenant should the lab use for internal Tectara testing?
2. **Kundenportal service token:** Provide when ready.
3. **MailOps service token / base URL:** Provide when ready.
4. **Lead source priority:** Should M1 consume (a) existing Kundenportal leads, (b) LeadPilot via existing n8n bridge, or (c) extend `lead-gen-crm` to push leads into Kundenportal first?  
   **Recommendation:** make Kundenportal the single source of truth and add a small `lead-gen-crm → Kundenportal` bridge, then the sales agent only reads from Kundenportal.
5. **Voice transport:** For eventual phone calls, do you prefer Twilio, sipgate, or a web-only demo first?

---

## 7. Immediate next action

If you approve, I will create the `sales-agent-lab` repo, scaffold M0, and get a first draft-generating agent running against Kundenportal using local Ollama.
