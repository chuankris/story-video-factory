# Story Video Factory

English | [中文](#中文)

A Codex director skill for reviewed story-to-video production workflows targeting Douyin and similar short-video platforms.

This skill coordinates the big picture: topic selection, outline review, script review, storyboard, prompt planning, provider routing, asset intake, composition, quality checks, and publishing packs.

It is designed to work with smaller specialized skills, such as a style skill for `初刻拍案惊奇`, a comic-video composer, Minimax media provider, Jimeng browser provider, and Douyin publishing pack.

## What It Does

- Manages production state and review gates.
- Chooses between comic-video, image-comic, AI-video, and hybrid modes.
- Routes tasks to available providers or future sub-skills.
- Keeps provider-specific details out of the central workflow.
- Prevents premature composition before assets are ready.
- Supports parallel work while another episode is rendering or waiting on image generation.

## Skill Structure

```text
story-video-factory/
  SKILL.md
  agents/
    openai.yaml
  references/
    output-spec.md
    provider-routing.md
    skill-map.md
    workflow.md
```

## Installation

Clone or copy this folder into your Codex skills directory:

```bash
git clone https://github.com/chuankris/story-video-factory.git ~/.codex/skills/story-video-factory
```

On Windows, copy or clone it under:

```text
%USERPROFILE%\.codex\skills\story-video-factory
```

## Recommended Architecture

Use this as the big director skill:

- `story-video-factory`: workflow, state, modes, provider routing.
- `chuke-storytelling-video`: 初刻拍案惊奇 / classical storyteller style.
- `comic-video-composer`: image-to-video composition.
- `minimax-media-provider`: Minimax TTS and video generation.
- `jimeng-browser-provider`: browser-assisted Jimeng image generation.
- `douyin-publisher-pack`: title, cover, caption, tags, and publishing checklist.

## Repository

GitHub: https://github.com/chuankris/story-video-factory

---

# 中文

[English](#story-video-factory) | 中文

这是一个面向抖音等短视频平台的 Codex 总控 skill，用来管理“故事到视频”的完整生产流程。

它不负责某一种具体文风或某一个供应商细节，而是负责大流程：选题、梗概审阅、脚本审阅、分镜、提示词规划、供应商路由、素材接收、合成、质检和发布包。

它适合和多个小 skill 配合使用，例如 `初刻拍案惊奇` 风格 skill、漫画转视频合成 skill、Minimax 媒体供应商 skill、即梦浏览器自动化 skill、抖音发布包 skill。

## 能做什么

- 管理生产状态和审阅关卡。
- 在漫画视频、图文漫画、AI 视频、混合视频之间选择模式。
- 根据现有工具和额度路由任务。
- 把供应商细节拆到小 skill，避免总控 skill 变臃肿。
- 防止在素材未完成时提前进入合成。
- 在某一集渲染或跑图等待时，并行推进下一集的审阅工作。

## Skill 结构

```text
story-video-factory/
  SKILL.md
  agents/
    openai.yaml
  references/
    output-spec.md
    provider-routing.md
    skill-map.md
    workflow.md
```

## 安装

把本仓库 clone 或复制到 Codex skills 目录：

```bash
git clone https://github.com/chuankris/story-video-factory.git ~/.codex/skills/story-video-factory
```

Windows 下通常放到：

```text
%USERPROFILE%\.codex\skills\story-video-factory
```

## 推荐架构

把它作为大的导演 skill：

- `story-video-factory`：流程、状态、模式、供应商路由。
- `chuke-storytelling-video`：初刻拍案惊奇 / 古典说书体风格。
- `comic-video-composer`：漫画图转视频合成。
- `minimax-media-provider`：Minimax TTS 和视频生成。
- `jimeng-browser-provider`：即梦浏览器辅助跑图。
- `douyin-publisher-pack`：标题、封面、简介、标签和发布检查。

## 仓库

GitHub: https://github.com/chuankris/story-video-factory
