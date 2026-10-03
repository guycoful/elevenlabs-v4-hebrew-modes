#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""speak.py: הקראה בעברית עם ElevenLabs v4 ומצב דיבור.

דוגמאות:
  python3 speak.py --list-modes
  python3 speak.py --list-voices
  python3 speak.py --mode whisper --text "זה סוד" --voice VOICE_ID --out out.mp3
  python3 speak.py --mode whisper --text "זה סוד" --dry-run     (בלי רשת, בלי קרדיטים)

המפתח נקרא ממשתנה הסביבה ELEVENLABS_API_KEY. כל הקראה אמיתית עולה קרדיטים בחשבון שלכם.
מצב "-" מקריא בלי תגית, ומצב שכתוב בסוגריים מרובעים נשלח כמו שהוא, למשל "[whispers]".
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MODES = os.path.join(HERE, "..", "reference", "modes.json")
API = "https://api.elevenlabs.io/v1"
SOFT_LIMIT = 1500   # מעל זה מומלץ לפצל, כדי שקטע לא ייחתך או יאבד סגנון


def load_modes():
    d = json.load(open(MODES, encoding="utf-8"))
    return {**d["modes"], **d["sound_events"]}


def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        sys.exit("חסר ELEVENLABS_API_KEY. הגדירו אותו במשתנה סביבה, לא בקובץ שנשמר בריפו.")
    return k


def call(req):
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"שגיאה {e.code} מ-ElevenLabs: {e.read().decode('utf-8', 'replace')[:300]}")


def build_text(mode, text, modes):
    if mode == "-":
        return text
    if mode.startswith("["):
        return mode + " " + text
    if mode not in modes:
        sys.exit(f"מצב לא מוכר: {mode}. הריצו --list-modes")
    return modes[mode]["tag"] + " " + text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", default="-")
    ap.add_argument("--text")
    ap.add_argument("--voice")
    ap.add_argument("--out", default="out.mp3")
    ap.add_argument("--model", default=os.environ.get("ELEVENLABS_MODEL", "eleven_v4"))
    ap.add_argument("--stability", type=float, default=0.5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-modes", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()
    modes = load_modes()

    if a.list_modes:
        for k, v in modes.items():
            print(f"{k:20} {v['tag']:42} {v['he']}")
        return
    if a.list_voices:
        req = urllib.request.Request(f"{API}/voices", headers={"xi-api-key": key()})
        for v in json.loads(call(req))["voices"]:
            print(v["voice_id"], v["name"], "|", v.get("category", ""))
        return
    if not a.text:
        ap.error("חסר --text")
    body = {
        "text": build_text(a.mode, a.text, modes),
        "model_id": a.model,
        "voice_settings": {"stability": a.stability, "similarity_boost": 0.75},
    }
    if len(a.text) > SOFT_LIMIT:
        print(f"אזהרה: {len(a.text)} תווים. מומלץ לפצל לקטעים קצרים יותר.", file=sys.stderr)
    if a.dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=1))
        return
    if not a.voice:
        ap.error("חסר --voice. הריצו --list-voices ובחרו קול שלכם או קול שמותר לכם להשתמש בו")
    req = urllib.request.Request(
        f"{API}/text-to-speech/{a.voice}?output_format=mp3_44100_128",
        data=json.dumps(body).encode(),
        headers={"xi-api-key": key(), "Content-Type": "application/json"},
    )
    open(a.out, "wb").write(call(req))
    print("נשמר:", a.out)


if __name__ == "__main__":
    main()
