"""Visual asset quality gate.

A generated gradient is intentionally not considered a scene visual.  Channel profiles
can opt into a required minimum coverage so provider credit failures don't silently
become downloadable, visually empty videos.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


class VisualQualityError(RuntimeError):
    """The requested storyboard did not have enough genuine media assets."""


def _asset_issue(item: Any) -> str:
    """Return an explanation if the renderer would lack genuine visual source media."""
    if item is None:
        return "no media selected"
    if getattr(item, "kind", "") == "generated" or getattr(item, "source", "") == "generated":
        return "provider failed; procedural gradient fallback"
    if getattr(item, "kind", "") not in ("image", "video"):
        return "unsupported media type"
    path = getattr(item, "path", None)
    if not path:
        return "missing downloaded asset path"
    file = Path(path)
    if not file.is_file() or file.stat().st_size == 0:
        return "asset missing or empty"
    if getattr(item, "kind", "") == "image":
        try:
            with Image.open(file) as img:
                img.verify()
        except (OSError, ValueError, UnidentifiedImageError):
            return "image file is corrupt or unsupported"
    return ""


def audit_scene_visuals(shots: Sequence[Any], media: Sequence[Any], scene_count: int) -> dict[str, Any]:
    """Build an auditable scene-by-scene coverage report before encoding a video.

    Every split shot of a scene must have valid media. This prevents an otherwise
    attractive opening from concealing ten missing storyboard images.
    """
    if scene_count < 1:
        raise ValueError("scene_count must be positive")
    if len(shots) != len(media):
        raise ValueError("each shot must have one media item")

    parts: dict[int, list[tuple[str, str]]] = {i: [] for i in range(scene_count)}
    for shot, item in zip(shots, media):
        idx = int(shot.index)
        if idx not in parts:
            raise ValueError(f"shot scene index {idx} outside storyboard")
        parts[idx].append((getattr(item, "source", "unknown"), _asset_issue(item)))

    scenes = []
    for index, assets in parts.items():
        problems = sorted({issue for _, issue in assets if issue})
        if not assets:
            problems.append("no shots for scene")
        scenes.append({
            "scene": index + 1,
            "ok": bool(assets) and not problems,
            "sources": sorted({source for source, _ in assets}),
            "issues": problems,
        })
    ready = sum(scene["ok"] for scene in scenes)
    return {
        "scene_count": scene_count,
        "complete_scenes": ready,
        "coverage": round(ready / scene_count, 4),
        "missing_scenes": [scene["scene"] for scene in scenes if not scene["ok"]],
        "scenes": scenes,
    }


def require_visual_coverage(report: dict[str, Any], minimum: float) -> None:
    """Stop bad output early instead of quietly substituting generic backgrounds."""
    if not 0 <= minimum <= 1:
        raise ValueError("visual coverage threshold must be between 0 and 1")
    if report["coverage"] >= minimum:
        return
    missing = ", ".join(str(i) for i in report["missing_scenes"])
    raise VisualQualityError(
        f"Visual quality gate blocked render: only {report['complete_scenes']}/"
        f"{report['scene_count']} scenes have actual media (minimum {minimum:.0%}). "
        f"Missing/problem scenes: {missing}. Check visual_audit.json in the Actions artifact. "
        "The AI image provider may be rate-limited or out of credits; use a working image "
        "provider/API key or supply correctly licensed local scene assets. "
        "No gradient-only MP4 was produced."
    )
