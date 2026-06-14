# Prompt Assembly Spec

Status: M0 draft

## Purpose

Define how pure comic panel prompts are assembled from story, style, character, and provider constraints.

## Canonical Input Blocks

Each final provider prompt is assembled from these blocks:

1. `panel_intent`: what this panel must accomplish in the story.
2. `scene_action`: visible scene, subject action, and emotional beat.
3. `character_block`: relevant character card details.
4. `style_block`: selected style profile.
5. `composition_block`: camera angle, framing, subject placement, depth.
6. `world_rules`: era, location, objects, and continuity constraints.
7. `text_policy`: whether readable text is allowed.
8. `provider_suffix`: provider-specific quality and format instructions.

## Recommended Order

Use this order for Jimeng and GPT-image prompts:

```text
[Panel intent, one sentence]
[Scene/action, concrete visual nouns and verbs]
[Character block, only characters visible in this panel]
[Style block, compressed but specific]
[Composition and lighting]
[World/era constraints]
[Text policy]
[Provider suffix]
```

Put the most important scene and character details first. Do not bury the subject after a long style paragraph.

## Negative Rules

For providers without a separate negative prompt field, rewrite negative rules as natural language constraints.

Instead of:

```text
negative: modern objects, watermark, logo
```

Use:

```text
The scene contains no phones, cars, plastic objects, neon signs, English letters, watermarks, or logos.
```

## Length Budget

V1 should keep each Jimeng prompt concise enough for browser input reliability.

Recommended target:

- 120-220 Chinese characters for simple panels.
- 220-420 Chinese characters for complex panels.
- Avoid long global style blocks repeated verbatim if they drown out the panel action.

If a prompt is too long, preserve in this order:

1. Panel action.
2. Visible character traits.
3. Style/color/lighting.
4. Era and forbidden objects.
5. Secondary texture details.

## Example

Style summary:

```text
Minguo supernatural suspense comic, semi-realistic Chinese comic linework, cold blue rainy shadows and warm red candlelight, cinematic vertical framing, old wood and paper textures, restrained horror, no gore.
```

Character card:

```text
Paper bride: young woman-shaped paper effigy, pale paper-like face, red bridal veil, embroidered red wedding robe, rigid posture, delicate painted brows, small vermilion lips, not a living human.
```

Panel intent:

```text
Show the first reveal of the ghost marriage hall and the bride beside the coffin.
```

Final Jimeng prompt:

```text
民国旧宅冥婚喜堂，雨夜，画面表现纸新娘第一次出场。纸扎新娘坐在黑色棺材旁，红盖头半遮，苍白纸脸，彩绘细眉，朱砂小口，红色绣花嫁衣，姿态僵硬不像活人。红烛照亮棺木和白纸钱，门外冷蓝雨光渗入室内。国风悬疑漫画，半写实电影感，冷蓝阴影与暖红烛光强对比，竖版9:16，高细节。画面无水印、无logo、无现代物品；不要生成可读文字。
```

## Prompt Output Schema

Prompt entries should use stable panel IDs. Provider runners should receive provider-specific prompt files in V1:

- `prompts-jimeng.json`
- `prompts-gpt-image.json`

The shared `prompts.json` can be used for planning, but do not feed a mixed-provider file to a runner that does not filter by `provider`.

```json
[
  {
    "id": "p001",
    "panel_intent": "opening hook",
    "prompt": "...final provider prompt...",
    "provider": "jimeng",
    "count": 1,
    "reference_image": null,
    "image_to_image": false
  }
]
```

## Provider Suffix Examples

Jimeng suffix:

```text
竖版9:16，高细节，适合手机竖屏观看。画面无水印、无logo、无现代物品；不要生成可读文字。
```

GPT-image suffix:

```text
Create a vertical 9:16 comic illustration with coherent character design, clear mobile-readable composition, high detail, and no logo or watermark. Avoid readable text inside the image unless explicitly requested.
```
