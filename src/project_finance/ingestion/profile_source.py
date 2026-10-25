from __future__ import annotations

import csv
import fnmatch
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

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
# NORMALIZATION
# ============================================================

def normalize_name(value: Any) -> str:

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
# DATASET IDENTIFICATION
# ============================================================

def identify_dataset(
    path: Path,
    mapping_config: dict,
) -> str | None:

    datasets = mapping_config.get(
        "datasets",
        {},
    )

    matches = []

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

    if len(matches) > 1:

        raise ValueError(
            "Dataset identification is ambiguous.\n"
            f"File: {path.name}\n"
            f"Matches: {matches}"
        )

    return None


# ============================================================
# FILE DISCOVERY
# ============================================================

def discover_files() -> list[Path]:

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
# ENCODING
# ============================================================

def detect_encoding(path: Path) -> str:

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
# SEPARATOR
# ============================================================

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
            "Table does not start in A1."
        )

    if coverage < 0.80:

        raise ValueError(
            "First row does not look like a "
            "complete header.\n"
            f"Header coverage: {coverage:.1%}"
        )

    blank_headers = [
        index + 1
        for index, value in enumerate(first_row)
        if not value
    ]

    if blank_headers:

        raise ValueError(
            "Blank header columns detected:\n"
            f"{blank_headers}"
        )

    normalized = [
        normalize_name(value)
        for value in first_row
    ]

    if len(normalized) != len(set(normalized)):

        duplicates = sorted({
            value
            for value in normalized
            if normalized.count(value) > 1
        })

        raise ValueError(
            "Duplicate headers detected:\n"
            + ", ".join(duplicates)
        )


# ============================================================
# READ CSV
# ============================================================

def read_csv(
    path: Path,
) -> tuple[pd.DataFrame, str, str]:

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
        low_memory=False,
    )

    return (
        df,
        separator,
        encoding,
    )


# ============================================================
# MAPPING
# ============================================================

def build_mapping(
    dataset_config: dict,
) -> dict[str, str]:

    result = {}

    raw_mapping = dataset_config.get(
        "column_mapping",
        {},
    )

    for source, settings in raw_mapping.items():

        if isinstance(settings, dict):

            canonical = settings.get(
                "canonical"
            )

        else:
            canonical = settings

        if canonical:

            result[
                normalize_name(source)
            ] = str(canonical)

    return result


def build_drop_columns(
    dataset_config: dict,
) -> set[str]:

    drop_config = dataset_config.get(
        "drop_columns",
        {},
    )

    if isinstance(drop_config, dict):

        source_columns = drop_config.keys()

    elif isinstance(drop_config, list):

        source_columns = drop_config

    else:

        source_columns = []

    return {
        normalize_name(value)
        for value in source_columns
    }


# ============================================================
# CONTRACT
# ============================================================

def get_contract_columns(
    contract: dict,
) -> tuple[
    set[str],
    set[str],
]:

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
# CLASSIFICATION
# ============================================================

def classify_column(
    source_column: str,
    mapping: dict[str, str],
    drops: set[str],
    required: set[str],
    optional: set[str],
) -> tuple[str, str]:

    normalized = normalize_name(
        source_column
    )

    if normalized in drops:

        return (
            "DROP",
            "-",
        )

    if normalized in mapping:

        canonical = mapping[
            normalized
        ]

        if canonical in required:

            return (
                "REQUIRED",
                canonical,
            )

        if canonical in optional:

            return "OPTIONAL", canonical
        

        return (
            "MAPPED",
            canonical,
        )

    return (
        "UNKNOWN",
        "-",
    )


# ============================================================
# EXAMPLE VALUES
# ============================================================

def example_values(
    series: pd.Series,
) -> str:

    values = (
        series
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(3)
        .tolist()
    )

    result = []

    for value in values:

        if len(value) > 30:
            value = value[:27] + "..."

        result.append(value)

    if not result:
        return "<no values>"

    return " | ".join(result)


# ============================================================
# PROFILE
# ============================================================

