#!/usr/bin/env python3
import os, json, datetime, sys, requests
from bs4 import BeautifulSoup

URL_TEMPLATE = "https://mocheck.nbtc.go.th/search-equipments/{id}"
STATE_FILE   = "state.json"
BLANK_LIMIT  = 300
TARGET_TYPE  = "Cellular Mobile (GSM/WCDMA/LTE/NR)"

def load_state():
    try:
        return json.load(open(STATE_FILE))["last_id"]
    except Exception:
        return int(os.getenv("START_ID", "1628277"))

def save_state(last_id):
    json.dump({"last_id": last_id}, open(STATE_FILE, "w"), indent=2)

def fetch(id_):
    try:
        r = requests.get(URL_TEMPLATE.format(id=id_), timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table.table tbody tr")
        if not rows:
            return None
        ttype = rows[0].find_all("td")[0].get_text(strip=True)
        if ttype != TARGET_TYPE:
            return None
        return {
            "id": id_,
            "brand": rows[0].find_all("td")[1].get_text(strip=True),
            "model": rows[0].find_all("td")[2].get_text(strip=True),
            "cert":  rows[0].find_all("td")[3].get_text(strip=True),
        }
    except Exception:
        return None

def main():
    last = load_state()
    blanks = 0
    new_devices = []

    while blanks < BLANK_LIMIT:
        last += 1
        dev = fetch(last)
        if dev:
            blanks = 0
            new_devices.append(dev)
        else:
            blanks += 1

    save_state(last)

    if new_devices:
        # write the list for GitHub Actions
        with open('new_devices.json', 'w', encoding='utf-8') as f:
            json.dump(new_devices, f, ensure_ascii=False, indent=2)
        print("New NR devices:", *new_devices, sep="\n")
        sys.exit(1)   # non-zero => workflow detects new devices
    else:
        with open('new_devices.json', 'w', encoding='utf-8') as f:
            json.dump([], f)  # empty array
        print("No new devices today.")

if __name__ == "__main__":
    main()
    
