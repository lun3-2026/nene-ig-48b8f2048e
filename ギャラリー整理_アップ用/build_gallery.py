#!/usr/bin/env python3
"""Regenerate gallery.html and index.html from the images/ folder + categories.json.
- images/ folder = source of truth for which images exist.
- categories.json = {filename: category_key} classification.
- Category keys:
    poll   = アンケート（投票結果）
    juku   = Q&A: 塾のこと
    gakko  = Q&A: 学校・受験情報
    benkyo = Q&A: 勉強法・家庭学習
    kokoro = Q&A: 声かけ・メンタル
    sonota = Q&A: その他
    incomplete = 要確認（質問のみ・回答のみ等、削除候補。公開ページには出ない）
- New images not present in categories.json default to "poll".
- Legacy value "other" is treated as "sonota".
Run: python3 build_gallery.py
"""
import os, json, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ROOT, "images")
CATS = os.path.join(ROOT, "categories.json")
IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
DEFAULT_LABEL = "poll"   # new images default to アンケート

QA_KEYS = ["juku", "gakko", "benkyo", "kokoro", "sonota"]
VALID = {"poll", "incomplete", *QA_KEYS}
LEGACY = {"other": "sonota"}

LABELS = {
    "poll": "アンケート",
    "juku": "塾のこと",
    "gakko": "学校・受験情報",
    "benkyo": "勉強法・家庭学習",
    "kokoro": "声かけ・メンタル",
    "sonota": "その他",
    "incomplete": "要確認",
}

def jsstr(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')

# 1) gather image files (NFC), sorted
names = []
for f in os.listdir(IMG):
    if os.path.splitext(f)[1].lower() in IMG_EXT:
        names.append(unicodedata.normalize("NFC", f))
names = sorted(set(names))

# 2) load categories, apply default for new / legacy mapping
cats = {}
if os.path.exists(CATS):
    cats = {unicodedata.normalize("NFC", k): v for k, v in json.load(open(CATS, encoding="utf-8")).items()}
labels = {}
for n in names:
    lab = cats.get(n)
    lab = LEGACY.get(lab, lab)
    if lab not in VALID:
        lab = DEFAULT_LABEL
    labels[n] = lab
# prune categories for images that no longer exist, keep existing decisions
new_cats = {n: labels[n] for n in names}
if new_cats != cats:
    json.dump(new_cats, open(CATS, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)

# 3) build ALL_IMAGES + CAT_BY_IDX + counts
all_lines = []
cat_arr = []
for idx, n in enumerate(names):
    all_lines.append('  {name: "%s", src: "images/" + encodeURIComponent("%s"), idx: %d},'
                     % (jsstr(n), jsstr(n), idx))
    cat_arr.append(labels[n])

counts = {k: 0 for k in VALID}
for n in names:
    counts[labels[n]] += 1
counts["qa"] = sum(counts[k] for k in QA_KEYS)
total = len(names)
public_total = total - counts["incomplete"]

# 4) fill templates
gt = open(os.path.join(ROOT, "gallery.template.html"), encoding="utf-8").read()
gt = gt.replace("__ALL_IMAGES__", "\n".join(all_lines))
gt = gt.replace("__CAT_BY_IDX__", json.dumps(cat_arr, separators=(",", ":")))
gt = gt.replace("__COUNTS__", json.dumps(counts, separators=(",", ":")))
open(os.path.join(ROOT, "gallery.html"), "w", encoding="utf-8").write(gt)

it = open(os.path.join(ROOT, "index.template.html"), encoding="utf-8").read()
it = it.replace("__POLL__", f"{counts['poll']:,}")
it = it.replace("__QA__", f"{counts['qa']:,}")
it = it.replace("__TOTAL__", f"{public_total:,}")
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(it)

print(f"built: total={total} public={public_total} " +
      " ".join(f"{k}={counts[k]}" for k in ["poll", "qa"] + QA_KEYS + ["incomplete"]))
