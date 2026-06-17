# Postmortem: 响五声就好

Episode id: `five-rings-home-2006-001`  
Mode: `pure_comic`  
Status: published  
Published: 2026-06-17, exact platform metrics pending  
Primary provider: GPT-image  
Caption style: `douyin-msyh-top`

## Summary

This episode validates a second production-ready pure-comic lane: nostalgic family realism. The story uses a concrete rule from an older communication era: every Friday at 7 PM, the son calls home and lets the phone ring five times to report safety without spending long-distance fees. The emotional release comes when the sixth ring happens and the mother answers immediately.

The strongest reusable insight is that the story does not need a big event. A small rule, repeated over time, becomes a ritual; breaking the ritual creates the climax.

## Story Pattern

Formula:

```text
Era constraint + family money constraint + private rule + repeated ritual + one broken rule + quiet final line
```

For this episode:

```text
2006 long-distance fees + poor college family + five rings mean safe + mother counts every Friday + sixth ring + "妈今天不数铃"
```

Why it works:

- The hook is counterintuitive: "my mother never answered my calls".
- The rule is easy to remember: "five rings".
- The setting is specific enough to feel real: phone card, landline, campus phone booth.
- The ending is not loud; it gives the audience room to feel.

## Visual Lessons

Keep:

- Warm home light versus cold campus/night light.
- Old landline, phone card, coins, thermos, enamel cup, wall calendar, vegetables.
- Mother as a real 45-50 year old county-town parent, not a pretty young woman.
- Soft semi-realistic painterly comic linework with paper texture.
- Top caption safe-zone with Microsoft YaHei and muted red/blue highlights.

Avoid:

- Making the mother too young or fashion-model-like.
- Overloading montage panels so captions compete with visual detail.
- Letting the image model generate readable Chinese story text.
- Modern objects: smartphones, QR codes, LED screens, current campus signage.

## Workflow Lessons

What worked:

- Review-first flow: outline, script, visual bible, then image generation.
- First generating cover and p001-p002 before committing to the full batch.
- Using user visual feedback to refine the mother age before generating the rest.
- Post-rendered captions kept text readable and avoided Douyin bottom UI.

What to improve:

- The cover needed a manual `1080x1920` normalization step. Future cover handling should be automated or integrated into `build_publish_carousel.py`.
- `selected-candidates.json` can reference cover and panels, but post-production currently only reads panel selections for rendering. Future scripts should treat cover as a first-class selected asset.
- A dedicated review checklist for "mother/father age realism" would prevent the first-cover issue from recurring.

## Reusable Prompt Notes

For nostalgic parent stories, include these constraints early in the prompt:

```text
clearly middle-aged 45-50 year old Chinese mother/father, ordinary county-town parent, worn hands, practical clothes, tired gentle eyes, not glamorous, not a young fashion model
```

For 2000s China era control, include:

```text
old landline telephone, phone card, coins, thermos, enamel cup, wall calendar, no smartphones, no QR codes, no modern LED screens, no contemporary branding
```

## Next Iterations

Good follow-up story families:

- Father delivery story: a father never enters the university gate.
- Teacher memory story: a teacher's ordinary sentence becomes meaningful years later.
- Another object-rule story: bus card, meal ticket, prepaid phone card, radio, old umbrella.

## Metrics To Fill Later

- Published URL:
- Publish time:
- First-hour views:
- First-hour likes:
- First-hour comments:
- Completion / swipe-through signal:
- Best audience comment:
- What to change next time:
