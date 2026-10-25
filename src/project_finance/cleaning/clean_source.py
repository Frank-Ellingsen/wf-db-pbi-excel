from __future__ import annotations

import csv
import fnmatch
import re
import sys
import unicodedata
from datetime import datetime, timezone
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
# NAME NORMALIZATION
# ============================================================

def normalize_name(value: Any) -> str:
    """
    Normalize names for matching only.

    Examples:
        Årsbudsjett   -> arsbudsjett
        Avvik i %     -> avvik_i_pct
    """

    text = str(value).strip().lower()

    replacements = {
        "æ": "ae",
        "ø": "o",
        "å": "a",
        "%": "pct",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text,
    )

    text = re.sub(
        r"_+",
        "_",
        text,
    )

    return text.strip("_")


# ============================================================
# YAML
# ============================================================

def load_yaml(path: Path) -> dict:
    """
    Load YAML configuration.
    """

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
# FILE DISCOVERY
# ============================================================

def discover_files() -> list[Path]:
    """
    Find CSV source files.
    """

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sorted(
        file
        for file in RAW_DIR.glob("*.csv")
        if not file.name.startswith("~$")
    )


# ============================================================
# DATASET IDENTIFICATION
# ============================================================

def identify_dataset(
    path: Path,
    mapping_config: dict,
) -> str:
    """
    Identify dataset using file_patterns
    from column_mapping.yaml.
    """

    datasets = mapping_config.get(
        "datasets",
        {},
    )

    matches: list[str] = []

    for dataset_name, config in datasets.items():

        patterns = config.get(
            "file_patterns",
            [],
        )

        for pattern in patterns:

            if fnmatch.fnmatch(
                path.name.lower(),
                pattern.lower(),
            ):
                matches.append(dataset_name)
                break

    if len(matches) == 1:
        return matches[0]

    if len(matches) == 0:
        raise ValueError(
            "Unable to identify dataset type.\n"
            f"File: {path.name}"
        )

    raise ValueError(
        "Ambiguous dataset identification.\n"
        f"File: {path.name}\n"
        f"Matches: {matches}"
    )


# ============================================================
# ENCODING DETECTION
# ============================================================

def detect_encoding(path: Path) -> str:
    """
    Try common encodings.
    """

    encodings = (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin1",
    )

    for encoding in encodings:

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
        f"Unable to determine encoding: {path.name}"
    )


# ============================================================
# SEPARATOR DETECTION
# ============================================================

def detect_separator(
    path: Path,
    encoding: str,
) -> str:
    """
    Detect CSV delimiter.
    """

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

        candidates = {
            ",": sample.count(","),
            ";": sample.count(";"),
            "\t": sample.count("\t"),
            "|": sample.count("|"),
        }

        separator = max(
            candidates,
            key=candidates.get,
        )

        if candidates[separator] == 0:
            raise ValueError(
                f"No CSV separator detected: {path.name}"
            )

        return separator


# ============================================================
# STRUCTURE VALIDATION
# ============================================================

def validate_structure(
    path: Path,
    separator: str,
    encoding: str,
) -> None:
    """
    Enforce WF1 A1 tabular standard.
    """

    preview = pd.read_csv(
        path,
        sep=separator,
        encoding=encoding,
        header=None,
        nrows=5,
        dtype=str,
        keep_default_na=False,
    )

    if preview.empty:
        raise ValueError(
            "CSV file is empty."
        )

    first_row = [
        str(value).strip()
        for value in preview.iloc[0].tolist()
    ]

    total = len(first_row)

    populated = sum(
        bool(value)
        for value in first_row
    )

    coverage = (
        populated / total
        if total
        else 0
    )

    if not first_row or not first_row[0]:
        raise ValueError(
            "Table does not start correctly in A1."
        )

    if coverage < 0.80:
        raise ValueError(
            "First row is not a complete header.\n"
            f"Header coverage: {coverage:.1%}"
        )

    if any(
        not value
        for value in first_row
    ):
        raise ValueError(
            "Blank column header detected."
        )

    normalized = [
        normalize_name(value)
        for value in first_row
    ]

    if len(normalized) != len(set(normalized)):
        raise ValueError(
            "Duplicate column names detected."
        )


# ============================================================
# READ SOURCE
# ============================================================

def read_source(
    path: Path,
) -> tuple[pd.DataFrame, str, str]:
    """
    Read validated source CSV.
    """

    encoding = detect_encoding(path)

    separator = detect_separator(
        path,
        encoding,
    )

    validate_structure(
        path,
        separator,
        encoding,
    )

    df = pd.read_csv(
        path,
        sep=separator,
        encoding=encoding,
        header=0,
        low_memory=False,
    )

    return df, separator, encoding


# ============================================================
# MAPPING BUILDERS
# ============================================================

