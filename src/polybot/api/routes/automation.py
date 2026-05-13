from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from polybot.agents.importer import clone_agent_repos
from polybot.core.config import Settings, get_settings
from polybot.core.logging import get_logger
from polybot.core.security import verify_automation_secret
from polybot.knowledge.obsidian import ObsidianVault
from polybot.resources.markdown import render_agent_note, render_generic_note, render_twitter_thread_note
from polybot.resources.parsers import parse_agent_repos, parse_twitter_thread_sources

router = APIRouter()
logger = get_logger(__name__)


class ImportTwitterThreadsRequest(BaseModel):
    source_path: str | None = Field(default=None)
    overwrite: bool = False


class ImportAgentsRequest(BaseModel):
    source_path: str | None = Field(default=None)
    clone: bool = False
    update_existing: bool = False
    overwrite_notes: bool = False


class GenericNoteRequest(BaseModel):
    folder: str = Field(examples=["Ideas"])
    title: str
    body: str
    metadata: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)
    overwrite: bool = False


class AutomationResult(BaseModel):
    status: str
    count: int = 0
    files: list[str] = Field(default_factory=list)
@router.post(
    "/twitter-threads/import",
    dependencies=[Depends(verify_automation_secret)],
    response_model=AutomationResult,
)
async def import_twitter_threads(
    request: ImportTwitterThreadsRequest,
    settings: Settings = Depends(get_settings),
) -> AutomationResult:
    source_path = Path(request.source_path) if request.source_path else settings.resources_dir / "twitter-threads"
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()

    files: list[str] = []
    for thread in parse_twitter_thread_sources(source_path):
        note = render_twitter_thread_note(thread)
        path = vault.write_note(
            folder="Sources/Twitter-Threads",
            title=thread.note_title,
            body=note,
            overwrite=request.overwrite,
        )
        files.append(str(path))

    logger.info("twitter_threads_imported", count=len(files), source=str(source_path))
    return AutomationResult(status="ok", count=len(files), files=files)


@router.post(
    "/agents/import",
    dependencies=[Depends(verify_automation_secret)],
    response_model=AutomationResult,
)
async def import_agents(
    request: ImportAgentsRequest,
    settings: Settings = Depends(get_settings),
) -> AutomationResult:
    source_path = Path(request.source_path) if request.source_path else settings.resources_dir / "agents-list"
    repos = parse_agent_repos(source_path)

    if request.clone:
        clone_agent_repos(
            repos=repos,
            target_dir=settings.external_agents_dir,
            dry_run=False,
            update_existing=request.update_existing,
        )

    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()

    files: list[str] = []
    for repo in repos:
        note = render_agent_note(repo)
        path = vault.write_note(
            folder="Tools/Agents",
            title=repo.name,
            body=note,
            overwrite=request.overwrite_notes,
        )
        files.append(str(path))

    logger.info("agents_imported", count=len(files), cloned=request.clone, source=str(source_path))
    return AutomationResult(status="ok", count=len(files), files=files)


@router.post(
    "/notes",
    dependencies=[Depends(verify_automation_secret)],
    response_model=AutomationResult,
)
async def create_note(
    request: GenericNoteRequest,
    settings: Settings = Depends(get_settings),
) -> AutomationResult:
    vault = ObsidianVault(settings.obsidian_vault_dir)
    vault.ensure_structure()
    body = render_generic_note(title=request.title, body=request.body, metadata=request.metadata)
    path = vault.write_note(
        folder=request.folder,
        title=request.title,
        body=body,
        overwrite=request.overwrite,
    )
    logger.info("generic_note_created", file=str(path))
    return AutomationResult(status="ok", count=1, files=[str(path)])
