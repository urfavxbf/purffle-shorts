# Bakit Nga Ba? — Tagalog Shorts video factory

This repo is a customized fork of PurffleShorts for the Filipino educational channel **Bakit Nga Ba?**.
The first episode covers *Bakit May Nagchi-Cheat Kahit Mahal Ka Nila?*

## Ready now

- Editorial script and SEO metadata: [`examples/bakit-nga-ba-cheaters.json`](../examples/bakit-nga-ba-cheaters.json)
- Separate, safe channel profile: [`channels/bakit-nga-ba.env`](../channels/bakit-nga-ba.env)
- Export-only GitHub Actions renderer (PR/push/manual triggers): [`bakit-nga-ba-render.yml`](../.github/workflows/bakit-nga-ba-render.yml)
- Offline configuration/schema guard tests: [`test_bakit_nga_ba_profile.py`](../tests/test_bakit_nga_ba_profile.py)

The episode uses an eleven-scene Filipino explainer, original Maya/Nico character descriptions repeated in every image prompt, Filipino Microsoft neural voice (`fil-PH-AngeloNeural`), captions, transitions, SFX and a 9:16 output.

**Do not confuse 3D-look imagery with true 3D character animation.**
The upstream renderer applies motion (Ken Burns effects, zooms and transitions) to generated **still images**, not rigged character animation or prompt-to-video clips. Generated characters can vary between images. This channel rejects procedural-background fallbacks and uses a prepared 11-image Cloudflare storyboard. Always watch the result before publishing.

## Run manually in GitHub

1. Merge the reviewed PR into `main` **after CI passes**. Forks may initially disable GitHub Actions; enable workflows in repository **Actions** if required.
2. In **Actions**, choose **Bakit Nga Ba - Render Short (manual, no upload)** → **Run workflow**.
3. Choose **`local`** (default) to download our pre-generated, reusable 11-scene story art from Cloudflare and render it; `pollinations` is an optional, rate-limited alternative. Start with `1080x1920`; `720x1280` is a faster fallback.
4. After a successful run, open that run's **Artifacts** section and download `bakit-nga-ba-cheaters-short`. Review the MP4, captions, images, audio and metadata before making any publishing decision. The artifact now also contains `visual_audit.json` with per-scene coverage.

The action also builds a review MP4 when the relevant PR or `main` is updated. It does **not** run on a timer and does **not** automatically publish anywhere. There is no YouTube authentication in this workflow.

## Run on your own machine

Install Python 3.10+, ffmpeg and fonts; then install the repo:

```bash
python -m pip install -e ".[dev]"
pytest -q tests/test_bakit_nga_ba_profile.py
python -m purffle_shorts make \
  --script examples/bakit-nga-ba-cheaters.json \
  --env-file channels/bakit-nga-ba.env \
  --no-upload
```

For a local machine, download the 11 `scene_XX.jpg.b64` items from the Cloudflare Worker URL noted below and base64-decode each to `media/bakit-nga-ba-cheaters/scene_XX.jpg` first. Exports go to `output_videos/` by default; `script.json`, `metadata.json`, `cover.jpg`, `captions.srt` and `short.mp4` are the expected deliverables when successful.

## Cost, service limits and safety

- No OpenAI LLM key is needed for the **fixed episode** because the complete script is already checked in.
- Microsoft Edge neural voices usually do not need a paid API key, but require network access and are subject to provider availability.
- Pollinations' image generation can require a paid key or rate-limit anonymous calls. It is **not a guaranteed unlimited free service**; add a GitHub Actions secret named `POLLINATIONS_API_KEY` if your account has one, or supply licensed local images. When blocked, GitHub Actions produces a `bakit-nga-ba-visual-audit` diagnostic artifact instead of falsely reporting a complete video.
- Google Flow is **not directly integrated into this repository**. If desired, generate clips there separately; true motion would require those clips to be imported as local video assets.
- Running GitHub Actions can consume included Actions minutes and storage quotas. The channel render runs on relevant PRs or pushes to `main`, plus manual triggers. There is **no scheduled loop**.
- Music plays only if an appropriately licensed audio asset exists. The built-in SFX are synthesized. Do not upload third-party media without permission.
- The `UPLOAD=false` profile, `UPLOAD=false` job environment and `--no-upload` command are deliberate layered safeguards. Do **not** remove them without explicit approval.
- Do not commit API keys, OAuth tokens, Google credentials, or private media. Use repository Actions **Secrets and variables** for credentials.

## Optional next upgrades

- Add persistent AI character reference images for stronger Maya/Nico continuity.
- Provide a tested license-cleared background music track in `music/`.
- Integrate text-to-video through a supported, explicitly authorized provider once a suitable free/paid API is selected.
- Add channel-specific episode templates and release review process. **No automated posting** until the channel owner explicitly approves it.

## Why the first 47-second render was rejected

The first uploaded MP4 had only the initial character artwork, with almost every later shot showing plain blue/orange/purple gradients. Investigation confirmed that upstream `Visuals.for_scene` intentionally substitutes a `generated` gradient when the configured image provider rejects or rate-limits a request. A voiceover and MP4 can still complete, which disguised the broken storyboard.

**New safeguard:** `MIN_VISUAL_COVERAGE=1.0` makes the channel fail the job at the footage stage unless every scene has a non-gradient, readable visual asset. `visual_audit.json` is always saved to the video folder, GitHub Actions reports missing scene numbers in its job summary, and failed jobs offer a diagnostic artifact. This solves silent failure, not the external free-tier restriction itself.

**Important distinction:** A valid picture is not proof of true character animation or style consistency. Human review of the 3D look is still required; this pipeline makes Ken Burns movements on static images and cannot independently deliver rigged 3D animation without another video provider. Do not run repeated keyless requests expecting unlimited free scene generation.

## Prepared character scene library

All 11 portrait storyboard images were generated on the connected Cloudflare account using Workers AI (`@cf/black-forest-labs/flux-2-klein-4b`) and stored in a dedicated KV namespace. A read-only Cloudflare Worker serves their base64 content at `https://bakit-nga-ba-art.wordplays-transcribe.workers.dev/scene_01.jpg.b64` through `scene_11.jpg.b64`. The GitHub Actions workflow downloads and decodes every JPEG into `media/bakit-nga-ba-cheaters/scene_XX.jpg`, verifies each file and checks the images are different before starting the renderer. This avoids spending AI credits again per render; no Cloudflare API credentials are committed to GitHub.

The 11 images are **original AI-generated 3D-look still images** with camera motion, *not* modeled/rigged 3D animation. Character identity continuity and emotional storytelling still require viewing the finished video. Photos are not embedded into git to avoid repository bloat; Cloudflare storage must remain available. The scene host is publicly readable, so do not place confidential images there.
