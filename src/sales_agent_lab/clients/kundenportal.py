"""Minimal Kundenportal AIO client."""

from typing import Any

import httpx
from pydantic import BaseModel

from sales_agent_lab.config import settings


class Lead(BaseModel):
    id: str
    status: str | None
    company_name: str | None
    contact_person: str | None
    email: str | None
    phone: str | None
    quality_score: float | None
    source_data: dict[str, Any] | None


class DraftPayload(BaseModel):
    tenant_id: str
    request_id: str
    kind: str
    status: str = "proposed"
    title: str
    content: dict[str, Any]
    targets: list[dict[str, Any]]
    related: dict[str, Any]
    policy: dict[str, Any]
    actor_id: str | None = None
    actor_type: str = "agent"
    trace_id: str | None = None


class KundenportalClient:
    def __init__(self, base_url: str | None = None, service_token: str | None = None) -> None:
        self.base_url = (base_url or settings.kundenportal_base_url).rstrip("/")
        self.service_token = service_token or settings.kundenportal_service_token
        if not self.service_token:
            raise RuntimeError("KUNDENPORTAL_SERVICE_TOKEN is not configured")
        self._headers = {
            "Authorization": f"Bearer {self.service_token}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        with httpx.Client(timeout=30.0, headers=self._headers) as client:
            response = client.request(method, self._url(path), **kwargs)
            response.raise_for_status()
            return response

    def list_leads(
        self,
        tenant_id: str | None = None,
        status: str | None = "new",
        min_quality: float | None = None,
        limit: int = 50,
    ) -> list[Lead]:
        params: dict[str, Any] = {"tenant_id": tenant_id or settings.kundenportal_tenant_id, "limit": limit}
        if status:
            params["status"] = status
        if min_quality is not None:
            params["min_quality"] = min_quality
        resp = self._request("GET", "/api/aio/leads", params=params)
        return [Lead.model_validate(item) for item in resp.json().get("leads", [])]

    def create_lead(self, payload: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        body = {"tenant_id": tenant_id or settings.kundenportal_tenant_id, **payload}
        resp = self._request("POST", "/api/aio/leads", json=body)
        return resp.json()

    def create_draft(self, payload: DraftPayload) -> dict[str, Any]:
        resp = self._request("POST", "/api/aio/drafts", json=payload.model_dump(exclude_none=True))
        return resp.json()

    def decide_approval(self, draft_id: str, decision: str, tenant_id: str | None = None) -> dict[str, Any]:
        body = {
            "tenant_id": tenant_id or settings.kundenportal_tenant_id,
            "draft_id": draft_id,
            "decision": decision,
        }
        resp = self._request("POST", "/api/aio/approvals/decide", json=body)
        return resp.json()

    def get_drafts(
        self,
        tenant_id: str | None = None,
        status: str | None = None,
        kind: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"tenant_id": tenant_id or settings.kundenportal_tenant_id, "limit": limit}
        if status:
            params["status"] = status
        if kind:
            params["kind"] = kind
        resp = self._request("GET", "/api/aio/drafts", params=params)
        return resp.json().get("drafts", [])
