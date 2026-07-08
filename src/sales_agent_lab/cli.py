"""CLI entry point for sales-agent-lab."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sales_agent_lab.clients.kundenportal import KundenportalClient
from sales_agent_lab.config import settings

app = typer.Typer(name="sales-agent", help="Sales Agent Lab CLI")
console = Console()


@app.command()
def status():
    """Show configuration status (without secrets)."""
    table = Table(title="sales-agent-lab configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("LLM base URL", settings.llm_base_url)
    table.add_row("LLM default model", settings.llm_default_model)
    table.add_row("Kundenportal base URL", settings.kundenportal_base_url)
    table.add_row("Kundenportal tenant ID", settings.kundenportal_tenant_id)
    table.add_row("Kundenportal service token", "set" if settings.kundenportal_service_token else "MISSING")
    table.add_row("MailOps base URL", settings.mailops_base_url)
    table.add_row("MailOps service token", "set" if settings.mailops_service_token else "MISSING")
    table.add_row("Agent min quality score", str(settings.agent_min_quality_score))
    table.add_row("Voice enabled", str(settings.voice_enabled))
    console.print(table)


@app.command()
def list_leads(
    status: str = "new",
    min_quality: Optional[float] = None,
    limit: int = 10,
):
    """List leads from Kundenportal."""
    try:
        client = KundenportalClient()
        leads = client.list_leads(status=status, min_quality=min_quality, limit=limit)
    except Exception as e:
        console.print(f"[red]Failed to list leads: {e}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"Leads (status={status})")
    table.add_column("ID", style="cyan")
    table.add_column("Company")
    table.add_column("Contact")
    table.add_column("Email")
    table.add_column("Quality")
    for lead in leads:
        table.add_row(
            lead.id,
            lead.company_name or "",
            lead.contact_person or "",
            lead.email or "",
            str(lead.quality_score) if lead.quality_score is not None else "",
        )
    console.print(table)


def main():
    app()


if __name__ == "__main__":
    main()
