"""Minimal MailOps client."""

from typing import Any

import httpx

from sales_agent_lab.config import settings


class MailOpsClient:
    def __init__(self, base_url: str | None = None, service_token: str | None = None) -> None:
        self.base_url = (base_url or settings.mailops_base_url).rstrip("/")
        self.service_token = service_token or settings.mailops_service_token
        if not self.service_token:
            raise RuntimeError("MAILOPS_SERVICE_TOKEN is not configured")
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

    def send_approved_draft(self, draft_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        body = {
            "tenant_id": tenant_id or settings.kundenportal_tenant_id,
            "draft_id": draft_id,
            "send_mode": "auto_after_approval",
        }
        resp = self._request("POST", "/v1/mailops/send/approved-draft", json=body)
        return resp.json()

    def send_raw_email(
        self,
        to: list[str],
        subject: str,
        text: str,
        html: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "tenant_id": tenant_id or settings.kundenportal_tenant_id,
            "to": to,
            "subject": subject,
            "text": text,
        }
        if html:
            body["html"] = html
        resp = self._request("POST", "/v1/mailops/send/raw", json=body)
        return resp.json()
