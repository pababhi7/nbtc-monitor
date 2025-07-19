#!/usr/bin/env python3
"""
Daily incremental scraper for MoCheck.
Persists:
  - .last_id   → where to resume next day
  - known.json → already-seen device names
Scans up to 500 new IDs per run, stops on "Whoops".
"""
import os, sys, json, requests, re
from bs4 import BeautifulSoup

BASE_URL   = "https://mocheck.nbtc.go.th/search-equipments/{}"
LAST_FILE  = ".last_id"
KNOWN_FILE = "known.json"
BOT_TOKEN  = os.getenv("BOT_TOKEN")
CHAT_ID    = os.getenv("CHAT_ID")

HEADERS = {"User-Agent": "MoCheck-Scraper/1.0"}

# ---------- helpers ----------
def load_int(path: str, default: int) -> int:
    try:
        with open(path) as f:
            return int(f.read().strip())
    except Exception:
        return default

def save_int(path: str, value: int):
    with open(path, "w") as f:
        f.write(str(value))

def load_known() -> set[str]:
    try:
        return set(json.load(open(KNOWN_FILE)))
    except Exception:
        return set()

def save_known(names: set[str]):
    json.dump(sorted(names), open(KNOWN_FILE, "w"), ensure_ascii=False, indent=2)

def get_device_name(eq_id: int) -> str | None:
    r = requests.get(BASE_URL.format(eq_id), headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return None
    if "Whoops, looks like something went wrong." in r.text:
        print("End-of-data marker found – stopping.")
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in ["h2", "h3"]:
        h = soup.find(tag)
        if h and re.search(r'[ก-๙]', h.get_text(strip=True)):
            return h.get_text(strip=True)
    return None

# ---------- main ----------
current = load_int(LAST_FILE, 1628277)
known   = load_known()
new_devices = []

MAX_PAGES = 500        # scan up to 500 pages per run
for offset in range(MAX_PAGES):
    eq_id = current + offset
    name = get_device_name(eq_id)
    if name is None:          # 404 or "Whoops"
        current = eq_id       # remember stopping point
        break
    if name not in known:
        new_devices.append(name)
        known.add(name)
    current = eq_id + 1       # advance

# persist state
save_int(LAST_FILE, current)
save_known(known)

if new_devices:
    first = new_devices[0]
    with open("new_device.txt", "w", encoding="utf-8") as f:
        f.write(first)
    if BOT_TOKEN and CHAT_ID:
        import telegram
        telegram.Bot(BOT_TOKEN).send_message(CHAT_ID, f"🔍 MoCheck: อุปกรณ์ใหม่\n{first}")
    sys.exit(77)  # GitHub flag: new device found
else:
    print("No new devices.")
    sys.exit(0)
  
