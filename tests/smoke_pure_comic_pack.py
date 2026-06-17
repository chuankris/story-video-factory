"""Smoke tests for pure comic packaging tools.

Run from project root (the worktree directory):
    python -m pytest tests/smoke_pure_comic_pack.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "story-video-factory" / "scripts"))

import render_lettered_panels as rlp
import build_publish_carousel as bpc
import generate_qc_report as gqr
import generate_publish_pack as gpp

SAMPLE_EPISODE = (Path(__file__).parent.parent / "../../episodes/star-in-uniform-001").resolve()


@pytest.fixture
def minimal_episode(tmp_path):
    ep = tmp_path / "test-episode-001"
    ep.mkdir()
    script = {"segments": [
        {"id": "p001", "text": "测试文案第一行，内容完整。"},
        {"id": "p002", "text": "测试文案第二行，故事继续。"},
    ]}
    (ep / "script.json").write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
    meta = {
        "episode_id": "test-episode-001", "title": "测试集",
        "production_mode": "pure_comic", "draft_mode": False,
        "target_panel_count": 2,
        "provider_plan": {"production_panels": "gpt-image"},
        "jimeng_budget": {"max_prompts": 0},
        "gpt_image_budget": {"max_images": 2},
        "minimax_budget": {"tts": False, "video": False},
    }
    (ep / "episode-meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    raw_dir = ep / "assets" / "images-raw"
    raw_dir.mkdir(parents=True)
    for pid in ("p001", "p002"):
        Image.new("RGB", (1080, 1920), color=(200, 180, 150)).save(raw_dir / f"{pid}_001.png")
    # Map approved sources so render_lettered_panels can proceed
    selected = {"p001": "assets/images-raw/p001_001.png", "p002": "assets/images-raw/p002_001.png"}
    (ep / "selected-candidates.json").write_text(json.dumps(selected, ensure_ascii=False), encoding="utf-8")
    return ep


@pytest.fixture
def minimal_episode_with_finals(minimal_episode):
    images_dir = minimal_episode / "assets" / "images"
    images_dir.mkdir(parents=True)
    for pid in ("p001", "p002"):
        Image.new("RGB", (1080, 1920), color=(200, 180, 150)).save(images_dir / f"{pid}.png")
    return minimal_episode


# --- script.json encoding ---

def test_script_json_utf8_bom_readable(minimal_episode):
    script = {"segments": [{"id": "p001", "text": "清晨六点，妈妈把校服熨好了。"}]}
    bom_path = minimal_episode / "script.json"
    bom_path.write_bytes(b'\xef\xbb\xbf' + json.dumps(script, ensure_ascii=False).encode("utf-8"))
    scripts = rlp.load_script(minimal_episode)
    assert "p001" in scripts
    assert "清晨" in scripts["p001"]


def test_load_script_returns_all_segments(minimal_episode):
    scripts = rlp.load_script(minimal_episode)
    assert set(scripts.keys()) == {"p001", "p002"}


# --- caption-layout mismatch ---

def test_caption_layout_mismatch_causes_exit(minimal_episode):
    src = minimal_episode / "assets" / "images-raw" / "p001_001.png"
    with pytest.raises(SystemExit):
        rlp.render_panel(
            episode=minimal_episode, panel_id="p001",
            script_text="测试文案第一行，内容完整。",
            lines=["错误文案，", "与脚本不符。"],
            source=src, dry_run=False,
        )


def test_caption_layout_match_passes(minimal_episode):
    src = minimal_episode / "assets" / "images-raw" / "p001_001.png"
    script_text = "测试文案第一行，内容完整。"
    lines = ["测试文案第一行，", "内容完整。"]
    assert "".join(lines) == script_text
    out = rlp.render_panel(
        episode=minimal_episode, panel_id="p001",
        script_text=script_text, lines=lines,
        source=src, dry_run=False,
    )
    assert out.exists()
    with Image.open(out) as img:
        assert img.size == (1080, 1920)


# --- render output size ---

def test_rendered_panel_is_1080x1920(minimal_episode):
    rlp.process_episode(minimal_episode)
    for pid in ("p001", "p002"):
        out = minimal_episode / "assets" / "images" / f"{pid}.png"
        assert out.exists(), f"{pid}.png missing"
        with Image.open(out) as img:
            assert img.size == (1080, 1920), f"{pid}: {img.size}"


def test_douyin_msyh_top_style_renders_1080x1920(minimal_episode):
    src = minimal_episode / "assets" / "images-raw" / "p001_001.png"
    script_text = "测试文案第一行，内容完整。"
    lines = ["测试文案第一行，", "内容完整。"]
    out = rlp.render_panel(
        episode=minimal_episode,
        panel_id="p001",
        script_text=script_text,
        lines=lines,
        source=src,
        dry_run=False,
        style="douyin-msyh-top",
    )
    assert out.exists()
    with Image.open(out) as img:
        assert img.size == (1080, 1920)


def test_douyin_msyh_top_style_uses_utf8_layout_lines(minimal_episode):
    layout = {
        "p001": {
            "source": "assets/images-raw/p001_001.png",
            "lines": ["测试文案第一行，", "内容完整。"],
        }
    }
    (minimal_episode / "caption-layout.json").write_text(
        json.dumps(layout, ensure_ascii=False), encoding="utf-8"
    )
    rlp.process_episode(minimal_episode, only_panel="p001", style="douyin-msyh-top")
    rendered = minimal_episode / "assets" / "images" / "p001.png"
    assert rendered.exists()
    saved_layout = rlp.load_caption_layout(minimal_episode)
    assert "".join(saved_layout["p001"]["lines"]) == "测试文案第一行，内容完整。"


# --- carousel ---

def test_carousel_order_and_naming(minimal_episode_with_finals):
    bpc.build_carousel(minimal_episode_with_finals, force=True)
    carousel_dir = minimal_episode_with_finals / "output" / "publish" / "carousel"
    files = sorted(f.name for f in carousel_dir.glob("*.png"))
    assert files == ["01-p001.png", "02-p002.png"]


def test_carousel_requires_final_images(minimal_episode):
    with pytest.raises(SystemExit):
        bpc.build_carousel(minimal_episode, force=True)


def test_carousel_ratio_check(minimal_episode_with_finals):
    bpc.build_carousel(minimal_episode_with_finals, force=True)
    for f in (minimal_episode_with_finals / "output" / "publish" / "carousel").glob("*.png"):
        ok, (w, h) = bpc.check_ratio(f)
        assert ok, f"{f.name}: {w}x{h} is not 9:16"


def test_carousel_can_include_cover(minimal_episode_with_finals):
    Image.new("RGB", (1080, 1920), color=(180, 160, 130)).save(
        minimal_episode_with_finals / "assets" / "images" / "cover.png"
    )
    bpc.build_carousel(minimal_episode_with_finals, force=True, include_cover=True)
    carousel_dir = minimal_episode_with_finals / "output" / "publish" / "carousel"
    files = sorted(f.name for f in carousel_dir.glob("*.png"))
    assert files == ["00-cover.png", "01-p001.png", "02-p002.png"]


# --- QC report ---

def test_qc_report_generates_without_error(minimal_episode_with_finals):
    gqr.generate_report(minimal_episode_with_finals, force=False)
    report = minimal_episode_with_finals / "output" / "qc-report.generated.md"
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "## p001" in content
    assert "## p002" in content
    assert "Carousel-Level QC" in content


def test_qc_report_no_mojibake(minimal_episode_with_finals):
    gqr.generate_report(minimal_episode_with_finals, force=False)
    report = minimal_episode_with_finals / "output" / "qc-report.generated.md"
    content = report.read_text(encoding="utf-8")
    assert "测试集" in content


# --- Publish pack ---

def test_publish_pack_generates_without_error(minimal_episode_with_finals):
    gpp.generate_pack(minimal_episode_with_finals, force=False)
    pack = minimal_episode_with_finals / "output" / "publish" / "pack.generated.md"
    assert pack.exists()
    content = pack.read_text(encoding="utf-8")
    assert "Title Options" in content
    assert "Cover Text" in content
    assert "Posting Checklist" in content


def test_publish_pack_no_video_reference(minimal_episode_with_finals):
    gpp.generate_pack(minimal_episode_with_finals, force=False)
    pack = minimal_episode_with_finals / "output" / "publish" / "pack.generated.md"
    content = pack.read_text(encoding="utf-8")
    assert "draft.mp4" not in content


def test_publish_pack_lists_panel_order(minimal_episode_with_finals):
    ep = minimal_episode_with_finals
    bpc.build_carousel(ep, force=True)
    gpp.generate_pack(ep, force=False)
    content = (ep / "output" / "publish" / "pack.generated.md").read_text(encoding="utf-8")
    assert "p001" in content
    assert "p002" in content


def test_publish_pack_has_no_todo_placeholders(minimal_episode_with_finals):
    ep = minimal_episode_with_finals
    bpc.build_carousel(ep, force=True)
    gpp.generate_pack(ep, force=False)
    content = (ep / "output" / "publish" / "pack.generated.md").read_text(encoding="utf-8")
    assert "# TODO" not in content


def test_prepare_command_output_is_ascii(minimal_episode_with_finals):
    script = Path(__file__).parent.parent / "skills" / "story-video-factory" / "scripts" / "prepare_pure_comic_episode.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(minimal_episode_with_finals),
            "--skip-render",
            "--skip-carousel",
            "--skip-qc",
            "--skip-pack",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result.stdout.encode("ascii")


def test_prepare_command_accepts_caption_style_and_cover(minimal_episode_with_finals):
    Image.new("RGB", (1080, 1920), color=(180, 160, 130)).save(
        minimal_episode_with_finals / "assets" / "images" / "cover.png"
    )
    script = Path(__file__).parent.parent / "skills" / "story-video-factory" / "scripts" / "prepare_pure_comic_episode.py"
    subprocess.run(
        [
            sys.executable,
            str(script),
            str(minimal_episode_with_finals),
            "--skip-render",
            "--skip-qc",
            "--skip-pack",
            "--caption-style",
            "douyin-msyh-top",
            "--include-cover",
            "--force",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    files = sorted(
        p.name for p in (minimal_episode_with_finals / "output" / "publish" / "carousel").glob("*.png")
    )
    assert files == ["00-cover.png", "01-p001.png", "02-p002.png"]


# --- New episode scaffolding ---

def test_new_pure_comic_episode_creates_standard_files(tmp_path):
    import new_pure_comic_episode as npe

    ep = tmp_path / "ring-home-001"
    npe.create_episode(
        ep,
        title="响五声就好",
        panel_count=11,
        era="2006 China",
        theme="长途电话亲情",
    )

    assert (ep / "episode-meta.json").exists()
    assert (ep / "script.json").exists()
    assert (ep / "storyboard.json").exists()
    assert (ep / "assets" / "refs").is_dir()
    assert (ep / "assets" / "images-raw").is_dir()
    assert (ep / "assets" / "images").is_dir()
    assert (ep / "output" / "publish").is_dir()

    meta = json.loads((ep / "episode-meta.json").read_text(encoding="utf-8-sig"))
    assert meta["episode_id"] == "ring-home-001"
    assert meta["title"] == "响五声就好"
    assert meta["target_panel_count"] == 11
    assert meta["era"] == "2006 China"
    assert meta["theme"] == "长途电话亲情"
    assert meta["provider_plan"]["production_panels"] == "gpt-image"
    assert meta["provider_plan"]["caption_style"] == "douyin-msyh-top"

    selected = json.loads((ep / "selected-candidates.json").read_text(encoding="utf-8-sig"))
    jimeng = json.loads((ep / "prompts-jimeng.json").read_text(encoding="utf-8-sig"))
    assert selected == {}
    assert jimeng == []


def test_new_pure_comic_episode_refuses_existing_without_force(tmp_path):
    import new_pure_comic_episode as npe

    ep = tmp_path / "existing-001"
    npe.create_episode(ep, title="第一次")

    with pytest.raises(SystemExit):
        npe.create_episode(ep, title="第二次")

    meta = json.loads((ep / "episode-meta.json").read_text(encoding="utf-8-sig"))
    assert meta["title"] == "第一次"


def test_new_pure_comic_episode_force_recreates_existing(tmp_path):
    import new_pure_comic_episode as npe

    ep = tmp_path / "force-001"
    npe.create_episode(ep, title="旧标题")
    (ep / "extra.txt").write_text("remove me", encoding="utf-8")

    npe.create_episode(ep, title="新标题", force=True)

    meta = json.loads((ep / "episode-meta.json").read_text(encoding="utf-8-sig"))
    assert meta["title"] == "新标题"
    assert not (ep / "extra.txt").exists()


def test_new_pure_comic_episode_cli_help_runs():
    script = Path(__file__).parent.parent / "skills" / "story-video-factory" / "scripts" / "new_pure_comic_episode.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--title" in result.stdout
    assert "--panel-count" in result.stdout


# --- Sample episode integration ---

@pytest.mark.skipif(not SAMPLE_EPISODE.exists(), reason="sample episode not present")
def test_sample_episode_final_images_are_1080x1920():
    panels = sorted((SAMPLE_EPISODE / "assets" / "images").glob("p*.png"))
    assert len(panels) == 10, f"Expected 10 panels, found {len(panels)}"
    for p in panels:
        with Image.open(p) as img:
            assert img.size == (1080, 1920), f"{p.name}: {img.size}"


@pytest.mark.skipif(not SAMPLE_EPISODE.exists(), reason="sample episode not present")
def test_sample_carousel_order():
    carousel_dir = SAMPLE_EPISODE / "output" / "publish" / "carousel"
    files = sorted(f.name for f in carousel_dir.glob("*.png"))
    expected = [f"{i:02d}-p{i:03d}.png" for i in range(1, 11)]
    assert files == expected
