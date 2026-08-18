import os
import re
from collections import Counter, defaultdict
from urllib.parse import urlparse

from dotenv import load_dotenv
from notification_validation import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("ERROR: SUPABASE_URL or SUPABASE_KEY is missing.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_all():
    all_rows = []
    start = 0
    batch_size = 1000

    while True:
        response = (
            supabase.table("updates")
            .select("*")
            .range(start, start + batch_size - 1)
            .execute()
        )
        rows = response.data or []
        all_rows.extend(rows)

        if len(rows) < batch_size:
            break

        start += batch_size

    return all_rows


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def main():
    rows = fetch_all()

    print("=" * 70)
    print("MAHAUPDATE SUPABASE READ-ONLY AUDIT")
    print("=" * 70)
    print(f"Total records: {len(rows)}")

    print("\nSOURCE COUNTS")
    print("-" * 70)
    source_counts = Counter(row.get("source") or "MISSING SOURCE" for row in rows)
    for source, count in source_counts.most_common():
        print(f"{source}: {count}")

    print("\nTYPE COUNTS")
    print("-" * 70)
    type_counts = Counter(row.get("type") or "MISSING TYPE" for row in rows)
    for update_type, count in type_counts.most_common():
        print(f"{update_type}: {count}")

    print("\nMISSING IMPORTANT FIELDS")
    print("-" * 70)
    missing = defaultdict(list)
    for row in rows:
        row_id = row.get("id")
        for field in ["source", "title", "type", "official_url", "first_seen"]:
            if not row.get(field):
                missing[field].append(row_id)

    if missing:
        for field, ids in missing.items():
            print(f"{field}: {len(ids)}")
            print("IDs:", ids[:20])
    else:
        print("No missing important fields found.")

    print("\nINVALID OR SUSPICIOUS URLs")
    print("-" * 70)
    bad_urls = []
    for row in rows:
        url = str(row.get("official_url") or "").strip()
        if not url:
            bad_urls.append((row.get("id"), "EMPTY", row.get("title")))
            continue
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            bad_urls.append((row.get("id"), url, row.get("title")))

    print(f"Found: {len(bad_urls)}")
    for item in bad_urls[:30]:
        print(item)

    print("\nDUPLICATE OFFICIAL URLs")
    print("-" * 70)
    urls = defaultdict(list)
    for row in rows:
        url = clean_text(row.get("official_url"))
        if url:
            urls[url].append(row)

    duplicate_urls = {url: records for url, records in urls.items() if len(records) > 1}
    print(f"Duplicate URL groups: {len(duplicate_urls)}")
    for url, records in list(duplicate_urls.items())[:30]:
        print(f"\nURL: {url}")
        for record in records:
            print(f"  ID={record.get('id')} | {record.get('source')} | {record.get('title')}")

    print("\nPOSSIBLE DUPLICATE TITLES")
    print("-" * 70)
    titles = defaultdict(list)
    for row in rows:
        key = (clean_text(row.get("source")), clean_text(row.get("title")))
        if key[1]:
            titles[key].append(row)

    duplicate_titles = {key: records for key, records in titles.items() if len(records) > 1}
    print(f"Duplicate title groups: {len(duplicate_titles)}")
    for (source, title), records in list(duplicate_titles.items())[:30]:
        print(f"\nSOURCE: {source}")
        print(f"TITLE: {title}")
        for record in records:
            print(f"  ID={record.get('id')} | URL={record.get('official_url')}")

    print("\nURL DOMAIN SUMMARY BY SOURCE")
    print("-" * 70)
    source_domains = defaultdict(Counter)
    for row in rows:
        source = row.get("source") or "UNKNOWN"
        url = row.get("official_url") or ""
        domain = urlparse(url).netloc.lower()
        if domain:
            source_domains[source][domain] += 1

    for source in sorted(source_domains):
        print(f"\n{source}")
        for domain, count in source_domains[source].most_common(10):
            print(f"  {count:4}  {domain}")

    print("\nPOSSIBLE HOMEPAGE URLs")
    print("-" * 70)
    homepage_like = []
    for row in rows:
        url = str(row.get("official_url") or "").strip()
        if not url:
            continue
        path = urlparse(url).path.rstrip("/")
        if path in ("", "/") or len(path) < 4:
            homepage_like.append(row)

    print(f"Found: {len(homepage_like)}")
    for row in homepage_like[:30]:
        print(f"{row.get('source')} | {row.get('title')} | {row.get('official_url')}")

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
