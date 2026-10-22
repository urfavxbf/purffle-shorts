"""Offline channel contract tests; these never generate or upload media."""

import json
from pathlib import Path

from dotenv import dotenv_values

from purffle_shorts.script import Script

ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "examples" / "bakit-nga-ba-cheaters.json"
PROFILE = ROOT / "channels" / "bakit-nga-ba.env"
WORKFLOW = ROOT / ".github" / "workflows" / "bakit-nga-ba-render.yml"


def test_filippino_short_schema_and_story_arc():
    raw = json.loads(EPISODE.read_text(encoding="utf-8"))
    episode = Script.from_dict(raw)
    assert episode.language == "fil"
    assert episode.style == "explainer"
    assert episode.category == "education"
    assert 8 <= len(episode.scenes) <= 12
    assert all(scene.narration.strip() and scene.image_prompt.strip() for scene in episode.scenes)
    assert all(scene.speaker == "A" for scene in episode.scenes)
    assert "nagchi-cheat" in episode.scenes[0].narration.lower()
    assert "hindi excuse" in episode.narration.lower()
    assert "niloko ka" in episode.narration.lower()
    assert "Bakit Nga Ba?" in episode.narration


def test_3d_look_prompt_consistency():
    episode = Script.from_dict(json.loads(EPISODE.read_text(encoding="utf-8")))
    for scene in episode.scenes:
        prompt = scene.image_prompt.lower()
        for phrase in ("3d animation look", "yellow hoodie", "teal jacket", "portrait 9:16"):
            assert phrase in prompt


def test_profile_is_fil_and_export_only():
    env = dotenv_values(PROFILE)
    assert env["LANGUAGE"] == "fil"
    assert env["TTS_VOICE"] == "fil-PH-AngeloNeural"
    assert env["RESOLUTION"] == "1080x1920"
    assert env["UPLOAD"] == "false"
    assert env["KEEP_VIDEOS"] == "true"
    assert env["SCRIPT_REVIEW"] == "off"
    assert all("KEY" not in key or not val for key, val in env.items() if key.endswith("_API_KEY"))


def test_workflow_requires_manual_action_and_enforces_no_upload():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "schedule:" not in text
    assert "pull_request:" not in text
    assert "--no-upload" in text
    assert 'UPLOAD: "false"' in text
    assert "--script examples/bakit-nga-ba-cheaters.json" in text
    assert "upload-artifact@v4" in text
