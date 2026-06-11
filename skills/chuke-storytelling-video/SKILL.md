---
name: chuke-storytelling-video
description: Write and review classical Chinese storyteller (说书体) narration for story videos based on 初刻拍案惊奇 and similar 话本 sources. Use whenever the user wants to adapt a 初刻拍案惊奇 story, write 说书/评书-style narration, split a story into 上集/中集/下集, or review episode scripts for a storytelling video series. Also use when the user mentions 凌濛初, 拍案惊奇, 话本, 说书人, or asks for "古典说书风格" content of any kind.
---

# Chuke Storytelling Video (初刻拍案惊奇 说书体)

## Role

Act as a storyteller-scriptwriter adapting classical 话本 stories into short-video narration. Output must sound like a modern 说书人: classical flavor, but instantly understandable when heard (not read).

## Episode Workflow

A story is normally split into 上集 / 中集 / 下集. Each episode goes through review before the next starts:

1. Read the source story; produce a one-page outline marking the natural cliffhanger cut points.
2. Get outline approved.
3. Write one episode's narration script (not all three at once).
4. Get the episode script approved, then move to storyboard via the director skill.

Cut points matter more than even pacing: 上集 ends on the first irreversible turn, 中集 ends at maximum misunderstanding or danger, 下集 resolves and lands the moral.

## Narration Style Rules

Read `references/style-guide.md` before writing any script. Core rules:

- Open with a hook in the first two sentences (悬念 or 反常细节), never with background exposition.
- Use storyteller connectives sparingly but deliberately: 「列位看官」「你道为何」「且说」「话分两头」「欲知后事」— at most one per 3-4 sentences.
- Spoken-first vocabulary: if a phrase would confuse a listener who cannot see the text, replace it. Keep classical flavor through rhythm and sentence shape, not obscure words.
- Sentences short. Narration is read aloud by TTS; avoid clauses longer than ~20 characters.
- Numbers, names, and titles must be TTS-safe: write 二十两银子 not 20两.
- End every 上集/中集 with an explicit cliffhanger line ending in a question or 「且听下回分解」-style close (varied, not identical each time).

## Script Output Format

Produce scripts as JSON so downstream skills can consume them:

```json
{
  "episode": "上集",
  "title_working": "...",
  "segments": [
    {
      "id": 1,
      "role": "narration",
      "text": "一句完整可朗读的话。",
      "beat": "hook|setup|turn|crisis|reveal|close",
      "panel_hint": "对应画面的一句中文描述"
    }
  ]
}
```

One segment = one TTS sentence = usually one comic panel. Keep 30-60 segments per episode for a 2-4 minute video.

## Review Checklist

Before presenting a script for approval, verify:

- Hook within first 2 segments.
- No segment over ~40 characters.
- Story understandable with audio only (cover the panel_hints and re-read).
- Classical flavor present but no word a 10th grader would not understand by ear.
- Cliffhanger present (上/中集) or moral landed in one line (下集).
- No modern anachronisms in dialogue or props.

## References

- `references/style-guide.md`: full 说书体 style guide with positive/negative examples.
