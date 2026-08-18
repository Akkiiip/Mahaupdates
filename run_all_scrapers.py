"""Run all MahaUpdate official-source scrapers safely in local and cloud environments."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRAPERS = [
    "mpsc_updates.py", "midc_updates.py", "police_updates.py",
    "nhm_updates.py", "pwd_updates.py", "mjp_updates.py",
    "public_health_updates.py", "msedcl_updates.py",
    "mahatransco_updates.py", "mahagenco_updates.py",
    "forest_updates.py", "dma_updates.py", "wcd_updates.py",
    "dfsl_updates.py", "dmer_updates.py", "sainik_welfare_updates.py",
    "ssc_updates.py", "railway_updates.py", "aai_updates.py",
    "upsc_updates.py", "ibps_updates.py",
]

ROOT = Path(__file__).resolve().parent
TIMEOUT_SECONDS = 300

def main():
    print("=" * 65)
    print("MAHAUPDATE - MASTER SCRAPER RUNNER")
    print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 65)

    results = []

    for scraper in SCRAPERS:
        path = ROOT / scraper

        if not path.exists():
            print(f"\nSKIPPED: {scraper} (file not found)")
            results.append((scraper, "SKIPPED"))
            continue

        print(f"\nRunning: {scraper}")

        try:
            completed = subprocess.run(
                [sys.executable, str(path)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=TIMEOUT_SECONDS,
            )

            stdout = completed.stdout or ""
            stderr = completed.stderr or ""

            if stdout.strip():
                print(stdout.strip())

            if completed.returncode == 0:
                print(f"SUCCESS: {scraper}")
                results.append((scraper, "SUCCESS"))
            else:
                if stderr.strip():
                    print("ERROR:", stderr.strip())
                print(f"FAILED: {scraper}")
                results.append((scraper, "FAILED"))

        except subprocess.TimeoutExpired:
            print(f"TIMEOUT: {scraper} ({TIMEOUT_SECONDS}s)")
            results.append((scraper, "TIMEOUT"))

        except Exception as exc:
            print(f"ERROR: {scraper} - {exc}")
            results.append((scraper, "FAILED"))

    print("\n" + "=" * 65)
    print("FINAL SUMMARY")
    print("=" * 65)

    for scraper, status in results:
        print(f"{status:8} {scraper}")

    success = sum(status == "SUCCESS" for _, status in results)
    skipped = sum(status == "SKIPPED" for _, status in results)
    timeout = sum(status == "TIMEOUT" for _, status in results)
    failed = sum(status == "FAILED" for _, status in results)

    print("-" * 65)
    print(
        f"Total: {len(results)} | Success: {success} | "
        f"Failed: {failed} | Timeout: {timeout} | Skipped: {skipped}"
    )
    print("Finished:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Remote government-site outages are reported in the summary but do not
    # fail the entire GitHub Actions automation.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
