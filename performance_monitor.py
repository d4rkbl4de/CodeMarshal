#!/usr/bin/env python3
"""
Performance monitoring for 50K production test.

Notes:
- This is designed for the CodeMarshal repo layout in this workspace.
- Progress is derived from the most recently updated manifest in:
  ./storage/observations/*.manifest.json
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path


class PerformanceMonitor:
    def __init__(self, pid: int, output_file: str = "performance_metrics.json"):
        self.pid = pid
        self.output_file = output_file
        self.start_time = datetime.now()
        self.metrics: list[dict] = []

        try:
            import psutil  # type: ignore

            self.psutil = psutil
        except Exception:
            self.psutil = None

    def _read_latest_manifest_progress(self) -> int:
        obs_dir = Path(__file__).resolve().parent / "storage" / "observations"
        if not obs_dir.exists():
            return 0

        manifests = list(obs_dir.glob("*.manifest.json"))
        if not manifests:
            return 0

        latest = max(manifests, key=lambda p: p.stat().st_mtime)
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            return int(data.get("files_processed", 0))
        except Exception:
            return 0

    def save_metrics(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=2)

    def generate_report(self):
        if not self.metrics:
            return

        last = self.metrics[-1]
        report = {
            "test_completed": datetime.now().isoformat(),
            "total_duration_seconds": last.get("elapsed_seconds", 0.0),
            "total_files_processed": last.get("files_processed", 0),
            "peak_memory_mb": max(m.get("memory_mb", 0.0) for m in self.metrics),
            "average_memory_mb": sum(m.get("memory_mb", 0.0) for m in self.metrics)
            / len(self.metrics),
            "average_cpu_percent": sum(m.get("cpu_percent", 0.0) for m in self.metrics)
            / len(self.metrics),
            "average_speed_files_per_sec": (
                (last.get("files_processed", 0) / last.get("elapsed_seconds", 1.0))
                if last.get("elapsed_seconds", 0.0) > 0
                else 0.0
            ),
            "final_speed_files_per_sec": last.get("speed_files_per_sec", 0.0),
        }

        with open("performance_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("\n\n" + "=" * 70)
        print("PERFORMANCE REPORT")
        print("=" * 70)
        for key, value in report.items():
            if "seconds" in key:
                hours = float(value) / 3600.0
                print(
                    f"{key.replace('_', ' ').title()}: {value:.1f}s ({hours:.2f} hours)"
                )
            elif "memory" in key:
                print(f"{key.replace('_', ' ').title()}: {value:.1f}MB")
            elif "speed" in key:
                print(f"{key.replace('_', ' ').title()}: {value:.1f} files/sec")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")

    def monitor(self):
        if not self.psutil:
            print("psutil is required for performance_monitor.py")
            print("Install it in your venv: pip install psutil")
            return 2

        try:
            process = self.psutil.Process(self.pid)
        except self.psutil.NoSuchProcess:
            print(f"Process {self.pid} not found")
            return 1

        print(f"PERFORMANCE MONITOR - PID: {self.pid}")
        print("=" * 70)
        print("Elapsed    |   Memory   |  CPU  |  Files  |   Speed   |   ETA")
        print("(HH:MM:SS) |   (MB)     |  (%)  | Processed | (files/s) | (HH:MM:SS)")
        print("-" * 70)

        last_file_count = 0
        last_check_time = time.time()

        while True:
            try:
                if not process.is_running():
                    break

                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent(interval=0.5)
                elapsed = datetime.now() - self.start_time

                files_processed = self._read_latest_manifest_progress()

                current_time = time.time()
                time_diff = current_time - last_check_time
                if time_diff > 0 and files_processed > last_file_count:
                    speed = (files_processed - last_file_count) / time_diff
                    last_file_count = files_processed
                    last_check_time = current_time
                else:
                    speed = 0.0

                total_files_estimate = 50000
                if speed > 0 and files_processed > 0:
                    remaining_files = max(0, total_files_estimate - files_processed)
                    eta_seconds = remaining_files / speed
                    eta = timedelta(seconds=eta_seconds)
                else:
                    eta = timedelta(seconds=0)

                metric = {
                    "timestamp": datetime.now().isoformat(),
                    "elapsed_seconds": elapsed.total_seconds(),
                    "memory_mb": memory_mb,
                    "cpu_percent": cpu_percent,
                    "files_processed": files_processed,
                    "speed_files_per_sec": speed,
                    "eta_seconds": eta.total_seconds(),
                }
                self.metrics.append(metric)

                elapsed_str = str(elapsed).split(".")[0]
                eta_str = (
                    str(eta).split(".")[0] if eta.total_seconds() > 0 else "--:--:--"
                )

                print(
                    f"\r{elapsed_str:9s} | {memory_mb:8.1f}MB | {cpu_percent:5.1f}% | {files_processed:7d} | {speed:8.1f}/s | {eta_str}",
                    end="",
                )

                if len(self.metrics) % 30 == 0:
                    self.save_metrics()

                time.sleep(2)

            except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                break
            except KeyboardInterrupt:
                print("\n\nMonitoring interrupted")
                break

        self.save_metrics()
        self.generate_report()
        return 0


def main():
    parser = argparse.ArgumentParser(description="Performance monitor for CodeMarshal")
    parser.add_argument("--pid", type=int, required=True, help="Process ID to monitor")
    parser.add_argument(
        "--output", default="performance_metrics.json", help="Output file"
    )

    args = parser.parse_args()

    monitor = PerformanceMonitor(args.pid, args.output)
    return monitor.monitor()


if __name__ == "__main__":
    raise SystemExit(main())