def build_column_mapping(
    dataset_config: dict,
) -> dict[str, str]:
    """
    Build:
        normalized source name -> canonical name
    """

    result: dict[str, str] = {}

    raw_mapping = dataset_config.get(
        "column_mapping",
        {},
    )

    for source_name, settings in raw_mapping.items():

        if isinstance(settings, dict):
            canonical = settings.get(
                "canonical"
            )
        else:
            canonical = settings

        if canonical:

            result[
                normalize_name(source_name)
            ] = str(canonical)

    return result


def build_drop_columns(
    dataset_config: dict,
) -> set[str]:
    """
    Return normalized source columns
    that must be removed.
    """

    raw_drop = dataset_config.get(
        "drop_columns",
        {},
    )

    if isinstance(raw_drop, dict):
        columns = raw_drop.keys()

    elif isinstance(raw_drop, list):
        columns = raw_drop

    else:
        columns = []

    return {
        normalize_name(column)
        for column in columns
    }


# ============================================================
# CONTRACT HELPERS
# ============================================================

def get_contract_columns(
    contract: dict,
) -> tuple[set[str], set[str]]:
    """
    Return required and optional canonical columns.
    """

    required = set(
        contract.get(
            "required_columns",
            {},
        ).keys()
    )

    optional = set(
        contract.get(
            "optional_columns",
            {},
        ).keys()
    )

    return required, optional


# ============================================================
# CLEAN / CANONICALIZE
# ============================================================

def canonicalize_dataframe(
    df: pd.DataFrame,
    dataset_config: dict,
    contract: dict,
) -> tuple[
    pd.DataFrame,
    list[str],
    list[str],
]:
    """
    Apply the WF1 canonical mapping.

    Steps:
    1. Remove configured DROP columns.
    2. Rename mapped source columns.
    3. Reject unmapped source columns.
    4. Verify required canonical fields.
    5. Return canonical DataFrame.
    """

    mapping = build_column_mapping(
        dataset_config
    )

    drop_columns = build_drop_columns(
        dataset_config
    )

    required, optional = get_contract_columns(
        contract
    )

    output = df.copy()

    columns_to_drop: list[str] = []
    rename_map: dict[str, str] = {}
    unknown_columns: list[str] = []

    for column in output.columns:

        normalized = normalize_name(
            column
        )

        # ----------------------------------------------------
        # DROP
        # ----------------------------------------------------

        if normalized in drop_columns:

            columns_to_drop.append(
                column
            )

            continue

        # ----------------------------------------------------
        # MAP
        # ----------------------------------------------------

        if normalized in mapping:

            rename_map[column] = (
                mapping[normalized]
            )

            continue

        # ----------------------------------------------------
        # ALREADY CANONICAL
        # ----------------------------------------------------

        if (
            normalized in required
            or normalized in optional
        ):

            rename_map[column] = normalized

            continue

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        unknown_columns.append(
            column
        )

    # --------------------------------------------------------
    # Unknown fields should not silently disappear
    # --------------------------------------------------------

    if unknown_columns:

        unknown_text = "\n".join(
            f"  - {column}"
            for column in unknown_columns
        )

        raise ValueError(
            "Unmapped columns detected:\n"
            f"{unknown_text}\n\n"
            "Update column_mapping.yaml before cleaning."
        )

    # --------------------------------------------------------
    # Drop derived/unwanted fields
    # --------------------------------------------------------

    if columns_to_drop:

        output = output.drop(
            columns=columns_to_drop
        )

    # --------------------------------------------------------
    # Rename
    # --------------------------------------------------------

    output = output.rename(
    columns=rename_map
)    # --------------------------------------------------------
    # Duplicate canonical names are dangerous
    # --------------------------------------------------------

    duplicate_columns = (
        output.columns[
            output.columns.duplicated()
        ]
        .tolist()
    )

    if duplicate_columns:

        raise ValueError(
            "Duplicate canonical columns after mapping:\n"
            + "\n".join(
                f"  - {column}"
                for column in duplicate_columns
            )
        )

    # --------------------------------------------------------
    # Required canonical fields
    # --------------------------------------------------------

    missing_required = sorted(
        required
        - set(output.columns)
    )

    if missing_required:

        raise ValueError(
            "Missing required canonical columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing_required
            )
        )

    return (
        output,
        columns_to_drop,
        list(rename_map.keys()),
    )


# ============================================================
# BASIC VALUE CLEANING
# ============================================================

