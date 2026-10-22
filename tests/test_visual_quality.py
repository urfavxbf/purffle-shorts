"""Regression tests for the all-gradient video defect reported in the first Short."""

from types import SimpleNamespace

import pytest
from PIL import Image

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
