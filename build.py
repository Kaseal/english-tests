"""Validate the question bank in data/questions/*.json and build questions.js.

Usage:  python build.py
Only the Python standard library is used.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
DATA_DIR = ROOT / "data" / "questions"
OUT = ROOT / "questions.js"   # loaded by index.html

QUESTIONS_PER_TEST = 29
TEST_MINUTES = 30

# category -> (Polish label, slots in one test). Slots must sum to QUESTIONS_PER_TEST.
CATEGORIES = {
    "tenses":               ("Czasy gramatyczne", 5),
    "conditionals":         ("Okresy warunkowe", 2),
    "passive":              ("Strona bierna", 2),
    "modals":               ("Czasowniki modalne", 2),
    "reported":             ("Mowa zależna", 1),
    "relative":             ("Zaimki względne", 1),
    "verb_patterns":        ("Gerund / bezokolicznik / used to", 2),
    "articles_quantifiers": ("Przedimki i określniki ilości", 2),
    "grammar_misc":         ("Zaimki, przyimki, stopniowanie, spójniki", 3),
    "phrasal_idioms":       ("Czasowniki frazowe i idiomy", 3),
    "vocabulary":           ("Słownictwo", 4),
    "communication":        ("Funkcje językowe", 2),
}

REQUIRED = ["id", "source", "category", "prompt", "text", "options", "correct",
            "translation_uk", "rule", "explanations_uk"]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def validate(questions):
    errors, warnings = [], []
    seen_ids, seen_keys = {}, {}
    for q in questions:
        where = f"{q.get('_file')}:{q.get('id', '?')}"
        for k in REQUIRED:
            if k not in q:
                errors.append(f"{where}: missing field '{k}'")
        if any(k not in q for k in REQUIRED):
            continue
        if q["id"] in seen_ids:
            errors.append(f"{where}: duplicate id (also in {seen_ids[q['id']]})")
        seen_ids[q["id"]] = q["_file"]
        if q["category"] not in CATEGORIES:
            errors.append(f"{where}: unknown category '{q['category']}'")
        opts = q["options"]
        if len(opts) != 4 or any(not isinstance(o, str) or not o.strip() for o in opts):
            errors.append(f"{where}: needs exactly 4 non-empty options")
        if len({o.strip().lower() for o in opts}) != len(opts):
            errors.append(f"{where}: duplicate options")
        corr = q["correct"]
        if (not isinstance(corr, list) or not 1 <= len(corr) <= 4
                or len(set(corr)) != len(corr)
                or any(not isinstance(i, int) or not 0 <= i < len(opts) for i in corr)):
            errors.append(f"{where}: bad 'correct' {corr}")
        if len(q["explanations_uk"]) != len(opts) or any(not e.strip() for e in q["explanations_uk"]):
            errors.append(f"{where}: needs one non-empty explanation per option")
        elif isinstance(corr, list):
            # Explanations of correct options start with "Правильно" / "Також правильно";
            # a mismatch usually means the answer key and the explanations disagree.
            for i, e in enumerate(q["explanations_uk"]):
                says_ok = e.strip().startswith(("Правильно", "Також правильно"))
                if says_ok != (i in corr):
                    warnings.append(f"{where}: option {i} explanation does not match the answer key")
        if not q["prompt"].strip() or not q["translation_uk"].strip():
            errors.append(f"{where}: empty prompt or translation_uk")
        r = q["rule"]
        if not isinstance(r, dict) or not r.get("name", "").strip() or not r.get("text_uk", "").strip():
            errors.append(f"{where}: rule needs 'name' and 'text_uk'")
        key = norm(q["prompt"] + " " + q["text"]) + "|" + "|".join(sorted(norm(o) for o in opts))
        if key in seen_keys:
            warnings.append(f"{where}: looks like a duplicate of {seen_keys[key]}")
        seen_keys[key] = where
    return errors, warnings


def main():
    questions = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"{path.name}: invalid JSON: {e}")
        for q in items:
            q["_file"] = path.name
        questions.extend(items)

    errors, warnings = validate(questions)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    if errors:
        sys.exit(f"\n{len(errors)} error(s); questions.js not written.")

    slots = sum(n for _, n in CATEGORIES.values())
    assert slots == QUESTIONS_PER_TEST, f"category slots sum to {slots}"

    print(f"{'category':22} {'total':>6} {'multi':>6} {'orig':>6}")
    for cat, (_, n) in CATEGORIES.items():
        qs = [q for q in questions if q["category"] == cat]
        multi = sum(len(q["correct"]) > 1 for q in qs)
        orig = sum(q["source"] != "generated" for q in qs)
        flag = "  <-- fewer than slots" if len(qs) < n else ""
        print(f"{cat:22} {len(qs):6} {multi:6} {orig:6}{flag}")
    print(f"{'TOTAL':22} {len(questions):6} "
          f"{sum(len(q['correct']) > 1 for q in questions):6} "
          f"{sum(q['source'] != 'generated' for q in questions):6}")

    data = {
        "perTest": QUESTIONS_PER_TEST,
        "minutes": TEST_MINUTES,
        "categories": {c: {"label": l, "slots": n} for c, (l, n) in CATEGORIES.items()},
        "questions": [{k: q[k] for k in REQUIRED} for q in questions],
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(f"window.QUESTION_DATA = {payload};\n", encoding="utf-8")
    print(f"\nWrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
