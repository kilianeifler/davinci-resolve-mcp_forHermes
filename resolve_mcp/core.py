"""Core, testable helpers for the DaVinci Resolve MCP server."""

from pathlib import Path
from typing import Any

PAGE_NAMES = frozenset({"media", "cut", "edit", "fusion", "color", "fairlight", "deliver"})
MAX_IMPORT_PATHS = 50
MAX_MEDIA_POOL_ITEMS = 500


def normalize_page(page: str) -> str:
    if not isinstance(page, str):
        raise ValueError("page must be a string")
    normalized = page.strip().lower()
    if normalized not in PAGE_NAMES:
        choices = ", ".join(sorted(PAGE_NAMES))
        raise ValueError(f"page must be one of: {choices}")
    return normalized


def build_status(resolve: Any) -> dict[str, Any]:
    project = resolve.GetCurrentProject()
    timeline = project.GetCurrentTimeline() if project else None
    return {
        "connected": True,
        "version": resolve.GetVersionString(),
        "page": resolve.GetCurrentPage(),
        "project": project.GetName() if project else None,
        "timeline": timeline.GetName() if timeline else None,
    }


def normalize_import_paths(paths: list[str]) -> list[str]:
    if not isinstance(paths, list) or not paths:
        raise ValueError("provide a non-empty list of absolute media file paths")
    if len(paths) > MAX_IMPORT_PATHS:
        raise ValueError(f"at most {MAX_IMPORT_PATHS} files can be imported per call")

    normalized: list[str] = []
    for raw_path in paths:
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError("each media path must be a non-empty string")
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            raise ValueError(f"media path must be absolute: {raw_path}")
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"media file does not exist: {raw_path}") from exc
        if not resolved.is_file():
            raise ValueError(f"media path is not a file: {raw_path}")
        normalized.append(str(resolved))
    return normalized


def clip_names_from_folder(folder: Any, limit: int = 100) -> list[str]:
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_MEDIA_POOL_ITEMS:
        raise ValueError(f"limit must be between 1 and {MAX_MEDIA_POOL_ITEMS}")
    items = folder.GetClipList() or []
    return [item.GetName() for item in items[:limit]]


def normalize_name(name: str, label: str = "name") -> str:
    if not isinstance(name, str):
        raise ValueError(f"{label} must be a string")
    normalized = name.strip()
    if not normalized:
        raise ValueError(f"{label} must not be blank")
    if len(normalized) > 255:
        raise ValueError(f"{label} must be 255 characters or fewer")
    return normalized


def normalize_clip_names(names: list[str]) -> list[str]:
    if not isinstance(names, list) or not names:
        raise ValueError("provide a non-empty list of media pool clip names")
    if len(names) > 100:
        raise ValueError("at most 100 clips can be appended per call")
    normalized = [normalize_name(name, "clip name") for name in names]
    if len(set(normalized)) != len(normalized):
        raise ValueError("clip names must be unique within one call")
    return normalized


def prepare_import_items(paths: list[str]) -> list[dict[str, str]]:
    return [{"FilePath": path} for path in normalize_import_paths(paths)]
