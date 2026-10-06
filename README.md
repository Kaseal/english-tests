# Angielski – próbne testy, klasa 8

A static practice-test page for the Polish 8th-grade English exam. Each round has 29 random
questions, a 30-minute timer, and a scored review of wrong answers. Explanations, rules and
translations in the review are in Ukrainian.

## Layout

```
pdf/                    original past tests (2019–2025)
data/questions/*.json   question bank (originals: *-orig.json, generated: *-gen*.json)
index.html              the page: markup, CSS and JS (open it directly or via GitHub Pages)
questions.js            generated question data loaded by index.html (commit it)
build.py                validates the bank and writes questions.js
```

## Rebuild

```
python build.py
```

Standard library only. The script stops with a list of errors if a question is malformed
(not exactly 4 options, bad `correct` indices, missing Ukrainian fields, duplicate ids, unknown
category). It prints warnings for likely duplicate questions and for explanations that disagree
with the answer key.

## Question format

```json
{
  "id": "cond-g001",                  // unique
  "source": "wiosna-2024 #3" | "generated",
  "category": "conditionals",         // one of CATEGORIES in build.py
  "prompt": "Uzupełnij lukę.",        // Polish instruction
  "text": "If you heat ice, it ___",  // English content, may be ""
  "options": ["melts.", "will melted.", "would melt.", "melted."],
  "correct": [0],                     // 1–4 indices into options
  "translation_uk": "...",
  "rule": { "name": "Zero Conditional (0-й тип)", "text_uk": "..." },
  "explanations_uk": ["Правильно: ...", "...", "...", "..."]   // one per option
}
```

Explanations of correct options start with "Правильно" (or "Також правильно"). The build checks
this so the explanations stay consistent with `correct`.

## Test composition

`CATEGORIES` in `build.py` sets how many of the 29 questions come from each category. Options are
shuffled every round. A question counts as correct only when exactly the right set of options is
ticked. Score colours: ≤50% red, 51–84% yellow, ≥85% green.

Add `?min=1` to the URL to shorten the timer to 1 minute (handy for testing).

## Publish on GitHub Pages

Commit the repository (including the generated `questions.js`), then go to **Settings → Pages →
Deploy from a branch** and choose `main` with the `/ (root)` folder.
