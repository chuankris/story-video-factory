# Story Video Factory

English | [中文](#中文)

A reviewed story-production factory for Douyin-style image carousels, comic videos, and later direct video workflows.

The current V1 mainline is **pure comic carousel first**: write the story, generate still comic panels, render readable Chinese captions locally, package the carousel, then publish. Video, TTS, Jimeng automation, and MiniMax are provider lanes that can be added after the comic path is stable.

## Current Focus

- Primary mode: `pure_comic`
- Output: Douyin-ready image carousel
- Captions: locally rendered Microsoft YaHei top safe-zone style
- Main image provider: GPT-image in Codex
- Human review gates: outline, script, visual bible, first image, final assets

Validated sample episodes:

- `episodes/gaokao-apple-set-001` — modern warm family comic
- `episodes/five-rings-home-2006-001` — nostalgic 2006 family-rule comic, published

Reusable story pattern:

- `references/story-patterns/nostalgic-family-rule.md`

## Quick Start: Pure Comic

Create a new episode scaffold:

```bash
python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/<episode-id> --title "Story Title" --panel-count 11
```

Optional metadata:

```bash
python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/<episode-id> --title "Story Title" --panel-count 11 --era "2006 China" --theme "family"
```

After outline, script, storyboard, visual bible, prompts, and selected images are approved, package the carousel:

```bash
python skills/story-video-factory/scripts/prepare_pure_comic_episode.py episodes/<episode-id> --caption-style douyin-msyh-top --include-cover --force --force-render --contact-sheet
```

Upload files from:

```text
episodes/<episode-id>/output/publish/carousel/
```

## Workflow

```text
idea
→ outline review
→ script + storyboard review
→ visual bible + prompts review
→ image generation/import
→ selected-candidates.json
→ local caption rendering
→ carousel packaging
→ QC report
→ publishing pack
→ publish + postmortem
```

Large media under `episodes/*/assets/` and `episodes/*/output/` is intentionally ignored by git. Commit reviewable text artifacts, not generated images.

## Skills

| Skill | Purpose |
| --- | --- |
| `story-video-factory` | Director: workflow states, review gates, modes, provider routing |
| `gpt-image-provider` | GPT-image covers, key frames, style anchors, and precision panels in Codex |
| `jimeng-browser-provider` | Jimeng image/video generation via Playwright browser automation |
| `minimax-media-provider` | MiniMax TTS, image-01, and Hailuo video generation via API |
| `comic-video-composer` | FFmpeg composition: Ken Burns, subtitles, audio alignment, QC |
| `douyin-publisher-pack` | Titles, cover text, captions, hashtags, risk review, posting checklist |
| `chuke-storytelling-video` | Chuke / 说书体 long-form episode workflow |

## Structure

```text
story-video-factory/
  skills/
    story-video-factory/        # director + pure-comic scripts
    gpt-image-provider/
    jimeng-browser-provider/
    minimax-media-provider/
    comic-video-composer/
    douyin-publisher-pack/
    chuke-storytelling-video/
  references/
    templates/pure-comic-episode/
    modes/
    caption-styles/
    story-patterns/
  episodes/
    <episode-id>/
```

## Setup

- **GPT-image**: available through Codex built-in image generation; no API key needed for the built-in path.
- **MiniMax**: set `MINIMAX_API_KEY` for TTS/image/video API calls. Bearer auth only; no GroupId required.
- **Jimeng**: install Playwright and log in once with `jimeng_run.py login`; browser session files stay local.
- **Composition**: install `ffmpeg` for comic-to-video workflows.
- **Windows terminals**: run `chcp 65001` before inspecting Chinese script output to avoid GBK mojibake.

## Tests

```bash
python -m pytest tests/smoke_pure_comic_pack.py -q
```

## Repository

GitHub: https://github.com/chuankris/story-video-factory

---

# 中文

面向抖音图文、漫画转视频、后续直出视频的故事生产工厂。

当前 V1 主线是 **先把纯漫画图文跑稳**：先定故事、脚本和视觉方案，再生成静态漫画图，本地加可读中文标题/字幕，打包成抖音图文 carousel，最后发布和复盘。视频、TTS、即梦自动化、MiniMax 都是后续可接入的 provider 链路，不再抢主线。

## 当前重点

- 主模式：`pure_comic`
- 输出：抖音图文 carousel
- 字幕：本地渲染，微软雅黑，顶部安全区
- 主生图：Codex 内置 GPT-image
- 人工审阅关卡：大纲、脚本、视觉圣经、首图、最终资产

已验证样片：

- `episodes/gaokao-apple-set-001`：现代温情家庭漫画
- `episodes/five-rings-home-2006-001`：2006 年代亲情漫画，已发布

已沉淀故事模型：

- `references/story-patterns/nostalgic-family-rule.md`

## 快速开始：纯漫画

创建新 episode：

```bash
python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/<episode-id> --title "故事标题" --panel-count 11
```

可带时代和主题：

```bash
python skills/story-video-factory/scripts/new_pure_comic_episode.py episodes/<episode-id> --title "故事标题" --panel-count 11 --era "2006 China" --theme "亲情"
```

当大纲、脚本、分镜、视觉圣经、提示词和选图都审阅通过后，打包发布图文：

```bash
python skills/story-video-factory/scripts/prepare_pure_comic_episode.py episodes/<episode-id> --caption-style douyin-msyh-top --include-cover --force --force-render --contact-sheet
```

发布目录：

```text
episodes/<episode-id>/output/publish/carousel/
```

## 生产流程

```text
选题
→ 大纲审阅
→ 脚本 + 分镜审阅
→ 视觉圣经 + prompts 审阅
→ 生图 / 手动导入图片
→ selected-candidates.json
→ 本地加字
→ 图文 carousel 打包
→ QC 报告
→ 发布包
→ 发布 + 复盘
```

`episodes/*/assets/` 和 `episodes/*/output/` 下的大图和输出文件默认不进 git。仓库只提交可审阅、可复用的文本资产。

## Skill 列表

| Skill | 职责 |
| --- | --- |
| `story-video-factory` | 导演：生产状态、审阅关卡、模式选择、provider 路由 |
| `gpt-image-provider` | Codex 内置 GPT-image：封面、关键帧、风格锚点、精修图 |
| `jimeng-browser-provider` | 即梦网页自动化跑图/视频，Playwright 操作浏览器 |
| `minimax-media-provider` | MiniMax TTS、image-01、海螺视频 API |
| `comic-video-composer` | FFmpeg 本地合成：运镜、字幕、配音对齐、质检 |
| `douyin-publisher-pack` | 标题、封面文案、简介、标签、风险检查、发布清单 |
| `chuke-storytelling-video` | 初刻 / 说书体长篇故事流程 |

## 项目结构

```text
story-video-factory/
  skills/
    story-video-factory/        # 导演 + 纯漫画脚本
    gpt-image-provider/
    jimeng-browser-provider/
    minimax-media-provider/
    comic-video-composer/
    douyin-publisher-pack/
    chuke-storytelling-video/
  references/
    templates/pure-comic-episode/
    modes/
    caption-styles/
    story-patterns/
  episodes/
    <episode-id>/
```

## 使用前配置

- **GPT-image**：Codex 内置生图可直接用，不需要额外 API key。
- **MiniMax**：设置 `MINIMAX_API_KEY`，用于 TTS、生图、视频 API；Bearer 鉴权，无需 GroupId。
- **即梦**：安装 Playwright，首次用 `jimeng_run.py login` 手动登录；浏览器会话保存在本地，不入库。
- **合成**：漫画转视频时需要本机安装 `ffmpeg`。
- **Windows 终端**：查看中文输出前先 `chcp 65001`，避免 GBK 终端把 UTF-8 中文显示成乱码。

## 测试

```bash
python -m pytest tests/smoke_pure_comic_pack.py -q
```

## 仓库

GitHub: https://github.com/chuankris/story-video-factory
