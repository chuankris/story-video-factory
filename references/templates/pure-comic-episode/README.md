# Pure Comic Episode Template

Copy this folder to `episodes/<episode-id>/` when starting a new pure comic episode.

After copying, create these working folders locally:

```text
assets/refs/
assets/images-raw/
assets/images/
assets/audio/
assets/video/
output/publish/
```

Large media under `assets/` and `output/` is intentionally ignored by git. Commit reviewable text files, not provider downloads.

Minimum path for a new episode:

1. Fill `episode-meta.json`.
2. Draft `outline.md` for user review.
3. Draft `script.json` and `storyboard.json` for user review.
4. Draft visual bible files.
5. Generate/import raw images.
6. Record accepted raw images in `selected-candidates.json`.
7. Run `prepare_pure_comic_episode.py`.
