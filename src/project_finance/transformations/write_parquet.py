from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow
import yaml


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CURATED_DIR = PROJECT_ROOT / "data" / "curated"
LOG_DIR = PROJECT_ROOT / "logs"

CONTRACT_FILE = (
    PROJECT_ROOT
    / "config"
    / "dataset_contracts.yaml"
)


# ============================================================
# PARQUET SETTINGS
# ============================================================

PARQUET_ENGINE = "pyarrow"
PARQUET_COMPRESSION = "snappy"


# ============================================================
# CONFIG
# ============================================================

def load_yaml(path: Path) -> dict:
    """Load YAML configuration."""

    if not path.exists():
        raise FileNotFoundError(
            f"Missing configuration file:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file) or {}


# ============================================================
# HASHING
# ============================================================

def calculate_sha256(path: Path) -> str:
    """
    Calculate SHA-256 checksum for a file.
    """

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


# ============================================================
# DISCOVER CURATED CSV FILES
# ============================================================

def discover_curated_csv() -> list[Path]:
    """
    Find validated curated CSV datasets.
    """

    CURATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sorted(
        path
        for path in CURATED_DIR.glob("*.csv")
        if not path.name.startswith("~$")
    )


# ============================================================
# DATASET CONTRACT
# ============================================================

def get_contract(
    dataset_name: str,
    contracts_config: dict,
) -> dict:
    """
    Get contract for a dataset.
    """

    datasets = contracts_config.get(
        "datasets",
        {},
    )

    if dataset_name not in datasets:
        raise ValueError(
            "No dataset contract found for: "
            f"{dataset_name}"
        )

    return datasets[dataset_name]


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

def check_required_columns(
    df: pd.DataFrame,
    contract: dict,
) -> None:
    """
    Verify that all required canonical columns
    still exist in the curated dataset.
    """

    required = set(
        contract.get(
            "required_columns",
            {},
        ).keys()
    )

    missing = sorted(
        required - set(df.columns)
    )

    if missing:

        missing_text = "\n".join(
            f"  - {column}"
            for column in missing
        )

        raise ValueError(
            "Missing required canonical columns:\n"
            f"{missing_text}"
        )


# ============================================================
# WRITE PARQUET
# ============================================================

def write_parquet_file(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Write DataFrame to Parquet.

    The pandas index is intentionally excluded.
    """

    df.to_parquet(
        output_path,
        engine=PARQUET_ENGINE,
        compression=PARQUET_COMPRESSION,
        index=False,
    )


# ============================================================
# ROUND-TRIP VERIFICATION
# ============================================================

def verify_parquet(
    source_df: pd.DataFrame,
    parquet_path: Path,
) -> dict[str, Any]:
    """
    Read generated Parquet back and verify
    basic structural integrity.
    """

    parquet_df = pd.read_parquet(
        parquet_path,
        engine=PARQUET_ENGINE,
    )

    source_rows = len(source_df)
    parquet_rows = len(parquet_df)

    source_columns = list(
        source_df.columns
    )

    parquet_columns = list(
        parquet_df.columns
    )

    row_count_match = (
        source_rows == parquet_rows
    )

    column_count_match = (
        len(source_columns)
        == len(parquet_columns)
    )

    column_names_match = (
        source_columns == parquet_columns
    )

    if not row_count_match:

        raise ValueError(
            "Parquet row count differs from "
            "validated CSV.\n"
            f"CSV rows     : {source_rows}\n"
            f"Parquet rows : {parquet_rows}"
        )

    if not column_count_match:

        raise ValueError(
            "Parquet column count differs from "
            "validated CSV.\n"
            f"CSV columns     : {len(source_columns)}\n"
            f"Parquet columns : {len(parquet_columns)}"
        )

    if not column_names_match:

        raise ValueError(
            "Parquet column names or order differ "
            "from validated CSV."
        )

    return {
        "rows_source": source_rows,
        "rows_parquet": parquet_rows,
        "columns_source": len(source_columns),
        "columns_parquet": len(parquet_columns),
        "row_count_match": row_count_match,
        "column_count_match": column_count_match,
        "column_names_match": column_names_match,
    }


# ============================================================
# PROCESS ONE DATASET
# ============================================================

def process_dataset(
    csv_path: Path,
    contracts_config: dict,
) -> dict[str, Any]:
    """
    Convert one validated curated CSV to Parquet.
    """

    dataset_name = csv_path.stem

    print()
    print("=" * 100)
    print(f"DATASET : {dataset_name}")
    print("=" * 100)

    started_at = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Contract
    # --------------------------------------------------------

    contract = get_contract(
        dataset_name=dataset_name,
        contracts_config=contracts_config,
    )

    # --------------------------------------------------------
    # Read curated CSV
    # --------------------------------------------------------

    df = pd.read_csv(
        csv_path,
        low_memory=False,
    )

    # --------------------------------------------------------
    # Required column check
    # --------------------------------------------------------

    check_required_columns(
        df=df,
        contract=contract,
    )

    # --------------------------------------------------------
    # Output path
    # --------------------------------------------------------

    parquet_path = (
        CURATED_DIR
        / f"{dataset_name}.parquet"
    )

    # --------------------------------------------------------
    # Write Parquet
    # --------------------------------------------------------

    write_parquet_file(
        df=df,
        output_path=parquet_path,
    )

    # --------------------------------------------------------
    # Read back and verify
    # --------------------------------------------------------

    verification = verify_parquet(
        source_df=df,
        parquet_path=parquet_path,
    )

    # --------------------------------------------------------
    # SHA-256
    # --------------------------------------------------------

    csv_hash = calculate_sha256(
        csv_path
    )

    parquet_hash = calculate_sha256(
        parquet_path
    )

    # --------------------------------------------------------
    # File sizes
    # --------------------------------------------------------

    csv_size = csv_path.stat().st_size
    parquet_size = parquet_path.stat().st_size

    completed_at = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {
        "dataset": dataset_name,
        "status": "PASS",
        "source_csv": str(csv_path),
        "parquet_file": str(parquet_path),

        "rows": len(df),
        "columns": len(df.columns),

        "engine": PARQUET_ENGINE,
        "compression": PARQUET_COMPRESSION,

        "csv_bytes": csv_size,
        "parquet_bytes": parquet_size,

        "csv_sha256": csv_hash,
        "parquet_sha256": parquet_hash,

        "verification": verification,

        "started_at_utc": started_at.isoformat(),
        "completed_at_utc": completed_at.isoformat(),
    }

    print(f"Rows            : {result['rows']:,}")
    print(f"Columns         : {result['columns']}")
    print(f"Engine          : {PARQUET_ENGINE}")
    print(f"Compression     : {PARQUET_COMPRESSION}")
    print(f"CSV bytes       : {csv_size:,}")
    print(f"Parquet bytes   : {parquet_size:,}")
    print("Round-trip rows : PASS")
    print("Round-trip cols : PASS")
    print(f"Output          : {parquet_path}")
    print("STATUS          : PASS")

    return result


# ============================================================
# AUDIT REPORT
# ============================================================

def write_report(
    results: list[dict[str, Any]],
    contract_version: str,
) -> Path:
    """
    Write one JSON audit report for the
    Parquet materialization run.
    """

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    report_path = (
        LOG_DIR
        / f"parquet_{timestamp}.json"
    )

    report = {
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "contract_version": contract_version,

        "pandas_version": pd.__version__,

        "pyarrow_version": pyarrow.__version__,

        "engine": PARQUET_ENGINE,

        "compression": PARQUET_COMPRESSION,

        "datasets": results,
    }

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return report_path


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    """
    WF1 WF1 curated CSV -> Silver Parquet.
    """

    print()
    print("=" * 100)
    print("WF1 PARQUET WRITER V1")
    print("=" * 100)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Curated      : {CURATED_DIR}")
    print(f"Contracts    : {CONTRACT_FILE}")

    # --------------------------------------------------------
    # Load contracts
    # ----------------------------------------

    try:

        contracts_config = load_yaml(
            CONTRACT_FILE
        )

    except Exception as exc:

        print()
        print("CONFIG ERROR")
        print(str(exc))

        return 1

    contract_version = str(
        contracts_config.get(
            "version",
            "unknown",
        )
    )

    # --------------------------------------------------------
    # Discover validated CSV files
    # --------------------------------------------------------

    csv_files = discover_curated_csv()

    if not csv_files:

        print()
        print(
            "No validated curated CSV files found."
        )

        return 1

    print()
    print(
        f"Datasets detected: {len(csv_files)}"
    )

    for path in csv_files:
        print(
            f"  - {path.name}"
        )

    # --------------------------------------------------------
    # Process datasets
    # --------------------------------------------------------

    results: list[dict[str, Any]] = []

    failed = 0

    for csv_path in csv_files:

        dataset_name = csv_path.stem

        try:

            result = process_dataset(
                csv_path=csv_path,
                contracts_config=contracts_config,
            )

        except Exception as exc:

            failed += 1

            result = {
                "dataset": dataset_name,
                "status": "FAIL",
                "source_csv": str(csv_path),
                "error": str(exc),
            }

            print()
            print("=" * 100)
            print(f"DATASET : {dataset_name}")
            print("=" * 100)
            print("STATUS          : FAIL")
            print(f"ERROR           : {exc}")

        results.append(
            result
        )

    # --------------------------------------------------------
    # Audit report
    # --------------------------------------------------------

    report_path = write_report(
        results=results,
        contract_version=contract_version,
    )

    passed = (
        len(results) - failed
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("PARQUET SUMMARY")
    print("=" * 100)

    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Total  : {len(results)}")
    print(f"Report : {report_path}")

    print("=" * 100)

    return 1 if failed else 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )