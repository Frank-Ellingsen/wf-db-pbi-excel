from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
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
# TECHNICAL COLUMNS
# ============================================================

TECHNICAL_COLUMNS = {
    "_dataset",
    "_source_file",
    "_loaded_at_utc",
    "_run_id",
    "_contract_version",
    "_validated_at_utc",
}


# ============================================================
# CONFIG
# ============================================================

def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing configuration file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file) or {}


# ============================================================
# FILE DISCOVERY
# ============================================================

def discover_parquet_files() -> list[Path]:
    CURATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sorted(
        path
        for path in CURATED_DIR.glob("*.parquet")
        if not path.name.startswith("~$")
    )


# ============================================================
# CONTRACT
# ============================================================

def get_contract(
    dataset_name: str,
    contracts_config: dict,
) -> dict:

    datasets = contracts_config.get(
        "datasets",
        {},
    )

    if dataset_name not in datasets:
        raise ValueError(
            f"No dataset contract found for: {dataset_name}"
        )

    return datasets[dataset_name]


def get_contract_fields(
    contract: dict,
) -> dict[str, dict[str, Any]]:

    fields: dict[str, dict[str, Any]] = {}

    for name, settings in contract.get(
        "required_columns",
        {},
    ).items():

        fields[name] = {
            **settings,
            "required": True,
        }

    for name, settings in contract.get(
        "optional_columns",
        {},
    ).items():

        fields[name] = {
            **settings,
            "required": False,
        }

    return fields


# ============================================================
# TYPE HANDLING
# ============================================================

def expected_type(
    contract_type: str,
) -> str:

    mapping = {
        "string": "string",
        "integer": "integer",
        "number": "number",
        "boolean": "boolean",
    }

    value = str(
        contract_type
    ).strip().lower()

    if value not in mapping:
        raise ValueError(
            f"Unsupported contract datatype: {contract_type}"
        )

    return mapping[value]


def actual_type(
    arrow_type: pa.DataType,
) -> str:

    if (
        pa.types.is_string(arrow_type)
        or pa.types.is_large_string(arrow_type)
    ):
        return "string"

    if pa.types.is_integer(
        arrow_type
    ):
        return "integer"

    if (
        pa.types.is_floating(arrow_type)
        or pa.types.is_decimal(arrow_type)
    ):
        return "number"

    if pa.types.is_boolean(
        arrow_type
    ):
        return "boolean"

    if pa.types.is_null(
        arrow_type
    ):
        return "null"

    return str(
        arrow_type
    )


def compatible(
    expected: str,
    actual: str,
) -> bool:

    if expected == actual:
        return True

    # Integers are valid generic numbers.
    if expected == "number" and actual == "integer":
        return True

    return False


# ============================================================
# VALIDATE ONE DATASET
# ============================================================

def validate_dataset(
    parquet_path: Path,
    contracts_config: dict,
) -> dict[str, Any]:

    dataset_name = parquet_path.stem

    contract = get_contract(
        dataset_name,
        contracts_config,
    )

    contract_fields = get_contract_fields(
        contract
    )

    # read_schema reads the effective Arrow schema
    # from the Parquet file metadata.
    schema = pq.read_schema(
        parquet_path
    )

    parquet_fields = {
        field.name: field
        for field in schema
    }

    checks: list[dict[str, Any]] = []

    passed = True

    # --------------------------------------------------------
    # CONTRACT FIELDS
    # --------------------------------------------------------

    for column, settings in contract_fields.items():

        required = settings[
            "required"
        ]

        logical_expected = expected_type(
            settings.get(
                "type",
                "string",
            )
        )

        if column not in parquet_fields:

            if required:
                status = "FAIL"
                message = "Required column missing."
                passed = False
            else:
                status = "PASS"
                message = "Optional column not present."

            checks.append(
                {
                    "column": column,
                    "status": status,
                    "expected": logical_expected,
                    "actual": None,
                    "message": message,
                }
            )

            continue

        field = parquet_fields[
            column
        ]

        logical_actual = actual_type(
            field.type
        )

        type_ok = compatible(
            logical_expected,
            logical_actual,
        )

        if type_ok:
            status = "PASS"
            message = "Datatype compatible."
        else:
            status = "FAIL"
            message = "Datatype mismatch."
            passed = False

        checks.append(
            {
                "column": column,
                "status": status,
                "expected": logical_expected,
                "actual": logical_actual,
                "physical_type": str(
                    field.type
                ),
                "message": message,
            }
        )

    # --------------------------------------------------------
    # UNEXPECTED BUSINESS COLUMNS
    # --------------------------------------------------------

    allowed_business_columns = set(
        contract_fields.keys()
    )

    parquet_column_names = set(
        parquet_fields.keys()
    )

    unexpected = sorted(
        parquet_column_names
        - allowed_business_columns
        - TECHNICAL_COLUMNS
    )

    for column in unexpected:

        passed = False

        checks.append(
            {
                "column": column,
                "status": "FAIL",
                "expected": None,
                "actual": actual_type(
                    parquet_fields[column].type
                ),
                "physical_type": str(
                    parquet_fields[column].type
                ),
                "message": "Unexpected business column.",
            }
        )

    technical_columns = sorted(
        parquet_column_names
        & TECHNICAL_COLUMNS
    )

    return {
        "dataset": dataset_name,
        "status": (
            "PASS"
            if passed
            else "FAIL"
        ),
        "parquet_file": str(
            parquet_path
        ),
        "column_count": len(
            schema
        ),
        "technical_columns": technical_columns,
        "checks": checks,
        "arrow_schema": str(
            schema
        ),
    }


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(
    result: dict[str, Any],
) -> None:

    print()
    print("=" * 100)
    print(
        "DATASET :",
        result["dataset"],
    )
    print("=" * 100)

    print(
        "Status  :",
        result["status"],
    )

    print(
        "Columns :",
        result["column_count"],
    )

    print()
    print("SCHEMA CHECK")
    print("-" * 100)

    for check in result["checks"]:

        print(
            "[{}] {}".format(
                check["status"],
                check["column"],
            )
        )

        if check["expected"] is not None:
            print(
                "  Expected :",
                check["expected"],
            )

        if check["actual"] is not None:
            print(
                "  Actual   :",
                check["actual"],
            )

        if check.get(
            "physical_type"
        ) is not None:

            print(
                "  Physical :",
                check["physical_type"],
            )

        print(
            "  Message  :",
            check["message"],
        )

    print()
    print("Technical columns:")

    technical_columns = result[
        "technical_columns"
    ]

    if technical_columns:

        for column in technical_columns:
            print(
                "  -",
                column,
            )

    else:
        print("  None")


# ============================================================
# AUDIT REPORT
# ============================================================

def write_report(
    results: list[dict[str, Any]],
    contract_version: str,
) -> Path:

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
        / (
            "parquet_schema_"
            + timestamp
            + ".json"
        )
    )

    report = {
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "contract_version": contract_version,
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

    print()
    print("=" * 100)
    print(
        "WF1 PARQUET SCHEMA VALIDATOR V1"
    )
    print("=" * 100)

    print(
        "Curated   :",
        CURATED_DIR,
    )

    print(
        "Contracts :",
        CONTRACT_FILE,
    )

    # --------------------------------------------------------
    # CONTRACT CONFIG
    # --------------------------------------------------------

    try:

        contracts_config = load_yaml(
            CONTRACT_FILE
        )

    except Exception as exc:

        print()
        print("CONFIG ERROR")
        print(exc)

        return 1

    contract_version = str(
        contracts_config.get(
            "version",
            "unknown",
        )
    )

    # --------------------------------------------------------
    # PARQUET FILES
    # --------------------------------------------------------

    parquet_files = discover_parquet_files()

    if not parquet_files:

        print()
        print(
            "No Parquet files found."
        )

        return 1

    print()
    print(
        "Datasets detected:",
        len(parquet_files),
    )

    for path in parquet_files:
        print(
            "  -",
            path.name,
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    results: list[
        dict[str, Any]
    ] = []

    failed = 0

    for parquet_path in parquet_files:

        dataset_name = (
            parquet_path.stem
        )

        try:

            result = validate_dataset(
                parquet_path=parquet_path,
                contracts_config=contracts_config,
            )

        except Exception as exc:

            result = {
                "dataset": dataset_name,
                "status": "FAIL",
                "parquet_file": str(
                    parquet_path
                ),
                "column_count": 0,
                "technical_columns": [],
                "checks": [],
                "arrow_schema": None,
                "fatal_error": str(
                    exc
                ),
            }

        results.append(
            result
        )

        print_result(
            result
        )

        if result["status"] != "PASS":

            failed += 1

            if "fatal_error" in result:

                print()
                print(
                    "ERROR:",
                    result["fatal_error"],
                )

    # --------------------------------------------------------
    # AUDIT REPORT
    # --------------------------------------------------------

    report_path = write_report(
        results=results,
        contract_version=contract_version,
    )

    passed = (
        len(results)
        - failed
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print(
        "PARQUET SCHEMA SUMMARY"
    )
    print("=" * 100)

    print(
        "Passed :",
        passed,
    )

    print(
        "Failed :",
        failed,
    )

    print(
        "Total  :",
        len(results),
    )

    print(
        "Report :",
        report_path,
    )

    print("=" * 100)

    return (
        1
        if failed
        else 0
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )