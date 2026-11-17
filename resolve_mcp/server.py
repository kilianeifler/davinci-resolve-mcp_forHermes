"""Local MCP tools for controlling DaVinci Resolve through its scripting API."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from resolve_mcp.core import (
    build_status,
    clip_names_from_folder,
    normalize_clip_names,
    normalize_name,
    normalize_page,
    prepare_import_items,
)

mcp = FastMCP("davinci-resolve")


def _resolve() -> Any:
    try:
        import DaVinciResolveScript as dvr_script
    except ImportError as exc:
        raise RuntimeError(
            "DaVinci Resolve scripting module is unavailable; check the MCP server environment."
        ) from exc
    resolve = dvr_script.scriptapp("Resolve")
    if resolve is None:
        raise RuntimeError(
            "Could not connect to DaVinci Resolve. Keep Resolve open and set External scripting to Local."
        )
    return resolve


def _current_project(resolve: Any) -> Any:
    project = resolve.GetCurrentProject()
    if project is None:
        raise RuntimeError("No Resolve project is currently open.")
    return project


@mcp.tool()
def resolve_status() -> dict[str, Any]:
    """Read the connected Resolve version, active page, project, and timeline."""
    return build_status(_resolve())


@mcp.tool()
def list_projects() -> list[str]:
    """List project names in Resolve's currently selected project-library folder."""
    projects = _resolve().GetProjectManager().GetProjectListInCurrentFolder()
    return projects or []


@mcp.tool()
def list_media_pool(limit: int = 100) -> dict[str, Any]:
    """List clip names from the open project's root Media Pool folder (read-only)."""
    resolve = _resolve()
    project = _current_project(resolve)
    clips = clip_names_from_folder(project.GetMediaPool().GetRootFolder(), limit)
    return {"count": len(clips), "clips": clips}


@mcp.tool()
def set_page(page: str) -> dict[str, Any]:
    """Switch Resolve's visible workspace page; accepts media, cut, edit, fusion, color, fairlight, or deliver."""
    normalized = normalize_page(page)
    opened = bool(_resolve().OpenPage(normalized))
    if not opened:
        raise RuntimeError(f"Resolve did not open the {normalized!r} page.")
    return {"opened": True, "page": normalized}


@mcp.tool()
def create_project(name: str) -> dict[str, Any]:
    """Create and activate a new Resolve project. This changes the project library; use only on explicit user request."""
    project_name = normalize_name(name, "project name")
    project = _resolve().GetProjectManager().CreateProject(project_name)
    if project is None:
        raise RuntimeError(f"Resolve could not create project {project_name!r}; it may already exist.")
    return {"created": True, "project": project.GetName()}


@mcp.tool()
def save_current_project() -> dict[str, Any]:
    """Save the active Resolve project to disk. This writes project data; use only on explicit user request."""
    resolve = _resolve()
    _current_project(resolve)
    saved = bool(resolve.GetProjectManager().SaveProject())
    if not saved:
        raise RuntimeError("Resolve did not save the active project.")
    return {"saved": True}


@mcp.tool()
def import_media(paths: list[str]) -> dict[str, Any]:
    """Import explicitly named existing media files into the current Media Pool folder; use only on explicit user request."""
    import_items = prepare_import_items(paths)
    project = _current_project(_resolve())
    imported = project.GetMediaPool().ImportMedia(import_items) or []
    return {"count": len(imported), "clips": [item.GetName() for item in imported]}


@mcp.tool()
def create_empty_timeline(name: str) -> dict[str, Any]:
    """Create a blank timeline in the active project; this changes project data, so use only on explicit user request."""
    timeline_name = normalize_name(name, "timeline name")
    project = _current_project(_resolve())
    timeline = project.GetMediaPool().CreateEmptyTimeline(timeline_name)
    if timeline is None:
        raise RuntimeError(f"Resolve could not create timeline {timeline_name!r}.")
    return {"created": True, "timeline": timeline.GetName()}


@mcp.tool()
def append_media_pool_clips(clip_names: list[str]) -> dict[str, Any]:
    """Append named root-folder Media Pool clips to the active timeline; this edits the timeline, so use only on explicit user request."""
    names = normalize_clip_names(clip_names)
    project = _current_project(_resolve())
    media_pool = project.GetMediaPool()
    items = media_pool.GetRootFolder().GetClipList() or []
    matches: dict[str, list[Any]] = {}
    for item in items:
        item_name = item.GetName()
        if item_name in names:
            matches.setdefault(item_name, []).append(item)
    missing = [name for name in names if name not in matches]
    ambiguous = [name for name in names if len(matches.get(name, [])) > 1]
    if missing:
        raise ValueError(f"clip(s) not found in the root Media Pool folder: {', '.join(missing)}")
    if ambiguous:
        raise ValueError(f"clip name(s) are ambiguous in the root Media Pool folder: {', '.join(ambiguous)}")
    appended = media_pool.AppendToTimeline(
        [{"mediaPoolItem": matches[name][0]} for name in names]
    )
    if not appended:
        raise RuntimeError("Resolve did not append the requested clips.")
    return {"appended": len(appended), "clips": names}


if __name__ == "__main__":
    mcp.run(transport="stdio")
