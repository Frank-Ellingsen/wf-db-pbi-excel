from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(r"C:\Users\frank\Desktop\WF1")
SRC = PROJECT_ROOT / "src" / "project_finance"
LOG_DIR = PROJECT_ROOT / "logs"

STEPS = [
    ("RAW to Historical Silver", SRC / "run_pipeline.py"),
    ("Build DuckDB Silver", SRC / "database" / "build_duckdb.py"),
    ("Build Business Gold Layer", SRC / "database" / "build_gold.py"),
    ("Build Gold Reporting Views", SRC / "database" / "build_gold_reporting.py"),
    ("Publish Power BI DuckDB (v1.5.0)", SRC / "database" / "build_powerbi_duckdb.py"),
    ("Build Excel Model & Sandbox Visuals", SRC / "reports" / "build_excel_model.py"),
]


def run_step(name: str, script: Path, log) -> bool:
    print("\n" + "=" * 100)
    print(f"STEP: {name}")
    print("=" * 100)
    log.write("\n" + "=" * 100 + "\n")
    log.write(f"STEP: {name}\n")
    log.write("=" * 100 + "\n")
    log.flush()

    if not script.exists():
        msg = f"ERROR: Script not found: {script}"
        print(msg)
        log.write(msg + "\n")
        return False

    process = subprocess.Popen(
        [sys.executable, str(script)],
        cwd=str(script.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert process.stdout is not None
    for line in process.stdout:
        try:
            print(line, end="")
        except UnicodeEncodeError:
            print(line.encode("ascii", errors="replace").decode("ascii"), end="")
        log.write(line)


    return_code = process.wait()
    result = "PASS" if return_code == 0 else f"FAIL (exit code {return_code})"
    print(f"\nSTEP RESULT: {result}")
    log.write(f"\nSTEP RESULT: {result}\n")
    log.flush()
    return return_code == 0


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"wf1_full_refresh_{stamp}.log"

    print("=" * 100)
    print("WF1 FULL REFRESH")
    print("=" * 100)
    print(f"Python : {sys.executable}")
    print(f"Project: {PROJECT_ROOT}")
    print(f"Log    : {log_path}")

    with log_path.open("w", encoding="utf-8") as log:
        log.write("WF1 FULL REFRESH\n")
        log.write(f"Python : {sys.executable}\n")
        log.write(f"Project: {PROJECT_ROOT}\n")

        for name, script in STEPS:
            if not run_step(name, script, log):
                print("\n" + "=" * 100)
                print("WF1 FULL REFRESH FAILED")
                print(f"Failed step: {name}")
                print(f"See log: {log_path}")
                print("=" * 100)
                return 1

    print("\n" + "=" * 100)
    print("WF1 FULL REFRESH COMPLETE")
    print("All steps completed successfully.")
    print(f"Log: {log_path}")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
