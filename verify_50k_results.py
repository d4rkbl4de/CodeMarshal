#!/usr/bin/env python3
"""
Verify results of 50K production test.

This script is repo-local (does not assume ~/.codemarshal). It checks:
- performance_report.json (if present)
- storage/observations manifests and observation files
- expected export/report artifacts if generated

For the authoritative post-test checks, you should also run:
  codemarshal query . --stats
  codemarshal query . --pattern="boundary_violations" --count
  codemarshal export --format=html --full --output=final_constitutional_report.html
  codemarshal integrity verify --all
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def verify_results() -> bool:
    print("VERIFYING 50K PRODUCTION TEST RESULTS")
    print("=" * 70)

    checks: list[tuple[str, bool]] = []

    repo_root = Path(__file__).resolve().parent

    # 1) Performance report (optional)
    perf_path = repo_root / "performance_report.json"
    if perf_path.exists():
        perf = json.loads(perf_path.read_text(encoding="utf-8"))

        print("Performance Metrics:")
        print(f"  Total files processed: {perf.get('total_files_processed', 'N/A')}")
        print(f"  Peak memory: {float(perf.get('peak_memory_mb', 0.0)):.1f}MB")
        print(f"  Average speed: {float(perf.get('average_speed_files_per_sec', 0.0)):.1f} files/sec")
        print(f"  Total duration: {float(perf.get('total_duration_seconds', 0.0)):.1f}s")

        checks.append(("Memory < 3GB", float(perf.get("peak_memory_mb", 0.0)) < 3000.0))
        checks.append(("Files processed > 0", int(perf.get("total_files_processed", 0)) > 0))
    else:
        print("performance_report.json not found (ok if you did not run performance_monitor.py)")

    # 2) Observation storage
    obs_dir = repo_root / "storage" / "observations"
    if obs_dir.exists():
        obs_files = list(obs_dir.glob("*.observation.json"))
        manifests = list(obs_dir.glob("*.manifest.json"))

        print("\nObservation Storage:")
        print(f"  Observation files: {len(obs_files)}")
        print(f"  Manifest files: {len(manifests)}")

        checks.append(("Observations stored", len(obs_files) > 0))
        checks.append(("Manifest(s) present", len(manifests) > 0))

        # Spot-check integrity hash field presence (format may vary by schema)
        samples = obs_files[:10]
        hash_present = 0
        for p in samples:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if "integrity_hash" in data or "hash" in data:
                    hash_present += 1
            except Exception:
                pass
        if samples:
            print(f"  Samples with hash field: {hash_present}/{len(samples)}")
            checks.append(("Hash field present in most samples", hash_present >= max(1, int(0.8 * len(samples)))))
    else:
        print("\nstorage/observations not found")
        checks.append(("Observations stored", False))

    # 3) Generated report artifacts
    report_html = repo_root / "final_constitutional_report.html"
    checks.append(("HTML report generated", report_html.exists()))

    # 4) Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    all_passed = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("50K PRODUCTION TEST VERIFIED SUCCESSFULLY")
        return True

    print("Some checks failed. Review logs and rerun the CLI post-test verification commands.")
    return False


if __name__ == "__main__":
    success = verify_results()
    raise SystemExit(0 if success else 1)
