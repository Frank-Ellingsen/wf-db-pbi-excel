from __future__ import annotations

import csv
import fnmatch
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
STAGING_DIR = PROJECT_ROOT / "data" / "staging"

MAPPING_FILE = (
    PROJECT_ROOT
    / "config"
    / "column_mapping.yaml"
)

CONTRACT_FILE = (
    PROJECT_ROOT
    / "config"
    / "dataset_contracts.yaml"
)


# ============================================================
# SETTINGS
# ============================================================

ABSOLUTE_TOLERANCE = 0.01
RELATIVE_TOLERANCE = 1e-9


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass
class CheckResult:
    check: str
    status: str
    raw_value: Any
    staging_value: Any
    difference: Any
    message: str


# ============================================================
# YAML
# ============================================================

def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing configuration:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file) or {}


# ============================================================
# DATASET IDENTIFICATION
# ============================================================

def identify_dataset(
    path: Path,
    mapping_config: dict,
) -> str:

    matches: list[str] = []

    datasets = mapping_config.get(
        "datasets",
        {},
    )

    for dataset_name, config in datasets.items():

        for pattern in config.get(
            "file_patterns",
            [],
        ):

            if fnmatch.fnmatch(
                path.name.lower(),
                pattern.lower(),
            ):
                matches.append(dataset_name)
                break

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise ValueError(
            f"Unable to identify dataset: {path.name}"
        )

    raise ValueError(
        f"Ambiguous dataset: {path.name}\n"
        f"Matches: {matches}"
    )


# ============================================================
# CSV READING
# ============================================================

def detect_encoding(path: Path) -> str:

    for encoding in (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin1",
    ):

        try:
            with path.open(
                "r",
                encoding=encoding,
            ) as file:
                file.read(8192)

            return encoding

        except UnicodeDecodeError:
            continue

    raise ValueError(
        f"Unable to detect encoding: {path.name}"
    )


def detect_separator(
    path: Path,
    encoding: str,
) -> str:

    with path.open(
        "r",
        encoding=encoding,
        newline="",
    ) as file:
        sample = file.read(8192)

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )

        return dialect.delimiter

    except csv.Error:

        counts = {
            ",": sample.count(","),
            ";": sample.count(";"),
            "\t": sample.count("\t"),
            "|": sample.count("|"),
        }

        separator = max(
            counts,
            key=counts.get,
        )

        if counts[separator] == 0:
            raise ValueError(
                f"Unable to detect separator: {path.name}"
            )

        return separator


def read_raw(path: Path) -> pd.DataFrame:

    encoding = detect_encoding(path)

    separator = detect_separator(
        path,
        encoding,
    )

    return pd.read_csv(
        path,
        sep=separator,
        encoding=encoding,
        low_memory=False,
    )


def read_staging(
    dataset_name: str,
) -> pd.DataFrame:

    path = (
        STAGING_DIR
        / f"{dataset_name}.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Missing staging dataset:\n{path}"
        )

    return pd.read_csv(
        path,
        low_memory=False,
    )


# ============================================================
# MAPPING HELPERS
# ============================================================

def get_source_to_canonical_mapping(
    dataset_config: dict,
) -> dict[str, str]:

    result: dict[str, str] = {}

    for source, settings in dataset_config.get(
        "column_mapping",
        {},
    ).items():

        if isinstance(settings, dict):
            canonical = settings.get(
                "canonical"
            )
        else:
            canonical = settings

        if canonical:
            result[source] = str(canonical)

    return result


# ============================================================
# NUMERIC HELPERS
# ============================================================

def numeric_sum(
    series: pd.Series,
) -> float:

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    return float(
        numeric.sum(
            skipna=True
        )
    )


def numbers_match(
    left: float,
    right: float,
) -> bool:

    return math.isclose(
        left,
        right,
        rel_tol=RELATIVE_TOLERANCE,
        abs_tol=ABSOLUTE_TOLERANCE,
    )


# ============================================================
# BASIC CHECKS
# ============================================================

