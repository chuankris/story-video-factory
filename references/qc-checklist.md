# Pure Comic QC Checklist

Status: M0 draft

Use this checklist for every selected production panel.

Each item should be marked `pass`, `fail`, or `n.a.`.

## Per-Panel Checks

Panel metadata:

- Panel id.
- Selected file path.
- Provider.
- Download method.
- Width and height.
- File size.
- Source candidate path.

Image quality:

- Resolution passes production gate.
- File is not a browser preview.
- Image is sharp enough for mobile viewing.
- No obvious compression artifacts.

Story fit:

- Panel matches the intended story beat.
- Main subject/action is readable at mobile size.
- Panel order makes sense in the carousel.

Style consistency:

- Color palette matches style profile.
- Line/texture matches style profile.
- Lighting matches style profile.
- Composition does not feel like a different project.

Character consistency:

- Face/age impression matches character card.
- Hair/costume matches character card.
- Signature object/mark is correct if visible.
- Temperament/posture is consistent.
- No forbidden character change appears.

World consistency:

- Era and setting are consistent.
- No unwanted modern objects.
- Props support the story.

Text and artifacts:

- No watermark or logo.
- No unwanted readable text.
- If generated text appears, user explicitly accepted it or panel is marked for rerun.
- No obvious malformed hands/faces unless acceptable for the style.

Decision:

- Accept to `assets/images/`.
- Rerun with revised prompt.
- Keep as draft only.
- Replace via manual intake.

## QC Report Format

Recommended `output/qc-report.md` section per panel:

```text
## p001

File: assets/images/p001.png
Source: assets/images-raw/p001_001.png
Provider: jimeng
Method: preview_download
Size: 3040x5404, 14.2 MB

Checks:
- resolution: pass
- story fit: pass
- style consistency: pass
- character consistency: fail
- unwanted text: n.a.

Decision: rerun
Reason: face looks like a living bride, not a paper effigy.
Next prompt change: emphasize paper texture, rigid joints, painted facial features.
```

## Carousel-Level Checks

Run these checks after all selected panels pass per-panel QC.

Carousel metadata:

- Episode id.
- Total panel count.
- First image / cover image path.
- Caption source: `script.json`.

Overall sequence:

- First image works as a cover on mobile.
- First image establishes hook or strongest visual promise.
- Panel order is understandable without video narration.
- Captions progress in the same order as images.
- No two adjacent panels feel accidentally duplicated.
- Final panel provides payoff, cliffhanger, or continuation hook.

Platform fit:

- All panels are 9:16 or safely croppable to 9:16.
- Important subject details are visible on a phone screen.
- No required story information depends on tiny in-image text.
- Publishing package has title, description, tags, and comment prompt.

Carousel decision:

- Ready for publishing pack.
- Needs panel reorder.
- Needs caption rewrite.
- Needs one or more panel reruns.
