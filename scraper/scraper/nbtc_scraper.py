#!/usr/bin/env python3
"""
Scrape NBTC ‘Cellular Mobile (GSM/WCDMA/LTE/NR)’ equipment.
Exits 0 → nothing new, 1 → new NR device found (used by the workflow).
"""
import os, json, datetime, sys, requests
from bs4 import BeautifulSoup

URL_TEMPLATE = "https://mocheck.nbtc.go.th/search-equipments/{id}"
STATE_FILE   = "state.json"
BLANK_LIMIT  = 500
TARGET_TYPE  = "Cellular Mobile (GSM/WCDMA/LTE/NR)"

def load_state():
    try:
        return json.load(open(STATE_FILE))["last_id"]
    except Exception:
        # fallback: let CI pass it via env, else hard-code
        return int(os.getenv("START_ID", "1628277"))

def save_state(last_id):
    json.dump({"last_id": last_id}, open(STATE_FILE, "w"), indent=2)

def fetch(id_):
    try:
        r = requests.get(URL_TEMPLATE.format(id=id_), timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # find the 4-column table
        rows = soup.select("table.table tbody tr")
        if not rows:
            return None
        data = {td.get_text(strip=True) for td in rows[0].find_all("td")}
        # row order: Type | Brand | Model | Cert-No
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
        print("New NR devices:", *new_devices, sep="\n")
        # write to GITHUB_OUTPUT for the workflow
        with open(os.getenv("GITHUB_OUTPUT", "/dev/null"), "a") as gh:
            gh.write("new_devices=" + json.dumps(new_devices) + "\n")
        sys.exit(1)   # triggers notification job
    else:
        print("No new devices today.")

if __name__ == "__main__":
    main()
