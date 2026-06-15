# Example: 妈妈把星星缝进我的校服

This is a text-only pure comic example extracted from the M1 trial episode.

It intentionally excludes generated images and publish outputs because large media files are not committed to git.

Use this example to inspect:

- `script.json` as caption source of truth.
- `storyboard.json` panel planning.
- bilingual `prompts-gpt-image.json` with English generation prompts and Chinese review descriptions.
- `selected-candidates.json` as the approved raw-source manifest.

To run this as a real episode, copy the folder to `episodes/star-in-uniform-001/`, provide the referenced raw images under `assets/images-raw/`, then run the pure comic packaging command.
