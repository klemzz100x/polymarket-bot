from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from polybot.domain.models import AgentRepo, TwitterThreadSource


DEFAULT_THREAD_LINKS = ["[[Arbitrage]]", "[[Execution]]", "[[Market Making]]"]


def render_frontmatter(metadata: Mapping[str, Any]) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {_format_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def render_twitter_thread_note(thread: TwitterThreadSource) -> str:
    title = thread.note_title
    metadata = {
        "type": "twitter-thread",
        "source": thread.url,
        "author": thread.author or "",
        "status_id": thread.status_id or "",
        "status": "to_summarize",
        "created": _today(),
        "tags": ["source/twitter", "polymarket", "research"],
    }

    return f"""{render_frontmatter(metadata)}
# {title}

## Source
{thread.url}

## Resume
A completer apres extraction du contenu complet du thread.

## Concepts cles
- Polymarket
- Trading automatise
- Recherche a qualifier

## Idees exploitables
- Verifier si le thread contient une hypothese testable.
- Transformer toute strategie mentionnee en spec de backtest.
- Classer les idees entre execution, pricing, market making, arbitrage, data ou tooling.

## Strategies mentionnees
- A extraire.

## Risques / limites
- Source non auditee.
- Performance annoncee potentiellement non reproductible.
- Risque de survivorship bias et de marketing.

## A tester
- Extraire le contenu via workflow n8n ou script de scraping autorise.
- Faire une note strategie separee si une idee semble robuste.
- Lier les hypotheses a un backtest reproductible.

## Liens lies
{_bullet_links(DEFAULT_THREAD_LINKS)}
"""


def render_agent_note(repo: AgentRepo) -> str:
    metadata = {
        "type": "external-agent",
        "repo": repo.url,
        "owner": repo.owner,
        "status": "to_test",
        "created": _today(),
        "tags": ["tool/agent", "external-repo"],
    }

    return f"""{render_frontmatter(metadata)}
# {repo.name}

## Repo
{repo.url}

## Description
A completer apres lecture du README et du code.

## Utilite potentielle
- Evaluer si l'outil peut accelerer la recherche, le scraping, l'orchestration ou la documentation.

## Cas d'usage pour Polymarket
- Recherche automatisee.
- Documentation d'agents IA.
- Generation de notes Obsidian.
- Experimentation hors chemin critique d'execution.

## Avantages
- A auditer.

## Risques
- Code externe non audite.
- Dependances et licences a verifier.
- Aucune cle ou wallet ne doit etre expose a ce repo.

## Dependances
- A extraire depuis le projet.

## Statut
A tester

## Notes techniques
- Repertoire local cible: `external-agents/{repo.local_dir_name}`.
"""


def render_generic_note(
    title: str,
    body: str,
    metadata: Mapping[str, str | int | float | bool | list[str]],
) -> str:
    full_metadata: dict[str, Any] = {"type": "note", "created": _today(), **metadata}
    return f"{render_frontmatter(full_metadata)}\n# {title}\n\n{body.strip()}\n"


def _bullet_links(links: Sequence[str]) -> str:
    return "\n".join(f"- {link}" for link in links)


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _format_yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_quote_yaml_scalar(str(item)) for item in value) + "]"
    return _quote_yaml_scalar(str(value))


def _quote_yaml_scalar(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'