def check_row_count(
    raw: pd.DataFrame,
    staging: pd.DataFrame,
) -> CheckResult:

    raw_rows = len(raw)
    staging_rows = len(staging)

    difference = (
        staging_rows - raw_rows
    )

    passed = (
        difference == 0
    )

    return CheckResult(
        check="row_count",
        status="PASS" if passed else "FAIL",
        raw_value=raw_rows,
        staging_value=staging_rows,
        difference=difference,
        message=(
            "Row counts match."
            if passed
            else "Row counts do not match."
        ),
    )


# ============================================================
# SUM CHECK
# ============================================================

def check_numeric_sum(
    raw: pd.DataFrame,
    staging: pd.DataFrame,
    source_column: str,
    canonical_column: str,
) -> CheckResult:

    if source_column not in raw.columns:

        return CheckResult(
            check=f"sum:{canonical_column}",
            status="FAIL",
            raw_value=None,
            staging_value=None,
            difference=None,
            message=(
                f"Missing RAW column: "
                f"{source_column}"
            ),
        )

    if canonical_column not in staging.columns:

        return CheckResult(
            check=f"sum:{canonical_column}",
            status="FAIL",
            raw_value=None,
            staging_value=None,
            difference=None,
            message=(
                f"Missing STAGING column: "
                f"{canonical_column}"
            ),
        )

    raw_sum = numeric_sum(
        raw[source_column]
    )

    staging_sum = numeric_sum(
        staging[canonical_column]
    )

    difference = (
        staging_sum - raw_sum
    )

    passed = numbers_match(
        raw_sum,
        staging_sum,
    )

    return CheckResult(
        check=f"sum:{canonical_column}",
        status="PASS" if passed else "FAIL",
        raw_value=raw_sum,
        staging_value=staging_sum,
        difference=difference,
        message=(
            "Financial control total reconciled."
            if passed
            else "Financial control total differs."
        ),
    )


# ============================================================
# DIMENSION CHECKS
# ============================================================

def check_primary_key(
    staging: pd.DataFrame,
    primary_key: list[str],
) -> list[CheckResult]:

    results: list[CheckResult] = []

    missing_columns = [
        column
        for column in primary_key
        if column not in staging.columns
    ]

    if missing_columns:

        results.append(
            CheckResult(
                check="primary_key_columns",
                status="FAIL",
                raw_value=None,
                staging_value=None,
                difference=None,
                message=(
                    "Missing primary key columns: "
                    + ", ".join(missing_columns)
                ),
            )
        )

        return results

    # --------------------------------------------------------
    # NULL
    # --------------------------------------------------------

    null_rows = int(
        staging[
            primary_key
        ]
        .isna()
        .any(axis=1)
        .sum()
    )

    results.append(
        CheckResult(
            check="primary_key_null",
            status=(
                "PASS"
                if null_rows == 0
                else "FAIL"
            ),
            raw_value=None,
            staging_value=null_rows,
            difference=None,
            message=(
                "No NULL primary keys."
                if null_rows == 0
                else "NULL primary keys detected."
            ),
        )
    )

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    duplicate_rows = int(
        staging.duplicated(
            subset=primary_key,
            keep=False,
        ).sum()
    )

    results.append(
        CheckResult(
            check="primary_key_duplicate",
            status=(
                "PASS"
                if duplicate_rows == 0
                else "FAIL"
            ),
            raw_value=None,
            staging_value=duplicate_rows,
            difference=None,
            message=(
                "Primary key is unique."
                if duplicate_rows == 0
                else "Duplicate primary keys detected."
            ),
        )
    )

    return results


# ============================================================
# DATASET-SPECIFIC FINANCIAL CHECKS
# ============================================================

FACT_RECONCILIATION_COLUMNS = {

    "erp_finance": {
        "Budsjett": "budget",
        "Regnskap": "actual",
    },

    "framsikt_finance": {
        "Regnskap hiå.": "actual_ytd",
        "Budsjett hiå.": "budget_ytd",
        "Årsbudsjett": "annual_budget",
        "Regnskap i fjor": "actual_prior_year",
    },
}


# ============================================================
# RECONCILE DATASET
# ============================================================

