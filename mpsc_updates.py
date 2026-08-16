"""Fetch latest MPSC updates and sync them to Supabase."""

import base64
import json
import os
import re
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from supabase import create_client

BASE_URL = "https://mpsc.gov.in"
API_URL = f"{BASE_URL}/web/api/v1/home"
KEY = b"1234567812345678"
CRC_KEY = b"S300cr3t!@#Key$%^&*()_+[]{}|;':,.<>?/~`"
SEEN_FILE = Path("seen_updates.json")
TEST_MODE = False

def decrypt(ciphertext):
    decryptor = Cipher(algorithms.AES(KEY), modes.CBC(KEY)).decryptor()
    padded = decryptor.update(base64.b64decode(ciphertext)) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()

def classify(title):
    title = title.lower()
    rules = [("Recommendation List", ("recommendation list",)), ("Merit List", ("merit list",)), ("Answer Key", ("answer key",)), ("Hall Ticket", ("hall ticket", "admission certificate")), ("Corrigendum", ("corrigendum",)), ("Exam Date", ("exam date", "examination date", "exam schedule", "time table")), ("Result", ("result",)), ("Advertisement", ("advertisement", "notification"))]
    return next((category for category, keywords in rules if any(word in title for word in keywords)), "Other")

def advertisement_numbers(title):
    return list(dict.fromkeys(re.findall(r"\b\d{1,3}/\d{4}\b", title)))

def recruitment_title(title):
    title = re.sub(r"\bAdv(?:t)?\.?\s*(?:No\.?)?\s*[-:]?\s*\d{1,3}/\d{4}(?:\s*(?:&|,|and)\s*\d{1,3}/\d{4})*", "", title, flags=re.I)
    endings = r"Announcement\s+Regarding\s+(?:Revised\s+)?Result|Revised(?:\s+(?:Recommendation\s+List|Merit\s+List|Result))?|Recommendation\s+List|Merit\s+List|Final\s+Answer\s+Key|Answer\s+Key|Corrigendum|Hall\s+Ticket|Admission\s+Certificate|Exam\s+Date|Result"
    title = re.sub(rf"\s*[-–—]?\s*(?:{endings})\s*$", "", title, flags=re.I)
    title = re.sub(r"\s+-\s*", " - ", title)
    title = re.sub(r"(?<=\d)-(?=\s)", " - ", title)
    return re.sub(r"\s{2,}", " ", title).strip(" -")

def load_seen():
    if not SEEN_FILE.exists(): return []
    try: return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    except Exception: return []

def get_marathi_title(update):
    for key in ["descInMarathi", "descInMarathiLanguage", "marathiDescription", "descriptionInMarathi", "descMarathi"]:
        value = update.get(key)
        if isinstance(value, str) and value.strip(): return value.strip()
    return ""

def sync_supabase(client, record, last_seen):
    table = client.table("updates")
    existing = table.select("id").eq("official_url", record["url"]).execute().data
    if existing:
        table.update({"last_seen": last_seen, "title_english": record["title_english"], "title_marathi": record["title_marathi"]}).eq("official_url", record["url"]).execute()
        return "updated"
    table.insert({"source": "MPSC", "title": record["title"], "title_english": record["title_english"], "title_marathi": record["title_marathi"], "type": record["type"], "advertisement_numbers": record["advertisement_numbers"], "recruitment_title": record["recruitment_title"], "status": "pending", "official_url": record["url"], "first_seen": record["first_seen"], "last_seen": last_seen}).execute()
    return "inserted"

def main():
    supabase_url = os.getenv("SUPABASE_URL"); supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set."); return
    supabase = create_client(supabase_url, supabase_key)
    crc = f"{zlib.crc32(CRC_KEY) & 0xffffffff:x}"
    response = requests.get(API_URL, headers={"Authorization": f"|#|#{crc}"}, timeout=30); response.raise_for_status()
    updates = json.loads(decrypt(response.text))["latestUpdateList"][:10]
    if TEST_MODE: updates.append({"descInEnglish": "Advt No. 999/2026 - TEST ENGINEER, Maharashtra Government Service - Announcement Regarding Result", "url": "https://example.com/test-mpsc-update-999-2026.pdf"})
    seen = {(entry["url"] if isinstance(entry, dict) else entry): entry for entry in load_seen()}
    for record in seen.values():
        if isinstance(record, dict):
            record.pop("advertisement_no", None); record["advertisement_numbers"] = advertisement_numbers(record["title"]); record["recruitment_title"] = recruitment_title(record["title"]); record.setdefault("title_english", record.get("title", "")); record.setdefault("title_marathi", "")
    inserted = updated = 0
    for update in updates:
        title = update["descInEnglish"].strip(); title_marathi = get_marathi_title(update)
        link = update.get("url") or f"{BASE_URL}/web/api/v1/downloadFileImage/english/{quote(update['englishFileName'])}"
        update_type = classify(title); adv_numbers = advertisement_numbers(title); status = "EXISTING" if link in seen else "NEW"
        if status == "NEW" or not isinstance(seen[link], dict):
            seen[link] = {"url": link, "title": title, "title_english": title, "title_marathi": title_marathi, "type": update_type, "advertisement_numbers": adv_numbers, "recruitment_title": recruitment_title(title), "first_seen": datetime.now(timezone.utc).isoformat()}
        else:
            seen[link]["title"] = title; seen[link]["title_english"] = title
            if title_marathi: seen[link]["title_marathi"] = title_marathi
        result = sync_supabase(supabase, seen[link], datetime.now(timezone.utc).isoformat())
        inserted += result == "inserted"; updated += result != "inserted"
        print(f"STATUS: {status}\nTYPE: {update_type}\nADVT NO: {', '.join(adv_numbers) or 'N/A'}\nTITLE: {title}\nURL: {link}\n")
    SEEN_FILE.write_text(json.dumps(list(seen.values()), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"SUPABASE: inserted={inserted}, existing/updated={updated}")

if __name__ == "__main__": main()
