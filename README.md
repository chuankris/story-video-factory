# Story Video Factory

English | [中文](#中文)

A skill pack (superpowers-style plugin) for reviewed story-to-video production targeting Douyin and similar short-video platforms.

One director skill coordinates the pipeline; small specialized skills handle style, providers, composition, and publishing.

## Skills

| Skill | Purpose |
| --- | --- |
| `story-video-factory` | Director: workflow states, review gates, modes, provider routing |
| `chuke-storytelling-video` | 初刻拍案惊奇 / 说书体 narration, 上中下集 episode workflow |
| `jimeng-browser-provider` | Jimeng image generation via Playwright (no API exists) |
| `minimax-media-provider` | MiniMax TTS + Hailuo video generation via API |
| `gpt-image-provider` | GPT-image refs/key frames — **Codex environment only** |
| `comic-video-composer` | FFmpeg composition: Ken Burns, subtitles, audio align, QC |
| `douyin-publisher-pack` | Titles, cover text, captions, hashtags, risk review, checklist |

## Structure

```text
story-video-factory/
  .claude-plugin/
    plugin.json
    marketplace.json
  skills/
    story-video-factory/        # director
    chuke-storytelling-video/
    comic-video-composer/
    minimax-media-provider/
    jimeng-browser-provider/
    gpt-image-provider/
    douyin-publisher-pack/
```

Each skill is a folder with `SKILL.md` plus optional `scripts/` and `references/`.

## Installation (Claude Code)

```text
/plugin marketplace add chuankris/story-video-factory
/plugin install story-video-factory@story-video-factory
```

## Setup

- **MiniMax**: set `MINIMAX_API_KEY` and `MINIMAX_GROUP_ID` env vars.
- **Jimeng**: `pip install playwright && playwright install chromium`, then `python skills/jimeng-browser-provider/scripts/jimeng_run.py login` and log in manually once.
- **Composition**: `ffmpeg` on PATH.

## Pipeline

story source → outline → script (说书体) → storyboard → prompts → images (Jimeng/GPT-image) + TTS (MiniMax) [+ video shots (Hailuo)] → compose (FFmpeg) → QC → publishing pack. Every creative artifact passes human review before the next stage.

## Repository

GitHub: https://github.com/chuankris/story-video-factory

---

# 中文

面向抖音等短视频平台的「故事转视频」skill 包（仿 superpowers 的插件结构）：一个导演 skill 管大流程，多个小 skill 各管一摊。

## Skill 列表

| Skill | 职责 |
| --- | --- |
| `story-video-factory` | 导演：生产状态、审阅关卡、模式选择、供应商路由 |
| `chuke-storytelling-video` | 初刻拍案惊奇 / 说书体文案，上中下集审阅流程 |
| `jimeng-browser-provider` | 即梦无 API，用 Playwright 操作网页批量跑图、下载 |
| `minimax-media-provider` | MiniMax 语音合成 + 海螺视频生成（API，需 key） |
| `gpt-image-provider` | GPT-image 角色参考图/关键帧 —— **仅 Codex 环境可用** |
| `comic-video-composer` | FFmpeg 本地合成：运镜、字幕、配音对齐、质检 |
| `douyin-publisher-pack` | 标题、封面文案、简介、标签、风险检查、发布清单 |

## 安装（Claude Code）

```text
/plugin marketplace add chuankris/story-video-factory
/plugin install story-video-factory@story-video-factory
```

## 使用前配置

- **MiniMax**：设置环境变量 `MINIMAX_API_KEY`、`MINIMAX_GROUP_ID`。
- **即梦**：`pip install playwright && playwright install chromium`，首次运行 `jimeng_run.py login` 手动登录一次（会话保存在本地，不入库）。
- **合成**：本机装好 `ffmpeg`。

## 生产链路

选题 → 梗概 → 说书体脚本 → 分镜 → 提示词 → 跑图（即梦/GPT-image）+ 配音（MiniMax）[+ 高光动镜（海螺）] → 本地合成 → 质检 → 发布包。每个创作环节都先过人工审阅再进下一步。

## 仓库

GitHub: https://github.com/chuankris/story-video-factory