def clean_string_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Basic non-destructive string cleanup.

    - Trim leading/trailing whitespace.
    - Convert empty strings to missing values.

    No business transformations occur here.
    """

    result = df.copy()

    string_columns = result.select_dtypes(
        include=[
            "object",
            "string",
        ]
    ).columns

    for column in string_columns:

        result[column] = (
            result[column]
            .map(
                lambda value:
                value.strip()
                if isinstance(value, str)
                else value
            )
        )

        result[column] = result[column].replace(
            "",
            pd.NA,
        )

    return result


# ============================================================
# METADATA
# ============================================================

def add_metadata(
    df: pd.DataFrame,
    dataset_name: str,
    source_file: str,
) -> pd.DataFrame:
    """
    Add technical lineage metadata.

    Business values remain untouched.
    """

    result = df.copy()

    result["_dataset"] = dataset_name
    result["_source_file"] = source_file

    result["_loaded_at_utc"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    return result


# ============================================================
# WRITE STAGING
# ============================================================

def write_staging(
    df: pd.DataFrame,
    dataset_name: str,
) -> Path:
    """
    Write canonical staging CSV.

    One staging file per logical dataset.
    """

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        STAGING_DIR
        / f"{dataset_name}.csv"
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    return output_path


# ============================================================
# PROCESS FILE
# ============================================================

def process_file(
    path: Path,
    mapping_config: dict,
    contracts_config: dict,
) -> bool:
    """
    Clean one raw source file.
    """

    print()
    print("=" * 100)
    print(f"PROCESSING: {path.name}")
    print("=" * 100)

    try:

        # ----------------------------------------------------
        # Identify dataset
        # ----------------------------------------------------

        dataset_name = identify_dataset(
            path,
            mapping_config,
        )

        print(
            f"Dataset        : {dataset_name}"
        )

        # ----------------------------------------------------
        # Get configs
        # ----------------------------------------------------

        dataset_configs = (
            mapping_config.get(
                "datasets",
                {},
            )
        )

        contracts = (
            contracts_config.get(
                "datasets",
                {},
            )
        )

        if dataset_name not in dataset_configs:

            raise ValueError(
                f"No mapping config for {dataset_name}"
            )

        if dataset_name not in contracts:

            raise ValueError(
                f"No dataset contract for {dataset_name}"
            )

        dataset_config = (
            dataset_configs[
                dataset_name
            ]
        )

        contract = contracts[
            dataset_name
        ]

        # ----------------------------------------------------
        # Read source
        # ----------------------------------------------------

        df, separator, encoding = (
            read_source(path)
        )

        rows_input = len(df)
        columns_input = len(
            df.columns
        )

        # ----------------------------------------------------
        # Canonicalize
        # ----------------------------------------------------

        cleaned, dropped, renamed = (
            canonicalize_dataframe(
                df=df,
                dataset_config=dataset_config,
                contract=contract,
            )
        )

        # ----------------------------------------------------
        # Basic string cleanup
        # ----------------------------------------------------

        cleaned = clean_string_columns(
            cleaned
        )

        # ----------------------------------------------------
        # Lineage metadata
        # ----------------------------------------------------

        cleaned = add_metadata(
            df=cleaned,
            dataset_name=dataset_name,
            source_file=path.name,
        )

        # ----------------------------------------------------
        # Write staging
        # ----------------------------------------------------

        output_path = write_staging(
            df=cleaned,
            dataset_name=dataset_name,
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        print(
            f"Encoding       : {encoding}"
        )

        print(
            f"Separator      : {repr(separator)}"
        )

        print(
            f"Rows input     : {rows_input:,}"
        )

        print(
            f"Rows output    : {len(cleaned):,}"
        )

        print(
            f"Columns input  : {columns_input}"
        )

        print(
            f"Columns output : {len(cleaned.columns)}"
        )

        print()

        print("Dropped columns:")

        if dropped:

            for column in dropped:
                print(
                    f"  X {column}"
                )

        else:
            print("  None")

        print()

        print(
            f"Output: {output_path}"
        )

        print("STATUS: PASS")

        return True

    except Exception as exc:

        print()
        print("STATUS: FAIL")
        print(str(exc))

        return False


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    """
    WF1 canonical cleaning entry point.
    """

    print()
    print("=" * 100)
    print("WF1 SOURCE CLEANER V1")
    print("=" * 100)

    print(
        f"Project root : {PROJECT_ROOT}"
    )

    print(
        f"Raw folder   : {RAW_DIR}"
    )

    print(
        f"Staging      : {STAGING_DIR}"
    )

    print(
        f"Mapping      : {MAPPING_FILE}"
    )

    print(
        f"Contracts    : {CONTRACT_FILE}"
    )

    try:

        mapping_config = load_yaml(
            MAPPING_FILE
        )

        contracts_config = load_yaml(
            CONTRACT_FILE
        )

    except Exception as exc:

        print()
        print("CONFIG ERROR")
        print(str(exc))

        return 1

    files = discover_files()

    if not files:

        print()
        print(
            "No CSV files found in data/raw."
        )

        return 0

    print()
    print(
        f"Files detected: {len(files)}"
    )

    for path in files:
        print(
            f"  - {path.name}"
        )

    passed = 0
    failed = 0

    for path in files:

        success = process_file(
            path=path,
            mapping_config=mapping_config,
            contracts_config=contracts_config,
        )

        if success:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 100)
    print("CLEANING SUMMARY")
    print("=" * 100)

    print(
        f"Passed : {passed}"
    )

    print(
        f"Failed : {failed}"
    )

    print(
        f"Total  : {len(files)}"
    )

    print("=" * 100)

    return 1 if failed else 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )