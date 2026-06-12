# Jimeng Automation Notes

## Selector Update Procedure

When `jimeng_run.py` fails with "not found — update selectors.json":

1. Open `jimeng-errors/<id>_<ts>.png` to see what the page actually looked like.
2. Run `jimeng_run.py login` to get a headed browser; navigate to the generate page.
3. DevTools → inspect the element → derive a stable selector. Prefer text selectors (`button:has-text('生成')`), role/state attributes (`[contenteditable='true'][role='textbox']`), and attribute fragments (`[class*='submit-butt']`) over full hashed class names, which change every deploy. Note the prompt editor is ProseMirror contenteditable — there is no textarea, and text must be typed via keyboard insertion (`set_prompt` in jimeng_run.py handles this).
4. Edit `scripts/selectors.json` (candidates are tried in order — put the new one first, keep old as fallback).
5. Rerun `generate`; completed ids skip automatically.

If Claude in Chrome is available in the session, an alternative to fixing selectors is driving the page interactively with it — useful for one-off runs; Playwright remains better for unattended batches.

## Style Prefix Pattern

Panel consistency on a UI generator comes from the prompt, since there is no seed/reference API. Maintain per-IP a fixed prefix and prepend it to every panel prompt:

```text
中国古典话本连环画风格，明代服饰场景，水墨线条加淡彩，
主角程宰：四十岁男性商人，瘦长脸，山羊胡，灰色长衫。
画面内容：<这一格的具体描述>
竖版 3:4 构图，无文字，无现代元素
```

Rules: character block identical every prompt; only the 画面内容 line varies; state "无文字" or Jimeng draws gibberish captions.

## Etiquette / Risk

- Pace requests like a human (the script sleeps between prompts); run batches in tens, not hundreds.
- Use your own logged-in membership account; do not multi-account or evade rate limits.
- Generated-content review failures are content policy, not bugs — rewrite the prompt.
- The persistent profile dir holds your session cookies. Never commit it; it is gitignored.
