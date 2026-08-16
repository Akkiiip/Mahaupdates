"""Run all MahaUpdate official-source scrapers safely."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from datetime import datetime

SCRAPERS = [
    "mpsc_updates.py",
    "midc_updates.py",
    "police_updates.py",
    "nhm_updates.py",
    "pwd_updates.py",
    "mjp_updates.py",
    "public_health_updates.py",
    "msedcl_updates.py",
    "mahatransco_updates.py",
    "mahagenco_updates.py",
    "forest_updates.py",
    "dma_updates.py",
    "wcd_updates.py",
    "dfsl_updates.py",
    "dmer_updates.py",
    "sainik_welfare_updates.py",
    "ssc_updates.py",
    "railway_updates.py",
    "aai_updates.py",
    "upsc_updates.py",
    "ibps_updates.py",
]

ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("=" * 65)
    print("MAHAUPDATE — MASTER SCRAPER RUNNER")
    print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 65)

    results = []

    for scraper in SCRAPERS:
        path = ROOT / scraper
        if not path.exists():
            print(f"\n⚠ SKIPPED: {scraper} (file not found)")
            results.append((scraper, "SKIPPED"))
            continue

        print(f"\n▶ Running: {scraper}")
        try:
            completed = subprocess.run(
                [sys.executable, str(path)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=180,
            )

            if completed.stdout.strip():
                print(completed.stdout.strip())

            if completed.returncode == 0:
                print(f"✓ SUCCESS: {scraper}")
                results.append((scraper, "SUCCESS"))
            else:
                if completed.stderr.strip():
                    print("ERROR:", completed.stderr.strip())
                print(f"✗ FAILED: {scraper}")
                results.append((scraper, "FAILED"))

        except subprocess.TimeoutExpired:
            print(f"✗ TIMEOUT: {scraper}")
            results.append((scraper, "TIMEOUT"))
        except Exception as exc:
            print(f"✗ ERROR: {scraper} — {exc}")
            results.append((scraper, "FAILED"))

    print("\n" + "=" * 65)
    print("FINAL SUMMARY")
    print("=" * 65)
    for scraper, status in results:
        print(f"{status:8} {scraper}")

    success = sum(status == "SUCCESS" for _, status in results)
    skipped = sum(status == "SKIPPED" for _, status in results)
    failed = len(results) - success - skipped

    print("-" * 65)
    print(f"Total: {len(results)} | Success: {success} | Failed: {failed} | Skipped: {skipped}")
    print("Finished:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