def reconcile_dataset(
    raw_path: Path,
    dataset_name: str,
    mapping_config: dict,
    contract_config: dict,
) -> list[CheckResult]:

    raw = read_raw(
        raw_path
    )

    staging = read_staging(
        dataset_name
    )

    results: list[CheckResult] = []

    # --------------------------------------------------------
    # ROW COUNT
    # --------------------------------------------------------

    results.append(
        check_row_count(
            raw,
            staging,
        )
    )

    # --------------------------------------------------------
    # FACT RECONCILIATION
    # --------------------------------------------------------

    financial_columns = (
        FACT_RECONCILIATION_COLUMNS.get(
            dataset_name,
            {},
        )
    )

    for source_column, canonical_column in (
        financial_columns.items()
    ):

        results.append(
            check_numeric_sum(
                raw=raw,
                staging=staging,
                source_column=source_column,
                canonical_column=canonical_column,
            )
        )

    # --------------------------------------------------------
    # DIMENSION PRIMARY KEY
    # --------------------------------------------------------

    contract = (
        contract_config
        .get("datasets", {})
        .get(dataset_name, {})
    )

    primary_key = contract.get(
        "primary_key",
        [],
    )

    if primary_key:

        results.extend(
            check_primary_key(
                staging=staging,
                primary_key=primary_key,
            )
        )

    return results


# ============================================================
# PRINT RESULTS
# ============================================================

def print_results(
    dataset_name: str,
    raw_path: Path,
    results: list[CheckResult],
) -> bool:

    print()
    print("=" * 100)
    print(f"DATASET : {dataset_name}")
    print(f"RAW     : {raw_path.name}")
    print("=" * 100)

    dataset_passed = True

    for result in results:

        print()
        print(
            f"[{result.status}] "
            f"{result.check}"
        )

        if result.raw_value is not None:
            print(
                f"  RAW       : "
                f"{result.raw_value}"
            )

        if result.staging_value is not None:
            print(
                f"  STAGING   : "
                f"{result.staging_value}"
            )

        if result.difference is not None:
            print(
                f"  DIFFERENCE: "
                f"{result.difference}"
            )

        print(
            f"  MESSAGE   : "
            f"{result.message}"
        )

        if result.status != "PASS":
            dataset_passed = False

    print()

    print(
        "RESULT  : "
        + (
            "PASS"
            if dataset_passed
            else "FAIL"
        )
    )

    return dataset_passed


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    print()
    print("=" * 100)
    print("WF1 STAGING RECONCILIATION V1")
    print("=" * 100)

    print(
        f"Raw      : {RAW_DIR}"
    )

    print(
        f"Staging  : {STAGING_DIR}"
    )

    try:

        mapping_config = load_yaml(
            MAPPING_FILE
        )

        contract_config = load_yaml(
            CONTRACT_FILE
        )

    except Exception as exc:

        print()
        print("CONFIG ERROR")
        print(str(exc))

        return 1

    raw_files = sorted(
        path
        for path in RAW_DIR.glob("*.csv")
        if not path.name.startswith("~$")
    )

    if not raw_files:

        print()
        print(
            "No RAW CSV files found."
        )

        return 1

    passed = 0
    failed = 0

    for raw_path in raw_files:

        try:

            dataset_name = identify_dataset(
                raw_path,
                mapping_config,
            )

            results = reconcile_dataset(
                raw_path=raw_path,
                dataset_name=dataset_name,
                mapping_config=mapping_config,
                contract_config=contract_config,
            )

            success = print_results(
                dataset_name=dataset_name,
                raw_path=raw_path,
                results=results,
            )

            if success:
                passed += 1
            else:
                failed += 1

        except Exception as exc:

            failed += 1

            print()
            print("=" * 100)
            print(
                f"FAILED: {raw_path.name}"
            )
            print("=" * 100)
            print(str(exc))

    print()
    print("=" * 100)
    print("RECONCILIATION SUMMARY")
    print("=" * 100)

    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Total  : {len(raw_files)}")

    print("=" * 100)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(
        main()
    )