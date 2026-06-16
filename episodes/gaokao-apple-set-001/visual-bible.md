# Visual Bible

## Approved Direction For Review

Working direction: `handwritten_douyin_story` with mixed panels.

This episode should feel like a warm gaokao diary comic, not a cinematic illustrated film. The visual language should be closer to native Douyin handwritten story posts: big readable handwritten Chinese text, colored brush emphasis, paper texture, and mixed panel layouts.

## Layout Rule

Use multiple panel types across the episode:

- `single_scene` for emotional anchors.
- `two_panel` for contrast.
- `three_panel` for small emotional turns.
- `four_panel` for action sequence.
- `detail_collage` for objects and proof.
- `mobile_safe_cover` for the cover image.

## Text Policy

Do not ask the image model to render final Chinese story text. The model should leave upper or left blank zones. Final text is added locally.

Important mobile-safe rules:

- No critical text in bottom 22%.
- Avoid right 18% for faces/key props because of Douyin buttons.
- Top text should sit below status bar area.
- Cover image must be readable under real phone UI.

## Story Tone

Warm, realistic, and tender. Do not shame students who have expensive devices. Do not frame the mother as tragic. The emotional point is quiet support, not poverty spectacle.

## Provider Plan

- GPT-image for cover and panels in this M2 test.
- English prompt for generation.
- Chinese prompt_zh for review.
- Selected raw sources must be recorded in `selected-candidates.json` before final rendering.
