"""Regression tests for the all-gradient video defect reported in the first Short."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from purffle_shorts.config import Settings
from purffle_shorts.media import Visuals
from purffle_shorts.pipeline import shots_requiring_media
from purffle_shorts.visual_quality import VisualQualityError, audit_scene_visuals, require_visual_coverage


def _shot(index):
    return SimpleNamespace(index=index)


def _media(source="generated", kind="generated", path=None):
    return SimpleNamespace(source=source, kind=kind, path=path)


def test_first_scene_only_is_not_acceptable(tmp_path):
    first_image = tmp_path / "scene01.png"
    Image.new("RGB", (128, 192), (50, 80, 110)).save(first_image)
    media = [_media("pollinations", "image", first_image)] + [_media() for _ in range(10)]
    audit = audit_scene_visuals([_shot(i) for i in range(11)], media, 11)

    assert audit["complete_scenes"] == 1
    assert audit["missing_scenes"] == list(range(2, 12))
    with pytest.raises(VisualQualityError, match="only 1/11 scenes"):
        require_visual_coverage(audit, minimum=1.0)


def test_all_valid_assets_pass_even_when_one_scene_has_multiple_shots(tmp_path):
    photos = []
    for i in range(3):
        path = tmp_path / f"scene{i}.png"
        Image.new("RGB", (64, 96), (50 + i, 70, 90)).save(path)
        photos.append(_media("local", "image", path))
    audit = audit_scene_visuals([_shot(0), _shot(0), _shot(1)], [photos[0], photos[1], photos[2]], 2)
    assert audit["coverage"] == 1.0
    require_visual_coverage(audit, minimum=1.0)


def test_corrupted_or_missing_image_is_not_counted(tmp_path):
    broken = tmp_path / "bad.png"
    broken.write_bytes(b"this is not an image")
    audit = audit_scene_visuals(
        [_shot(0), _shot(1)], [_media("local", "image", broken), _media("local", "image", tmp_path / "gone.jpg")], 2
    )
    assert audit["coverage"] == 0.0
    assert "image file is corrupt or unsupported" in audit["scenes"][0]["issues"]
    assert "asset missing or empty" in audit["scenes"][1]["issues"]


def test_default_threshold_does_not_break_existing_gradient_demo():
    audit = audit_scene_visuals([_shot(0)], [_media()], 1)
    require_visual_coverage(audit, minimum=0.0)
    with pytest.raises(ValueError, match="between 0 and 1"):
        require_visual_coverage(audit, minimum=1.01)


def test_mismatch_and_missing_scene_fail_diagnostic():
    audit = audit_scene_visuals([_shot(0)], [_media("local", "image")], 2)
    assert audit["missing_scenes"] == [1, 2]
    with pytest.raises(ValueError, match="each shot"):
        audit_scene_visuals([_shot(0)], [], 1)


def test_numbered_scene_assets_map_to_scene_not_shot(tmp_path):
    """A 10-shot edit with 2 scenes must request only 2 numbered scene images."""
    folder = tmp_path / "episode"
    folder.mkdir()
    for i in (1, 2):
        Image.new("RGB", (768, 1360), (40 * i, 80, 100)).save(folder / f"scene_{i:02d}.jpg")

    settings = Settings(media_dir=str(folder), visual_sources=["local"], resolution=(1080, 1920))
    shots = [
        SimpleNamespace(index=i, part=part)
        for i in range(2)
        for part in range(5)
    ]
    wanted, numbered = shots_requiring_media(shots, settings)
    assert numbered is True
    assert [(s.index, s.part) for s in wanted] == [(0, 0), (1, 0)]

    visuals = Visuals(settings)
    items = visuals.for_scenes([("query", "", 3) for _ in wanted], "topic", tmp_path / "results")
    assert [Path(m.path).name for m in items] == ["scene_01.jpg", "scene_02.jpg"]
    mapped = [items[s.index] for s in shots]
    assert [Path(x.path).stem for x in mapped] == [
        f"scene_{s.index + 1:02d}" for s in shots
    ]


def test_missing_numbered_scene_never_picks_unrelated_local_picture(tmp_path):
    folder = tmp_path / "episode"
    folder.mkdir()
    Image.new("RGB", (768, 1360), (40, 80, 100)).save(folder / "scene_01.jpg")
    settings = Settings(media_dir=str(folder), visual_sources=["local"])
    visuals = Visuals(settings)
    first = visuals.for_scene(0, "closeup couple", "", "relationship", 4, tmp_path)
    second = visuals.for_scene(1, "sunrise walk", "", "relationship", 4, tmp_path)
    assert first.kind == "image"
    assert second.kind == "generated"
