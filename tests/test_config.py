"""Smoke test for configuration."""

from sales_agent_lab.config import settings


def test_settings_load():
    assert settings.kundenportal_tenant_id
    assert settings.llm_default_model