def profile_dataset(
    path: Path,
    df: pd.DataFrame,
    dataset_name: str,
    dataset_mapping: dict,
    contract: dict,
    encoding: str,
    separator: str,
) -> bool:

    mapping = build_mapping(
        dataset_mapping
    )

    drops = build_drop_columns(
        dataset_mapping
    )

    required, optional = (
        get_contract_columns(
            contract
        )
    )

    detected_canonical = set()

    profile_rows = []

    for source_column in df.columns:

        status, canonical = classify_column(
            source_column=str(source_column),
            mapping=mapping,
            drops=drops,
            required=required,
            optional=optional,
        )

        if canonical != "-":

            detected_canonical.add(
                canonical
            )

        series = df[source_column]

        null_pct = (
            series.isna().mean() * 100
            if len(series)
            else 0
        )

        profile_rows.append(
            {
                "source_column": source_column,
                "canonical": canonical,
                "status": status,
                "dtype": str(series.dtype),
                "null_pct": round(
                    null_pct,
                    2,
                ),
                "unique": int(
                    series.nunique(
                        dropna=True
                    )
                ),
                "examples": example_values(
                    series
                ),
            }
        )

    profile = pd.DataFrame(
        profile_rows
    )

    missing_required = sorted(
        required
        - detected_canonical
    )

    unknown_columns = profile.loc[
        profile["status"] == "UNKNOWN",
        "source_column",
    ].tolist()

    drop_columns = profile.loc[
        profile["status"] == "DROP",
        "source_column",
    ].tolist()

    print()
    print("=" * 100)

    print(
        f"FILE         : {path.name}"
    )

    print(
        f"DATASET      : {dataset_name}"
    )

    print(
        f"DATASET TYPE : "
        f"{contract.get('dataset_type', 'unknown')}"
    )

    print(
        f"ROWS         : {len(df):,}"
    )

    print(
        f"COLUMNS      : {len(df.columns):,}"
    )

    print(
        f"ENCODING     : {encoding}"
    )

    print(
        f"SEPARATOR    : {repr(separator)}"
    )

    print("=" * 100)

    print()
    print("COLUMN PROFILE")
    print("-" * 100)

    with pd.option_context(
        "display.max_rows",
        None,
        "display.max_columns",
        None,
        "display.width",
        220,
        "display.max_colwidth",
        40,
    ):

        print(
            profile.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # CONTRACT
    # --------------------------------------------------------

    print()
    print("DATA CONTRACT CHECK")
    print("-" * 100)

    if missing_required:

        print("FAIL")

        print(
            "Missing required columns:"
        )

        for column in missing_required:

            print(
                f"  - {column}"
            )

        contract_pass = False

    else:

        print(
            "PASS - All required "
            "canonical columns detected."
        )

        contract_pass = True

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    print()
    print("UNKNOWN COLUMNS")
    print("-" * 100)

    if unknown_columns:

        for column in unknown_columns:

            print(
                f"  ? {column}"
            )

    else:

        print("None")

    # --------------------------------------------------------
    # DROP
    # --------------------------------------------------------

    print()
    print("DERIVED / DROP COLUMNS")
    print("-" * 100)

    if drop_columns:

        for column in drop_columns:

            print(
                f"  X {column}"
            )

    else:

        print("None")

    return contract_pass


# ============================================================
# PROCESS FILE
# ============================================================

def process_file(
    path: Path,
    mapping_config: dict,
    contracts_config: dict,
) -> bool:

    try:

        dataset_name = identify_dataset(
            path,
            mapping_config,
        )

        if dataset_name is None:

            raise ValueError(
                "Unable to identify dataset type.\n"
                f"File: {path.name}"
            )

        mappings = mapping_config[
            "datasets"
        ]

        contracts = contracts_config[
            "datasets"
        ]

        if dataset_name not in contracts:

            raise ValueError(
                "No dataset contract found for:\n"
                f"{dataset_name}"
            )

        dataset_mapping = mappings[
            dataset_name
        ]

        contract = contracts[
            dataset_name
        ]

        df, separator, encoding = (
            read_csv(path)
        )

        return profile_dataset(
            path=path,
            df=df,
            dataset_name=dataset_name,
            dataset_mapping=dataset_mapping,
            contract=contract,
            encoding=encoding,
            separator=separator,
        )

    except Exception as exc:

        print()
        print("=" * 100)

        print(
            f"FILE FAILED: {path.name}"
        )

        print("=" * 100)

        print(str(exc))

        print("=" * 100)

        return False


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    print()

    print("=" * 100)

    print(
        "WF1 SOURCE DATA PROFILER V2"
    )

    print("=" * 100)

    print(
        f"Project root : {PROJECT_ROOT}"
    )

    print(
        f"Raw folder   : {RAW_DIR}"
    )

    print(
        f"Mapping file : {MAPPING_FILE}"
    )

    print(
        f"Contract file: {CONTRACT_FILE}"
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
            "No CSV files found."
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

        if process_file(
            path,
            mapping_config,
            contracts_config,
        ):

            passed += 1

        else:

            failed += 1

    print()
    print("=" * 100)

    print(
        "PROFILE SUMMARY"
    )

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


if __name__ == "__main__":

    sys.exit(
        main()
    )