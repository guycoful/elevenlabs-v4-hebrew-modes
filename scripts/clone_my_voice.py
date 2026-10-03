#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clone_my_voice.py: יוצר קול משלכם ב-ElevenLabs מהקלטה קצרה שלכם, ומדפיס voice_id.

  python3 clone_my_voice.py --name "הקול שלי" --sample my_voice.mp3 --i-confirm-this-is-my-own-voice

חובה: ההקלטה היא של מי שמריץ את הסקריפט, או של אדם שנתן אישור כתוב לשכפול הקול שלו.
הקלטה נקייה: חדר שקט, בלי מוזיקה ובלי רעש, כמה דקות של דיבור רגיל.
יצירת קול תופסת מקום בחשבון (voice slot) ולפעמים נספרת כפעולת עריכה. אין כאן הקראה, ולכן אין עלות קרדיטים של טקסט.
המפתח נקרא ממשתנה הסביבה ELEVENLABS_API_KEY.
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

API = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io/v1")


def multipart(fields, files):
    b = uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, path in files:
        ct = mimetypes.guess_type(path)[0] or "application/octet-stream"
        head = f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{os.path.basename(path)}"\r\nContent-Type: {ct}\r\n\r\n'
        out += [head.encode(), open(path, "rb").read(), b"\r\n"]
    out.append(f"--{b}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={b}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--sample", required=True, nargs="+")
    ap.add_argument("--i-confirm-this-is-my-own-voice", action="store_true")
    a = ap.parse_args()
    if not a.i_confirm_this_is_my_own_voice:
        sys.exit("עצרתי. הוסיפו --i-confirm-this-is-my-own-voice רק אם ההקלטה היא הקול שלכם, או שיש לכם אישור כתוב מבעל הקול.")
    for p in a.sample:
        if not os.path.isfile(p):
            sys.exit(f"הקובץ לא נמצא: {p}")
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("חסר ELEVENLABS_API_KEY במשתנה סביבה.")
    body, ct = multipart({"name": a.name}, [("files", p) for p in a.sample])
    req = urllib.request.Request(f"{API}/voices/add", data=body, headers={"xi-api-key": key, "Content-Type": ct})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"שגיאה {e.code} מ-ElevenLabs: {e.read().decode('utf-8', 'replace')[:300]}")
    print("voice_id:", r.get("voice_id"))
    print("עכשיו אפשר: python3 speak.py --mode warm_calm --text 'שלום' --voice", r.get("voice_id"))


if __name__ == "__main__":
    main()
