from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from polybot.core.config import Settings, get_settings
from polybot.core.logging import get_logger
from polybot.core.security import verify_automation_secret
from polybot.knowledge.obsidian import ObsidianVault
from polybot.obsidian.reports import render_collection_report, render_incident_report
from polybot.resources.markdown import render_generic_note

router = APIRouter(dependencies=[Depends(verify_automation_secret)])
logger = get_logger(__name__)


class MarketAlertRequest(BaseModel):
    title: str
    market_id: str | None = None
    severity: str = "info"
    message: str
    metadata: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)


class IncidentRequest(BaseModel):
    title: str
    severity: str
    body: str
    metadata: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)


class GenerateNoteRequest(BaseModel):
    folder: str = "Ideas"
    title: str
    body: str
    metadata: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)
    overwrite: bool = False


class CollectionReportRequest(BaseModel):
    title: str = "Daily Collection Report"
    source: str
    rows_seen: int = 0
    rows_written: int = 0
    notes: list[str] = Field(default_factory=list)


@router.post("/market-alert")
async def market_alert(
    request: MarketAlertRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    body = render_generic_note(
        title=request.title,
        body=(
            f"## Alert\n{request.message}\n\n"
            f"## Metadata\n- Market ID: `{request.market_id or ''}`\n"
            f"- Severity: `{request.severity}`\n\n"
            "## Links\n- [[Data Layer]]\n- [[Risk Framework]]\n"
        ),
        metadata={"type": "market-alert", "severity": request.severity, **request.metadata},
    )
    path = vault.write_note("Market-Research", request.title, body, overwrite=True)
    logger.info("market_alert_note_created", file=str(path))
    return {"status": "ok", "file": str(path)}


@router.post("/incident")
async def incident(
    request: IncidentRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    body = render_incident_report(
        title=request.title,
        severity=request.severity,
        body=request.body,
        metadata=request.metadata,
    )
    path = vault.write_note("Post-Mortems", request.title, body, overwrite=False)
    logger.info("incident_note_created", file=str(path))
    return {"status": "ok", "file": str(path)}


@router.post("/generate-note")
async def generate_note(
    request: GenerateNoteRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    body = render_generic_note(request.title, request.body, request.metadata)
    path = vault.write_note(request.folder, request.title, body, overwrite=request.overwrite)
    logger.info("webhook_note_created", file=str(path))
    return {"status": "ok", "file": str(path)}


@router.post("/collection-report")
async def collection_report(
    request: CollectionReportRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    body = render_collection_report(
        title=request.title,
        source=request.source,
        rows_seen=request.rows_seen,
        rows_written=request.rows_written,
        notes=request.notes,
    )
    path = vault.write_note("Data", request.title, body, overwrite=False)
    logger.info("collection_report_created", file=str(path))
    return {"status": "ok", "file": str(path)}

